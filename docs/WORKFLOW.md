# 🔁 Bookworm: workflow

← [Roadmap](ROADMAP.md) · [Boards](boards/README.md)

> How a [roadmap](ROADMAP.md) stage becomes work: the stages, stories and tasks on GitHub, the [boards](boards/README.md) that group them by domain, and the test-driven cycle every story follows. Adapted from Sinapsis' and Xolo's workflow, so the same words mean the same things in all three repos.

## 📖 Vocabulary

Every doc, issue and skill uses these words, and only these.

| Term          | Meaning                                                                                  | On GitHub                             | In the docs                                  |
| ------------- | ---------------------------------------------------------------------------------------- | ------------------------------------- | -------------------------------------------- |
| **Stage**     | One of the roadmap's steps                                                               | A milestone, plus a `stage:XXX` label | `docs/stages/NN-*.md`                        |
| **Story**     | One behavior a stage delivers, closed when all its test IDs are green                    | An issue labeled `story`              | A row in its stage's Stories table           |
| **Task**      | One concrete step toward closing a story, usually one PR                                 | A sub-issue of its story              | A row in its board's Tickets table           |
| **Board**     | A domain that groups stories and tasks across stages                                     | A `board:XXX` label                   | `docs/boards/XXX.md`                         |
| **Ticket**    | Any story or task                                                                        | An issue                              | Its board's Tickets table                    |
| **Test ID**   | One test case, `XXX-NNN` with the board's prefix                                         | Listed in the story's body            | The story's row and its board's tickets      |
| **Record**    | One file in `data/`: a library or a catalogue                                            | —                                     | `data/libraries/`, `data/catalogues/`        |
| **Catalogue** | Software at a URL that lists books (UNAM Descubridor, Nautilo). Many libraries may share one | —                                     | `data/catalogues/<slug>.md`                  |
| **Adapter**   | One way of searching one kind of catalogue, id `<system>.<method>` (`vufind.api`)         | —                                     | `src/bookworm/modules/catalogues/adapters/`  |

Use "story" for the rows in the stage files; don't call them "areas" or "features". Say "catalogue" for the software and "library" for the building: they're different records.

## 🗂️ Structure on GitHub

| Level | Created                                       | Labels                            | Milestone   |
| ----- | --------------------------------------------- | --------------------------------- | ----------- |
| Story | When its stage starts, or when it's picked up | `story`, `board:XXX`, `stage:XXX` | Its stage   |
| Task  | As the work needs it, never planned ahead     | `board:XXX`, `stage:XXX`          | Its story's |

- **Stories** describe the behavior and hold its test cases with their IDs. A story whose test cases span several stages carries each `stage:` label, but only the earliest milestone.
- **Tasks** name the test IDs they turn green, if any.
- **One board per ticket.** Tasks take their story's board, unless the task changes another domain.
- **Filtering:** by stage `milestone:"Census"`, by board `label:board:CAT`, or both.
- **Only the current stage is in build order.** Later stages keep their stories as a reference and get ordered when they start.

> ⚠️ The GitHub repo doesn't exist yet (see the roadmap's open decisions). Until it does, stories live only in the stage files, with "—" in their Issue column, and the ticket skills stop at the draft.

Every stage file has a Stories table:

|Column|Content|
|---|---|
|#|Build order (only once the stage is ordered)|
|Story|The story's name and, in parentheses, its board's prefix, which is also its test ID prefix|
|Issue|Link to the story's issue|
|Test IDs|The IDs the story must turn green, e.g. `CAT-001–CAT-009`|

Test IDs are numbered per board (`CAT-001`, `CAT-002`…), allocated when a story is written up, and never reused.

Use the project skills to create and close tickets, so titles, bodies, labels and records stay consistent:
- `create-story`
- `create-task`
- `close-ticket`

## 🧪 Test-driven cycle

Every behavior is written as a test case before it's built, so nothing is assumed along the way.

1. **Pick a story and open its first task.** The story's test cases are its acceptance criteria.
2. **Resolve blocking decisions first.** If a case depends on an open decision, decide it in the story and update the case. Don't pick an answer in the code.
3. **Red:** write the tests, marked with their ID (`@pytest.mark.test_id("CAT-004")`), and check that they fail.
4. **Green:** write the least code that makes them pass.
5. **Refactor** with the tests green (`make verify`), and open a PR that mentions the task and its test IDs.
6. **Record the ticket** in its board's file when it's opened, and update its status when it's closed.
7. **Prove it on a real catalogue.** Before closing a story that adds or changes an adapter, run its `live` test (`make test-live ID=…`) against the real catalogue at least once, and commit the recording it was built from.

⚠️ A behavior without a test ID isn't built. First add the case to the story, with a new ID.

### Data work (the MAP board)

Adding records is work too, but its "test" is `make check-records` plus a person checking the source. A census story lists what it will cover (an alcaldía, a university's libraries) and is done when those records exist, pass the check, and carry `verification` with a date and a source.
