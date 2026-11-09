"""
Bookworm's domain errors.

WHY A HIERARCHY AND NOT EXCEPTIONS FROM THE LIBRARIES WE USE
    Callers (the lookup service, the CLI) decide what to do by the *kind* of
    failure: a catalogue that is down is retried later, one that changed its
    HTML needs an adapter fix, one whose robots.txt says no is never asked.
    httpx, Playwright and YAML each raise their own exceptions for these, so
    the layer that talks to them (repositories, adapters) translates at the
    boundary and raises one of these, `from` the original.

    Same shape as Sinapsis' and Xolo's `errors.py`: subclass the closest one
    per case so callers and tests can catch it by name. `detail` is the
    message a person reads. The CLI maps these to exit codes in one place
    (`cli.py`), as the API projects map them to HTTP status codes.
"""


class DomainError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    """A slug, record or file that doesn't exist."""


class InvalidRecordError(DomainError):
    """A file in `data/` that doesn't parse or doesn't match its model. The
    detail names the file and the field."""


# --- Talking to a catalogue -------------------------------------------------
#
# Raised by adapters, caught by the gateway, which tries the catalogue's next
# access method or reports the failure for that catalogue only. One broken
# catalogue never fails a whole lookup.


class CatalogueError(DomainError):
    """Base for anything that went wrong asking a catalogue."""


class CatalogueUnavailableError(CatalogueError):
    """Timeouts, connection errors, 5xx: try again later, nothing to fix."""


class CatalogueBlockedError(CatalogueError):
    """403, 429, a CAPTCHA or a login wall: the catalogue refused us. Slow
    down or stop; don't retry in a loop."""


class CatalogueChangedError(CatalogueError):
    """The response didn't have the shape the adapter expects (missing
    element, unexpected JSON). The adapter needs updating, and the detail
    says what was expected where."""


class UnsupportedQueryError(CatalogueError):
    """This access method can't answer this kind of query (e.g. an HTML form
    with no ISBN field). The gateway moves on to the next method."""
