#!/usr/bin/env python3
"""sporhund.py — spike 1: one question end-to-end, no UI.

decompose (LLM, tiny prompt, JSON out) -> Brave search -> canonicalize +
merge with provenance -> fetch + extract -> one synthesis pass with
citations -> answer AND the results list it came from.

The loop lives here in python; the model gets one small question per step.
Backends come from keys.ini (gitignored) — empty value = backend off.

  python sporhund.py "your question"
  python sporhund.py --model gpt-oss:120b --read 4 "your question"
"""
import argparse
import configparser
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
USER_AGENT = "sporhund/0.001 (+https://github.com/aweussom/i-want-usable-internet-again)"
# Tracking params whose removal never changes the page served. Sloppy
# canonicalization UNDERCOUNTS agreement (PLAN.md, merge section), so only
# provably-inert params go here.
TRACKING_PARAMS = ("utm_", "fbclid", "gclid", "msclkid", "mc_cid", "mc_eid", "ref_src")
THINK_RE = re.compile(r"^\s*<think>.*?</think>\s*", re.DOTALL)


def load_keys():
    ini = Path(__file__).parent / "keys.ini"
    if not ini.exists():
        sys.exit("keys.ini not found — copy keys.ini.template and fill it in.")
    cfg = configparser.ConfigParser()
    cfg.read(ini, encoding="utf-8")
    return cfg


def cfg_key(cfg, section):
    """Sections use api_key or key interchangeably; empty/absent = off."""
    if section not in cfg:
        return ""
    return (cfg[section].get("api_key", "") or cfg[section].get("key", "")).strip()


def llm_chat(base_url, api_key, model, messages, max_tokens=8192):
    """max_tokens is shared between reasoning and answer on thinking models
    (Ollama puts reasoning in its own field but it eats the same budget
    FIRST) — starve it and content comes back empty. Be generous."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = {"model": model, "messages": messages, "max_tokens": max_tokens}
    r = requests.post(f"{base_url.rstrip('/')}/chat/completions",
                      json=body, headers=headers, timeout=300)
    if r.status_code == 400 and "max_completion_tokens" in r.text:
        # OpenAI reasoning-family models renamed the knob.
        body["max_completion_tokens"] = body.pop("max_tokens")
        r = requests.post(f"{base_url.rstrip('/')}/chat/completions",
                          json=body, headers=headers, timeout=300)
    r.raise_for_status()
    choice = r.json()["choices"][0]
    text = THINK_RE.sub("", choice["message"].get("content") or "").strip()
    if not text:
        raise RuntimeError(
            f"empty content (finish_reason={choice.get('finish_reason')}) — "
            f"likely reasoning ate the whole max_tokens budget")
    return text


def decompose(question, n, llm, locale=""):
    """Question -> n search queries. The model is a query compiler, nothing
    more; any parse failure falls back to searching the question verbatim."""
    prompt = (
        f"Compile {n} web search queries that together would answer the "
        f"question below. Different angles, keyword-style, no operators.\n")
    if locale:
        # Round 1 of the Perplexity face-off taught this: every backend
        # answered from US retail because every query was English. Local
        # availability lives behind local-language queries — and behind
        # site:.<tld>, the veteran manual fix for locale-blind ranking
        # (the one operator exception to the no-operators rule).
        prompt += (f"The asker is in country '{locale}'. If local "
                   f"availability, prices, or news could matter, write at "
                   f"least one query in that country's language, and you "
                   f"may add site:.{locale} to that one query only.\n")
    prompt += (f"Question: {question}\n"
               f'Reply with ONLY a JSON array of {n} strings.')
    try:
        text = llm([{"role": "user", "content": prompt}], max_tokens=2000)
        start, end = text.find("["), text.rfind("]")
        queries = json.loads(text[start:end + 1])
        queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
        if queries:
            return queries[:n]
    except Exception as e:
        print(f"  decompose failed ({e}) — searching the question verbatim")
    return [question]


def brave_search(query, key, count, country=""):
    params = {"q": query, "count": count}
    if country:
        params["country"] = country
    r = requests.get(
        BRAVE_ENDPOINT, params=params,
        headers={"X-Subscription-Token": key, "Accept": "application/json"},
        timeout=20)
    r.raise_for_status()
    hits = r.json().get("web", {}).get("results", [])
    return [{"url": h.get("url", ""), "title": h.get("title", ""),
             "snippet": h.get("description", "")} for h in hits if h.get("url")]


def canonicalize(url):
    p = urlparse(url)
    params = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
              if not any(k.lower().startswith(t) for t in TRACKING_PARAMS)]
    return urlunparse((
        "https", p.netloc.lower(), p.path.rstrip("/") or "/",
        p.params, urlencode(params), ""))


def merge(per_query_results):
    """Union, never rank. Each URL carries a provenance vector: which
    queries found it, at what rank."""
    seen = {}
    for qi, results in enumerate(per_query_results):
        for rank, hit in enumerate(results, start=1):
            canon = canonicalize(hit["url"])
            entry = seen.setdefault(canon, {**hit, "found_by": []})
            entry["found_by"].append((qi, rank))
    return list(seen.values())


def fetch_extract(url, max_chars):
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    r.raise_for_status()
    html = r.text
    try:
        import trafilatura
        text = trafilatura.extract(html) or ""
    except ImportError:
        text = re.sub(r"(?is)<(script|style|nav|header|footer).*?</\1>", " ", html)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
    return text.strip()[:max_chars]


def synthesize(question, sources, llm):
    numbered = "\n\n".join(
        f"[{i}] {s['title']}\n{s['url']}\n{s['text']}"
        for i, s in enumerate(sources, start=1))
    prompt = (
        "Answer the question using ONLY the numbered sources below. Cite "
        "every claim as [n]. If the sources disagree or leave a gap, say so "
        "explicitly — a stated gap beats a guess. Be concise.\n\n"
        f"Question: {question}\n\nSources:\n{numbered}")
    return llm([{"role": "user", "content": prompt}])


def crosscheck(question, our_answer, reader_llm, judge_llm):
    """Borrowed reader (PLAN.md item 4): an independent model answers the
    same question BLIND — it never sees our sources or answer, so its
    agreement is corroboration and its disagreement is a dig-here marker,
    never ground truth."""
    reader_answer = reader_llm([{"role": "user", "content": question}])
    prompt = (
        "Two independent answers to the same question. A is built from live "
        "web retrieval with citations; B is a separate model answering from "
        "its own knowledge. Compare them and report, tersely:\n"
        "1. AGREE: claims both make.\n"
        "2. DISAGREE: claims where they conflict (quote both sides).\n"
        "3. B-ONLY: things B adds that A lacks (possibly stale — B has a "
        "training cutoff; A searched today).\n"
        "4. DIG: what to search next to settle the disagreements.\n\n"
        f"Question: {question}\n\n--- A (retrieval) ---\n{our_answer}\n\n"
        f"--- B (reader) ---\n{reader_answer}")
    return judge_llm([{"role": "user", "content": prompt}])


def main():
    ap = argparse.ArgumentParser(description="spike 1: one question end-to-end")
    ap.add_argument("question")
    ap.add_argument("--queries", type=int, default=3)
    ap.add_argument("--per-query", type=int, default=5)
    ap.add_argument("--read", type=int, default=6, help="pages to fetch+read")
    ap.add_argument("--page-chars", type=int, default=5000)
    ap.add_argument("--model", default=None, help="synthesis model override")
    ap.add_argument("--no-crosscheck", action="store_true",
                    help="skip the borrowed-reader comparison")
    args = ap.parse_args()

    cfg = load_keys()
    brave_key = cfg_key(cfg, "brave")
    if not brave_key:
        sys.exit("[brave] api_key is empty — the front door is not optional.")
    oc = cfg["ollama_cloud"]
    # Two models, mirroring the eventual NPU/GPU split: a small fast one for
    # query compilation, a big one for synthesis. Defaults avoid heavy
    # thinking models — their reasoning shares (and can exhaust) max_tokens.
    model = args.model or oc.get("model", "mistral-large-3:675b")
    decompose_model = oc.get("decompose_model", "gemma4:31b")

    def make_llm(m):
        def call(messages, max_tokens=8192):
            return llm_chat(oc["base_url"], cfg_key(cfg, "ollama_cloud"),
                            m, messages, max_tokens)
        return call

    country = cfg["brave"].get("country", "").strip()

    t0 = time.perf_counter()
    queries = decompose(args.question, args.queries, make_llm(decompose_model),
                        locale=country)
    print(f"queries ({time.perf_counter()-t0:.1f}s):")
    for q in queries:
        print(f"  - {q}")

    t1 = time.perf_counter()
    per_query = []
    for q in queries:
        try:
            per_query.append(brave_search(q, brave_key, args.per_query, country))
        except Exception as e:
            print(f"  brave failed for {q!r}: {e}")
            per_query.append([])
    merged = merge(per_query)
    # Reading order: corroboration first (found by most queries), then best
    # single rank. This is triage, not ranking-for-the-user.
    merged.sort(key=lambda e: (-len(e["found_by"]), min(r for _, r in e["found_by"])))
    print(f"search: {sum(map(len, per_query))} hits -> {len(merged)} unique "
          f"({time.perf_counter()-t1:.1f}s)")

    t2 = time.perf_counter()
    sources = []
    for entry in merged:
        if len(sources) >= args.read:
            break
        try:
            text = fetch_extract(entry["url"], args.page_chars)
        except Exception as e:
            print(f"  fetch failed {entry['url']}: {e}")
            continue
        if len(text) < 200:   # cookie walls, JS shells: nothing to read
            continue
        sources.append({**entry, "text": text})
    print(f"read {len(sources)} pages ({time.perf_counter()-t2:.1f}s)")
    if not sources:
        sys.exit("nothing readable was retrieved — no answer to give.")

    t3 = time.perf_counter()
    answer = synthesize(args.question, sources, make_llm(model))
    print(f"synthesis: {model} ({time.perf_counter()-t3:.1f}s)\n")
    print("=" * 72)
    print(answer)
    print("=" * 72)
    print("\nSources (what was actually retrieved and read):")
    for i, s in enumerate(sources, start=1):
        prov = ", ".join(f"q{qi+1}#r{rank}" for qi, rank in s["found_by"])
        print(f"  [{i}] {s['title']}\n      {s['url']}\n      found by: {prov}")

    reader_key = cfg_key(cfg, "openai")
    if reader_key and not args.no_crosscheck:
        t4 = time.perf_counter()
        reader_model = cfg["openai"].get("model", "gpt-5.6-luna")
        reader_url = cfg["openai"].get("base_url", "https://api.openai.com/v1")
        def reader(messages, max_tokens=8192):
            return llm_chat(reader_url, reader_key, reader_model,
                            messages, max_tokens)
        try:
            report = crosscheck(args.question, answer, reader, make_llm(model))
            print(f"\nCross-check vs {reader_model} "
                  f"({time.perf_counter()-t4:.1f}s) — disagreement is a "
                  f"dig-here marker, not a verdict:")
            print(report)
        except Exception as e:
            print(f"\ncross-check failed (continuing without): {e}")
    print(f"\ntotal {time.perf_counter()-t0:.1f}s")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
