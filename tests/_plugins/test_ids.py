"""
The `test_id` marker: ties a test to the test case(s) it proves, by the IDs in
its story (`docs/WORKFLOW.md`).

    @pytest.mark.test_id("DIR-002")
    async def test_reports_both_dependencies_reachable(...): ...

    pytestmark = pytest.mark.test_id("DIR-003")   # every test in the module

- The marker itself is registered in pytest.ini, with the others.
- IDs are checked at collection: anything that isn't `XXX-NNN` stops the run.
- `pytest --test-id DIR-002` (repeatable) runs only the tests with that ID.
- Each ID is added to the test's `user_properties`, so it shows up in JUnit
  reports (`--junitxml`).

Marking is optional: an unmarked test runs as usual.
"""

import re

import pytest

MARKER = "test_id"
TEST_ID_PATTERN = re.compile(r"^[A-Z]{3}-\d{3}$")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--test-id",
        action="append",
        default=[],
        metavar="XXX-NNN",
        help="Only run tests marked with this test ID (repeatable).",
    )


def _test_ids(item: pytest.Item) -> set[str]:
    ids: set[str] = set()
    for marker in item.iter_markers(name=MARKER):
        if not marker.args:
            raise pytest.UsageError(f"{item.nodeid}: @pytest.mark.{MARKER}() needs at least one ID")
        for test_id in marker.args:
            if not isinstance(test_id, str) or not TEST_ID_PATTERN.match(test_id):
                raise pytest.UsageError(
                    f"{item.nodeid}: {test_id!r} isn't a test ID (expected XXX-NNN, e.g. DIR-002)"
                )
            ids.add(test_id)
    return ids


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    wanted = set(config.getoption("test_id") or [])
    selected: list[pytest.Item] = []
    deselected: list[pytest.Item] = []

    for item in items:
        ids = _test_ids(item)
        for test_id in sorted(ids):
            item.user_properties.append((MARKER, test_id))
        (selected if not wanted or ids & wanted else deselected).append(item)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected
