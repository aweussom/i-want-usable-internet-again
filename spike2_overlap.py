#!/usr/bin/env python3
"""spike 2: does the corroborator earn its keep?

Brave and SearXNG side by side over stratified real queries, measuring
canonicalized-URL overlap. ~95% overlap -> SearXNG tells us nothing and
the verifier idea dies; ~30% -> the disagreement IS the product.
Stratified because one average over mixed query types misrepresents all
of them — the news stratum is where the provenance vector must earn out.

  python spike2_overlap.py
"""
import sys
import time

import requests

from torehund import brave_search, canonicalize, cfg_key, load_keys

STRATA = {
    "tech": [
        "python asyncio task cancellation best practice",
        "openvino npu driver linux install",
        "intel arc b60 24gb price availability",
        "flask server sent events keepalive",
        "transformers trust remote code importerror losskwargs",
        "docker compose healthcheck depends_on",
        "powershell 7 ternary operator",
        "sqlite wal mode concurrent readers",
        "rust vs go for cli tools",
        "git worktree vs clone",
    ],
    "news": [
        "statsbudsjettet 2027 skatteendringer",
        "nordnorge kraftpriser vinter",
        "svalbard turisme nye regler",
        "bompenger elbil endringer 2026",
        "norsk presse ntb eierskap",
        "eu ai act enforcement start",
        "intel foundry latest news",
        "norges bank rentebeslutning",
        "helseplattformen status midt-norge",
        "equinor melkøya elektrifisering",
    ],
    "academic": [
        "mixture of experts expert offloading inference",
        "retrieval augmented generation evaluation benchmark",
        "kv cache compression large language models",
        "near duplicate detection shingling minhash",
        "press publishers right article 15 copyright directive",
        "chain of custody provenance web information",
        "wire service news homogenization study",
        "int4 quantization accuracy degradation llm",
        "search engine result overlap study",
        "source criticism media literacy education",
    ],
}
TOP_N = 10   # compare Brave's top-N against SearXNG's full result set


def searxng_search(base_url, query):
    r = requests.get(f"{base_url.rstrip('/')}/search",
                     params={"q": query, "format": "json"}, timeout=30)
    r.raise_for_status()
    d = r.json()
    return ([h["url"] for h in d.get("results", []) if h.get("url")],
            [e for e, _reason in d.get("unresponsive_engines", [])])


def main():
    cfg = load_keys()
    brave_key = cfg_key(cfg, "brave")
    sx_url = cfg["searxng"].get("base_url", "").strip()
    if not (brave_key and sx_url):
        sys.exit("need both [brave] api_key and [searxng] base_url")

    grand = []
    for stratum, queries in STRATA.items():
        rows = []
        for q in queries:
            try:
                b = [canonicalize(h["url"]) for h in brave_search(q, brave_key, TOP_N)]
                sx_raw, dead = searxng_search(sx_url, q)
                sx = {canonicalize(u) for u in sx_raw}
            except Exception as e:
                print(f"  SKIP {q!r}: {e}")
                continue
            bset = set(b)
            corroborated = len(bset & sx)
            rows.append((q, len(bset), corroborated, len(sx - bset), dead))
            time.sleep(1.2)   # Brave free tier is rate-limited; be polite
        print(f"\n== {stratum} ==")
        print(f"{'corr':>5} {'brave':>5} {'sx-only':>7}  query")
        for q, nb, corr, sx_only, dead in rows:
            note = f"  [dead: {','.join(dead)}]" if dead else ""
            print(f"{corr:>5} {nb:>5} {sx_only:>7}  {q[:52]}{note}")
        if rows:
            pct = 100 * sum(c for _, _, c, _, _ in rows) / max(1, sum(n for _, n, _, _, _ in rows))
            uniq = sum(u for _, _, _, u, _ in rows) / len(rows)
            grand.append((stratum, pct, uniq))

    print("\n== verdict material ==")
    for stratum, pct, uniq in grand:
        print(f"  {stratum:>9}: {pct:4.0f}% of Brave's top-{TOP_N} corroborated by SearXNG; "
              f"avg {uniq:.0f} SearXNG-only URLs/query")
    print("\n(high corroboration + many sx-only URLs = SearXNG adds signal both ways;")
    print(" ~95% corroboration + few sx-only = it's telling us nothing Brave didn't.)")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
