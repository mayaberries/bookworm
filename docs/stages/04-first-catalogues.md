# 🔌 First catalogues: real adapters where most books are

← [Census](03-census.md) · Next: [Coverage](05-coverage.md) →

Write the adapters for the catalogues that hold most of what people look for, starting with VuFind because one adapter covers several catalogues (UNAM Descubridor, Nautilo, UAM Iztapalapa).

📍 Milestone: First catalogues · label `stage:catalogues`

## 🎬 What the stage demonstrates

- `bookworm find --isbn …` returns real availability from at least three catalogues.
- A VuFind catalogue whose API is off falls back to HTML without anyone touching its record.

## ✅ Exit criteria

- All test IDs assigned to this stage are green, including one `live` test per adapter run at least once
- Each wired catalogue has `automation: allowed` and `robots_checked_on`

## 🧩 Stories

Not ordered yet.

|#|Story|Issue|Test IDs|
|---|---|---|---|
||VuFind REST API adapter, `vufind.api` ([CAT](../boards/CAT.md))|||
||VuFind HTML adapter, `vufind.html`, with holdings ([CAT](../boards/CAT.md))|||
||Wire UNAM Descubridor, Nautilo and UAM Iztapalapa ([MAP](../boards/MAP.md))|||
||Biblioteca Vasconcelos browser adapter, if its terms allow ([CAT](../boards/CAT.md))|||

### 📝 Story notes

- Quick check for VuFind's API: `<base>/api/v1/search?lookfor=maffie` returns JSON if it's on.
- Holdings in VuFind are often a second request (`/Record/<id>/Holdings`). Decide per adapter whether `search` fetches them (`holdings=None` otherwise).

## ❓ Open decisions

- Whether `vufind.html` fetches holdings for every result or only the first N.
