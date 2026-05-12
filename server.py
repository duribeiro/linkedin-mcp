"""LinkedIn MCP Server — API REST oficial para contas pessoais.

Endpoints:
  - Profile:   /v2/me, /v2/userinfo
  - Posts:     POST /v2/ugcPosts         (scope: w_member_social)
  - Articles:  POST /v2/ugcPosts         (shareMediaCategory=ARTICLE)
  - Insights:  /v2/socialActions/{urn}/shareStatistics
  - Feed:      /v2/shares

Autor: Theo (Hermes Agent) — Licença MIT
"""

import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from auth import LinkedInAuth

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("linkedin-mcp")

server = Server("linkedin-mcp")
auth = LinkedInAuth()


# ═══════════════════════════════════════════════════════════════════════
# Tool implementations
# ═══════════════════════════════════════════════════════════════════════

import httpx


async def _get_headers():
    token = await auth.get_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202510",
    }


# ── Profile ──────────────────────────────────────────────────────────

async def get_my_profile(sections: str = "all") -> list[TextContent]:
    headers = await _get_headers()
    person_urn = await auth.get_person_urn()
    parts = {}

    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {await auth.get_access_token()}"},
        )
        r.raise_for_status()
        parts["basic"] = r.json()

    if sections in ("all", "liteprofile"):
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.linkedin.com/v2/me", headers=headers)
            r.raise_for_status()
            parts["liteprofile"] = r.json()

    return [TextContent(type="text", text=json.dumps(parts, indent=2, ensure_ascii=False))]


# ── Posts ────────────────────────────────────────────────────────────

async def create_post(
    text: str,
    url: str = "",
    visibility: str = "PUBLIC",
) -> list[TextContent]:
    person_urn = await auth.get_person_urn()
    headers = await _get_headers()
    headers["Content-Type"] = "application/json"

    body = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "shareCommentary": {"text": text},
            "shareMediaCategory": "ARTICLE" if url else "NONE",
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
    }

    if url:
        body["specificContent"]["media"] = [{
            "status": "READY",
            "originalUrl": url,
        }]

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=body)

        result = {
            "status": r.status_code,
            "share_id": r.headers.get("X-RestLi-Id", ""),
        }
        if r.status_code >= 400:
            result["error"] = r.text[:500]
        else:
            result["success"] = True

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


# ── Articles ─────────────────────────────────────────────────────────

async def create_article(
    title: str,
    body_text: str,
    description: str = "",
    visibility: str = "PUBLIC",
) -> list[TextContent]:
    person_urn = await auth.get_person_urn()
    headers = await _get_headers()
    headers["Content-Type"] = "application/json"

    commentary = f"{title}\n{description}" if description else title

    body = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "shareCommentary": {"text": commentary},
            "shareMediaCategory": "ARTICLE",
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
    }

    # Adiciona corpo do artigo
    if body_text:
        body["specificContent"]["shareContent"] = {
            "shareMediaCategory": "ARTICLE",
            "description": {"text": description or title},
            "title": title,
        }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=body)
        result = {
            "status": r.status_code,
            "share_id": r.headers.get("X-RestLi-Id", ""),
        }
        if r.status_code >= 400:
            result["error"] = r.text[:500]
            result["request_body"] = body
        else:
            result["success"] = True
        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def get_my_articles(count: int = 10) -> list[TextContent]:
    person_urn = await auth.get_person_urn()
    headers = await _get_headers()
    url = f"https://api.linkedin.com/v2/shares?q=owners&owners={person_urn}&count={min(count, 50)}&sortBy=CREATED"

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            return [TextContent(type="text", text=json.dumps({"error": r.status_code, "message": r.text[:500]}))]

        data = r.json()
        articles = []
        for element in data.get("elements", []):
            specific = element.get("specificContent", {})
            cat = specific.get("shareMediaCategory", "")
            content = specific.get("shareContent", {})
            if cat == "ARTICLE" or content:
                articles.append({
                    "id": element.get("id", ""),
                    "title": content.get("title", ""),
                    "text": specific.get("shareCommentary", {}).get("text", ""),
                    "created": element.get("created", {}).get("time", ""),
                })

        return [TextContent(type="text", text=json.dumps({"total": len(articles), "articles": articles}, indent=2, ensure_ascii=False))]


# ── Insights ────────────────────────────────────────────────────────

async def get_share_stats(share_id: str) -> list[TextContent]:
    headers = await _get_headers()
    url = f"https://api.linkedin.com/v2/socialActions/{share_id}/shareStatistics"

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        stats = {
            "share_id": share_id,
            "impressions": data.get("totalShareStatistics", {}).get("impressionCount", 0),
            "likes": data.get("totalShareStatistics", {}).get("likeCount", 0),
            "comments": data.get("totalShareStatistics", {}).get("commentCount", 0),
            "shares": data.get("totalShareStatistics", {}).get("shareCount", 0),
            "clicks": data.get("totalShareStatistics", {}).get("clickCount", 0),
        }
        return [TextContent(type="text", text=json.dumps(stats, indent=2))]


# ── Feed ─────────────────────────────────────────────────────────────

async def get_my_feed(count: int = 10) -> list[TextContent]:
    person_urn = await auth.get_person_urn()
    headers = await _get_headers()
    url = f"https://api.linkedin.com/v2/shares?q=owners&owners={person_urn}&count={min(count, 50)}&sortBy=CREATED"

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            return [TextContent(type="text", text=json.dumps({"error": r.status_code, "message": r.text[:500]}))]

        data = r.json()
        posts = []
        for element in data.get("elements", []):
            specific = element.get("specificContent", {})
            posts.append({
                "id": element.get("id", ""),
                "text": specific.get("shareCommentary", {}).get("text", ""),
                "category": specific.get("shareMediaCategory", ""),
                "created": element.get("created", {}).get("time", 0),
            })

        return [TextContent(type="text", text=json.dumps({"total": len(posts), "posts": posts}, indent=2, ensure_ascii=False))]


# ═══════════════════════════════════════════════════════════════════════
# Tool registry
# ═══════════════════════════════════════════════════════════════════════

TOOLS = {
    "get_my_profile": Tool(
        name="get_my_profile",
        description="Retorna o perfil do LinkedIn do usuário autenticado. sections: 'all', 'basic', 'liteprofile'.",
        inputSchema={
            "type": "object",
            "properties": {
                "sections": {"type": "string", "description": "Partes do perfil: 'all', 'basic', 'liteprofile'"}
            },
        },
    ),
    "create_post": Tool(
        name="create_post",
        description="Cria um post no LinkedIn da conta autenticada. text: texto do post. url: link opcional para compartilhar. visibility: 'PUBLIC' (padrão) ou 'CONNECTIONS'.",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto do post"},
                "url": {"type": "string", "description": "URL opcional para compartilhar (card)"},
                "visibility": {"type": "string", "description": "PUBLIC ou CONNECTIONS"},
            },
            "required": ["text"],
        },
    ),
    "create_article": Tool(
        name="create_article",
        description="Publica um artigo (long-form) no LinkedIn. title: título. body_text: corpo do artigo. description: subtítulo opcional.",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título do artigo"},
                "body_text": {"type": "string", "description": "Corpo do artigo (texto)"},
                "description": {"type": "string", "description": "Subtítulo/descrição curta (opcional)"},
                "visibility": {"type": "string", "description": "PUBLIC ou CONNECTIONS"},
            },
            "required": ["title", "body_text"],
        },
    ),
    "get_my_articles": Tool(
        name="get_my_articles",
        description="Lista os últimos artigos publicados no LinkedIn. count: quantos retornar (padrão 10).",
        inputSchema={
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Quantos artigos retornar (padrão: 10)"},
            },
        },
    ),
    "get_share_stats": Tool(
        name="get_share_stats",
        description="Retorna estatísticas (impressões, likes, comentários, compartilhamentos) de um post/artigo.",
        inputSchema={
            "type": "object",
            "properties": {
                "share_id": {"type": "string", "description": "URN do post (ex: urn:li:share:7123456789)"},
            },
            "required": ["share_id"],
        },
    ),
    "get_my_feed": Tool(
        name="get_my_feed",
        description="Retorna os posts recentes do feed do usuário autenticado.",
        inputSchema={
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Quantos posts retornar (padrão: 10, máx: 50)"},
            },
        },
    ),
}

HANDLERS = {
    "get_my_profile": get_my_profile,
    "create_post": create_post,
    "create_article": create_article,
    "get_my_articles": get_my_articles,
    "get_share_stats": get_share_stats,
    "get_my_feed": get_my_feed,
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    return list(TOOLS.values())


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    handler = HANDLERS.get(name)
    if not handler:
        raise ValueError(f"Unknown tool: {name}")
    logger.info("Tool called: %s(%s)", name, arguments)
    return await handler(**arguments)


# ═══════════════════════════════════════════════════════════════════════
# Entrypoint
# ═══════════════════════════════════════════════════════════════════════

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run():
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    run()
