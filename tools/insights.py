"""Tools de insights — LinkedIn Analytics API."""

import json
import httpx
from auth import LinkedInAuth


def register_insight_tools(server, auth: LinkedInAuth):
    """Registra tools de analytics no MCP server."""

    @server.tool()
    async def get_share_stats(share_id: str) -> str:
        """Retorna estatísticas de um post/artigo específico (views, likes, comments, shares).

        Args:
            share_id: ID do post (ex: 'urn:li:share:7123456789')
        """
        headers = await auth.get_headers()

        url = f"https://api.linkedin.com/v2/socialActions/{share_id}/shareStatistics"

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()

            data = r.json()
            stats = {
                "share_id": share_id,
                "total_share_statistics": {
                    "views": data.get("totalShareStatistics", {}).get("clickCount", 0),
                    "impressions": data.get("totalShareStatistics", {}).get("impressionCount", 0),
                    "engagement": data.get("totalShareStatistics", {}).get("engagement", 0),
                    "likes": data.get("totalShareStatistics", {}).get("likeCount", 0),
                    "comments": data.get("totalShareStatistics", {}).get("commentCount", 0),
                    "shares": data.get("totalShareStatistics", {}).get("shareCount", 0),
                },
            }
            return json.dumps(stats, indent=2)

    @server.tool()
    async def get_profile_stats() -> str:
        """Retorna estatísticas agregadas do perfil (views, search appearances, etc.).

        Nota: Essa API do LinkedIn é limitada — retorna dados de visualização de perfil.
        """
        headers = await auth.get_headers()
        person_urn = await auth.get_person_urn()

        url = f"https://api.linkedin.com/v2/networkSizes/{person_urn}?edgeType=CompanyFollowedSize"

        results = {}

        async with httpx.AsyncClient(timeout=20) as client:
            # Network size (conexões)
            r = await client.get(
                f"https://api.linkedin.com/v2/networkSizes/{person_urn}?edgeType=CompanyFollowedSize",
                headers=headers,
            )
            if r.status_code == 200:
                results["connections"] = r.json()
            else:
                results["connections"] = {"error": r.status_code}

            # Tentativa de pegar analytics agregado
            person_id = person_urn.split(":")[-1]
            r = await client.get(
                f"https://api.linkedin.com/v2/people/(id:{person_id})?projection=(id,firstName,lastName,numConnections)",
                headers=headers,
            )
            if r.status_code == 200:
                results["profile"] = r.json()
            else:
                results["profile_raw"] = {"error": r.status_code}

        return json.dumps(results, indent=2)
