# Bookworm

This is a project aimed at using tools like Playwright, API calls, and others to webcrawl and explore online library catalogues so we can know if a book we're looking for is available in x library.

We're gonna be using Mexico City as a usecase. We need to map all the libraries we have in the city. We need to create a database that has all the data needed of each library to know how to interact with it.

## The problem

Mexico City has no single catalogue that covers all its libraries. The 16 alcaldías run more than 200 neighborhood public libraries, and the city network's site ([Red de Bibliotecas Públicas CDMX](https://web.sectei.cdmx.gob.mx/bibliotecas/red/)) mostly offers directories and open-access links, not a combined book search. Most small branches have no online catalogue at all, so the only way to check them is to call or visit.

The large collections do have searchable catalogues, and they hold most of what people look for. But each one runs different software, with different search interfaces, URL schemes and levels of machine access. Bookworm's job is to know, for each library, how to ask "do you have this book?" and how to read the answer.

## Library landscape

| Library | Catalogue | Software | Machine access | Status |
|---|---|---|---|---|
| UNAM Descubridor | `bibmacro-descubridor.dgb.unam.mx` | VuFind 9.0 | Clean search URLs (`/Search/Results?lookfor=Maffie&type=Author`); exports to RefWorks/EndNote; REST API possible | Verified |
| Biblioteca Nacional (Nautilo) | `nautilo.iib.unam.mx` | Likely VuFind (`/Record/<id>` pattern) | Record pages show call number and copy availability | Verified (software not confirmed) |
| LIBRUNAM | Via `bibliotecas.unam.mx` | Unknown | Current direct URL not found yet | Not verified |
| UAM Iztapalapa | `biblioteca.izt.uam.mx/vufind` | VuFind | Same as other VuFind instances, if enabled | Not verified |
| Biblioteca Vasconcelos | `bibliotecavasconcelos.gob.mx` | Unknown | Web UI only (author, title, subject, keyword); blocked automated fetches | Not verified |
| Biblioteca de México | `bibliotecademexico.gob.mx` | Possibly Aleph (per an older UNAM thesis) | Web UI only (Base / Método / Término form, results open in new tab); **robots.txt blocks automated access** | Not verified |
| Alcaldía branch libraries (200+) | None | — | Phone or in person | — |

"Verified" means the catalogue page was actually loaded and inspected. Everything else is inferred from search results or the software it appears to run.

### Notes on the main collections

- **Biblioteca Vasconcelos** (Buenavista): about 580,000 books. The call number in a result shows where the book sits on the shelves. Its [interlibrary loan page](https://bibliotecavasconcelos.gob.mx/info_detalle.php?id=51) lists agreements with UNAM, UAM, Instituto Mora, ITAM, the Benjamin Franklin library and several Miguel Hidalgo branches, each with a catalogue link, so it works as a rough directory of other catalogues.
- **Biblioteca de México** (La Ciudadela): a main catalogue search on its homepage, plus a separate catalogue for rare works from the 15th to 20th centuries.
- **LIBRUNAM**: the closest thing Mexico City has to a union catalogue, covering UNAM's many libraries. Anyone can search it. Borrowing is usually limited to the UNAM community, but many UNAM libraries let the public read on site.
- **Biblioteca Nacional (Nautilo)**: strong on Mexican publications.
- **Specialized libraries**: for academic or foreign-language titles, specialized collections such as UNAM's Instituto de Investigaciones Filosóficas or El Colegio de México are often better bets than the public network.
- **WorldCat** may help cover private universities that aren't reachable otherwise.

## Integration approaches

Libraries fall roughly into three groups, which shapes how Bookworm talks to each one:

1. **VuFind instances** (UNAM Descubridor, Nautilo, UAM Iztapalapa, possibly others). VuFind 9 ships a REST API at `/api/v1/search` that returns JSON, but each library decides whether to turn it on. When it's on, this is the cleanest path. When it's off, VuFind's predictable search URLs make HTML scraping straightforward. One adapter should cover all of them. Quick check: `https://bibmacro-descubridor.dgb.unam.mx/api/v1/search?lookfor=maffie` returns JSON if the API is enabled.
2. **Custom or legacy web catalogues** (Vasconcelos, Biblioteca de México). Web UI only, so these need browser automation (Playwright) or form scraping, with a specific adapter per site. Respect each site's robots.txt and terms; Biblioteca de México currently disallows automated access.
3. **No online catalogue** (most alcaldía branches). These can't be searched automatically. The database should still record them, with address and contact details, so the user knows where to call or visit.

## Library database

For each library, the database should record what's needed to interact with it, for example:

- Name, address, alcaldía, contact details
- Catalogue URL(s) and catalogue software (VuFind, Aleph, unknown, none)
- Access method (REST API, HTML scraping, browser automation, manual only) and whether automated access is allowed
- Lending policy (public borrowing, UNAM-only borrowing, on-site reading only)
- Interlibrary loan partners
- Verification status and date last checked

## Sources

- [Biblioteca Vasconcelos – info](https://bibliotecavasconcelos.gob.mx/info_detalle.php?id=14)
- [Biblioteca Vasconcelos – interlibrary loan partners](https://bibliotecavasconcelos.gob.mx/info_detalle.php?id=51)
- [Biblioteca Vasconcelos – how to search (Tumblr Q&A)](https://www.tumblr.com/vasconceloslibrary/156595351282/como-buscar-libro)
- [Biblioteca de México](https://bibliotecademexico.gob.mx/)
- [Red de Bibliotecas Públicas CDMX](https://web.sectei.cdmx.gob.mx/bibliotecas/red/)
- [UNAM Descubridor record (VuFind 9.0)](https://bibmacro-descubridor.dgb.unam.mx/Record/20.500.14330-TES01000195727/Description)
- [Nautilo record example](https://nautilo.iib.unam.mx/Record/000587809)
- [UAM Iztapalapa VuFind](https://biblioteca.izt.uam.mx/vufind/Record/musev2_2208/Holdings?lng=en)
- [UNAM thesis on LIBRUNAM](https://ru.dgb.unam.mx/jspui/bitstream/20.500.14330/TES01000349609/3/0349609.pdf)
- [UNAM thesis on Biblioteca de México's Aleph OPAC](https://ru.dgb.unam.mx/jspui/bitstream/20.500.14330/TES01000295088/3/295088.pdf)
