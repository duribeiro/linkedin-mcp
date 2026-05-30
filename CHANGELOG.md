# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-05-30

### ✨ Feat
- **server.py**: Add `upload_image` tool to upload images to LinkedIn API.
- **server.py**: Add `image_path` parameter to `create_post` to support posting images.
- **server.py**: Add `share_link` tool to share URLs with customized preview cards (title, description, thumbnail).
- **tests**: Add basic smoke tests (`tests/test_basic.py`) using `pytest`.
- **.github**: Add pull request template and CI workflow for automated testing.

### 🔧 Fix
- **server.py**: Replace obsolete/broken `create_article` tool with `share_link`.
- **server.py**: Fix bug in `create_post` by initializing `image_urn = None` to prevent `UnboundLocalError` when posting without an image.
- **auth.py**: Fix path resolution for `linkedin_config.json` to prevent errors when executed outside the project root directory.
- **server.py**: Remove duplicate `asyncio` import.
- **server.py**: Resolve ruff linting errors.

### ♻️ Refactor
- **auth.py**: Move credentials configuration to a secure `linkedin_config.json` file.
- **server.py**: Add `format_linkedin` helper for automatic markdown-like bold/italic text translation to Unicode characters.

## [1.0.0] - 2026-05-12

### Added
- Functional MCP server for LinkedIn API
- Profile tool (`tools/profile.py`) — basic data via `/v2/userinfo`
- Posts tool (`tools/posts.py`) — create and list posts
- Feed tool (`tools/feed.py`) — user feed
- Articles tool (`tools/articles.py`) — long-form articles
- Insights tool (`tools/insights.py`) — post metrics
- OAuth 2.0 authentication with LinkedIn (`auth.py`)
- Full documentation (`README.md`)
- MIT License
