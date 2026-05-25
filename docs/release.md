# v1 Release Checklist

Run these checks before publishing a v1 build:

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run mypy .
uv build
```

Then validate the built wheel in a clean temporary environment:

```bash
uv venv /tmp/tresto-v1-smoke
source /tmp/tresto-v1-smoke/bin/activate
pip install dist/tresto_ai-1.0.0-py3-none-any.whl
tresto --help
tresto models list
```

For an end-to-end local smoke test, run `codex login`, run `tresto init` inside a sample web application, install Playwright browsers, and create a small test with `tresto test create --test-name smoke.homepage`.
