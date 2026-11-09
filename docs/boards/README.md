# 🗂️ Bookworm: boards

← [Roadmap](../ROADMAP.md) · [Workflow](../WORKFLOW.md)

> Milestones cut the work by stage; boards cut it by domain. Every story and task on GitHub carries one board label, so the same issue can be found from its milestone or from its board. Each board's file lists its stories by stage and keeps a record of its tickets.

## 🏷️ Boards

|Board|Label|Covers|[Fnd](../stages/01-foundation.md)|[Dis](../stages/02-distribution.md)|[Cen](../stages/03-census.md)|[Cat](../stages/04-first-catalogues.md)|[Cov](../stages/05-coverage.md)|
|---|---|---|:-:|:-:|:-:|:-:|:-:|
|🏗️ [PLT · Platform](PLT.md)|`board:PLT`|Packaging and distribution (vaults, settings, plugin, releases), CLI and other entry points, test harness, CI|●|●||||
|📇 [DIR · Directory](DIR.md)|`board:DIR`|The record models, files, repositories and the record check (`modules/directory/`)|●|||||
|🗺️ [MAP · Census](MAP.md)|`board:MAP`|The records themselves: finding libraries and catalogues, checking robots.txt, verifying|||●|●||
|🔌 [CAT · Catalogues](CAT.md)|`board:CAT`|The adapter port, gateway and every adapter (`modules/catalogues/`)|●|||●|●|
|🔎 [LKP · Lookup](LKP.md)|`board:LKP`|Availability across libraries, outcomes, results (`modules/lookup/`)|●|●|||●|

## 📏 Rules

- **One board per ticket.** Every story and every task gets exactly one `board:XXX` label, plus its `stage:XXX` label and milestone; stories also carry `story`.
- **Tasks follow their story** unless the task changes another domain; then it takes that board's label instead.
- **The prefix is also the test ID prefix.** Test IDs are `XXX-NNN`, numbered per board, so a test ID tells you its board at a glance.
- **DIR is code, MAP is data.** Changing what a record *can* say is DIR; adding or correcting what records *do* say is MAP.
- **New stories pick an existing board.** Create a new board only when a story fits none of them; add its file here and its label on GitHub.
