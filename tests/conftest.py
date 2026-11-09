"""
The suite runs offline: record files live in a per-test temporary `data/`,
catalogues are fake adapters or recorded responses replayed through
httpx.MockTransport. Tests marked `live` (only `make test-live`) are the
exception and talk to real catalogues.

Fixtures are in tests/_fixtures/ and registered here. See the `write-tests`
skill.
"""

pytest_plugins = [
    "pytester",
    "tests._fixtures.settings",
    "tests._fixtures.adapters",
]
