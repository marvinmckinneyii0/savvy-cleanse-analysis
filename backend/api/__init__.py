"""Backend HTTP API layer (Presentation tier).

Currently hosts a single endpoint — the server-side spreadsheet parser that
replaced the removed client-side SheetJS dependency. Epic 3 (Phase 3 — Web
Application) will expand this package into the full customer/admin API surface;
until then it deliberately stays minimal.

Per the three-layer separation in architecture.md, modules here may import from
``pipeline`` / ``models`` but never the reverse.
"""
