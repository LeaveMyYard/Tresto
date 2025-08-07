"""AI agent for test generation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from jinja2 import Template
from rich.console import Console

if TYPE_CHECKING:
    from tresto.core.config import TrestoConfig

    from .connectors.base import AIConnector

from .connectors.base import ChatMessage
from .connectors.factory import ConnectorFactory

console = Console()


class TestGenerationAgent:
    """AI agent that generates test code from recorded actions."""

    def __init__(self, config: TrestoConfig) -> None:
        """Initialize the test generation agent."""
        self.config = config
        self.connector: AIConnector | None = None
        self._setup_connector()

    def _setup_connector(self) -> None:
        """Setup the AI connector based on configuration."""
        try:
            # Try to get the provider from config, default to anthropic
            provider = getattr(self.config.ai, "provider", "anthropic")
            self.connector = ConnectorFactory.create_connector(
                provider=provider, model_name=self.config.ai.model, temperature=self.config.ai.temperature
            )

            if not self.connector.is_available:
                console.print(f"[yellow]Warning: {provider} connector not available (missing API key?)[/yellow]")
                # Try to find an available connector
                available = ConnectorFactory.get_available_connectors()
                if available:
                    self.connector = available[0]
                    console.print(f"[green]Using {type(self.connector).__name__} instead[/green]")
                else:
                    console.print("[red]No AI connectors available. Please set API keys.[/red]")

        except (ValueError, ImportError, OSError) as e:
            console.print(f"[red]Error setting up AI connector: {e}[/red]")
            self.connector = None

    async def generate_test(
        self,
        test_name: str,
        description: str,
        recording_data: dict[str, Any],
        max_iterations: int = 5,
    ) -> str:
        """Generate test code from recording data."""

        if not self.connector:
            raise ValueError("No AI connector available. Please check your API keys.")

        console.print("🧠 Analyzing recorded actions...")

        # Create the initial prompt
        prompt = self._create_generation_prompt(test_name, description, recording_data)

        console.print("✍️  Generating initial test code...")

        # Generate initial test code
        test_code = await self._call_ai(prompt)

        console.print("🔄 Iterating and improving the code...")

        # Iterate and improve the code
        for iteration in range(max_iterations):
            console.print(f"   Iteration {iteration + 1}/{max_iterations}")

            # Analyze the code and suggest improvements
            analysis_prompt = self._create_analysis_prompt(test_code, recording_data)
            analysis = await self._call_ai(analysis_prompt)

            # If no improvements suggested, we're done
            if "no improvements" in analysis.lower() or "looks good" in analysis.lower():
                console.print("   ✅ Code looks good!")
                break

            # Generate improved code
            improvement_prompt = self._create_improvement_prompt(test_code, analysis)
            improved_code = await self._call_ai(improvement_prompt)

            # Update the test code
            test_code = improved_code

        console.print("🎯 Finalizing test code...")

        return test_code

    async def _call_ai(self, prompt: str) -> str:
        """Call the AI connector with the given prompt."""
        if not self.connector:
            raise ValueError("No AI connector available")

        try:
            messages = [ChatMessage(role="user", content=prompt)]
            result = await self.connector.generate(
                messages=messages,
                temperature=self.config.ai.temperature,
                max_tokens=4000,
            )
            return result.content

        except Exception as e:
            console.print(f"[red]Error calling AI: {e}[/red]")
            raise

    def _create_generation_prompt(self, test_name: str, description: str, recording_data: dict[str, Any]) -> str:
        """Create the initial code generation prompt."""

        actions_summary = self._summarize_actions(recording_data.get("actions", []))

        template = Template(
            """
You are an expert test automation engineer. Generate a high-quality Python test using Playwright based on the recorded user actions.

**Test Requirements:**
- Test Name: {{ test_name }}
- Description: {{ description }}
- Target URL: {{ url }}
- Page Title: {{ page_title }}

**Recorded Actions:**
{{ actions_summary }}

**Code Requirements:**
1. Use pytest and Playwright async API
2. Use proper type hints and modern Python
3. Include proper docstrings
4. Use data-testid selectors when available, fallback to other robust selectors
5. Add appropriate waits and assertions
6. Handle potential errors gracefully
7. Follow the test class pattern: class Test{ClassName}
8. Use descriptive method names starting with test_
9. Add meaningful assertions to verify the expected outcomes
10. Use expect() for assertions with Playwright

**Template Structure:**
```python
import pytest
from playwright.async_api import Page, expect

class Test{{ test_name|title|replace('_', '') }}:
    \"\"\"{{ description }}\"\"\"
    
    async def test_{{ test_name }}(self, page: Page) -> None:
        \"\"\"{{ description }}\"\"\"
        # Your test code here
```

Generate only the Python test code, no explanations.
        """.strip()
        )

        return template.render(
            test_name=test_name,
            description=description,
            url=recording_data.get("url", ""),
            page_title=recording_data.get("page_title", ""),
            actions_summary=actions_summary,
        )

    def _create_analysis_prompt(self, test_code: str, recording_data: dict[str, Any]) -> str:
        """Create prompt for analyzing and improving test code."""

        template = Template(
            """
Review this Playwright test code and suggest improvements:

**Current Test Code:**
```python
{{ test_code }}
```

**Original Recording Data:**
{{ recording_data }}

**Analysis Checklist:**
1. Are the selectors robust and unlikely to break?
2. Are there appropriate waits for dynamic content?
3. Are the assertions meaningful and complete?
4. Is error handling adequate?
5. Is the code readable and maintainable?
6. Are there any missing test steps from the recording?
7. Are there any unnecessary or redundant steps?

Provide specific improvement suggestions or say "no improvements needed" if the code looks good.
        """.strip()
        )

        return template.render(test_code=test_code, recording_data=json.dumps(recording_data, indent=2))

    def _create_improvement_prompt(self, test_code: str, analysis: str) -> str:
        """Create prompt for improving test code based on analysis."""

        template = Template(
            """
Improve this Playwright test code based on the analysis:

**Current Code:**
```python
{{ test_code }}
```

**Improvement Analysis:**
{{ analysis }}

Generate the improved Python test code implementing the suggested improvements. 
Return only the complete improved code, no explanations.
        """.strip()
        )

        return template.render(test_code=test_code, analysis=analysis)

    def _summarize_actions(self, actions: list[dict[str, Any]]) -> str:
        """Create a human-readable summary of recorded actions."""
        if not actions:
            return "No actions recorded"

        summary_lines = []
        for i, action in enumerate(actions, 1):
            action_type = action.get("type", "unknown")

            if action_type == "click":
                selectors = action.get("selectors", {})
                target = (
                    f"data-testid='{selectors.get('dataTestId')}'"
                    if selectors.get("dataTestId")
                    else f"#{selectors.get('id')}"
                    if selectors.get("id")
                    else f".{selectors.get('className')}"
                    if selectors.get("className")
                    else f"{selectors.get('tagName', 'element')}"
                )
                text = (
                    selectors.get("textContent", "")[:30] + "..."
                    if len(selectors.get("textContent", "")) > 30
                    else selectors.get("textContent", "")
                )
                summary_lines.append(f"{i}. Click on {target}" + (f" (text: '{text}')" if text else ""))

            elif action_type == "input":
                selectors = action.get("selectors", {})
                target = (
                    f"data-testid='{selectors.get('dataTestId')}'"
                    if selectors.get("dataTestId")
                    else f"#{selectors.get('id')}"
                    if selectors.get("id")
                    else f"name='{selectors.get('name')}'"
                    if selectors.get("name")
                    else f"input[type='{selectors.get('type')}']"
                    if selectors.get("type")
                    else "input field"
                )
                value = (
                    action.get("value", "")[:50] + "..."
                    if len(action.get("value", "")) > 50
                    else action.get("value", "")
                )
                summary_lines.append(f"{i}. Type '{value}' in {target}")

            elif action_type == "navigation":
                url = action.get("url", "")
                title = action.get("title", "")
                summary_lines.append(f"{i}. Navigate to {url}" + (f" (title: '{title}')" if title else ""))

        return "\n".join(summary_lines)
