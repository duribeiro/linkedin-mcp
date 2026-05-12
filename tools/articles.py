"""Tools de artigos — LinkedIn Articles API (Rich Media / Share API)."""

import json
import logging
import httpx
from auth import LinkedInAuth

logger = logging.getLogger("linkedin.articles")

SHARES_URL = "https://api.linkedin.com/v2/shares"
UGC_URL = "https://api.linkedin.com/v2/ugcPosts"
ASSETS_URL = "https://api.linkedin.com/v2/assets"


# ── helpers de upload de imagem ─────────────────────────────────────


async def _register_image(auth: LinkedInAuth, person_urn: str) -> str:
    """Registra uma imagem e retorna a URN da imagem."""
    headers = await auth.get_headers()
    headers["Content-Type"] = "application/json"

    body = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": person_urn,
            "serviceRelationships": [
                {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
            ],
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(ASSETS_URL, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        upload_url = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
        asset_urn = data["value"]["asset"]
        return asset_urn


async def _upload_image_binary(auth: LinkedInAuth, asset_urn: str, image_source_url: str):
    """Faz upload binário da imagem."""
    # Baixa a imagem da URL fornecida
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(image_source_url)
        r.raise_for_status()
        image_bytes = r.content

        # Faz upload pra URL de upload do LinkedIn
        upload_resp = await client.put(
            asset_urn.replace("urn:li:digitalmediaAsset:", ""),
            content=image_bytes,
        )
        logger.info("Image uploaded: %s -> %s", image_source_url, upload_resp.status_code)


# ── articles ────────────────────────────────────────────────────────


def register_article_tools(server, auth: LinkedInAuth):
    """Registra tools de criação de artigos no MCP server."""

    @server.tool()
    async def create_article(
        title: str,
        body_markdown: str,
        description: str = "",
        cover_image_url: str = "",
        tags: str = "",
        visibility: str = "PUBLIC",
    ) -> str:
        """Publica um artigo (long-form post) no LinkedIn.

        Artigos no LinkedIn são posts com shareMediaCategory='ARTICLE'
        que suportam formatação rica e corpo extenso.

        Args:
            title: Título do artigo
            body_markdown: Corpo em markdown (será convertido — o LinkedIn usa
                           um formato próprio, então markdown é melhor esforço)
            description: Subtítulo/descrição curta (~150 caracteres)
            cover_image_url: URL pública da imagem de capa
            tags: Tags separadas por vírgula (ex: 'IA,Agentes,Automação')
            visibility: 'PUBLIC' ou 'CONNECTIONS'
        """
        person_urn = await auth.get_person_urn()
        headers = await auth.get_headers()
        headers["Content-Type"] = "application/json"

        # 1. Se tem imagem de capa, faz upload
        media = []
        if cover_image_url:
            try:
                image_urn = await _register_image(auth, person_urn)
                await _upload_image_binary(auth, image_urn, cover_image_url)
                media.append({
                    "media": image_urn,
                    "status": "READY",
                })
                logger.info("Cover image uploaded: %s", image_urn)
            except Exception as e:
                logger.warning("Failed to upload cover image: %s", e)
                # continua sem imagem

        # 2. Monta o artigo como share
        # LinkedIn trata artigo como um UGC post com shareMediaCategory=ARTICLE
        commentary = title
        if description:
            commentary = f"{title}\n\n{description}"

        body = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "shareCommentary": {
                    "text": commentary,
                    "attributes": [],
                },
                "shareMediaCategory": "ARTICLE",
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility,
            },
        }

        # Adiciona o corpo do artigo como text/attribution
        if body_markdown:
            # LinkedIn usa "text" field dentro de shareContent pra artigos
            body["specificContent"]["shareContent"] = {
                "shareMediaCategory": "ARTICLE",
                "description": {"text": description or title},
                "title": title,
            }

        if media:
            body["specificContent"]["media"] = media

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(UGC_URL, headers=headers, json=body)

            import json as _json

            result = {
                "status": r.status_code,
                "share_id": r.headers.get("X-RestLi-Id", ""),
                "response": r.json() if r.text else {},
            }

            if r.status_code >= 400:
                result["error"] = True
                result["request_body"] = body
                logger.error("Article creation failed: %s", r.text[:500])
            else:
                result["success"] = True

            return json.dumps(result, indent=2, ensure_ascii=False)

    @server.tool()
    async def get_my_articles(count: int = 10) -> str:
        """Lista os últimos artigos publicados pelo usuário autenticado.

        Args:
            count: Quantos artigos retornar (padrão: 10)
        """
        person_urn = await auth.get_person_urn()
        headers = await auth.get_headers()

        # Usa LinkedIn Shares API pra buscar posts do tipo ARTICLE
        person_id = person_urn.split(":")[-1]
        url = f"https://api.linkedin.com/v2/shares?q=owners&owners={person_urn}&count={count}&sortBy=CREATED"

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=headers)

            if r.status_code != 200:
                return json.dumps({"error": r.status_code, "message": r.text[:500]}, indent=2)

            data = r.json()
            articles = []

            for element in data.get("elements", []):
                share = element
                specific = share.get("specificContent", {})
                if specific.get("shareMediaCategory") == "ARTICLE" or specific.get("shareContent"):
                    articles.append({
                        "id": share.get("id", ""),
                        "title": specific.get("shareContent", {}).get("title", ""),
                        "description": specific.get("shareContent", {}).get("description", {}).get("text", ""),
                        "commentary": specific.get("shareCommentary", {}).get("text", ""),
                        "created": share.get("created", {}).get("time", ""),
                    })

            return json.dumps({"total": len(articles), "articles": articles}, indent=2, ensure_ascii=False)
