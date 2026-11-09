---
name: create-command
description: Add or change a bookworm CLI command (Typer), the only entry point, which parses arguments into an input model, calls one service method and renders a table or JSON. Use for "add a catalogues list command", "find should take several ISBNs", "show results as CSV", "what exit code for X?".
---

# Create a command

The CLI (`src/bookworm/cli.py`) plays the role routes play in the API projects (`create-route` in Vetted, Sinapsis, Kalens and Xolo): **thin, one service call, errors mapped in one place.**

## 1. Shape

```python
@libraries_app.command("list")
def list_libraries(
    alcaldia: Annotated[Alcaldia | None, typer.Option(help="Only this alcaldía.")] = None,
    as_json: JsonOption = False,
) -> None:
    """Every library on record."""          # the help text people see
    service = build_directory_service(get_settings().data_dir)
    libraries = _run(lambda: service.list_libraries(alcaldia=alcaldia))
    if as_json:
        console.print_json(json.dumps([lib.model_dump(mode="json") for lib in libraries]))
        return
    ...  # a rich Table
```

- **Parse into the module's input model** (`BookQuery(...)`) inside `_run`, so a `ValidationError` becomes exit code 2 with Pydantic's message.
- **One service method per command**, called inside `_run`, which maps domain errors to exit codes from `EXIT_CODES` (most specific first, like `STATUS_CODES` in the API projects). A new error kind that needs its own code goes in that list above its parent.
- **Services come from the module's builder** (`build_directory_service`, `open_lookup_service`), never built from repositories here.
- **Async services run with `asyncio.run`** around one coroutine that opens and closes the service's clients.
- **Every command that prints data has `--json`**, printing the model with `model_dump_json()` / `model_dump(mode="json")`: scripts and tests read that, not the table.
- **Tables are for people.** Put the outcome first, the detail second; show `detail` when the service gave one (it says why: no catalogue, robots.txt, which adapter failed).
- **Sub-apps group nouns** (`libraries`, `records`; later `catalogues`). Verbs that are the product (`find`) are top-level.
- **No rules here.** If a command needs an `if` about the domain, it belongs in the service.

## 2. Exit codes

| Code | Meaning |
|---|---|
| 0 | done |
| 1 | other domain error |
| 2 | bad input (Typer usage errors and `ValidationError`) |
| 3 | not found |
| 4 | invalid records |

Change one only with a decision: scripts depend on them.

## 3. Test it

With `typer.testing.CliRunner` and `BOOKWORM_DATA_DIR` pointed at the test's `data_dir` (clear `get_settings`' cache around it; see `tests/test_platform.py`):

- the exit code for each error kind the command can hit;
- `--json` output parses into the service's model;
- not the rules: those are the service's tests.

## Checklist

- [ ] Input parsed into a model inside `_run`; one service call inside `_run`
- [ ] Service from the module's builder; no repositories or adapters imported here
- [ ] `--json` for anything that prints data; a table for people
- [ ] Exit codes from `EXIT_CODES`; tests for each
- [ ] Help text on the command and every option
- [ ] CLAUDE.md's command list updated
