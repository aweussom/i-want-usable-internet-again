# i-want-usable-internet-again — plan

*Named 2026-08-13: the repo states the grievance, the tool inside is
`torehund.py` — Tore Hund (felled a saint-king) × "Tore på sporet"
(lineage tracing as a TV format) × sporhund (what it is). "Tore Hund på
sporet" is the product-name front-runner if this ever ships; torehund.no
is the domain to check at Norid. (Earlier working names: intheknow.com —
taken, promised the wrong thing; sporhund.py — outpunned same day.
sporhund.no taken; urkilde.no had no A record, kept as backup.)*

## Why

Internet search is broken — SEO and ads won the ranking war, so finding
actual information via a results page is a chore. Perplexity got popular
by fixing this with a simple inversion: **stop ranking, start reading**.
An LLM fetches results, reads them, and answers with citations. Ranking
was defeated by adversaries; reading is much harder to fake.

The personal version, which is the actual spec: **verification fatigue**.
Tired of tracing every claim by hand, the rational fallback is to mentally
mark *everything* as spam/phishing — a defensive prior that is itself
lossy, because it costs the true positives too. So this is a
**verification prosthetic**, not a better answer engine: it transfers the
tedium — who else says this, independently? does a primary document exist?
is this fourteen sources or one wire story wearing fourteen hats? — and
hands back a pre-traced lineage for judgment that never ran out. The
energy did. (Corollary: by this framing the news-lineage mode is the core
product and general search is the side feature, not the other way around.)

This project is that inversion, run from home: searches instigated by a
**local** LLM that branches out, collects, reads, and presents. The
question — and the conclusions — stay on hardware we own. Which is also
forced by the framing above: a verification prosthetic you would have to
*verify* is a contradiction. The only agent exempt from the spam-prior is
one whose loop you can read.

Personal arc, for the record: ISP in 1996, AllTheWeb/FAST from December
1999. The 1999 job was indexing the whole web so one query could find one
page. This thing sends one question out as five, and the only index that
matters is the one forming in the conductor's context window.

## Architecture (as currently imagined)

**Local conductor, one clean retrieval API, local reading loop, borrowed
readers when free.**

1. **Conductor (local LLM, served by NoLlama).** Takes the user's
   question. Decomposes it into sub-questions. Formulates *better search
   queries than the user would* — that's a core thesis: the LLM is a
   query compiler. Runs the loop: search → fetch → read → notice what's
   missing → reformulate → search again. One-shot search-then-summarize
   (Perplexica et al.) is the thin version; the iterative loop is where
   "research" lives.
2. **Retrieval: Brave is the front door, SearXNG runs in parallel as
   corroborator.** Live results — always fresher than any LLM's training
   data. The LLM's memory is for knowing *how* to search, never *what's
   true this week*.
   - **Brave (front door).** Independent index (Cliqz/Tailcat lineage —
     the "own index" school, FAST's spiritual heir). One HTTP client,
     cheap per query, free tier exists. This is the path that must be
     fast and must not fail: the answer is constructible from Brave
     alone. Cheap fan-out also tolerates mediocre ranking, because
     reformulation compensates — which is precisely why it's the front
     door and not the expensive-precise backend.
   - **SearXNG (parallel, fail-open).** Self-hosted fan-out over 274
     engine adapters, 83 on by default — Mojeek, Marginalia, Wikipedia,
     plus the specialist corpora (OpenAlex, Crossref, PubMed, arXiv,
     Semantic Scholar; Stack Overflow, GitHub, Codeberg) reachable via
     `categories=`. Fired at the same time as Brave, never before it and
     never blocking it: per-engine `timeout` set so its answer lands
     inside Brave's latency budget, and whatever arrives late is simply
     absent from the merge. A degraded or dead instance costs a
     confidence annotation, not an answer. Note `search.formats` defaults
     to `html` only — JSON is a 403 until enabled.
   - **What SearXNG is for: corroboration and reputation, not recall.**
     Overlap between two backends that share no ranking function is a
     ranking-independent consensus signal. A URL surfaced by Brave *and*
     three independent engines is not the same object as one surfaced by
     Google alone; a domain absent from the small-web and academic
     corpora is a chaff signal for triage. Claim-level verification
     against the specialist corpora (post-synthesis, per citation) is the
     stronger version, and comes later — it needs citations worth
     checking first.
   - **Kagi**: metasearch + own small-web index (Teclis). Pricier per
     query, sells ranking quality and ad-hostility. Shape: fewer queries
     that must be good — LLM query-narrowing raises the value of each
     *expensive* query, which is the Kagi pairing. Deferred, not
     rejected: it ships as a SearXNG engine and `api_key`/`base_url` are
     per-engine settings, so adding it later is config rather than
     architecture. Verify whether the shipped `brave`/`kagi` engines use
     the paid APIs or scrape the HTML front ends. Verify current
     pricing/free tiers before committing — numbers above are from
     memory.
3. **Reading loop (local).** Fetch pages, extract (trafilatura-class
   tooling), let the model discard chaff. The search provider learns what
   we asked; nobody learns what we read or concluded.
4. **Borrowed readers (optional): free LLM API tiers.** Gemini free tier,
   Groq, Mistral, Cerebras, OpenRouter free models — web-connected ones
   are search engines that already did the reading. Fan sub-questions out,
   treat the answers as *sources to reconcile*, not truth.
   **Cross-provider disagreement is signal** — where two free readers
   differ is exactly where the conductor digs next. (Green lane ONLY —
   see TODONT.md before anyone suggests puppeteering logged-in web
   sessions.)

### The merge (where the signal is actually made)

Do **not** collapse the two result sets into one ranked list. Ranking is
the thing this project exists to stop doing; re-imposing a scalar score in
the merge step smuggles it back in one layer down. Union the URLs and give
each one a **provenance vector** instead: which backend found it, which
engines within SearXNG (it returns `engines` and `positions` per result),
what rank Brave gave it. That vector is what the triage model scores, and
what the results list shows the user.

Canonicalize before comparing — trailing slashes, `utm_*`, AMP variants,
mobile subdomains, redirect chains. Sloppy normalization silently
*undercounts* agreement, which corrupts the one output the merge exists to
produce.

### News is a different problem: independent origins, not mentions

For news, the merge's premise inverts. Fourteen outlets carrying a story is
usually **one NTB item copied fourteen times** — *oppgulp*, regurgitation —
so naive overlap counting scores pure repetition as maximal corroboration.
Confidently wrong, in exactly the way the provenance vector exists to
prevent. News therefore needs its own mode, whose unit of count is the
**independent origin**, not the mention. (This is also where the frontier
assistants fail: they will cite five outlets that are one wire story and
call it consensus.)

Backtracking is tractable, and unusually so in Norway:

- **Wire credit is often explicit** — "(NTB)", Reuters/AP/AFP credit lines.
  Much oppgulp self-identifies; detect it and collapse the cluster to one
  origin. High precision, nearly free.
- **The crediting norm is a citation graph.** "skriver VG", "som DN først
  omtalte", "ifølge Aftenposten" — Norwegian press ethics make this
  convention strong, and those phrases are edges a small model extracts
  reliably. A bigger asset here than in most media markets.
- **Near-duplicate clustering** (shingling or embeddings over article text)
  catches the oppgulp that *doesn't* credit. Local, cheap, the workhorse.
- **Timestamps are a tiebreaker only.** Republication rewrites them, CMSes
  lie, "oppdatert" muddies it. Never the primary signal.

The payoff is where the backtrack *terminates*: not the first newspaper but
the primary document — press release, SSB table, Brønnøysund filing, court
decision, police log, Stortinget paper, the actual study behind "forskning
viser". Same specialist-corpora machinery as item 2, pointed at registries
instead of journals.

Device fit: near-dup clustering and citation-edge extraction are NPU work;
synthesising the graph is the GPU pass.

**Provenance, not veracity — and say so.** A "realtime Faktisk.no" is the
wrong promise (see TODONT.md). The deliverable is a lineage claim, which is
auditable and often devastating on its own: *"traces to a single
anonymously-sourced story in one outlet, repeated 14 times, no primary
document found."*

Two limits to design around: Norwegian news is heavily paywalled, and
perversely the free wire copies are reachable while the originating scoop
behind VG+/DN is not — the backtrack will often die one hop short. And in
the EEA, systematic extraction of news snippets carries a
press-publishers'-right dimension (copyright directive art. 15) that
general web reading does not. Irrelevant for personal use; real if this
ships.

Prior art worth reading before building: **Churnalism.com** (Media
Standards Trust, ~2011) diffed articles against press releases and showed
the copy-paste percentage. It worked, and wasn't sustained. What's new here
is doing it at query time with a model in the loop.

### Output: an answer, and the results list it came from

The synthesis pass emits both, and the pairing is the honest one: the
answer is generated and can be wrong, while the results list is what was
actually retrieved and read, so the user can go around us entirely. It
also gives synthesis somewhere to degrade *to* — low confidence produces a
list with reading notes instead of a confident assertion.

The list is where provenance becomes visible: "Brave + 3 independent
engines, cited in OpenAlex" versus "Google only, no primary source". That
turns corroboration into something the user can judge, rather than a hidden
confidence number they have to trust.

### Device routing (the NoLlama-shaped part)

Branching is latency-bound and dumb; synthesis is quality-bound and slow.
- **NPU, small model**: query decomposition, query compilation, "is this
  page worth reading?" triage.
- **GPU (B60-class), big model**: the 262k-context synthesis pass with
  citations — a SERP's worth of fetched pages is the same workload as a
  whole novel.
- NoLlama already provides: dual-device routing, tool calling (search/
  fetch/read are the tools), prefix caching (the fixed agent prompt +
  tool schemas hit ~47× faster on repeat turns — a research loop calls
  the model dozens of times per question). Two footnotes from the
  2026-08-13 review: prefix caching is GPU/CPU-only (no CB backend on
  NPU), so keep the conductor prompt tiny rather than counting on cache;
  and tool calling is deliberately NPU-excluded — which is fine, because
  the loop lives in *our* Python (one tiny prompt per step, tight JSON
  back), not in the model.
- KV arithmetic caps the synthesis pass: ~96 KB/token for a 30B-class
  model means 262k tokens ≈ 24 GB of KV — a whole B60 before weights.
  Design synthesis as map-reduce (per-source reading notes small, final
  pass over notes), not one heroic full-context call.

### Dev harness (not the shipped path)

While the loop is being built, the synthesis backend can be whatever is
convenient: Ollama Cloud (already paid for) or the RTX 5090 box
(secondreader) — an OpenAI-compatible endpoint is an OpenAI-compatible
endpoint. Ledger note, so this never goes quietly: cloud dev is fine for
the *harness*; the shipped default stays local, because the privacy
ledger is the product.

## First consumer: Fuckfeed (i-want-my-facebook-back)

The feed is where unverified claims actually reach a person, and Fuckfeed
already solves the half torehund can't: extracting them (its `linkfix.js`
digs the real URL out of headline-only posts — the oppgulp entry point).
The integration contract is the TODONT scoping verbatim: the annotation is
**lineage, never a verdict** — *"traces to a single NTB item, repeated
14×, no primary document found"* rendered next to the post, judgment left
with the reader. It also fits Fuckfeed's doctrine (uncertainty is shown
and flagged, never silently judged) and leaves its one invariant untouched
(tracing happens entirely off Facebook).

- **Trace is a deliberate act**: a button next to Mute, not an auto-pass.
  A feed pass has dozens of posts; a trace costs ~40 s and ~1.5¢.
- **Later, selective auto-trace**: gated by a claim-shaped/news-flavored
  triage (NPU-sized question) with results cached locally keyed by
  canonical URL. Oppgulp recurs — the cache pays for itself the third
  time the same claim arrives. (This is a *result* cache, not the page
  cache the house preference warns about.)
- **Invocation shape deliberately undecided** — localhost HTTP service,
  CLI subprocess, or direct import all work. HTTP would make torehund a
  shared service for the whole whining-series, which is the convenience
  any other shape has to beat — but decide when Fuckfeed's side is real,
  not before.

### Second consumer: Nyhetene på nordnorsk

The Darwin-Awards digest (i-want-nyhetene-pa-nordnorsk) needs three
things that are all news-mode machinery:

- **Same-event collapse.** Its "Ideer videre" asks for embedding+HDBSCAN
  to group the same event across sources — that *is* the near-duplicate
  clustering + independent-origin backtrack. A viral dumb-things story is
  oppgulp in comedy form; "6 saker eller 1 sak syndikert 6 ganger?" is
  the founding question, shared rather than rebuilt.
- **Verification before mockery.** Reading a fabricated/satire story
  aloud as real news is the digest's worst failure mode — and the screen
  is a *lineage* question, not a truth question: no independent origin +
  no primary document → not manus material. Provenance-not-veracity
  holds even for comedy.
- **The primary-document terminus as material.** The politilogg or court
  record behind a Darwin story is reliably funnier and more accurate
  than the aggregator's fourth-hand retelling. The backtrack upgrades
  the joke, not just the sourcing.

## Positioning

- Don't compete with frontier assistants on synthesis quality (competing
  with Claude Desktop is silly). Compete on **orchestration, cost floor,
  and who holds the question**.
- Frontier assistants are single-oracle; this is a chorus with a local
  conductor.
- Privacy ledger, stated honestly: query strings leak to one
  privacy-branded search provider; sub-question fragmentation means no
  single LLM provider ever sees the whole question; pages read and
  conclusions drawn stay home.

## Cost sketch (verified 2026-08-11)

Rates, from the vendors' own pricing pages: **Brave Search $5/1k requests
with $5 of free credit monthly** (≈ first 1,000 queries free, 50 q/s).
**Kagi Search $12/1k**, no free tier, invoiced every 30 days or at $100.
SearXNG is $0 marginal — our own box.

A deep question ≈ 5–15 searches; at 10, and the LLM cost zero marginal
(local silicon):

| Questions/day | Queries/mo | Brave | Kagi | Both |
|---|---|---|---|---|
| 2 | ~600 | $0 | $7 | $7 |
| 5 | ~1,500 | $2.50 | $18 | $21 |
| 15 | ~4,500 | $17.50 | $54 | $72 |

So Brave is *free* at personal volume — the monthly credit covers ~100 deep
questions — and pennies past it. The meter points at pennies instead of ad
auctions, as claimed.

Kagi is ~$0.12 per deep question. The argument against buying it first:
**Kagi sells ranking quality, and this architecture deliberately discards
ranking** — the reading loop is the cleaner, provenance replaces rank. Buy
it only if the second spike shows Brave's *recall* is the weak link.

Two traps. Brave's **Answers** plan ($4/1k + $5/M tokens, 2 q/s) is
citation-grounded summarization — the thing we are building; take
**Search**. And Kagi's **Extract API** ($4/1k pages) is a tempting shortcut
for the extraction step in item 3, but paying someone to extract means they
learn *what we read*, not merely what we asked, which breaks the privacy
ledger's one real promise. Extraction stays local.

## Open questions

- Does the conductor compile *one* query for both backends, or one per
  backend? Brave wants keywords; SearXNG rewards a `categories=` choice
  Brave has no equivalent for. Two compilations per sub-question is more
  work for the cheapest step in the pipeline (NPU), so probably worth it —
  but measure whether category routing actually beats `general`.
- Kagi: as a SearXNG engine, as a direct second front door, or not yet?
  Verify current pricing and free tiers.
- Citation format and UI: CLI first? Web UI? (NoLlama's web UI is the
  wrong surface — this is its own front end.)
- Caching of fetched pages: house preference is *avoid caching, prefer
  wait* — but re-fetching the web on every follow-up has a real cost.
  Decide when it hurts, not before.
- ~~Name/domain~~: settled 2026-08-13 — repo `i-want-usable-internet-again`,
  tool `torehund.py`; product name front-runner "Tore Hund på sporet"
  (torehund.no unchecked). Domain purchase deferred until something ships.

## First spike (the 10-minute-honesty test)

One question end-to-end, no UI: decompose locally → 3 Brave queries →
fetch top hits → extract → one 30B synthesis pass with citations.
Then 5 real questions side-by-side against Perplexity. If the local
answer is competitive on even 3 of 5, the thesis holds and the loop is
worth building properly.

**Built 2026-08-13** (`torehund.py`, né sporhund.py): pipeline works
end-to-end in ~30 s
(dev harness: gemma4:31b decompose, mistral-large-3:675b synthesis via
Ollama Cloud). First real answer cited every claim, surfaced a price
disagreement instead of averaging it, and stated its gaps. The
borrowed-reader cross-check (gpt-5.6-luna, blind) landed on the first
run: retrieval saw *no retail listings*, the reader knew *why* (OEM
channel only) — disagreement as dig-here marker, working as designed.
Still open: the 5-question Perplexity side-by-side (needs human judging).

## Second spike (does the corroborator earn its keep?)

Cheap, and it decides whether the whole SearXNG half is worth building:
run ~30 real queries through Brave and SearXNG side by side and measure
canonicalized URL overlap. If overlap is ~95%, the corroborator is telling
us nothing Brave didn't already say, and the verifier idea dies here. If
it's ~30%, the disagreement *is* the product. Measure before building the
merge properly.

**Measured 2026-08-13** (`spike2_overlap.py`, 30 stratified queries,
local Docker instance): corroboration of Brave's top-10 was **tech 67% /
academic 54% / news 27%**, with 17–25 SearXNG-only URLs per query.
Nowhere near the 95% kill line — **the corroborator stays.** Notes:

- SearXNG's own `brave` engine was dead for the whole run, which is
  accidentally the *cleaner* measurement: the overlap counted is
  Brave-vs-genuinely-independent engines (google-cse, duckduckgo,
  mojeek, …) — exactly the ranking-independent consensus the merge
  wants, with no self-corroboration inflating it.
- News is the outlier in both directions — least corroboration, most
  unique URLs — confirming both that news needs its own mode and that
  it's where the provenance vector earns out. One news query
  ("norges bank rentebeslutning") had **zero** overlap.
- `unresponsive_engines` varied per query; the confidence annotation
  should record which engines were alive, not just how many agreed.
- Public searx.space instances were considered and rejected as the
  corroborator: query privacy (a stranger holds the question), JSON off
  by default, and someone else's uptime — self-hosting is the design.

