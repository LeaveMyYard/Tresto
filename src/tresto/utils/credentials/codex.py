from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.prompt import Confirm

from .errors import CredentialError
from .strategy import CredentialStrategy

if TYPE_CHECKING:
    from rich.console import Console

    from .store import CredentialStore

CODEX_AUTH_FILE = Path(os.getenv("CODEX_HOME", Path.home() / ".codex")) / "auth.json"
CODEX_ACCOUNT_ID_CLAIM = "https://api.openai.com/auth"


class CodexAuthProvider:
    """Reads browser-login credentials created by `codex login`."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or CODEX_AUTH_FILE

    def get_access_token(self) -> str | None:
        payload = self._read()
        tokens = payload.get("tokens")
        if not isinstance(tokens, dict):
            return None
        access_token = tokens.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            return None
        if _is_expired_jwt(access_token):
            return None
        return access_token

    def get_account_id(self, access_token: str | None = None) -> str | None:
        token = access_token or self.get_access_token()
        if not token:
            return None
        payload = _jwt_payload(token)
        auth_claims = payload.get(CODEX_ACCOUNT_ID_CLAIM)
        if not isinstance(auth_claims, dict):
            return None
        account_id = auth_claims.get("chatgpt_account_id")
        return account_id if isinstance(account_id, str) and account_id else None

    def login(self) -> str:
        if shutil.which("codex") is None:
            raise CredentialError("Codex CLI is not installed or not on PATH.")
        subprocess.run(["codex", "login"], check=True)
        access_token = self.get_access_token()
        if not access_token:
            raise CredentialError("Codex login completed, but no usable access token was found.")
        return access_token

    def openai_api_access_error(self, access_token: str) -> str | None:
        request = urllib.request.Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=15):
                return None
        except urllib.error.HTTPError as e:
            if e.code not in {401, 403}:
                return None
            body = e.read().decode("utf-8", errors="replace")
            return f"Codex browser auth cannot access the OpenAI API: {e.code} {body}"
        except (OSError, TimeoutError):
            return None

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise CredentialError(f"Could not read Codex auth file at {self.path}: {e}") from e
        if not isinstance(raw, dict):
            return {}
        return raw


class CodexCredentialStrategy(CredentialStrategy):
    connectors = {"codex", "chatgpt"}

    def __init__(
        self,
        store: CredentialStore,
        console: Console,
        codex_auth: CodexAuthProvider | None = None,
    ) -> None:
        super().__init__(store=store, console=console)
        self.codex_auth = codex_auth or CodexAuthProvider()

    def ensure(self) -> None:
        access_token = self.codex_auth.get_access_token()
        if access_token and self.codex_auth.get_account_id(access_token):
            self.console.print("[green]Using Codex browser auth from ~/.codex/auth.json[/green]")
            return

        self.console.print("[yellow]Codex browser auth is not available.[/yellow]")
        if not Confirm.ask("Run `codex login` now?", default=True):
            raise CredentialError("Codex browser auth is required for the Codex provider.")

        access_token = self.codex_auth.login()
        if not self.codex_auth.get_account_id(access_token):
            raise CredentialError("Codex login succeeded, but no ChatGPT account id was found in the token.")
        self.console.print("[green]Using Codex browser auth from ~/.codex/auth.json[/green]")

    def refresh(self, reason: str | None = None) -> None:
        if reason:
            self.console.print(f"[yellow]{reason}[/yellow]")
        self.console.print("Run `codex login` to refresh browser authentication.")
        access_token = self.codex_auth.login()
        if not self.codex_auth.get_account_id(access_token):
            raise CredentialError("Codex login succeeded, but no ChatGPT account id was found in the token.")


def _is_expired_jwt(token: str) -> bool:
    payload = _jwt_payload(token)
    exp = payload.get("exp")
    return isinstance(exp, int) and exp <= int(time.time()) + 60


def _jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload_part = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_part))
    except (ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload
