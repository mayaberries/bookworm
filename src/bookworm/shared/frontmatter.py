"""
Reading and writing record files: Markdown with YAML frontmatter.

WHY MARKDOWN AND NOT PLAIN YAML OR JSON
    A record has two readers. The code reads the frontmatter, validated by a
    model. A person reads the notes under it: how the catalogue behaves, what
    was tried, why a field has the value it has. Keeping both in one file
    means they're edited and reviewed together, and the folder opens as an
    Obsidian vault with the frontmatter shown as properties. See
    docs/DECISIONS.md, "Records are Markdown files".

This module only splits a file into (frontmatter dict, body). It knows
nothing about libraries or catalogues; the repositories do.
"""

from pathlib import Path
from typing import Any

import yaml

from bookworm.shared.errors import InvalidRecordError

DELIMITER = "---"


def read_record(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != DELIMITER:
        raise InvalidRecordError(f"{path}: must start with a '---' line opening the YAML frontmatter")
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == DELIMITER)
    except StopIteration:
        raise InvalidRecordError(f"{path}: the frontmatter has no closing '---' line") from None

    try:
        data = yaml.safe_load("".join(lines[1:end])) or {}
    except yaml.YAMLError as exc:
        raise InvalidRecordError(f"{path}: the frontmatter isn't valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise InvalidRecordError(f"{path}: the frontmatter must be a mapping of fields")
    return data, "".join(lines[end + 1 :]).strip()


def write_record(path: Path, data: dict[str, Any], body: str = "") -> None:
    front = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    path.write_text(f"{DELIMITER}\n{front}{DELIMITER}\n\n{body.strip()}\n", encoding="utf-8")
