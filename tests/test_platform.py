"""
The platform: the test-ID plugin, the committed records and the CLI's
error mapping.
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookworm.cli import app
from bookworm.shared.config import get_settings
from tests._fixtures.records import make_library

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.test_id("PLT-001")
@pytest.mark.parametrize("bad_id", ["PLT-2", "plt-002", "PLATFORM-002"])
def test_a_malformed_test_id_stops_the_run(pytester: pytest.Pytester, bad_id: str) -> None:
    pytester.makepyfile(
        test_marked=f"""
        import pytest

        @pytest.mark.test_id("{bad_id}")
        def test_something():
            pass
        """
    )
    result = pytester.runpytest("-p", "tests._plugins.test_ids", "-p", "no:asyncio", "-p", "no:cacheprovider")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines([f"*test_marked.py::test_something: '{bad_id}' isn't a test ID*"])


@pytest.mark.test_id("PLT-002")
def test_the_committed_records_are_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    # The real data/, not a temporary one: a record that doesn't load
    # fails the suite, and CI with it.
    monkeypatch.setenv("BOOKWORM_DATA_DIR", str(ROOT / "data"))
    get_settings.cache_clear()
    try:
        result = CliRunner().invoke(app, ["records", "check"])
    finally:
        get_settings.cache_clear()

    assert result.exit_code == 0, result.output
    assert "records ok" in result.output


@pytest.mark.test_id("PLT-003")
@pytest.mark.parametrize(
    ("args", "exit_code"),
    [
        (["libraries", "show", "nowhere"], 3),  # NotFoundError
        (["find", "--isbn", "123"], 2),  # invalid input
        (["records", "check"], 4),  # an invalid record
    ],
    ids=["not-found", "bad-input", "invalid-record"],
)
def test_domain_errors_become_exit_codes(
    monkeypatch: pytest.MonkeyPatch, data_dir: Path, args: list[str], exit_code: int
) -> None:
    make_library(data_dir, catalogue="ghost")
    monkeypatch.setenv("BOOKWORM_DATA_DIR", str(data_dir))
    get_settings.cache_clear()
    try:
        result = CliRunner().invoke(app, args)
    finally:
        get_settings.cache_clear()

    assert result.exit_code == exit_code, result.output
