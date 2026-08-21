# Repository instructions

Global agent instructions apply. This repository adds the following rules:

- `schemas/v1/` is the public contract. A released schema is immutable; compatible additions require a
  new minor schema version and breaking changes require a new major directory.
- Examples must be synthetic unless an exact media/publication grant is checked in and referenced.
- Never call a demonstration blind, sealed, unbiased, or independent.
- Official and community registries remain separate in storage, UI, and language.
- Unknown licensing state never renders as clear.
- Do not add `.github/workflows`; Forgejo is authoritative and GitHub Actions remain disabled.
- Run `ruff check .`, `mypy src`, and `pytest` before publishing a PR.
