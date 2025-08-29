from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from .execution import execute_html_exploration

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def inspect_html_tool(state: TestAgentState) -> TestAgentState:
    """Tool for interactively exploring HTML content using BeautifulSoup."""
    
    # Check if we have HTML content to inspect
    if state.last_run_result is None or state.last_run_result.soup is None:
        error_panel = Panel(
            "No HTML content available to inspect. Run a test first to capture HTML.",
            title="❌ No HTML Data",
            title_align="left",
            border_style="red",
            highlight=True,
        )
        console.print(error_panel)
        
        state.messages.append(
            HumanMessage(content="Error: No HTML content available to inspect. Run a test first to capture HTML.")
        )
        return state
    
    soup = state.last_run_result.soup
    llm = state.create_llm()

    # Interactive exploration loop
    while True:
        # Request HTML exploration command from AI
        command_request_message = HumanMessage(
            textwrap.dedent(
                """\
                You are exploring HTML content from a web page using BeautifulSoup.
                
                Available commands:
                - show/view/start: Show collapsed HTML structure (2 levels deep)
                - expand <css-selector>: Expand specific element (e.g., 'expand body', 'expand .main-content')
                - text <css-selector>: Show text content of an element
                - attrs <css-selector>: Show attributes of an element
                - finish: Complete exploration and move on
                - help: Show detailed help
                
                Provide ONLY the command you want to execute (e.g., "show" or "expand body").
                Start with "show" to see the overall structure, then explore specific areas.
                """
            )
        )
        
        # Stream the AI's command selection
        command_content = ""
        
        console.print()  # Add spacing before streaming
        
        with Live(console=console, refresh_per_second=10) as live:
            async for chunk in llm.astream(state.all_messages + [command_request_message]):
                if chunk.content:
                    command_content += chunk.content
                    
                    # Create markdown content for the command selection
                    markdown_content = Markdown(command_content)
                    char_count = len(command_content)
                    
                    # Display in a panel with character count
                    panel = Panel(
                        markdown_content,
                        title=f"🤖 AI selecting HTML command... ({char_count} characters)",
                        title_align="left",
                        border_style="yellow",
                        highlight=True,
                    )
                    live.update(panel)
        
        command = " ".join(command_content.split())
        console.print(f"🔍 Executing command: [bold cyan]{command}[/bold cyan]")
        
        # Execute the HTML exploration command
        try:
            result = execute_html_exploration(command, soup)

            if result is None:
                console.print("[bold green]✅ HTML exploration completed[/bold green]", justify="center")
                break
            
            # Display the result in a panel
            result_panel = Panel(
                result,
                title="📋 HTML Exploration Result",
                title_align="left",
                border_style="green",
                highlight=True,
            )
            console.print(result_panel)
            
            # Add to conversation context
            state.messages.append(AIMessage(content=f"Command: {command}"))
            state.messages.append(HumanMessage(content=f"HTML exploration result:\n{result}"))

        except Exception as e:  # noqa: BLE001
            error_panel = Panel(
                f"Error executing command '{command}': {e}",
                title="❌ Command Error",
                title_align="left",
                border_style="red",
                highlight=True,
            )
            console.print(error_panel)
            
            state.messages.append(
                HumanMessage(content=f"Error executing HTML command '{command}': {e}")
            )
    
    # Move local messages to main conversation
    state.messages.extend(state.local_messages)
    state.local_messages.clear()
    
    return state