# TODONT

Things we tried that didn't work, or that work but aren't worth doing. Each
entry explains *why not* so we don't re-litigate it in six months.

## Puppeteering users' logged-in free LLM web sessions as search backends (pre-abandoned 2026-08-11)

Idea: "BYOK where the K is a browser cookie" — drive chatgpt.com /
gemini.google.com etc. through the user's logged-in consumer sessions and
use the web-connected assistants as free retrieval backends.

**Verdict:** don't build it. Inherited scar tissue, not a fresh measurement
— this is the copilot-proxy lesson (2026-05-26, see agentry/TODONT.md)
with the blast radius moved onto *users'* accounts instead of our own.

**Why not:** consumer-ToS forbid automation; providers run active anti-bot
arms races; the DOM churns monthly so the scraper is permanently broken;
and a ban lands on the user's personal account. The green-lane version of
the same idea is fine and in PLAN.md: free *API tiers* (Gemini API, Groq,
Mistral, Cerebras, OpenRouter) — real keys, sanctioned programmatic
access, no cookies involved. If a provider offers only a logged-in web UI:
official API or not included.

## SearXNG as the primary retrieval plane (considered and demoted 2026-08-11)

Idea: promote SearXNG from fallback tier to *the* retrieval API, with Brave
and Kagi configured as engines inside it — both ship as engines, and
`api_key`/`base_url` are per-engine `settings.yml` values. One JSON
contract, one place for dedup and normalization, and 274 ready-made engine
adapters including the specialist corpora. Genuinely attractive; it is
almost exactly what PLAN.md's "one clean retrieval API" describes.

**Verdict:** not the plane. Keep it parallel and fail-open (see PLAN.md).

**Why not:** it puts our own instance on the critical path. Its uptime
becomes the system's uptime, `format=json` is off by default
(`search.formats: [html]` → 403), and the scraped engines fail *silently* —
a 200 OK with a thinner `results[]` and a note in `unresponsive_engines`,
i.e. quality regressions that don't look like errors. It also moves the
scraping arms race onto our home IP, which is the specific cost that
Brave's per-query pennies exist to absorb, in a project whose selling point
is running from home. Demoted to a parallel corroborator, every one of
those failure modes downgrades from "no answer" to "one fewer confidence
annotation".

**Not closed:** the specialist adapters (OpenAlex, Crossref, PubMed, arXiv,
Stack Overflow) are the real asset and are reachable either way — same
instance — so a verifier path can be promoted to a retrieval path later
without re-architecting. If the second spike shows Brave's *recall* is the
weak link rather than its ranking, revisit.

## Truth verdicts — a "realtime Faktisk.no" (scoped down 2026-08-11)

Idea: since we're already backtracking news stories to their origin, go one
step further and rule on whether claims are *true* — automated fact-checking
in the Faktisk.no mould.

**Verdict:** ship **provenance, not veracity**. The news mode traces
lineage and reports it; it does not adjudicate truth. Keep the wording out
of the UI too — no "verified", no truth badges.

**Why not:** Faktisk does human research with domain expertise and reaches
verdicts it can defend; an automated verdict is wrong in public, and wrong
in the direction that does the most damage (confidently blessing a false
claim). Provenance is the tractable half and is *already* the useful half:
"traces to a single anonymously-sourced story in one outlet, repeated 14
times, no primary document found" is auditable, is not a truth claim, and
tells the reader more than a verdict would. Also worth noting Faktisk is
owned by the same houses producing the oppgulp and checks claims rather
than lineage — so lineage is open ground, not a competitor.

**Adjacent and fine:** "does a primary document exist for this claim, and
what is it" is a retrieval question, not a truth judgement. That stays.
