# Directory Board

Every library and catalogue on record, from `data/libraries/` and `data/catalogues/`. The tables read each record's frontmatter live, so to change something, edit the record, not the board. New records: a new note in the right folder, then *Templates: Insert template*. `make check-records` validates them.

## Libraries

```dataview
TABLE WITHOUT ID
  file.link AS "Library",
  kind AS "Kind",
  alcaldia AS "Alcaldía",
  choice(catalogue, link("data/catalogues/" + catalogue), "—") AS "Catalogue",
  lending AS "Lending",
  verification.status AS "Verified",
  verification.checked_on AS "Checked"
FROM "data/libraries"
SORT alcaldia ASC, file.name ASC
```

## Catalogues

Bookworm only searches catalogues with `automation: allowed` and at least one access method.

```dataview
TABLE WITHOUT ID
  file.link AS "Catalogue",
  system AS "Software",
  automation AS "Automation",
  robots_checked_on AS "robots.txt checked",
  map(access, (a) => a.adapter) AS "Adapters",
  verification.status AS "Verified"
FROM "data/catalogues"
SORT file.name ASC
```

## No online catalogue: call or visit

```dataview
TABLE WITHOUT ID
  file.link AS "Library",
  alcaldia AS "Alcaldía",
  address AS "Address",
  contact.phone AS "Phone"
FROM "data/libraries"
WHERE !catalogue
SORT alcaldia ASC, file.name ASC
```

## To check

Catalogues whose robots.txt and terms nobody has read yet, and records not yet verified.

```dataview
TABLE WITHOUT ID
  file.link AS "Record",
  file.folder AS "Folder",
  automation AS "Automation",
  verification.status AS "Verified",
  verification.source AS "Source"
FROM "data/libraries" OR "data/catalogues"
WHERE automation = "unknown" OR verification.status != "verified"
SORT file.folder ASC, file.name ASC
```
