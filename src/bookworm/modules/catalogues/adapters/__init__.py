"""
Every adapter bookworm ships. Importing this package registers them.

One sub-package per catalogue system (`vufind/`, `aleph/`), or per site for
custom catalogues (`vasconcelos/`), with one module per access method and a
`mapping.py` of pure raw → canonical functions they share. See the
`create-adapter` skill.

Add the import here when you add an adapter; nothing is discovered.
"""

# from bookworm.modules.catalogues.adapters.vufind import api as vufind_api  # noqa: F401
