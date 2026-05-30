"""Tools de posts — POST /v2/ugcPosts (Share API)."""

import json
import httpx
from auth import LinkedInAuth


def register_post_tools(server, auth: LinkedInAuth):
    """Registra tools de criação de posts no MCP server."""

    UGC_URL = "https://api.linkedin.com/v2/ugcPosts"

    @server.tool()
    async def create_post(
        text: str,
        url: str = "",
        image_url: str | None = None,
        visibility: str = "PUBLIC",
    ) -> str:
        """Cria um post no LinkedIn da conta autenticada.

        Args:
            text: O texto do post (até ~3000 caracteres)
            url: URL opcional para compartilhar (aparece como card)
            image_url: URL pública de uma imagem para anexar (serve como thumbnail)
            visibility: 'PUBLIC' ou 'CONNECTIONS'
        """
        person_urn = await auth.get_person_urn()
        headers = await auth.get_headers()
        headers["Content-Type"] = "application/json"

        # Constrói o shareContent
        content_entities = []

        # Media (imagem) se fornecida
        media = []
        if image_url:
            # Primeiro registra a imagem e faz upload
            from .articles import _register_image, _upload_image_binary

            image_urn = await _register_image(auth, person_urn)
            await _upload_image_binary(auth, image_urn, image_url)
            media.append({
                "media": image_urn,
                "status": "READY",
                "title": {"text": "Imagem do post"},
            })

        # Artigo/comentário
        share_commentary = {"text": text}

        if url:
            content_entities.append({
                "entity": url,
                "thumbnails": [],
            })
            share_commentary["text"] = text

        body = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "shareCommentary": share_commentary,
                "shareMediaCategory": "NONE" if not media else "IMAGE",
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility,
            },
        }

        if media:
            body["specificContent"]["media"] = media

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(UGC_URL, headers=headers, json=body)
            r.raise_for_status()

            # Extrai ID do share
            share_id = r.headers.get("X-RestLi-Id", "")
            result = {"status": "ok", "share_id": share_id, "detail": r.json() if r.text else {}}
            return json.dumps(result, indent=2)

    @server.tool()
    async def create_post_with_article_link(
        text: str,
        article_url: str,
        preview_title: str = "",
        preview_description: str = "",
        visibility: str = "PUBLIC",
    ) -> str:
        """Cria post no LinkedIn compartilhando um link (aparece card com preview).

        Args:
            text: Texto que acompanha o link (recomendo 1-2 frases)
            article_url: URL completa do artigo/site
            preview_title: Título do card de preview
            preview_description: Descrição do card
            visibility: 'PUBLIC' ou 'CONNECTIONS'
        """
        person_urn = await auth.get_person_urn()
        headers = await auth.get_headers()
        headers["Content-Type"] = "application/json"

        body = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "ARTICLE",
                "media": [
                    {
                        "status": "READY",
                        "originalUrl": article_url,
                        "title": {"text": preview_title or article_url.split("/")[-1]},
                    }
                ],
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(UGC_URL, headers=headers, json=body)
            r.raise_for_status()
            share_id = r.headers.get("X-RestLi-Id", "")
            result = {"status": "ok", "share_id": share_id}
            return json.dumps(result, indent=2)
