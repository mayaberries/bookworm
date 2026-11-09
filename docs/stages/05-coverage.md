# 🌐 Coverage: the long tail, and day-to-day use

← [First catalogues](04-first-catalogues.md) · [Roadmap](../ROADMAP.md)

Adapters for the remaining catalogue systems the census found, ordered by how many libraries each unlocks; keeping results between runs; and a way to ask that isn't only a terminal.

📍 Milestone: Coverage · label `stage:coverage`

## 🧩 Stories

Not ordered yet; written up when the stage starts.

|#|Story|Issue|Test IDs|
|---|---|---|---|
||Adapters for the next catalogue systems (Aleph, Koha, Janium…) ([CAT](../boards/CAT.md))|||
||Results kept between runs, and "what changed since last time" ([LKP](../boards/LKP.md))|||
||Search by title/author across catalogues, with grouping of the same book ([LKP](../boards/LKP.md))|||

Distribution left two agent safeguards here: a per-run cap on catalogue requests, and a local result cache so an agent asking twice doesn't search twice. Both belong with the results story.

## ❓ Open decisions

- Results storage (roadmap).
- WorldCat (roadmap).
