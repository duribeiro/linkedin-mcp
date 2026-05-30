"""LinkedIn MCP Server — API REST oficial para contas pessoais.

Endpoints (atualizado maio/2026):
  - Profile:   /v2/userinfo
  - Images:    POST /rest/images?action=initializeUpload + PUT binary
  - Posts:     POST /rest/posts              (scope: w_member_social)
  - Share:     POST /rest/posts              (content.article — card de link)
  - Social:    /rest/socialActions/{urn}     (scope: r_member_social — RESTRITO)
  - Feed:      GET /rest/posts?author=...    (scope: r_member_social — RESTRITO)

Nota: /v2/shares, /v2/ugcPosts e /v2/socialActions/.../shareStatistics
      foram deprecados pela LinkedIn em 2025. Migramos para /rest/posts e
      /rest/socialActions.

      Ferramentas de leitura (feed, articles, stats) requerem r_member_social —
      escopo RESTRITO, liberado apenas para apps aprovados pela LinkedIn.
      Ferramentas de escrita (create_post, share_link, upload_image) funcionam
      com w_member_social, que qualquer app pode solicitar.

Autor: Theo (Hermes Agent) — Licença MIT
"""

import json
import logging
import os
from urllib.parse import quote

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from auth import LinkedInAuth

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("linkedin-mcp")

server = Server("linkedin-mcp")
auth = LinkedInAuth()

REST_POSTS_URL = "https://api.linkedin.com/rest/posts"
REST_IMAGES_URL = "https://api.linkedin.com/rest/images"

R_MEMBER_SOCIAL_NOTICE = (
    " ⚠️ LinkedIn exige o scope r_member_social para buscar posts/artigos. "
    "Esse escopo é RESTRITO — apenas apps aprovados pela LinkedIn. "
    "Seu token atual tem apenas w_member_social (publicar). "
    "Para habilitar leitura, solicite aprovação no LinkedIn Developer Portal."
)

# ── Unicode bold/italic formatting ──
# LinkedIn REST API não suporta markdown nativo, mas Unicode bold/italic
# renderiza corretamente no feed. Mapeamos A-Z, a-z, 0-9.

_BOLD_BASE = {
    ord('A'): '𝗔', ord('B'): '𝗕', ord('C'): '𝗖', ord('D'): '𝗗', ord('E'): '𝗘',
    ord('F'): '𝗙', ord('G'): '𝗚', ord('H'): '𝗛', ord('I'): '𝗜', ord('J'): '𝗝',
    ord('K'): '𝗞', ord('L'): '𝗟', ord('M'): '𝗠', ord('N'): '𝗡', ord('O'): '𝗢',
    ord('P'): '𝗣', ord('Q'): '𝗤', ord('R'): '𝗥', ord('S'): '𝗦', ord('T'): '𝗧',
    ord('U'): '𝗨', ord('V'): '𝗩', ord('W'): '𝗪', ord('X'): '𝗫', ord('Y'): '𝗬', ord('Z'): '𝗭',
    ord('a'): '𝗮', ord('b'): '𝗯', ord('c'): '𝗰', ord('d'): '𝗱', ord('e'): '𝗲', ord('f'): '𝗳',
    ord('g'): '𝗴', ord('h'): '𝗵', ord('i'): '𝗶', ord('j'): '𝗷', ord('k'): '𝗸', ord('l'): '𝗹',
    ord('m'): '𝗺', ord('n'): '𝗻', ord('o'): '𝗼', ord('p'): '𝗽', ord('q'): '𝗾', ord('r'): '𝗿',
    ord('s'): '𝘀', ord('t'): '𝘁', ord('u'): '𝘂', ord('v'): '𝘃', ord('w'): '𝘄', ord('x'): '𝘅',
    ord('y'): '𝘆', ord('z'): '𝘇',
    ord('0'): '𝟬', ord('1'): '𝟭', ord('2'): '𝟮', ord('3'): '𝟯', ord('4'): '𝟰',
    ord('5'): '𝟱', ord('6'): '𝟲', ord('7'): '𝟳', ord('8'): '𝟴', ord('9'): '𝟵',
}

_ITALIC_BASE = {
    ord('A'): '𝘈', ord('B'): '𝘉', ord('C'): '𝘊', ord('D'): '𝘋', ord('E'): '𝘌',
    ord('F'): '𝘍', ord('G'): '𝘎', ord('H'): '𝘏', ord('I'): '𝘐', ord('J'): '𝘑',
    ord('K'): '𝘒', ord('L'): '𝘓', ord('M'): '𝘔', ord('N'): '𝘕', ord('O'): '𝘖',
    ord('P'): '𝘗', ord('Q'): '𝘘', ord('R'): '𝘙', ord('S'): '𝘚', ord('T'): '𝘛',
    ord('U'): '𝘜', ord('V'): '𝘝', ord('W'): '𝘞', ord('X'): '𝘟', ord('Y'): '𝘠', ord('Z'): '𝘡',
    ord('a'): '𝘢', ord('b'): '𝘣', ord('c'): '𝘤', ord('d'): '𝘥', ord('e'): '𝘦', ord('f'): '𝘧',
    ord('g'): '𝘨', ord('h'): '𝘩', ord('i'): '𝘪', ord('j'): '𝘫', ord('k'): '𝘬', ord('l'): '𝘭',
    ord('m'): '𝘮', ord('n'): '𝘯', ord('o'): '𝘰', ord('p'): '𝘱', ord('q'): '𝘲', ord('r'): '𝘳',
    ord('s'): '𝘴', ord('t'): '𝘵', ord('u'): '𝘶', ord('v'): '𝘷', ord('w'): '𝘸', ord('x'): '𝘹',
    ord('y'): '𝘺', ord('z'): '𝘻',
}

_BOLD_ITALIC_BASE = {
    ord('A'): '𝘼', ord('B'): '𝘽', ord('C'): '𝘾', ord('D'): '𝘿', ord('E'): '𝙀',
    ord('F'): '𝙁', ord('G'): '𝙂', ord('H'): '𝙃', ord('I'): '𝙄', ord('J'): '𝙅',
    ord('K'): '𝙆', ord('L'): '𝙇', ord('M'): '𝙈', ord('N'): '𝙉', ord('O'): '𝙊',
    ord('P'): '𝙋', ord('Q'): '𝙌', ord('R'): '𝙍', ord('S'): '𝙎', ord('T'): '𝙏',
    ord('U'): '𝙐', ord('V'): '𝙑', ord('W'): '𝙒', ord('X'): '𝙓', ord('Y'): '𝙔', ord('Z'): '𝙕',
    ord('a'): '𝙖', ord('b'): '𝙗', ord('c'): '𝙘', ord('d'): '𝙙', ord('e'): '𝙚', ord('f'): '𝙛',
    ord('g'): '𝙜', ord('h'): '𝙝', ord('i'): '𝙞', ord('j'): '𝙟', ord('k'): '𝙠', ord('l'): '𝙡',
    ord('m'): '𝙢', ord('n'): '𝙣', ord('o'): '𝙤', ord('p'): '𝙥', ord('q'): '𝙦', ord('r'): '𝙧',
    ord('s'): '𝙨', ord('t'): '𝙩', ord('u'): '𝙪', ord('v'): '𝙫', ord('w'): '𝙬', ord('x'): '𝙭',
    ord('y'): '𝙮', ord('z'): '𝙯',
}


def format_linkedin(text: str) -> str:
    """Converte markdown-like tags para Unicode bold/italic (compatível com LinkedIn API).

    Suporta:
      - **texto** → 𝗯𝗼𝗹𝗱  (mathematical bold)
      - *texto*   → 𝘪𝘵𝘢𝘭𝘪𝘤 (mathematical italic)
      - ***texto*** → 𝙗𝙤𝙡𝙙-𝙞𝙩𝙖𝙡𝙞𝙘 (mathematical bold italic)

    Nota: ~texto~ (tachado) não é suportado pela API REST do LinkedIn.
    Não use triple backticks — LinkedIn API não renderiza blocos de código.
    """
    import re

    # Bold + italic: ***texto***
    text = re.sub(r'\*\*\*(.+?)\*\*\*', lambda m: m.group(1).translate(_BOLD_ITALIC_BASE), text)

    # Bold: **texto**
    text = re.sub(r'\*\*(.+?)\*\*', lambda m: m.group(1).translate(_BOLD_BASE), text)

    # Italic: *texto*
    text = re.sub(r'\*(.+?)\*', lambda m: m.group(1).translate(_ITALIC_BASE), text)

    return text


async def _get_headers() -> dict:
    """Retorna headers padrão com token e versão da API."""
    token = await auth.get_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202510",
    }


# ═══════════════════════════════════════════════════════════════════════
# Profile
# ═══════════════════════════════════════════════════════════════════════

async def get_my_profile(sections: str = "all") -> list[TextContent]:
    """Retorna o perfil do LinkedIn do usuário autenticado."""
    parts = {}

    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {await auth.get_access_token()}"},
        )
        r.raise_for_status()
        parts["basic"] = r.json()

    if sections in ("all", "liteprofile"):
        parts["liteprofile"] = {
            "id": parts["basic"].get("sub", ""),
            "localizedFirstName": parts["basic"].get("given_name", ""),
            "localizedLastName": parts["basic"].get("family_name", ""),
            "profilePicture": parts["basic"].get("picture", ""),
        }

    return [TextContent(type="text", text=json.dumps(parts, indent=2, ensure_ascii=False))]


# ═══════════════════════════════════════════════════════════════════════
# Image Upload (POST /rest/images?action=initializeUpload + PUT binário)
# ═══════════════════════════════════════════════════════════════════════

async def upload_image(image_path: str) -> list[TextContent]:
    """Faz upload de uma imagem e retorna a URN (urn:li:image:...).
    
    Usa a Images API (/rest/images) que substituiu a Assets API.
    Fluxo: inicializar upload → PUT binário na uploadUrl → retorna URN.
    
    Formatos aceitos: JPG, PNG, GIF (até 250 frames). Máx ~36 megapixels.
    """
    path = os.path.expanduser(image_path)
    if not os.path.isfile(path):
        return [TextContent(type="text", text=json.dumps({
            "error": f"Arquivo não encontrado: {path}",
        }, indent=2))]
    
    headers = await _get_headers()
    headers["Content-Type"] = "application/json"
    
    # ── 1. Inicializar upload ──
    person_urn = await auth.get_person_urn()
    body = {
        "initializeUploadRequest": {
            "owner": person_urn,
        }
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{REST_IMAGES_URL}?action=initializeUpload",
            headers=headers,
            json=body,
        )
        
        if r.status_code != 200:
            return [TextContent(type="text", text=json.dumps({
                "error": f"Falha ao inicializar upload ({r.status_code})",
                "detail": r.text[:500],
            }, indent=2))]
        
        data = r.json()
        value = data.get("value", {})
        upload_url = value.get("uploadUrl", "")
        image_urn = value.get("image", "")
        
        if not upload_url or not image_urn:
            return [TextContent(type="text", text=json.dumps({
                "error": "Resposta de inicialização sem uploadUrl ou image URN",
                "response": data,
            }, indent=2))]
    
    # ── 2. Upload binário (PUT) ──
    content_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
    }
    ext = os.path.splitext(path)[1].lower()
    content_type = content_type_map.get(ext, "image/png")
    
    with open(path, "rb") as f:
        image_bytes = f.read()
    
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.put(
            upload_url,
            content=image_bytes,
            headers={
                "Authorization": headers["Authorization"],
                "Content-Type": content_type,
            },
        )
        
        if r.status_code not in (200, 201):
            return [TextContent(type="text", text=json.dumps({
                "error": f"Falha no upload binário ({r.status_code})",
                "detail": r.text[:500],
                "image_urn": image_urn,  # URN gerada mesmo se upload falhou
            }, indent=2))]
    
    return [TextContent(type="text", text=json.dumps({
        "success": True,
        "image_urn": image_urn,
        "file": os.path.basename(path),
        "size_bytes": len(image_bytes),
    }, indent=2))]


# ═══════════════════════════════════════════════════════════════════════
# Posts (POST /rest/posts)
# ═══════════════════════════════════════════════════════════════════════

async def create_post(
    text: str,
    url: str = "",
    image_path: str = "",
    visibility: str = "PUBLIC",
) -> list[TextContent]:
    """Cria um post no LinkedIn usando o novo endpoint /rest/posts.
    
    Suporta:
      - Texto puro
      - URL compartilhada (card de link) — param 'url'
      - Imagem única — param 'image_path' (faz upload automaticamente)
      - Texto + imagem (image_path + text)
    """
    person_urn = await auth.get_person_urn()
    headers = await _get_headers()
    headers["Content-Type"] = "application/json"

    body: dict = {
        "author": person_urn,
        "commentary": format_linkedin(text),
        "visibility": visibility,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    # ── Imagem: faz upload primeiro, depois usa a URN ──
    if image_path:
        upload_result = await upload_image(image_path)
        upload_data = json.loads(upload_result[0].text)
        if "error" in upload_data:
            return upload_result  # repassa o erro
        image_urn = upload_data["image_urn"]
        body["content"] = {
            "media": {
                "id": image_urn,
                "altText": text[:120] if text else "Imagem",
            }
        }

    # ── URL compartilhada vira article content (card de link) ──
    elif url:
        body["content"] = {
            "article": {
                "source": url,
                "title": text[:200],
            }
        }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(REST_POSTS_URL, headers=headers, json=body)

        result: dict = {
            "status": r.status_code,
            "share_id": r.headers.get("X-RestLi-Id", ""),
        }
        if r.status_code >= 400:
            result["error"] = r.text[:500]
        else:
            result["success"] = True
            if image_urn:
                result["image_urn"] = image_urn

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


# ═══════════════════════════════════════════════════════════════════════
# Compartilhar URL (POST /rest/posts com content.article — card de link)
#
# ⚠️ NÃO é artigo Pulse long-form. A API REST do LinkedIn nunca expôs
#    criação de artigos Pulse com corpo inline. content.article é apenas
#    um card de link bonito (título + descrição + thumbnail + URL).
#    Artigos Pulse reais só são criados via interface web.
# ═══════════════════════════════════════════════════════════════════════

async def share_link(
    text: str,
    source_url: str,
    title: str = "",
    description: str = "",
    image_path: str = "",
    visibility: str = "PUBLIC",
) -> list[TextContent]:
    """Compartilha um link no LinkedIn com card personalizado.

    ⚠️ Isto NÃO é um artigo Pulse. É um card de link — o que aparece
    quando você cola uma URL no LinkedIn. A API REST não suporta
    criação de artigos long-form com corpo inline.
    
    Parâmetros:
      - text: legenda que aparece acima do card
      - source_url: URL que o card aponta
      - title: título do card (opcional, default=URL)
      - description: descrição abaixo do título (opcional)
      - image_path: thumbnail do card (opcional, faz upload auto)
    """
    person_urn = await auth.get_person_urn()
    headers = await _get_headers()
    headers["Content-Type"] = "application/json"

    article_content: dict = {
        "source": source_url,
        "title": title or source_url.split("/")[-1] or source_url,
        "description": (description or text)[:500],
    }

    # ── Thumbnail: faz upload primeiro ──
    thumbnail_urn = None
    if image_path:
        upload_result = await upload_image(image_path)
        upload_data = json.loads(upload_result[0].text)
        if "error" in upload_data:
            return upload_result
        thumbnail_urn = upload_data["image_urn"]
        article_content["thumbnail"] = thumbnail_urn

    body: dict = {
        "author": person_urn,
        "commentary": format_linkedin(text),
        "visibility": visibility,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {"article": article_content},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(REST_POSTS_URL, headers=headers, json=body)
        result: dict = {
            "status": r.status_code,
            "share_id": r.headers.get("X-RestLi-Id", ""),
        }
        if r.status_code >= 400:
            result["error"] = r.text[:500]
        else:
            result["success"] = True
            result["note"] = "Card de link (não é artigo Pulse)"
            if thumbnail_urn:
                result["thumbnail_urn"] = thumbnail_urn

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def get_my_articles(count: int = 10) -> list[TextContent]:
    """Lista artigos publicados (requer r_member_social — RESTRITO)."""
    person_urn = await auth.get_person_urn()
    headers = await _get_headers()
    headers["X-RestLi-Method"] = "FINDER"

    encoded_urn = quote(person_urn, safe="")
    url = f"{REST_POSTS_URL}?author={encoded_urn}&q=author&count={min(count, 50)}&sortBy=LAST_MODIFIED"

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)

        if r.status_code == 403:
            return [TextContent(type="text", text=json.dumps({
                "error": 403,
                "message": "Acesso negado." + R_MEMBER_SOCIAL_NOTICE,
            }, indent=2, ensure_ascii=False))]

        if r.status_code != 200:
            return [TextContent(type="text", text=json.dumps({
                "error": r.status_code,
                "message": r.text[:500],
            }, indent=2))]

        data = r.json()
        articles = []
        for element in data.get("elements", []):
            content = element.get("content", {})
            article = content.get("article", {})
            if article:
                articles.append({
                    "id": element.get("id", ""),
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "commentary": element.get("commentary", ""),
                    "createdAt": element.get("createdAt", 0),
                })

        return [TextContent(type="text", text=json.dumps({
            "total": len(articles),
            "articles": articles,
        }, indent=2, ensure_ascii=False))]


# ═══════════════════════════════════════════════════════════════════════
# Insights (socialActions — endpoint separado, não deprecado)
# ═══════════════════════════════════════════════════════════════════════

async def get_share_stats(share_id: str) -> list[TextContent]:
    """Retorna social actions (likes, comentários) de um post no LinkedIn.

    Nota: O novo endpoint /rest/socialActions não retorna mais impressions/clicks.
    Essas métricas exigem a Organization Analytics API (r_organization_social).
    Requer r_member_social (RESTRITO).
    """
    headers = await _get_headers()
    encoded_urn = quote(share_id, safe="")
    url = f"https://api.linkedin.com/rest/socialActions/{encoded_urn}"

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=headers)

        if r.status_code == 403:
            return [TextContent(type="text", text=json.dumps({
                "error": 403,
                "message": "Acesso negado." + R_MEMBER_SOCIAL_NOTICE,
            }, indent=2))]

        if r.status_code != 200:
            return [TextContent(type="text", text=json.dumps({
                "error": r.status_code,
                "message": r.text[:500],
            }, indent=2))]

        data = r.json()
        stats = {
            "share_id": share_id,
            "likes": data.get("likesSummary", {}).get("totalLikes", 0),
            "comments": data.get("commentsSummary", {}).get("totalFirstLevelComments", 0),
            "_note": "Endpoint requer r_member_social. Impressions/clicks/shares exigem Organization Analytics API.",
        }
        return [TextContent(type="text", text=json.dumps(stats, indent=2))]


# ═══════════════════════════════════════════════════════════════════════
# Feed (GET /rest/posts?author=... — requer r_member_social)
# ═══════════════════════════════════════════════════════════════════════

async def get_my_feed(count: int = 10) -> list[TextContent]:
    """Retorna posts recentes do autor (requer r_member_social — RESTRITO)."""
    person_urn = await auth.get_person_urn()
    headers = await _get_headers()
    headers["X-RestLi-Method"] = "FINDER"

    encoded_urn = quote(person_urn, safe="")
    url = f"{REST_POSTS_URL}?author={encoded_urn}&q=author&count={min(count, 50)}&sortBy=LAST_MODIFIED"

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)

        if r.status_code == 403:
            return [TextContent(type="text", text=json.dumps({
                "error": 403,
                "message": "Acesso negado." + R_MEMBER_SOCIAL_NOTICE,
            }, indent=2, ensure_ascii=False))]

        if r.status_code != 200:
            return [TextContent(type="text", text=json.dumps({
                "error": r.status_code,
                "message": r.text[:500],
            }, indent=2))]

        data = r.json()
        posts = []
        for element in data.get("elements", []):
            posts.append({
                "id": element.get("id", ""),
                "commentary": element.get("commentary", ""),
                "visibility": element.get("visibility", ""),
                "createdAt": element.get("createdAt", 0),
                "lifecycleState": element.get("lifecycleState", ""),
            })

        return [TextContent(type="text", text=json.dumps({
            "total": len(posts),
            "posts": posts,
        }, indent=2, ensure_ascii=False))]


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
                "sections": {"type": "string", "description": "Partes do perfil: 'all', 'basic', 'liteprofile'"},
            },
        },
    ),
    "upload_image": Tool(
        name="upload_image",
        description="Faz upload de uma imagem para o LinkedIn e retorna a URN (urn:li:image:...). Use esta URN em create_post ou share_link.",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Caminho absoluto do arquivo de imagem (JPG, PNG, GIF)"},
            },
            "required": ["image_path"],
        },
    ),
    "create_post": Tool(
        name="create_post",
        description="Cria um post no LinkedIn da conta autenticada. text: texto do post. url: link opcional para compartilhar (card). image_path: caminho da imagem para upload automático. visibility: 'PUBLIC' (padrão) ou 'CONNECTIONS'.",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto do post"},
                "url": {"type": "string", "description": "URL opcional para compartilhar (card)"},
                "image_path": {"type": "string", "description": "Caminho local da imagem para upload (JPG/PNG/GIF)"},
                "visibility": {"type": "string", "description": "PUBLIC ou CONNECTIONS"},
            },
            "required": ["text"],
        },
    ),
    "share_link": Tool(
        name="share_link",
        description="Compartilha um link com card personalizado no LinkedIn. ⚠️ NÃO é artigo Pulse — é um card de link (título + descrição + thumbnail + URL). A API REST não suporta criação de artigos long-form. text: legenda. source_url: URL do link. title: título do card. description: descrição. image_path: thumbnail (opcional, upload auto).",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto/legenda do post"},
                "source_url": {"type": "string", "description": "URL que o card aponta"},
                "title": {"type": "string", "description": "Título do card (opcional, default=nome da URL)"},
                "description": {"type": "string", "description": "Descrição abaixo do título (opcional)"},
                "image_path": {"type": "string", "description": "Caminho local da thumbnail (JPG/PNG/GIF)"},
                "visibility": {"type": "string", "description": "PUBLIC ou CONNECTIONS"},
            },
            "required": ["text", "source_url"],
        },
    ),
    "get_my_articles": Tool(
        name="get_my_articles",
        description="Lista os últimos artigos publicados no LinkedIn. ⚠️ Requer scope r_member_social (RESTRITO). count: quantos retornar (padrão 10).",
        inputSchema={
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Quantos artigos retornar (padrão: 10)"},
            },
        },
    ),
    "get_share_stats": Tool(
        name="get_share_stats",
        description="Retorna social actions (likes, comentários) de um post/artigo. ⚠️ Requer scope r_member_social (RESTRITO).",
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
        description="Retorna os posts recentes do feed do usuário autenticado. ⚠️ Requer scope r_member_social (RESTRITO).",
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
    "upload_image": upload_image,
    "create_post": create_post,
    "share_link": share_link,
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
