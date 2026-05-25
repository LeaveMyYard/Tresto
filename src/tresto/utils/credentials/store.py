from __future__ import annotations

import configparser
import stat
from pathlib import Path

TRESTO_HOME = Path.home() / ".tresto"
TRESTO_CREDENTIALS_FILE = TRESTO_HOME / "credentials"


class CredentialStore:
    """User-level credential storage for Tresto provider keys."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or TRESTO_CREDENTIALS_FILE

    def get(self, section: str, key: str) -> str | None:
        parser = self._read()
        if not parser.has_section(section):
            return None
        value = parser.get(section, key, fallback=None)
        return value or None

    def set(self, section: str, key: str, value: str) -> None:
        parser = self._read()
        if not parser.has_section(section):
            parser.add_section(section)
        parser.set(section, key, value)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            parser.write(f)
        self.path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def delete(self, section: str, key: str) -> None:
        parser = self._read()
        if not parser.has_section(section):
            return
        parser.remove_option(section, key)
        if not parser.items(section):
            parser.remove_section(section)

        if parser.sections():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as f:
                parser.write(f)
            self.path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        elif self.path.exists():
            self.path.unlink()

    def _read(self) -> configparser.ConfigParser:
        parser = configparser.ConfigParser()
        if self.path.exists():
            parser.read(self.path, encoding="utf-8")
        return parser
