# Face-off: sporhund v0.001 (one-shot) vs Perplexity Pro — 2026-08-13

Five questions, both engines, human-supplied ground truth where we have it.
sporhund halves in `roundN-*-sporhund.txt`; Perplexity answers pasted in
conversation (its answers used ~10 sources each).

## Round 1 — "Are there a 48 GB version of Intel graphics cards?"

**sporhund, narrowly.** Both found Max 1100 (48 GB) and the dual B60.
sporhund additionally surfaced Arc Pro B70/B65 (32 GB, newer) and the Max
1550; Perplexity had better prose and the HBM2e detail. Decider: Perplexity
claimed the dual B60 is "real products you can buy today" — an overclaim
(the user's own memory of Norwegian listings also failed verification; the
only find is a FINN broker listing). sporhund's hedge was calibration, not
cowardice.

## Round 2 — "Hva skjer med elektrifiseringen av Melkøya?"

**Perplexity, with an asterisk.** Perplexity: complete project picture
(konsesjon 2023, byggestart 2024, 420 kV Skaidi–Hyggevatn, 350–410 MW,
850 kt CO₂, 13,2 mrd, drift 2030) with primary sources (NVE, regjeringen,
Stortinget). sporhund read *three* Stortinget primary documents and caught
newer parliamentary turbulence (the 2025 vote, SV's flip, CCS/kjernekraft
alternatives) — but concluded "ikke endelig besluttet", overweighting the
stop-motions its queries selected for. Lesson: query selection bias — asking
about "status" pulled opposition documents; the answer needed both halves.

## Round 3 — OpenVINO MoE disk offload (we own the ground truth)

**Perplexity on points; both miss the sharp edges.** Truth (measured on our
hardware, TODONT.md): 2026.3, GPU plugin, XMX is a HARD gate (silent no-op
without; non-XMX iGPU can't even load big MoE — USM OOM). Perplexity got
2026.3/GPU/Intel/Arc right and *mentioned* XMX but framed it as a
performance preference, and overbroadly blessed Core Ultra iGPUs. sporhund
got 2026.3/GPU/Intel right, then padded the device list from a generic
system-requirements page (Iris Xe et al. — wrong: that's what OpenVINO
supports, not what offload supports). Neither engine knows the silent-no-op
fact — as far as we can tell it is published nowhere except our own repo.
The web can't tell you what only your bench knows.

## Round 4 — wire-service homogenization evidence

**Perplexity, decisively.** It produced the actual literature: Pew 2015
(~60% wire share), Whitney/Becker 1982 (concordance .915), Paterson/LSE
(85% verbatim duplication), the Australian AAP study (96%), mechanisms and
caveats — largely via open-access mirrors (aejmc.org, lse.ac.uk PDFs).
sporhund got a glossary quote: 6 of its 9 fetches died on 403s
(ResearchGate, T&F, OUP). Two architecture items confirmed: the specialist
corpora (OpenAlex/Semantic Scholar via SearXNG) must join retrieval, and
the reader needs an open-access-mirror strategy for paywalled DOIs.

## Round 5 — B60 pris/lager i Norge

**Perplexity, decisively.** It found godpris.no, Prisjakt, Proshop
(bestillingsvare), Multicom (på lager), SBHA, NOK prices (8 400–9 500 kr),
plus the FINN listing of the Dual (15 000 kr eks mva, broker). sporhund:
EU prices converted to NOK, honest gap statement, one stale date. The
`country=no` + `site:.no` query contributed nothing readable — **Brave's
Norwegian shopping/price-comparison coverage is thin**. This is the "if
Brave's recall is the weak link, revisit" trigger from TODONT.md, scoped
to the local-retail vertical.

## Verdict

Score: Perplexity 3 (rounds 3–5), sporhund 1 (round 1), round 2 split.
Against the spike-1 bar ("competitive on 3 of 5"): rounds 1, 2, 3 were
competitive; 4 and 5 were not. **The thesis survives on a technicality,
and the failures are all one missing thing: the loop.** This was one-shot
sporhund; PLAN.md itself says one-shot is the thin version. Every loss has
a mechanical cause with a known fix:

1. **The iterative loop** — round 5's own DIG output said "search retailer
   listings"; a conductor that acts on DIG re-queries into prisjakt-space.
   Round 2's one-sidedness likewise dies on the second pass.
2. **Specialist corpora in retrieval** (round 4) — the SearXNG instance
   already has the engines; wire them into sporhund, not just spike 2.
3. **403/paywall fallback** (round 4) — prefer open-access mirrors;
   half the reading list died unread.

Also recorded: Perplexity (2026-08) is fast, well-sourced, and cites
primary documents — the bar is much higher than the 2024-era memory of it.
We compete on orchestration, cost floor, and who holds the question — not
on beating their index with a 250-line one-shot.
