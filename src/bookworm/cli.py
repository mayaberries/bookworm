"""
The command line: bookworm's only entry point (the role routes play in the
API projects).

Each command parses its arguments into an input model, calls ONE service
method, and renders the result: a table for people, `--json` for scripts.
No rules live here. Domain errors become an exit code and a message in one
place, `_run`, as the API projects map them to HTTP status codes in one
handler. See the `create-command` skill.
"""

import asyncio
import json
from collections.abc import Callable
from typing import Annotated, NoReturn

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from bookworm.modules.catalogues import BookQuery, check_access
from bookworm.modules.directory import Alcaldia, build_directory_service
from bookworm.modules.lookup import AvailabilityReport, LibraryOutcome, open_lookup_service
from bookworm.shared.config import get_settings
from bookworm.shared.errors import DomainError, InvalidRecordError, NotFoundError

app = typer.Typer(no_args_is_help=True, help="Ask Mexico City's library catalogues whether they have a book.")
libraries_app = typer.Typer(no_args_is_help=True, help="The libraries in data/libraries/.")
records_app = typer.Typer(no_args_is_help=True, help="The record files in data/.")
app.add_typer(libraries_app, name="libraries")
app.add_typer(records_app, name="records")

console = Console()
err = Console(stderr=True)

# Most specific first, like STATUS_CODES in the API projects' errors.py.
EXIT_CODES: list[tuple[type[DomainError], int]] = [
    (NotFoundError, 3),
    (InvalidRecordError, 4),
    (DomainError, 1),
]
EXIT_USAGE = 2

JsonOption = Annotated[bool, typer.Option("--json", help="Print JSON instead of a table.")]


def _fail(detail: str, code: int) -> NoReturn:
    err.print(f"[red]error:[/red] {detail}")
    raise typer.Exit(code)


def _run[T](call: Callable[[], T]) -> T:
    try:
        return call()
    except ValidationError as exc:
        _fail(str(exc), EXIT_USAGE)
    except DomainError as exc:
        _fail(exc.detail, next(code for kind, code in EXIT_CODES if isinstance(exc, kind)))


# --- find -------------------------------------------------------------------

OUTCOME_STYLE = {
    LibraryOutcome.available: "[green]available[/green]",
    LibraryOutcome.held_not_available: "[yellow]held, not on the shelf[/yellow]",
    LibraryOutcome.held_status_unknown: "[yellow]held, status unknown[/yellow]",
    LibraryOutcome.not_found: "[dim]not found[/dim]",
    LibraryOutcome.check_manually: "[cyan]check by hand[/cyan]",
    LibraryOutcome.failed: "[red]search failed[/red]",
}


@app.command()
def find(
    isbn: Annotated[str | None, typer.Option(help="ISBN-10 or ISBN-13, hyphens allowed.")] = None,
    title: Annotated[str | None, typer.Option()] = None,
    author: Annotated[str | None, typer.Option()] = None,
    library: Annotated[
        list[str] | None, typer.Option("--library", "-l", help="Library slug; repeatable.")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    """Is this book at these libraries (default: all of them)?"""
    query = _run(lambda: BookQuery(isbn=isbn, title=title, author=author))

    async def lookup() -> AvailabilityReport:
        async with open_lookup_service(get_settings()) as service:
            return await service.find(query=query, library_slugs=library)

    report = _run(lambda: asyncio.run(lookup()))

    if as_json:
        console.print_json(report.model_dump_json())
        return
    table = Table("Library", "Result", "Details")
    for result in report.results:
        details = result.detail or ", ".join(
            f"{item.record.title}" + (f" ({len(item.holdings)} copies)" if item.holdings is not None else "")
            for item in result.found
        )
        table.add_row(result.library_name, OUTCOME_STYLE[result.outcome], details)
    console.print(table)


# --- libraries --------------------------------------------------------------


@libraries_app.command("list")
def list_libraries(
    alcaldia: Annotated[Alcaldia | None, typer.Option(help="Only this alcaldía.")] = None,
    catalogue: Annotated[str | None, typer.Option(help="Only libraries in this catalogue (slug).")] = None,
    as_json: JsonOption = False,
) -> None:
    """Every library on record."""
    service = build_directory_service(get_settings().data_dir)
    libraries = _run(lambda: service.list_libraries(alcaldia=alcaldia, catalogue=catalogue))
    if as_json:
        console.print_json(json.dumps([lib.model_dump(mode="json") for lib in libraries]))
        return
    table = Table("Slug", "Name", "Alcaldía", "Catalogue", "Verified")
    for lib in libraries:
        table.add_row(
            lib.slug, lib.name, lib.alcaldia or "", lib.catalogue or "—", lib.verification.status.value
        )
    console.print(table)


@libraries_app.command("show")
def show_library(slug: str, as_json: JsonOption = False) -> None:
    """One library's record."""
    service = build_directory_service(get_settings().data_dir)
    library = _run(lambda: service.get_library(slug=slug))
    if as_json:
        console.print_json(library.model_dump_json())
        return
    console.print(library.model_dump(exclude={"notes"}, exclude_defaults=True))
    if library.notes:
        console.print(library.notes)


# --- records ----------------------------------------------------------------


@records_app.command("check")
def check_records() -> None:
    """Validate every record in data/: fields, slugs they name, adapters and their options."""
    service = build_directory_service(get_settings().data_dir)
    issues = service.check_records()
    if not issues:
        catalogues = service.list_catalogues()
        issues = check_access(catalogues)
    for issue in issues:
        err.print(f"[red]{issue.path}[/red]: {issue.detail}")
    if issues:
        raise typer.Exit(4)
    console.print("[green]records ok[/green]")
