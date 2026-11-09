"""Infrastructure fixtures: an empty data/ per test and Settings pointing at it."""

from pathlib import Path

import pytest

from bookworm.shared.config import Settings


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    for folder in ("libraries", "catalogues"):
        (tmp_path / "data" / folder).mkdir(parents=True)
    return tmp_path / "data"


@pytest.fixture
def settings(data_dir: Path) -> Settings:
    return Settings(data_dir=data_dir, http_timeout_seconds=1.0, max_concurrent_catalogues=4)
