# Changelog

All notable changes to `pyncua` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-08-25

### Changed
- **`take` above 100 now raises `NCUAValidationError` instead of silently
  returning 100 rows.** The NCUA API caps `take` server-side without signalling
  it, while still reporting the true unpaginated count in `total_result_count` —
  so `take=500` returned 100 rows that a caller could easily mistake for the
  complete result set. Verified identical across all four paginated endpoints.
  Callers who relied on the old behaviour were receiving truncated data; page
  with `skip` in steps of 100 instead (see README ➝ Pagination).
- `skip < 0` and `take < 1` are likewise rejected client-side, before any
  request is issued. Both clients share the guard via `_requests.py`.

### Fixed
- Synced the `ruff-pre-commit` rev (was `v0.15.22`) with the `ruff==0.16.4` pin
  in `pyproject.toml` and `uv.lock`. They had diverged in #17, leaving CI and
  pre-commit enforcing different rule sets — the exact failure both files'
  comments warn about.
- `renovate.json` now enables the `pre-commit` manager and groups the ruff
  pin with the pre-commit rev into a single PR, so the two cannot drift apart
  again. Without the manager enabled, Renovate updated `pyproject.toml` alone.
- Formatted `README.md` and `docs/*.md` under ruff 0.16, which formats Python
  code blocks inside Markdown.

### Documentation
- Documented the 100-row `take` cap and a correct `skip` pagination loop.
- Documented that an unresolvable address returns `valid=True` with an empty
  `offices` list rather than raising — callers must check the list. The
  `valid=false` branch appears not to trigger for unresolvable input.
- Documented that `find_offices_by_address` (branch geography) and
  `search_credit_unions` (headquarters city) answer different questions.

### Added
- Initial project scaffolding.
