from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any, ClassVar, cast

from .errors import CredentialError
from .store import TRESTO_CREDENTIALS_FILE

if TYPE_CHECKING:
    from rich.console import Console

    from .store import CredentialStore


@dataclass(frozen=True)
class OIDCConfig:
    issuer_url: str
    client_id: str
    client_secret: str | None = None
    scopes: str = "openid profile email"
    audience: str | None = None
    resource: str | None = None
    redirect_host: str = "127.0.0.1"
    redirect_port: int = 0
    timeout_seconds: int = 300

    @classmethod
    def from_env(cls, prefix: str = "OPENAI") -> OIDCConfig | None:
        issuer_url = os.getenv(f"{prefix}_OIDC_ISSUER_URL")
        client_id = os.getenv(f"{prefix}_OIDC_CLIENT_ID")
        if not issuer_url or not client_id:
            return None

        return cls(
            issuer_url=issuer_url.rstrip("/"),
            client_id=client_id,
            client_secret=os.getenv(f"{prefix}_OIDC_CLIENT_SECRET") or None,
            scopes=os.getenv(f"{prefix}_OIDC_SCOPES", "openid profile email"),
            audience=os.getenv(f"{prefix}_OIDC_AUDIENCE") or None,
            resource=os.getenv(f"{prefix}_OIDC_RESOURCE") or None,
            redirect_host=os.getenv(f"{prefix}_OIDC_REDIRECT_HOST", "127.0.0.1"),
            redirect_port=int(os.getenv(f"{prefix}_OIDC_REDIRECT_PORT", "0")),
            timeout_seconds=int(os.getenv(f"{prefix}_OIDC_TIMEOUT_SECONDS", "300")),
        )


@dataclass(frozen=True)
class OIDCToken:
    access_token: str
    token_type: str = "Bearer"
    refresh_token: str | None = None
    id_token: str | None = None
    expires_at: int | None = None


class OIDCAuthenticator:
    callback_path: ClassVar[str] = "/callback"

    def __init__(self, config: OIDCConfig) -> None:
        self.config = config

    def login(self) -> OIDCToken:
        metadata = self._discover()
        authorization_endpoint = _required_metadata(metadata, "authorization_endpoint")
        token_endpoint = _required_metadata(metadata, "token_endpoint")

        code_verifier = secrets.token_urlsafe(64)
        code_challenge = _code_challenge(code_verifier)
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)

        receiver = _LoopbackReceiver(
            host=self.config.redirect_host,
            port=self.config.redirect_port,
            callback_path=self.callback_path,
            expected_state=state,
            timeout_seconds=self.config.timeout_seconds,
        )
        try:
            redirect_uri = receiver.redirect_uri
            auth_url = self._authorization_url(
                authorization_endpoint=authorization_endpoint,
                redirect_uri=redirect_uri,
                code_challenge=code_challenge,
                state=state,
                nonce=nonce,
            )
            if not webbrowser.open(auth_url):
                raise CredentialError(f"Could not open browser for OIDC login. Open this URL manually: {auth_url}")

            callback = receiver.wait_for_callback()
        finally:
            receiver.close()

        if callback.error:
            detail = callback.error_description or callback.error
            raise CredentialError(f"OIDC login failed: {detail}")
        if not callback.code:
            raise CredentialError("OIDC login did not return an authorization code.")

        return self._exchange_code(
            token_endpoint=token_endpoint,
            code=callback.code,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
        )

    def _discover(self) -> dict[str, Any]:
        url = f"{self.config.issuer_url}/.well-known/openid-configuration"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            raise CredentialError(f"Could not load OIDC discovery document from {url}: {e}") from e

    def _authorization_url(
        self,
        authorization_endpoint: str,
        redirect_uri: str,
        code_challenge: str,
        state: str,
        nonce: str,
    ) -> str:
        query = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": redirect_uri,
            "scope": self.config.scopes,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if self.config.audience:
            query["audience"] = self.config.audience
        if self.config.resource:
            query["resource"] = self.config.resource
        return f"{authorization_endpoint}?{urllib.parse.urlencode(query)}"

    def _exchange_code(
        self,
        token_endpoint: str,
        code: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> OIDCToken:
        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.config.client_id,
            "code_verifier": code_verifier,
        }
        if self.config.client_secret:
            body["client_secret"] = self.config.client_secret

        request = urllib.request.Request(
            token_endpoint,
            data=urllib.parse.urlencode(body).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            raise CredentialError(f"OIDC token exchange failed: {e.code} {error_body}") from e
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            raise CredentialError(f"OIDC token exchange failed: {e}") from e

        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise CredentialError("OIDC token response did not include an access_token.")

        expires_in = payload.get("expires_in")
        expires_at = int(time.time()) + int(expires_in) if isinstance(expires_in, int) else None
        return OIDCToken(
            access_token=access_token,
            token_type=str(payload.get("token_type") or "Bearer"),
            refresh_token=payload.get("refresh_token") if isinstance(payload.get("refresh_token"), str) else None,
            id_token=payload.get("id_token") if isinstance(payload.get("id_token"), str) else None,
            expires_at=expires_at,
        )


class OIDCCredentialMixin:
    oidc_env_prefix = "OPENAI"
    oidc_store_section = "openai_oidc"

    if TYPE_CHECKING:
        store: CredentialStore
        console: Console

    def _ensure_oidc_credentials(self) -> bool:
        config = OIDCConfig.from_env(self.oidc_env_prefix)
        if config is None:
            return False

        stored_token = self._stored_oidc_access_token()
        if stored_token:
            os.environ["OPENAI_API_KEY"] = stored_token
            return True

        self.console.print("Starting OIDC login in your browser.")
        token = OIDCAuthenticator(config).login()
        self._store_oidc_token(token)
        os.environ["OPENAI_API_KEY"] = token.access_token
        self.console.print(f"[green]Saved OIDC token metadata to {TRESTO_CREDENTIALS_FILE}[/green]")
        return True

    def _refresh_oidc_credentials(self) -> bool:
        config = OIDCConfig.from_env(self.oidc_env_prefix)
        if config is None:
            return False
        self.store.delete(self.oidc_store_section, "access_token")
        self.store.delete(self.oidc_store_section, "expires_at")
        self.store.delete(self.oidc_store_section, "refresh_token")
        self.store.delete(self.oidc_store_section, "id_token")
        self.store.delete("openai", "api_key")
        os.environ.pop("OPENAI_API_KEY", None)
        token = OIDCAuthenticator(config).login()
        self._store_oidc_token(token)
        os.environ["OPENAI_API_KEY"] = token.access_token
        return True

    def _stored_oidc_access_token(self) -> str | None:
        access_token = self.store.get(self.oidc_store_section, "access_token")
        if not access_token:
            return None

        expires_at_value = self.store.get(self.oidc_store_section, "expires_at")
        if expires_at_value:
            try:
                expires_at = int(expires_at_value)
            except ValueError:
                return None
            if expires_at <= int(time.time()) + 60:
                return None
        return access_token

    def _store_oidc_token(self, token: OIDCToken) -> None:
        self.store.set(self.oidc_store_section, "access_token", token.access_token)
        self.store.set(self.oidc_store_section, "token_type", token.token_type)
        if token.expires_at is not None:
            self.store.set(self.oidc_store_section, "expires_at", str(token.expires_at))
        if token.refresh_token:
            self.store.set(self.oidc_store_section, "refresh_token", token.refresh_token)
        if token.id_token:
            self.store.set(self.oidc_store_section, "id_token", token.id_token)


@dataclass(frozen=True)
class _CallbackResult:
    code: str | None = None
    error: str | None = None
    error_description: str | None = None


class _LoopbackReceiver:
    def __init__(
        self,
        host: str,
        port: int,
        callback_path: str,
        expected_state: str,
        timeout_seconds: int,
    ) -> None:
        self.callback_path = callback_path
        self.expected_state = expected_state
        self.timeout_seconds = timeout_seconds
        self._event = threading.Event()
        self._result: _CallbackResult | None = None

        receiver = self

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                receiver.handle_request(self)

            def log_message(self, _format: str, *_args: Any) -> None:
                return

        self._server = ThreadingHTTPServer((host, port), CallbackHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    @property
    def redirect_uri(self) -> str:
        host, port = cast("tuple[str, int]", self._server.server_address)
        return f"http://{host}:{port}{self.callback_path}"

    def wait_for_callback(self) -> _CallbackResult:
        if not self._event.wait(self.timeout_seconds):
            raise CredentialError("Timed out waiting for OIDC browser callback.")
        if self._result is None:
            raise CredentialError("OIDC browser callback failed.")
        return self._result

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

    def handle_request(self, handler: BaseHTTPRequestHandler) -> None:
        parsed = urllib.parse.urlparse(handler.path)
        if parsed.path != self.callback_path:
            self._send_response(handler, 404, "Tresto OIDC callback not found.")
            return

        query = urllib.parse.parse_qs(parsed.query)
        state = _single(query, "state")
        if state != self.expected_state:
            self._result = _CallbackResult(error="invalid_state", error_description="OIDC state did not match.")
            self._send_response(handler, 400, "Tresto OIDC login failed. You can close this tab.")
            self._event.set()
            return

        self._result = _CallbackResult(
            code=_single(query, "code"),
            error=_single(query, "error"),
            error_description=_single(query, "error_description"),
        )
        self._send_response(handler, 200, "Tresto OIDC login complete. You can close this tab.")
        self._event.set()

    def _send_response(self, handler: BaseHTTPRequestHandler, status: int, message: str) -> None:
        body = f"<!doctype html><html><body><p>{message}</p></body></html>".encode()
        handler.send_response(status)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)


def _required_metadata(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value:
        raise CredentialError(f"OIDC discovery document is missing {key}.")
    return value


def _code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _single(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if not values:
        return None
    return values[0]
