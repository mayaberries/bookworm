---
name: close-ticket
description: Close a bookworm story or task and update its board, stage and decision records. Use when a task's PR is merged or a story's test IDs are all green, e.g. "close issue 14" or "we're done with the VuFind API story".
---

# Close a ticket

Adapted from Sinapsis' and Xolo's `close-ticket`. Without a GitHub repo, skip step 2's `gh` calls and update the docs only.

## 1. Check it's really done

`gh issue view <N> --json title,labels,milestone,body,state,subIssues`, or the stage file's notes.

- **Task:** its test IDs pass (`make test ID="XXX-NNN XXX-NNN"`), `make verify` is green, its PR is merged (or the user says so), its "Done when" boxes are checked.
- **Story:** every sub-issue closed; every test ID 🟩; for an adapter story, its `live` test was run against the real catalogue (`make test-live ID=…`) and its recordings are committed; for a census story, `make check-records` is green and each new record has `verification` with a date and source.

If something is missing, say what and don't close. The user can still close it as not planned.

## 2. Update GitHub

- **Task:** in the parent story's test-case table, set the IDs it turned green to 🟩 (`gh issue edit <story> --body-file`).
- **Close:** `gh issue close <N> --comment "<one line: what was done, test IDs, PR>"`; `--reason "not planned"` when dropped.

## 3. Update the docs

- **Board file:** set the ticket's Status to `closed` (or `dropped`).
- **Stage:** if it was the stage's last open story, say so and review the exit criteria with the user.
- **Decisions:** if closing settled an open decision, record it in `docs/DECISIONS.md` (newest first: date, decision, why, implies) and move it from the stage's "Open decisions" to "Decisions made".
- **CLAUDE.md:** if the ticket added a command, a module or a convention, update it.

Don't commit unless the user asks.
