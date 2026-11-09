# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-11-09

### Added

- Clipboard, active window and shell command capture.
- Summaries and tags from a local Ollama model.
- Keyword and semantic search with sentence-transformers.
- OCR for images copied to the clipboard.
- GNOME Wayland window tracking through the Window Calls extension.
- Filter that replaces text that looks like a credential before saving.
- Automatic upgrade for databases made by an older schema.
- `capture.sh`, CI, tests, and contributor docs.

### Changed

- One event pipeline shared by the backend and the local runner.
- All ports published on localhost, and CORS limited to the dashboard.
- Unknown exit codes now show as unknown instead of failed.

### Fixed

- Clipboard, stats and search failing on a fresh database.
- Backend exiting on a fresh start before Postgres was ready.
- Agents stopping after the first request.
- Shell commands being lost when several arrived together.

[0.1.0]: https://github.com/jayhemnani9910/agentic-logger/releases/tag/v0.1.0
