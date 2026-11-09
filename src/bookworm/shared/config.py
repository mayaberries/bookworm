"""
The app's settings. See the `add-setting` skill.

Bookworm is an app, so it reads the environment (prefix `BOOKWORM_`, or a
`.env` at the repo root). Everything has a default that works from a fresh
clone. Settings are *how bookworm behaves everywhere*; anything about one
catalogue (its URL, its rate limit, its options) belongs in that catalogue's
record in `data/catalogues/`, not here.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOOKWORM_", env_file=".env", extra="ignore")

    data_dir: Path = Field(
        default=REPO_ROOT / "data", description="Where the library and catalogue records live."
    )

    # Identifies the client honestly without naming a person. Catalogues that
    # want to reach whoever runs it get the project URL once there is one.
    user_agent: str = "bookworm/0.1 (library availability checker)"
    http_timeout_seconds: float = Field(default=20.0, gt=0)

    # How many catalogues one lookup asks at the same time. Each catalogue's
    # own pace is its record's `min_seconds_between_requests`.
    max_concurrent_catalogues: int = Field(default=4, ge=1)

    browser_headless: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
