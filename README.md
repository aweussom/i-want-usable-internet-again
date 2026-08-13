# i-want-usable-internet-again

The internet's answer machinery optimizes for whoever is paying to be
found, so the rational reader ends up marking *everything* as
spam/phishing — verification fatigue as a lifestyle. This repo is the
repair attempt: **`torehund.py`**, a bloodhound that runs the tedious
half of source criticism so your judgment gets a pre-traced lineage
instead of a raw claim. (The name is a triple: Tore Hund, the Viking who
felled a saint-king; *Tore på sporet*, lineage tracing as a TV format;
and the sporhund it actually is.)

A local LLM (served by [NoLlama](https://github.com/aweussom/NoLlama))
decomposes your question, sends it out through independent search
backends, reads what comes back, and answers with **provenance, not
rank** — and for news, traces the fourteen identical articles back to
the one wire story they all regurgitated, hunting for the primary
document at the end of the trail.

It reports lineage, never truth verdicts. That distinction is
load-bearing; see [TODONT.md](TODONT.md).

Status: planning. Read [PLAN.md](PLAN.md) — the architecture, the cost
arithmetic, and the two spikes that decide whether the thesis survives
contact with reality.
