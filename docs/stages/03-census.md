# 🗺️ Census: every library we can find, and how to ask it

← [Distribution](02-distribution.md) · Next: [First catalogues](04-first-catalogues.md) →

Put a record in `data/` for every library in Mexico City we can find, with its catalogue (or `null`), and a record for every catalogue with its software and whether we may query it. This stage is mostly data work (the MAP board): its "tests" are `make check-records` and a person checking each source.

📍 Milestone: Census · label `stage:census`

## 🎬 What the stage demonstrates

- `bookworm libraries list --alcaldia …` lists every library known in that alcaldía, each with a verification date and source.
- Every catalogue on record has `automation` set from its robots.txt and terms, with `robots_checked_on`.
- For each catalogue shared by several libraries, each library's `catalogue_location` is known.

## ✅ Exit criteria

- Every story's coverage is on record and `make check-records` is green
- No catalogue has `automation: unknown`

## 🧩 Stories

Not ordered yet.

|#|Story|Issue|Test IDs|
|---|---|---|---|
||The public network: alcaldía branch libraries from the CDMX network's directory ([MAP](../boards/MAP.md))|||
||UNAM's libraries, with their codes in Descubridor and LIBRUNAM ([MAP](../boards/MAP.md))|||
||Large federal and university collections: Vasconcelos, Biblioteca de México, Nacional, UAM, IPN, Colmex, Mora ([MAP](../boards/MAP.md))|||
||Robots.txt and terms for every catalogue on record ([MAP](../boards/MAP.md))|||
||Find LIBRUNAM's current URL and record it ([MAP](../boards/MAP.md))|||

### 📝 Story notes

- The README's landscape table and sources are the starting point; Vasconcelos' interlibrary loan page is a rough directory of other catalogues.
- Record what can't be searched too: a branch with no catalogue still gets a record with its address and phone, so the lookup can say where to call.

## ❓ Open decisions

- Collect by hand or write importers per directory (roadmap). An importer would read a source and write records through `LibrariesRepository.save`; it would be a new module (`modules/census/`) and needs its own decision.
