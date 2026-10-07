"""FORGE service / transport layer.

Domain vs service boundary:
- `app.forge.canonical`, `app.forge.schemas`, `app.forge.provenance`
  remain pure domain. They do NOT import FastAPI or any transport concern.

- `app.forge.service.*` is the FORGE application/service layer. It may import
  from `app.forge.*` and from FastAPI.
"""
