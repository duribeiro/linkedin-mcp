# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Extended profile endpoint with full user data (in `dev`)
- New MCP tool for feed interaction (in `dev`)
- `.github/` structure with PR template and CI workflow

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
