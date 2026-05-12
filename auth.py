"""OAuth 2.0 para LinkedIn API — 3-legged flow com refresh automático."""

import json
import os
import time
import logging
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse

import httpx
from dotenv import load_dotenv

# Carrega do caminho canônico de secrets
load_dotenv(os.path.expanduser("~/.secrets/linkedin/.env"))

logger = logging.getLogger("linkedin.auth")

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
DEFAULT_SCOPES = ["openid", "profile", "email", "w_member_social"]
DEFAULT_REDIRECT = "http://localhost:8080/callback"


class LinkedInAuth:
    """Gerencia OAuth 2.0 do LinkedIn: login interativo + refresh transparente."""

    def __init__(self):
        self.client_id = os.getenv("CLIENTE_ID", os.getenv("LINKEDIN_CLIENT_ID", ""))
        self.client_secret = os.getenv("CLIENTE_SECRET", os.getenv("LINKEDIN_CLIENT_SECRET", ""))
        self.redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", DEFAULT_REDIRECT)
        self.token_path = os.path.expanduser(
            os.getenv("LINKEDIN_TOKEN_PATH", "~/.hermes/mcp-servers/linkedin/token.json")
        )
        self._token = None
        self._load_token()

    # ── token persistence ──────────────────────────────────────────

    def _load_token(self):
        try:
            with open(self.token_path) as f:
                self._token = json.load(f)
            logger.info("Token loaded from %s", self.token_path)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.info("No saved token — will authenticate on first tool call")

    def _save_token(self):
        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
        with open(self.token_path, "w") as f:
            json.dump(self._token, f, indent=2)
        logger.info("Token saved to %s", self.token_path)

    # ── access token getter (auto-refresh) ──────────────────────────

    async def get_access_token(self) -> str:
        """Retorna access token válido, renovando via refresh se necessário."""
        if not self._token:
            await self._authenticate()

        # Refresh se faltar < 5 min pra expirar
        expires_at = self._token.get("expires_at", 0)
        if time.time() + 300 > expires_at:
            await self._refresh()

        return self._token["access_token"]

    # ── 3-legged OAuth ──────────────────────────────────────────────

    async def _authenticate(self):
        """Fluxo completo: abre browser, captura code via servidor local, troca por token."""
        scopes = os.getenv("LINKEDIN_SCOPES", " ".join(DEFAULT_SCOPES))
        state = os.urandom(8).hex()

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scopes,
            "state": state,
        }
        auth_url = f"{AUTH_URL}?{urlencode(params)}"

        logger.info("Opening browser for LinkedIn auth: %s", auth_url)
        webbrowser.open(auth_url)

        # Aguarda callback no servidor local
        code = await self._wait_for_callback(state)
        await self._exchange_code(code)

    async def _wait_for_callback(self, expected_state: str) -> str:
        """Sobe servidor HTTP local e aguarda o redirect do LinkedIn."""
        result = {"code": None, "error": None}

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                qs = urlparse(self.path).query
                params = parse_qs(qs)
                if "code" in params:
                    result["code"] = params["code"][0]
                    state = params.get("state", [""])[0]
                    if state != expected_state:
                        result["error"] = "State mismatch — possible CSRF"
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<h1>Autenticado!</h1><p>Pode fechar essa aba.</p>")
                elif "error" in params:
                    result["error"] = params["error"][0]
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"<h1>Erro</h1>")
                else:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"<h1>Aguardando callback...</h1>")

            def log_message(self, *_):
                pass  # silencia logs do http.server

        import asyncio

        port = int(urlparse(self.redirect_uri).port or 8080)
        server = HTTPServer(("127.0.0.1", port), CallbackHandler)

        # Executa num thread separado (http.server é síncrono)
        loop = asyncio.get_running_loop()

        def serve():
            while result["code"] is None and result["error"] is None:
                server.handle_request()

        await loop.run_in_executor(None, serve)

        if result["error"]:
            raise RuntimeError(f"LinkedIn auth error: {result['error']}")

        if not result["code"]:
            raise RuntimeError("No authorization code received")

        return result["code"]

    async def _exchange_code(self, code: str):
        """Troca o authorization code por access + refresh tokens."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            self._store_response(resp)

    # ── refresh ─────────────────────────────────────────────────────

    async def _refresh(self):
        """Usa refresh_token pra gerar novo access token."""
        refresh = self._token.get("refresh_token")
        if not refresh:
            logger.warning("No refresh token — re-authenticating")
            await self._authenticate()
            return

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            self._store_response(resp)

    def _store_response(self, resp: httpx.Response):
        resp.raise_for_status()
        data = resp.json()
        self._token = {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", self._token.get("refresh_token") if self._token else None),
            "expires_at": time.time() + data.get("expires_in", 5184000),
            "scope": data.get("scope", ""),
        }
        self._save_token()

    # ── helpers ─────────────────────────────────────────────────────

    async def get_headers(self) -> dict:
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202510",
        }

    async def get_person_urn(self) -> str:
        """Retorna a Person URN do usuário autenticado."""
        token = await self.get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return f"urn:li:person:{data['sub']}"


# singleton
_auth_instance: LinkedInAuth | None = None


def get_auth() -> LinkedInAuth:
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = LinkedInAuth()
    return _auth_instance
