from __future__ import annotations

import os
import stat
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from rich.console import Console

from tresto.utils.credentials import (
    CodexAuthProvider,
    CodexCredentialStrategy,
    CredentialStore,
    OIDCToken,
    OpenAICredentialStrategy,
    ensure_provider_credentials,
    refresh_provider_credentials,
)

if TYPE_CHECKING:
    from pathlib import Path


class FakeCodexAuth(CodexAuthProvider):
    def __init__(
        self,
        access_token: str | None = None,
        login_token: str = "login-token",
        api_access_error: str | None = None,
    ) -> None:
        self.access_token = access_token
        self.login_token = login_token
        self.api_access_error = api_access_error
        self.login_called = False

    def get_access_token(self) -> str | None:
        return self.access_token

    def login(self) -> str:
        self.login_called = True
        return self.login_token

    def openai_api_access_error(self, access_token: str) -> str | None:
        return self.api_access_error

    def get_account_id(self, access_token: str | None = None) -> str | None:
        token = access_token or self.access_token
        if token in {self.access_token, self.login_token}:
            return "account-id"
        return None


def test_openai_strategy_uses_environment_first(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    strategy = OpenAICredentialStrategy(CredentialStore(tmp_path / "credentials"), Console())

    with patch("rich.prompt.Prompt.ask") as prompt:
        strategy.ensure()

    prompt.assert_not_called()
    assert os.environ["OPENAI_API_KEY"] == "env-key"


def test_openai_strategy_loads_stored_key(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    store = CredentialStore(tmp_path / "credentials")
    store.set("openai", "api_key", "stored-key")

    OpenAICredentialStrategy(store, Console()).ensure()

    assert os.environ["OPENAI_API_KEY"] == "stored-key"


def test_openai_strategy_prompts_and_saves_to_tresto_credentials(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("tresto.utils.credentials.store.TRESTO_CREDENTIALS_FILE", tmp_path / "credentials")
    monkeypatch.setattr("tresto.utils.credentials.openai.TRESTO_CREDENTIALS_FILE", tmp_path / "credentials")
    monkeypatch.setattr("webbrowser.open", lambda _url: True)

    with (
        patch("rich.prompt.Confirm.ask", side_effect=[False, True]),
        patch("rich.prompt.Prompt.ask", side_effect=["token", "prompted-key"]),
    ):
        ensure_provider_credentials("openai", Console())

    assert os.environ["OPENAI_API_KEY"] == "prompted-key"
    content = (tmp_path / "credentials").read_text(encoding="utf-8")
    assert "[openai]" in content
    assert "api_key = prompted-key" in content
    mode = stat.S_IMODE((tmp_path / "credentials").stat().st_mode)
    assert mode == 0o600


def test_openai_strategy_uses_codex_browser_auth_choice(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    codex_auth = FakeCodexAuth(access_token="codex-access-token")

    with patch("rich.prompt.Prompt.ask", return_value="codex") as prompt:
        OpenAICredentialStrategy(CredentialStore(tmp_path / "credentials"), Console(), codex_auth=codex_auth).ensure()

    prompt.assert_called_once()
    assert os.environ["OPENAI_API_KEY"] == "codex-access-token"
    assert os.environ["TRESTO_OPENAI_AUTH_SOURCE"] == "codex"


def test_openai_strategy_runs_codex_login_when_choice_has_no_token(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    codex_auth = FakeCodexAuth(access_token=None, login_token="new-codex-token")

    with (
        patch("rich.prompt.Prompt.ask", return_value="codex"),
        patch("rich.prompt.Confirm.ask", return_value=True),
    ):
        OpenAICredentialStrategy(CredentialStore(tmp_path / "credentials"), Console(), codex_auth=codex_auth).ensure()

    assert codex_auth.login_called is True
    assert os.environ["OPENAI_API_KEY"] == "new-codex-token"


def test_openai_strategy_falls_back_to_token_when_codex_lacks_api_scope(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    codex_auth = FakeCodexAuth(
        access_token="codex-access-token",
        api_access_error="Codex browser auth cannot access the OpenAI API: 403 missing scopes",
    )

    with (
        patch("rich.prompt.Prompt.ask", side_effect=["codex", "api-key"]),
        patch("rich.prompt.Confirm.ask", side_effect=[False, False]),
    ):
        OpenAICredentialStrategy(CredentialStore(tmp_path / "credentials"), Console(), codex_auth=codex_auth).ensure()

    assert os.environ["OPENAI_API_KEY"] == "api-key"
    assert os.environ["TRESTO_OPENAI_AUTH_SOURCE"] == "token"


def test_codex_strategy_uses_existing_browser_auth(tmp_path: Path) -> None:
    codex_auth = FakeCodexAuth(access_token="codex-access-token")
    strategy = CodexCredentialStrategy(CredentialStore(tmp_path / "credentials"), Console(), codex_auth=codex_auth)

    with patch("rich.prompt.Confirm.ask") as confirm:
        strategy.ensure()

    confirm.assert_not_called()
    assert codex_auth.login_called is False


def test_codex_strategy_runs_login_when_no_browser_auth(tmp_path: Path) -> None:
    codex_auth = FakeCodexAuth(access_token=None, login_token="new-codex-token")
    strategy = CodexCredentialStrategy(CredentialStore(tmp_path / "credentials"), Console(), codex_auth=codex_auth)

    with patch("rich.prompt.Confirm.ask", return_value=True):
        strategy.ensure()

    assert codex_auth.login_called is True


def test_openai_strategy_uses_stored_oidc_token(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_OIDC_ISSUER_URL", "https://auth.example.test")
    monkeypatch.setenv("OPENAI_OIDC_CLIENT_ID", "tresto-cli")

    store = CredentialStore(tmp_path / "credentials")
    store.set("openai_oidc", "access_token", "stored-access-token")
    store.set("openai_oidc", "expires_at", "4102444800")

    with patch("tresto.utils.credentials.oidc.OIDCAuthenticator.login") as login:
        OpenAICredentialStrategy(store, Console()).ensure()

    login.assert_not_called()
    assert os.environ["OPENAI_API_KEY"] == "stored-access-token"


def test_openai_strategy_runs_oidc_login_when_configured(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_OIDC_ISSUER_URL", "https://auth.example.test")
    monkeypatch.setenv("OPENAI_OIDC_CLIENT_ID", "tresto-cli")

    store = CredentialStore(tmp_path / "credentials")

    with patch(
        "tresto.utils.credentials.oidc.OIDCAuthenticator.login",
        return_value=OIDCToken(access_token="oidc-access-token", refresh_token="refresh-token", expires_at=4102444800),
    ) as login:
        OpenAICredentialStrategy(store, Console()).ensure()

    login.assert_called_once()
    assert os.environ["OPENAI_API_KEY"] == "oidc-access-token"
    assert store.get("openai_oidc", "access_token") == "oidc-access-token"
    assert store.get("openai_oidc", "refresh_token") == "refresh-token"


def test_openai_refresh_clears_stale_credentials_and_prompts(tmp_path: Path, monkeypatch: Any) -> None:
    credentials_path = tmp_path / "credentials"
    monkeypatch.setenv("OPENAI_API_KEY", "stale-env-key")
    monkeypatch.setattr("tresto.utils.credentials.store.TRESTO_CREDENTIALS_FILE", credentials_path)
    monkeypatch.setattr("tresto.utils.credentials.openai.TRESTO_CREDENTIALS_FILE", credentials_path)
    monkeypatch.setattr("webbrowser.open", lambda _url: True)

    CredentialStore(credentials_path).set("openai", "api_key", "stale-stored-key")

    with (
        patch("rich.prompt.Confirm.ask", side_effect=[False, True]),
        patch("rich.prompt.Prompt.ask", side_effect=["token", "fresh-key"]),
    ):
        refresh_provider_credentials("openai", console=Console())

    assert os.environ["OPENAI_API_KEY"] == "fresh-key"
    content = credentials_path.read_text(encoding="utf-8")
    assert "stale-stored-key" not in content
    assert "api_key = fresh-key" in content


def test_openai_refresh_restarts_oidc_when_configured(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "stale-env-key")
    monkeypatch.setenv("OPENAI_OIDC_ISSUER_URL", "https://auth.example.test")
    monkeypatch.setenv("OPENAI_OIDC_CLIENT_ID", "tresto-cli")

    store = CredentialStore(tmp_path / "credentials")
    store.set("openai_oidc", "access_token", "stale-token")

    with patch(
        "tresto.utils.credentials.oidc.OIDCAuthenticator.login",
        return_value=OIDCToken(access_token="fresh-oidc-token", expires_at=4102444800),
    ) as login:
        OpenAICredentialStrategy(store, Console()).refresh()

    login.assert_called_once()
    assert os.environ["OPENAI_API_KEY"] == "fresh-oidc-token"
    assert store.get("openai_oidc", "access_token") == "fresh-oidc-token"


def test_non_openai_connector_does_not_prompt(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("tresto.utils.credentials.store.TRESTO_CREDENTIALS_FILE", tmp_path / "credentials")

    with patch("rich.prompt.Prompt.ask") as prompt:
        ensure_provider_credentials("anthropic", Console())

    prompt.assert_not_called()
    assert not (tmp_path / "credentials").exists()
