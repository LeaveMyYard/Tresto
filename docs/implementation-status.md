# Implementation Status

Tresto v1 focuses on the core local workflow:

- initialize a project with `tresto init`
- list model providers with `tresto models list`
- create tests with `tresto test create`
- iterate tests with `tresto test iterate`
- run tests with `tresto test run`
- inspect per-test database/debug information with `tresto db`

## Implemented

- Typer CLI with Rich terminal output.
- `tresto.yaml` configuration.
- OpenAI API default provider using the Codex model `gpt-5.3-codex`.
- Secondary Anthropic and test/mock connectors.
- Playwright codegen recording.
- LangGraph agent loop for generation, test execution, inspection, and user input.
- Pytest + Playwright boilerplate generation.
- Per-test storage for metadata and agent artifacts.

## Not Required for v1

The future ideas in `PLANS.md` are intentionally outside this v1 release unless they become necessary for the core workflow:

- automatic `data-testid` insertion into application code
- large-test splitting into helper functions or multiple tests
- post-generation prompt actions
- richer human-in-the-loop persistence
- cloud model runner
