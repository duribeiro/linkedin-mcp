"""Tools de perfil — GET /v2/me e /v2/userinfo."""

import httpx
from auth import LinkedInAuth


def register_profile_tools(server, auth: LinkedInAuth):
    """Registra tools de perfil no MCP server."""

    @server.tool()
    async def get_my_profile(sections: str = "all") -> str:
        """Retorna o perfil do usuário autenticado no LinkedIn.

        Args:
            sections: Partes do perfil — 'all', 'basic', 'positions', 'education', 'skills'
        """
        headers = await auth.get_headers()
        person_urn = await auth.get_person_urn()

        parts = {}

        # Perfil básico via userinfo
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {await auth.get_access_token()}"},
            )
            r.raise_for_status()
            parts["basic"] = r.json()

        # LiteProfile via /v2/me
        if sections in ("all", "positions", "education", "skills"):
            async with httpx.AsyncClient() as client:
                me_headers = {
                    "Authorization": f"Bearer {await auth.get_access_token()}",
                    "LinkedIn-Version": "202510",
                }
                r = await client.get("https://api.linkedin.com/v2/me", headers=me_headers)
                r.raise_for_status()
                parts["liteprofile"] = r.json()

        # Experience / positions
        if sections in ("all", "positions"):
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.get(
                        f"https://api.linkedin.com/v2/positions?q=members&members={person_urn.split(':')[-1]}",
                        headers=headers,
                    )
                    if r.status_code == 200:
                        parts["positions"] = r.json()
                    else:
                        parts["positions"] = {"error": r.status_code, "message": r.text[:200]}
            except Exception as e:
                parts["positions"] = {"error": str(e)}

        import json
        return json.dumps(parts, indent=2, ensure_ascii=False)
