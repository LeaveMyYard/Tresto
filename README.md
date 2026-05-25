# Tresto 🎭🤖

## Status: v1

Turbocharge your testing with AI. Tresto pairs Playwright codegen with an agent that understands your intent and iterates toward robust, stable tests.

Convert manual checks into reliable automated E2E in minutes—no boilerplate, no lock‑in, just `tresto.yaml` at your project root.

### Why you’ll love it

- Manual testing everything is slow and fragile. It’s easy to miss regressions, hard to repeat precisely, and burns time every release.
- Writing E2E tests by hand is tedious. Locators break, timing is flaky, and keeping tests readable and maintainable takes effort.
- Tresto gives you the best of both worlds. Describe intent like you do in manual testing, and let AI produce durable, maintainable code you’d be proud to commit.

### What makes Tresto different

- Generates fully valid pytest + Playwright tests. No bespoke runner, no lock‑in. You keep industry‑standard tools and best practices.
- You stay in control. Ask the model to improve selectors, assert more precisely, or refactor flows—Tresto listens and iterates.
- Post‑release sanity. Tests started failing after your last release? Ask Tresto to investigate each failing test and determine if code needs updating or if it’s a real product bug.

## ✨ Features

- **🎯 Smart test generation**: Natural-language to runnable Playwright tests
- **🎭 Playwright integration**: Uses the Playwright Python stack
- **🤖 Agentic workflow**: Generate → run → analyze → iterate
- **🧠 OpenAI-first AI**: OpenAI API models by default, including Codex coding models
- **⚙️ YAML config**: Single `tresto.yaml` at your project root
- **🧪 Pytest-native**: Tests are discoverable and runnable with pytest

## 🚀 Quick Start

### Installation

```bash
pip install tresto-ai
```

Or from source:

```bash
git clone https://github.com/LeaveMyYard/Tresto.git
cd Tresto
uv tool install --no-cache .
```

### Initialize in your project

```bash
tresto init
```

This will create:

- test scaffold in your chosen directory (default: `./tresto/tests`)
- a `tresto.yaml` configuration file

Then install Playwright browsers once per machine:

```bash
playwright install
```

### Create and iterate on tests

```bash
# Open interactive AI-driven flow to create a test
tresto test create --test-name login.success   # optional name

# Plan a project-wide test structure without writing real test logic
tresto scaffold

# Iterate on an existing test with the agent
tresto test iterate --test-name login.success

# Run tests
tresto test run
```

## 📋 Requirements

- Python 3.13+
- Playwright browsers (`playwright install`)
- Browser auth or API key(s) for your selected AI provider(s)
  - For the default Codex provider, run `codex login`
  - For the OpenAI API provider, set `OPENAI_API_KEY`
  - Alternatively, configure an OIDC issuer with `OPENAI_OIDC_ISSUER_URL` and `OPENAI_OIDC_CLIENT_ID`

## 🛠️ Configuration (tresto.yaml)

After `tresto init`, edit `tresto.yaml`:

```yaml
project:
  name: my-awesome-app
  url: http://localhost:3000
  test_directory: ./tresto/tests

ai:
  connector: codex
  model: gpt-5.2-codex
  max_iterations: 5
  temperature: 0.1

browser:
  headless: true
  timeout: 30000
  viewport:
    width: 1280
    height: 720

recording:
  auto_wait: true
  capture_screenshots: true
  generate_selectors: auto

secrets:
  - ADMIN_EMAIL
  - ADMIN_PASSWORD
```

Notes:

- `connector: codex` uses browser auth from `~/.codex/auth.json`, created by `codex login`, and calls the ChatGPT Codex backend.
- `connector: openai` uses the OpenAI Platform API through `OPENAI_API_KEY`; ChatGPT/Codex browser tokens usually do not have those API scopes.
- Pasted OpenAI API keys can be stored in the user-level `~/.tresto/credentials` file with owner-only permissions.
- If `OPENAI_OIDC_ISSUER_URL` and `OPENAI_OIDC_CLIENT_ID` are set, Tresto uses a browser-based OIDC authorization-code flow with PKCE before falling back to API-key prompting. Optional OIDC settings are `OPENAI_OIDC_CLIENT_SECRET`, `OPENAI_OIDC_SCOPES`, `OPENAI_OIDC_AUDIENCE`, `OPENAI_OIDC_RESOURCE`, `OPENAI_OIDC_REDIRECT_HOST`, `OPENAI_OIDC_REDIRECT_PORT`, and `OPENAI_OIDC_TIMEOUT_SECONDS`.
- `secrets` is a list of application/test secret environment variable names exposed to generated tests through `tresto.secrets`.
- `connector` and `model` must be one of the values exposed by `tresto models list`.

## 📖 CLI Commands

- **`tresto`**: Shows a welcome panel and quick tips
- **`tresto init`**: Interactive setup; creates `tresto.yaml` and scaffolds tests
  - Options: `--force`
- **`tresto scaffold`**: Scan the codebase, plan an E2E test structure, create `tresto/README.md`, and write skipped placeholder test files
  - Options: `--force`, `--yes-db-cleanup`, `--no-db-cleanup`, `--max-files <n>`
- **`tresto models list`**: List available AI connectors and their models
- **`tresto test`**: Alias for running tests (equivalent to `tresto test run`)
- **`tresto test run [PYTEST_ARGS...]`**: Run tests via pytest, forwards extra args
- **`tresto test create [--test-name <name>]`**: Start agent to create a test
- **`tresto test iterate [--test-name <name>]`**: Iterate on a test with the agent
- **`tresto db list-tests|show|clear|info`**: Inspect and manage test data storage
- **`tresto version`**: Show Tresto version

Default provider:

- Tresto defaults to the Codex browser-auth provider with the model `gpt-5.2-codex`.
- OpenAI Platform API models remain available with `connector: openai` and `OPENAI_API_KEY`.
- Anthropic remains available by explicit `tresto.yaml` configuration.

## 🏗️ How it works

1. Inspect project and prompts based on your intent
2. Generate Playwright tests with the selected model
3. Run with pytest; collect logs, screenshots, insights
4. Iterate until assertions and flows are stable

## 🧰 Built with

Tresto is built on proven, open technologies:

- Python
- LangChain and LangGraph for agentic orchestration
- Playwright and Playwright codegen for robust, modern browser automation

Much thanks to the creators and maintainers of these projects—we stand on your shoulders.

## 🔭 Future plans

- Automatic locator improvements across your codebase
- Improved processing of larger tests
- Supervisor agent that reviews the main agent’s resulting test
- Cloud model runner: access multiple providers from one subscription
- …and more improvements coming

## 🤝 Contributing

See [docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md).

### Development

```bash
git clone https://github.com/LeaveMyYard/Tresto.git
cd Tresto
uv sync --dev
pre-commit install
pytest
ruff check .
mypy .
```

## 📄 License

MIT — see [LICENSE](LICENSE).

## 📞 Support

- Docs: `./docs/`
- Issues: https://github.com/LeaveMyYard/Tresto/issues
- Discussions: https://github.com/LeaveMyYard/Tresto/discussions
