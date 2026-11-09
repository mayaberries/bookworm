"""
The directory: every library and catalogue bookworm knows, as record files
in `data/`. Other modules import from here, never from its files.
"""

from pathlib import Path

from bookworm.modules.directory.repository import CataloguesRepository, LibrariesRepository
from bookworm.modules.directory.schemas import (
    AccessMethod,
    Alcaldia,
    Automation,
    Catalogue,
    CatalogueSystem,
    DirectoryIssue,
    Lending,
    Library,
    LibraryKind,
    VerificationStatus,
)
from bookworm.modules.directory.service import DirectoryService


def build_directory_service(data_dir: Path) -> DirectoryService:
    return DirectoryService(
        libraries_repo=LibrariesRepository(data_dir), catalogues_repo=CataloguesRepository(data_dir)
    )


__all__ = [
    "AccessMethod",
    "Alcaldia",
    "Automation",
    "Catalogue",
    "CatalogueSystem",
    "DirectoryIssue",
    "DirectoryService",
    "Lending",
    "Library",
    "LibraryKind",
    "VerificationStatus",
    "build_directory_service",
]
