"""Tools de feed — LinkedIn Shares API."""

import json
import httpx
from auth import LinkedInAuth


def register_feed_tools(server, auth: LinkedInAuth):
    """Registra tools de feed/timeline no MCP server."""

    @server.tool()
    async def get_my_feed(count: int = 10) -> str:
        """Retorna os posts recentes do feed do usuário autenticado.

        Args:
            count: Quantos posts retornar (padrão: 10, máx: 50)
        """
        person_urn = await auth.get_person_urn()
        headers = await auth.get_headers()

        url = f"https://api.linkedin.com/v2/shares?q=owners&owners={person_urn}&count={min(count, 50)}&sortBy=CREATED"

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                return json.dumps({"error": r.status_code, "message": r.text[:500]}, indent=2)

            data = r.json()
            posts = []

            for element in data.get("elements", []):
                specific = element.get("specificContent", {})
                posts.append({
                    "id": element.get("id", ""),
                    "text": specific.get("shareCommentary", {}).get("text", ""),
                    "category": specific.get("shareMediaCategory", "NONE"),
                    "created": element.get("created", {}).get("time", 0),
                    "visibility": element.get("visibility", {}).get(
                        "com.linkedin.ugc.MemberNetworkVisibility", "PUBLIC"
                    ),
                })

            return json.dumps({"total": len(posts), "posts": posts}, indent=2, ensure_ascii=False)
