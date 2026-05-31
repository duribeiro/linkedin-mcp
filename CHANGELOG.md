# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1](https://github.com/duribeiro/linkedin-mcp/compare/linkedin-mcp-v1.3.0...linkedin-mcp-v1.3.1) (2026-05-31)


### 🔧 Fix

* adjust README version badge URL to prevent semver parsing issues ([5851453](https://github.com/duribeiro/linkedin-mcp/commit/5851453704b9339d4db6cb5d4eb9f388bc531447))
* adjust README version badge URL to prevent semver parsing issues ([5851453](https://github.com/duribeiro/linkedin-mcp/commit/5851453704b9339d4db6cb5d4eb9f388bc531447))
* adjust README version badge URL to prevent semver parsing issues ([f875a35](https://github.com/duribeiro/linkedin-mcp/commit/f875a35797f567c803913ca0aa01b20299038661))


### 📝 Docs

* customize readme title as duribeiro ([a24ec59](https://github.com/duribeiro/linkedin-mcp/commit/a24ec59d7e17868c6cd2d20547efa13fee5eb8e0))
* edit readme title as mouraneto ([d178128](https://github.com/duribeiro/linkedin-mcp/commit/d178128db8c112078604857337da22d642a83b77))

## [1.3.0](https://github.com/duribeiro/linkedin-mcp/compare/linkedin-mcp-v1.2.0...linkedin-mcp-v1.3.0) (2026-05-31)


### ✨ Feat

* add Codex PR Reviewer workflow ([2f4cdaa](https://github.com/duribeiro/linkedin-mcp/commit/2f4cdaa3dac2224341b084f9c0d232edc27daea3))

## [1.2.0](https://github.com/duribeiro/linkedin-mcp/compare/linkedin-mcp-v1.1.0...linkedin-mcp-v1.2.0) (2026-05-30)


### Features

* add release-please GitHub Actions workflow and config ([2f31d39](https://github.com/duribeiro/linkedin-mcp/commit/2f31d399814a71f5e0014a33bd07e7e2d689544b))
* configure automated release-please workflow ([a45a900](https://github.com/duribeiro/linkedin-mcp/commit/a45a90083ad48d3ff515f66507e8d8ee3159c22b))
* migrate to /rest/posts API and add image upload support ([#2](https://github.com/duribeiro/linkedin-mcp/issues/2)) ([e364406](https://github.com/duribeiro/linkedin-mcp/commit/e3644064ae94662679571938b459d7944ba8f183))
* migrate to /rest/posts API, add upload_image, share_link, and format_linkedin ([1467d2d](https://github.com/duribeiro/linkedin-mcp/commit/1467d2dd3a724083731bce1c083a6324449bda86))


### Bug Fixes

* populate release-please workflow content ([639103e](https://github.com/duribeiro/linkedin-mcp/commit/639103e40ba267af6cbb97d430d88c0df2ed9bb4))
* populate release-please workflow content ([#4](https://github.com/duribeiro/linkedin-mcp/issues/4)) ([0351266](https://github.com/duribeiro/linkedin-mcp/commit/03512663c16b8b1de5a2f297322732f653a50f24))
* remove /v2/me calls — reuse /v2/userinfo for liteprofile ([8096fdf](https://github.com/duribeiro/linkedin-mcp/commit/8096fdfd816dfeb1927647dfb92d55496c184e03))
* remove duplicate asyncio import ([e04f124](https://github.com/duribeiro/linkedin-mcp/commit/e04f124eee8f9c645ac08a849d217a26ee900ddf))
* rename linkedin-config.json -&gt; linkedin_config.json for auth.py import ([960772b](https://github.com/duribeiro/linkedin-mcp/commit/960772b5e5bbb8539136742a391af98f8bc00748))
* resolve all ruff lint errors (F401, F841, E402) ([3875bee](https://github.com/duribeiro/linkedin-mcp/commit/3875beec192e9eefe7e084174387b9554e204354))
* resolve Codex review feedback on config path and create_post image_urn ([c048b64](https://github.com/duribeiro/linkedin-mcp/commit/c048b6471effba9e506d9782202dbf577ae030c7))


### Documentation

* add CONTRIBUTING.md, CHANGELOG.md, PR template, and CI workflow ([31673d1](https://github.com/duribeiro/linkedin-mcp/commit/31673d18801a16c6c29864b49eac241ce7ea2a33))
* translate CHANGELOG, CONTRIBUTING, and PR template to English ([0aa3c4a](https://github.com/duribeiro/linkedin-mcp/commit/0aa3c4a115d07bacdf41157e0c5433717aa2f065))
* update README and CHANGELOG for release v1.1.0 ([dbff614](https://github.com/duribeiro/linkedin-mcp/commit/dbff614366212032ee676e038585ce7f471bf95f))

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
