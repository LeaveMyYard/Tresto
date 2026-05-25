# Project Architecture

Tresto is a Python CLI that turns a manually recorded browser flow into a pytest + Playwright async test, then iterates on that test with an AI agent.

## Main Flow

1. The user runs `tresto init` in an application repository.
2. Tresto writes `tresto.yaml` and copies pytest/Playwright boilerplate into the configured test directory.
3. The user runs `tresto test create --test-name <name>`.
4. Tresto runs Playwright codegen and stores the recording under `.recordings`.
5. The LangGraph agent generates or updates the test file.
6. The agent runs the test, captures a Playwright trace and screenshot artifacts, inspects the trace when needed, and iterates until the test passes or it needs user input.

`tresto scaffold` is a separate planning-only flow. It scans the codebase, asks the model for a structured E2E test plan, writes `tresto/README.md`, creates skipped placeholder test files, and optionally scaffolds an app database cleanup pytest hook after user approval.

## Components

- CLI commands live under `tresto.commands` and expose `init`, `models`, `test`, `db`, and `version`.
- Configuration is loaded from `tresto.yaml` by `TrestoConfig`.
- The default AI provider is OpenAI API with `gpt-5.3-codex`; Anthropic remains available by explicit config.
- Browser recording is delegated to `playwright codegen`.
- Agent execution uses LangGraph with tools for code generation, test execution, trace inspection, and user questions.
- Test metadata, agent debug state, and artifacts are stored under internal directories in the configured test root.

## Configuration

Minimal v1 configuration:

```yaml
project:
  name: my-app
  url: http://localhost:3000
  test_directory: ./tresto/tests

ai:
  connector: openai
  model: gpt-5.3-codex

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
```

`OPENAI_API_KEY` configures the default provider. The `secrets` list in `tresto.yaml` is reserved for application secrets that generated tests may read through `tresto.secrets`.
