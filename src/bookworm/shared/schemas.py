"""
The model bases. Every model in bookworm extends one of these.

Same bases as Sinapsis' `shared/schemas.py` (the reference for Kalens and
Xolo too), minus what only an HTTP API needs. See the `create-model` skill.
"""

from pydantic import BaseModel, ConfigDict


class CoreModel(BaseModel):
    """Every model. Common config goes here."""


class InputModel(CoreModel):
    """Everything a person or a file supplies: CLI queries and record
    frontmatter. Unknown fields are an error, not silently dropped: a typo'd
    key in a library's record must not look like it was accepted."""

    model_config = ConfigDict(extra="forbid")


class FrozenModel(CoreModel):
    """Values handed between layers (canonical search results, reports).
    Frozen, so a layer can't change what another layer already decided."""

    model_config = ConfigDict(frozen=True)
