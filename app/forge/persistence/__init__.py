"""FORGE persistence layer (Book II / Bloc II.2).

Domain vs persistence boundary:
- `app.forge.canonical`, `app.forge.schemas`, `app.forge.provenance` are pure
  domain and never import persistence or DB libraries.
- `app.forge.persistence.*` implements the durable-truth substrate behind an
  explicit port. It stores canonical state; it never redefines canonical
  semantics ("Persistence != Canonical Authority").
"""
