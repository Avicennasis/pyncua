# Changelog

All notable changes to `pyncua` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Realign the `ruff-pre-commit` `rev` in `.pre-commit-config.yaml` with the
  `ruff==0.16.4` pin in `pyproject.toml` and `uv.lock`. The three had drifted:
  a dependency bump moved two of them and left pre-commit on `v0.15.22`, so
  pre-commit and CI were enforcing different default rule sets — the exact
  failure both files' comments warn against. No lint findings resulted; the
  tree passes clean under both versions, so the drift was latent. (#49722)

### Added
- Initial project scaffolding.
