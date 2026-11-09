---
name: UNAM Descubridor
system: vufind
system_version: '9.0'
base_url: https://bibmacro-descubridor.dgb.unam.mx
automation: unknown
access: []
verification:
  status: verified
  source: README landscape table (catalogue page loaded and inspected)
---

UNAM's discovery layer. Clean search URLs
(`/Search/Results?lookfor=Maffie&type=Author`) and exports to RefWorks/EndNote.

- To check: whether the VuFind REST API is on
  (`/api/v1/search?lookfor=maffie` returns JSON if it is).
- To check: robots.txt, then set `automation`.
- Example record: <https://bibmacro-descubridor.dgb.unam.mx/Record/20.500.14330-TES01000195727/Description>
