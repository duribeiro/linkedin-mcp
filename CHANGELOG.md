# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Endpoint de perfil estendido com dados completos do usuário (em `dev`)
- Nova ferramenta MCP para interação com feed (em `dev`)
- Estrutura `.github/` com PR template e CI workflow

## [1.0.0] - 2026-05-12

### Added
- Servidor MCP funcional para LinkedIn API
- Ferramenta de perfil (`tools/profile.py`) — dados básicos via `/v2/userinfo`
- Ferramenta de posts (`tools/posts.py`) — criar e listar posts
- Ferramenta de feed (`tools/feed.py`) — feed do usuário
- Ferramenta de artigos (`tools/articles.py`) — artigos long-form
- Ferramenta de estatísticas (`tools/insights.py`) — métricas de posts
- Autenticação OAuth 2.0 com LinkedIn (`auth.py`)
- Documentação completa (`README.md`)
- Licença MIT
