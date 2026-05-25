from __future__ import annotations

import os
import webbrowser
from typing import TYPE_CHECKING

from rich.prompt import Confirm, Prompt

from .codex import CodexAuthProvider
from .errors import CredentialError
from .oidc import OIDCCredentialMixin
from .store import TRESTO_CREDENTIALS_FILE
from .strategy import CredentialStrategy

if TYPE_CHECKING:
    from rich.console import Console

    from .store import CredentialStore

OPENAI_API_KEYS_URL = "https://platform.openai.com/api-keys"
OPENAI_AUTH_SOURCE_ENV = "TRESTO_OPENAI_AUTH_SOURCE"


class OpenAICredentialStrategy(OIDCCredentialMixin, CredentialStrategy):
    connectors = {"openai", "gpt"}
    env_names = ("OPENAI_API_KEY", "OPENAI_ADMIN_KEY")

    def __init__(
        self,
        store: CredentialStore,
        console: Console,
        codex_auth: CodexAuthProvider | None = None,
    ) -> None:
        super().__init__(store=store, console=console)
        self.codex_auth = codex_auth or CodexAuthProvider()

    def ensure(self) -> None:
        if any(os.getenv(name) for name in self.env_names):
            return
        if self._ensure_oidc_credentials():
            return

        stored_key = self.store.get("openai", "api_key")
        if stored_key:
            os.environ["OPENAI_API_KEY"] = stored_key
            os.environ[OPENAI_AUTH_SOURCE_ENV] = "stored_token"
            return

        self._prompt_for_credentials()

    def refresh(self, reason: str | None = None) -> None:
        auth_source = os.environ.get(OPENAI_AUTH_SOURCE_ENV)
        if reason:
            self.console.print(f"[yellow]{reason}[/yellow]")
        for env_name in self.env_names:
            os.environ.pop(env_name, None)
        os.environ.pop(OPENAI_AUTH_SOURCE_ENV, None)
        if not self._refresh_oidc_credentials():
            self.store.delete("openai", "api_key")
            if auth_source == "codex":
                self.console.print("[yellow]Codex browser auth was rejected by the OpenAI API.[/yellow]")
                self._prompt_for_api_key()
                return
            self._prompt_for_credentials()

    def _prompt_for_credentials(self) -> None:
        self.console.print("[yellow]OpenAI credentials are not set.[/yellow]")
        self.console.print("Choose how Tresto should authenticate to the OpenAI provider.")

        auth_method = Prompt.ask(
            "Authentication method",
            choices=["codex", "token"],
            default="codex",
        )
        if auth_method == "codex":
            self._use_codex_auth()
            return

        self._prompt_for_api_key()

    def _use_codex_auth(self) -> None:
        access_token = self.codex_auth.get_access_token()
        if access_token:
            self._apply_codex_token(access_token)
            return

        self.console.print("No usable Codex browser auth token was found.")
        if not Confirm.ask("Run `codex login` now?", default=True):
            raise CredentialError("Codex browser auth is required for the OpenAI provider.")

        self._apply_codex_token(self.codex_auth.login())

    def _apply_codex_token(self, access_token: str) -> None:
        access_error = self.codex_auth.openai_api_access_error(access_token)
        if access_error:
            self.console.print(f"[yellow]{access_error}[/yellow]")
            self.console.print("Use an OpenAI API key for this project, or sign into Codex with an account that has API access.")
            self._prompt_for_api_key()
            return

        os.environ["OPENAI_API_KEY"] = access_token
        os.environ[OPENAI_AUTH_SOURCE_ENV] = "codex"
        self.console.print("[green]Using Codex browser auth from ~/.codex/auth.json[/green]")

    def _prompt_for_api_key(self) -> None:
        self.console.print("Tresto uses the OpenAI API for this provider, so it needs an API key.")

        if Confirm.ask("Open the OpenAI API keys page in your browser?", default=True):
            webbrowser.open(OPENAI_API_KEYS_URL)

        api_key = Prompt.ask("Paste OPENAI_API_KEY for this session", password=True, default="")
        if not api_key:
            self.console.print(f"Create an API key at: {OPENAI_API_KEYS_URL}")
            raise CredentialError("OPENAI_API_KEY is required for the OpenAI provider.")

        os.environ["OPENAI_API_KEY"] = api_key
        os.environ[OPENAI_AUTH_SOURCE_ENV] = "token"

        if Confirm.ask(f"Save OPENAI_API_KEY to {TRESTO_CREDENTIALS_FILE} for future Tresto runs?", default=True):
            self.store.set("openai", "api_key", api_key)
            self.console.print(f"[green]Saved OpenAI credentials to {TRESTO_CREDENTIALS_FILE}[/green]")
