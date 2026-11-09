import pytest
from pydantic import ValidationError

from bookworm.modules.catalogues import BookQuery, QueryKind


@pytest.mark.test_id("CAT-001")
@pytest.mark.parametrize(
    ("given", "normalized"),
    [
        ("978-1-60732-222-1", "9781607322221"),
        ("978 1 60732 222 1", "9781607322221"),
        ("1-60732-222-X", "9781607322221"),  # ISBN-10 becomes its ISBN-13
        ("0-19-852663-6", "9780198526636"),
    ],
    ids=["hyphens", "spaces", "isbn10-x", "isbn10"],
)
def test_isbns_are_normalized_to_isbn13(given: str, normalized: str) -> None:
    query = BookQuery(isbn=given)

    assert query.isbn == normalized
    assert query.kind is QueryKind.isbn


@pytest.mark.test_id("CAT-001")
@pytest.mark.parametrize("bad", ["12345", "97816073222211", "abcdefghij"], ids=["short", "long", "letters"])
def test_a_malformed_isbn_is_rejected(bad: str) -> None:
    with pytest.raises(ValidationError, match="isn't an ISBN"):
        BookQuery(isbn=bad)


@pytest.mark.test_id("CAT-001")
@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({}, "give an isbn, or a title"),
        ({"title": "  ", "author": ""}, "give an isbn, or a title"),
        ({"isbn": "9781607322221", "title": "X"}, "not both"),
        ({"isbn": "9781607322221", "edition": "2"}, "Extra inputs"),
    ],
    ids=["empty", "blank", "both-kinds", "unknown-field"],
)
def test_a_query_needs_exactly_one_kind(fields: dict[str, str], expected: str) -> None:
    with pytest.raises(ValidationError, match=expected):
        BookQuery(**fields)


@pytest.mark.test_id("CAT-001")
def test_title_or_author_alone_is_a_title_author_query() -> None:
    assert BookQuery(author="Maffie").kind is QueryKind.title_author
