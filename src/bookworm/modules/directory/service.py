"""
The directory's use cases: finding libraries and catalogues, and the rules
that span records (a library's catalogue must exist, its loan partners too).

The repositories read one folder each; anything that needs both, or that
decides "missing is an error", is here. See the `create-service` skill.
"""

from bookworm.modules.directory.repository import CataloguesRepository, LibrariesRepository
from bookworm.modules.directory.schemas import Alcaldia, Catalogue, DirectoryIssue, Library
from bookworm.shared.errors import InvalidRecordError, NotFoundError


class DirectoryService:
    def __init__(self, *, libraries_repo: LibrariesRepository, catalogues_repo: CataloguesRepository) -> None:
        self.libraries_repo = libraries_repo
        self.catalogues_repo = catalogues_repo

    def get_library(self, *, slug: str) -> Library:
        library = self.libraries_repo.get(slug=slug)
        if library is None:
            raise NotFoundError(f"No library '{slug}' in data/libraries/.")
        return library

    def get_catalogue(self, *, slug: str) -> Catalogue:
        catalogue = self.catalogues_repo.get(slug=slug)
        if catalogue is None:
            raise NotFoundError(f"No catalogue '{slug}' in data/catalogues/.")
        return catalogue

    def list_libraries(
        self, *, alcaldia: Alcaldia | None = None, catalogue: str | None = None
    ) -> list[Library]:
        libraries = self.libraries_repo.list_all()
        if alcaldia is not None:
            libraries = [lib for lib in libraries if lib.alcaldia is alcaldia]
        if catalogue is not None:
            libraries = [lib for lib in libraries if lib.catalogue == catalogue]
        return libraries

    def list_catalogues(self) -> list[Catalogue]:
        return self.catalogues_repo.list_all()

    def catalogues_for(self, *, libraries: list[Library]) -> dict[str, Catalogue]:
        """The catalogues those libraries point at, by slug, each loaded once."""
        slugs = sorted({lib.catalogue for lib in libraries if lib.catalogue})
        return {slug: self.get_catalogue(slug=slug) for slug in slugs}

    def check_records(self) -> list[DirectoryIssue]:
        """Every problem in data/, without stopping at the first: each file
        parses and matches its model, and every slug a record names exists.
        Whether each catalogue's adapters are registered is the catalogues
        module's check (`check_access`)."""
        issues: list[DirectoryIssue] = []

        catalogues: dict[str, Catalogue] = {}
        for path in self.catalogues_repo.list_paths():
            try:
                catalogues[path.stem] = self.catalogues_repo.load(path)
            except InvalidRecordError as exc:
                issues.append(DirectoryIssue(path=str(path), detail=exc.detail))

        libraries: dict[str, Library] = {}
        for path in self.libraries_repo.list_paths():
            try:
                libraries[path.stem] = self.libraries_repo.load(path)
            except InvalidRecordError as exc:
                issues.append(DirectoryIssue(path=str(path), detail=exc.detail))

        for slug, library in libraries.items():
            where = str(self.libraries_repo.files.path_for(slug))
            if library.catalogue and library.catalogue not in catalogues:
                issues.append(
                    DirectoryIssue(path=where, detail=f"catalogue: no catalogue '{library.catalogue}'")
                )
            for partner in library.interlibrary_loan:
                if partner not in libraries:
                    issues.append(
                        DirectoryIssue(path=where, detail=f"interlibrary_loan: no library '{partner}'")
                    )

        return issues
