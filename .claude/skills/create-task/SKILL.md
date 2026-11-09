---
name: create-task
description: Create a task, a sub-issue of a bookworm story, labeled and recorded in its board. Use when picking up the next step of a story, e.g. "open a task to record the VuFind API responses" or "next task for the UNAM census".
---

# Create a task

Tasks aren't planned ahead: one is opened when a story is picked up or when new work appears. Each task belongs to exactly one story. Adapted from Sinapsis' and Xolo's `create-task`.

**GitHub:** without a repo (`gh repo view` fails), draft the task, then record it only in the board's Tickets table with Issue `—` and say so.

## 1. Find the parent story

- Get it from the user (number, or stage + story name): `gh issue view <N> --json title,labels,milestone,body,state`, or its row and notes in the stage file.
- If the story isn't written up yet, do that first with `create-story`. If it's closed, ask before adding work.

## 2. Draft the task

- **Scope:** one reviewable change, ideally one PR. Good tasks here: "record VuFind's responses and write the mapping", "census of Coyoacán's branches", "wire Nautilo's record to `vufind.api`". Propose a split if it's bigger.
- **Test IDs** it turns green, if any. A behavior with no ID: stop and add the case to the story first (next ID as in `create-story`).
- **Board:** the story's, unless the task changes another domain (a CAT story's task that changes a record's fields is DIR).
- **Blocked IDs (⛔):** resolve the decision in the story first, not in code.

Show the draft and confirm before creating.

**Title:** `XXX · <imperative, specific>` (e.g. `CAT · Map VuFind API results to BibRecord`). **Labels:** `board:XXX`, the story's `stage:`. No `story` label. **Milestone:** the story's.

**Body:**

```markdown
Part of #<story>.

<What to do, in a few lines or bullets.>

## Test IDs

- XXX-00N: <case summary>. Or "None (setup work)."

## Done when

- [ ] The listed test IDs are green; `make verify` is green
- [ ] PR open, mentioning this task and its test IDs
- [ ] <adapter: recordings committed, `make test-live ID=…` run once> <census: `make check-records` green, each record's verification dated and sourced>
```

## 3. Create it

```sh
gh issue create --title "<title>" --body-file <scratchpad file> \
  --label board:XXX --label stage:<stage> --milestone "<Milestone>" --parent <story number>
```

## 4. Record it

Add a row at the top of the Tickets table in `docs/boards/XXX.md` (the task's board): `|[#N](url)|task|<Stage>|open|XXX-00N|`. Stage files only list stories. Don't commit unless the user asks.
