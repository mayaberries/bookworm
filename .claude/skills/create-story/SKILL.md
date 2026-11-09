---
name: create-story
description: Write up one story of a bookworm stage, with its board, test cases and IDs, and create its GitHub issue once the repo exists. Use when starting work on a story, e.g. "let's tackle the VuFind API adapter" or "open the story for the UNAM census".
---

# Create a story

A story is one row in a stage file's Stories table. Use the vocabulary in `docs/WORKFLOW.md` (stage, story, task, board, ticket, test ID, record, catalogue, adapter). Adapted from Sinapsis' and Xolo's `create-story`; keep them compatible.

**GitHub:** the repo doesn't exist yet (`docs/ROADMAP.md`, open decisions). Check with `gh repo view --json nameWithOwner 2>/dev/null`. Without one, do steps 1–3 and 5 and put "—" in the Issue column; the test cases go in the stage file's story notes instead of an issue body.

## 1. Identify the story

- Find the stage file in `docs/stages/` and the story's row. The board is the prefix in parentheses, e.g. `VuFind REST API adapter, vufind.api ([CAT](../boards/CAT.md))`.
- If the row's Issue column already has a link, stop and show it.
- If the story isn't in the table, propose a row and a board (an existing one; `docs/boards/README.md`) and confirm first.
- If the stage is ordered, warn when earlier stories are still open; don't block.

|Stage file|Milestone|Label|
|---|---|---|
|01-foundation|Foundation|`stage:foundation`|
|02-distribution|Distribution|`stage:distribution`|
|03-census|Census|`stage:census`|
|04-first-catalogues|First catalogues|`stage:catalogues`|
|05-coverage|Coverage|`stage:coverage`|

## 2. Draft the test cases

Read the stage file (what it demonstrates, story notes, open decisions) and `docs/DECISIONS.md`. Then:

- Write each behavior as a test case: one observable outcome, given / when / then.
- **Adapter stories (CAT):** cases come from recorded responses: one per thing the mapping must handle (a hit with holdings, no hits, a status text to map, a page whose shape changed → `CatalogueChangedError`), plus one `live` case against the real catalogue. Look at the real catalogue first (`create-adapter` step 1); don't guess its responses.
- **Census stories (MAP):** the cases are coverage, not code: "every alcaldía branch listed in <source> has a record", "every catalogue has `automation` set". Name the source.
- Allocate test IDs `XXX-NNN` (board prefix, 3 digits, never reused). Next free number, from both sources, take the highest:
  - `grep -rhoE '\bXXX-[0-9]{3}\b' docs tests 2>/dev/null | sort -u | tail -1`
  - once the repo exists: `gh issue list --label board:XXX --state all --json body -q '.[].body' | grep -oE '\bXXX-[0-9]{3}\b' | sort -u | tail -1`
- List the open decisions that block any case and mark those cases ⛔.
- **Principles check:** flag any case that would query a catalogue not marked `automation: allowed`, or need the network in the offline suite.

## 3. Show the draft and confirm

Show title, labels, milestone and body; don't create anything until the user confirms.

**Title:** `XXX · <story name as in the stage table>`. **Labels:** `story`, `board:XXX`, `stage:<stage>`.

**Body:**

```markdown
<One or two sentences: what the story delivers.>

## Test cases

|ID|Given / when / then|Recording / source|Status|
|---|---|---|---|
|XXX-001|Given …, when …, then …|`tests/_recordings/vufind/search_isbn_hit.json` or "live" or a census source|⬜|

## Blocking decisions

- <Decision> (blocks XXX-00N). Or "None."

## Context

- Stage: docs/stages/<file>.md
- Board: docs/boards/XXX.md
- Decisions: docs/DECISIONS.md

Tasks are created as sub-issues as the work needs them.
```

Status values: ⬜ not started, 🟥 red (written, failing), 🟩 green, ⛔ blocked.

## 4. Create it (once the repo exists)

```sh
gh issue create --title "<title>" --body-file <scratchpad file> \
  --label story --label board:XXX --label stage:<stage> --milestone "<Milestone>"
```

Write the body file to the scratchpad, not the repo.

## 5. Record it in the docs

- **Stage file:** fill the row's Issue (`[#N](url)` or `—`) and Test IDs (`CAT-010–CAT-016`). Without an issue, add the test-case table under the story's note.
- **Board file** `docs/boards/XXX.md`: fill the Issue column in "Stories by stage", and add a row at the top of Tickets: `|[#N](url)|story|<Stage>|open|CAT-010–CAT-016|`.

Don't commit unless the user asks. Finish with the link (or the stage file's section) and offer to open the first task (`create-task`).
