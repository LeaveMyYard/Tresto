"""Code generation utilities for project inspection."""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState

    from .models import FileExplorationData


console = Console()


async def generate_inspection_goals(state: TestAgentState) -> str:
    """Generate project inspection goals."""
    llm = state.create_llm()

    goals_message = HumanMessage(
        textwrap.dedent(
            f"""\
            You are about to start exploring project files to understand the codebase structure.
            Before beginning exploration, you need to define clear inspection goals.
            
            Current context:
            - Test name: {state.test_name}
            - Test instructions: {state.test_instructions}
            - Project path: {Path.cwd()}
            
            YOUR TASK:
            Define 2-4 specific project inspection goals focused on finding files related to your test case.
            Focus on what you need to discover in the source code to understand the application structure.
            
            Example goals:
            • "Find React components related to user authentication (login, signup, etc.)"
            • "Locate API endpoints and services that handle user data"
            • "Identify form validation logic and error handling patterns"
            • "Find test files to understand existing testing patterns"
            • "Locate configuration files and understand project structure"
            
            Write your inspection goals clearly, one per line, starting with "Goal:".
            Be specific about what types of files and functionality you want to discover.
            """
        )
    )

    # Check verbose setting
    if not state.config.verbose:
        console.print("🎯 Defining project inspection goals...")
        goals_content = ""
        async for chunk in llm.astream(state.all_messages + [goals_message]):
            if chunk.content:
                goals_content += str(chunk.content)
        console.print("✅ Project inspection goals defined")
        return goals_content.strip()

    # Verbose mode - show live progress
    goals_content = ""
    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.all_messages + [goals_message]):
            if chunk.content:
                goals_content += str(chunk.content)

                panel = Panel(
                    goals_content,
                    title="🎯 Defining Project Inspection Goals",
                    title_align="left",
                    border_style="cyan",
                    padding=(1, 2),
                )
                live.update(panel)

    return goals_content.strip()


async def generate_file_exploration_command(
    state: TestAgentState, exploration_context: str = "", exploration_history: list[str] | None = None
) -> str:
    """Generate file exploration command using LLM."""
    llm = state.create_llm()

    context_prompt = f"\nContext from previous exploration:\n{exploration_context}" if exploration_context else ""

    # Format exploration history
    history_info = ""
    if exploration_history:
        history_str = "\n".join(
            [f"  {i + 1}. {cmd}" for i, cmd in enumerate(exploration_history[-5:])]
        )  # Last 5 commands
        history_info = f"\n\nRecent exploration commands:\n{history_str}"

    explore_message = HumanMessage(
        textwrap.dedent(
            f"""\
            You are exploring project files to understand the codebase structure.
            Issue ONE command at a time to investigate files systematically.
            {context_prompt}{history_info}
            
            AVAILABLE COMMANDS:
            • list <path> - List directory contents (start with 'list .')
            • read <file> - Read specific file contents  
            • find <pattern> - Find files matching pattern
            • finish - Complete exploration and generate report
            • help - Show command help
            
            🎯 SYSTEMATIC EXPLORATION STRATEGY:
            1. Start with 'list .' to see project structure
            2. Explore key directories: 'list src', 'list components', etc.
            3. Find relevant files: 'find login', 'find *.test.*', 'find component'
            4. Read important files: 'read src/App.js', 'read package.json'
            5. Focus on files related to your test case
            
            EXPLORATION EXAMPLES:
            • list . - See project root structure
            • list src - Explore source directory
            • find login - Find files related to login
            • read src/components/LoginForm.tsx - Read login component
            • find *.test.* - Find test files
            • find api - Find API-related files
            
            YOUR TASK:
            Write ONE file exploration command. Focus on discovering files related to your test case.
            Use 'finish' when you have sufficient understanding of the project structure.
            """
        )
    )

    # Check verbose setting
    if not state.config.verbose:
        console.print("📁 Generating file exploration command...")
        ai_content = ""
        async for chunk in llm.astream(state.all_messages + [explore_message]):
            if chunk.content:
                ai_content += str(chunk.content)
        console.print("✅ File exploration command generated")
        return ai_content.strip()

    # Verbose mode - show live progress
    ai_content = ""
    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.all_messages + [explore_message]):
            if chunk.content:
                ai_content += str(chunk.content)

                panel = Panel(
                    ai_content,
                    title=f"📁 Generating File Exploration Command ({len(ai_content)} chars)",
                    title_align="left",
                    border_style="yellow",
                )
                live.update(panel)

    return ai_content.strip()


async def generate_progress_reflection(
    state: TestAgentState, inspection_goals: str, exploration_attempts: int, recent_findings: list[str]
) -> str:
    """Generate a reflection on progress toward inspection goals."""
    llm = state.create_llm()

    findings_summary = "\n".join([f"- {finding}" for finding in recent_findings[-10:]])  # Last 10 findings

    reflection_message = HumanMessage(
        textwrap.dedent(
            f"""\
            You have been exploring project files for {exploration_attempts} attempts.
            Time to reflect on your progress toward your inspection goals.
            
            YOUR ORIGINAL INSPECTION GOALS:
            {inspection_goals}
            
            RECENT EXPLORATION FINDINGS:
            {findings_summary}
            
            YOUR TASK:
            Reflect on your progress and decide whether to continue or finish exploration.
            
            Think verbosely about:
            1. Which goals have you accomplished or made progress on?
            2. What important files or patterns are you still missing?
            3. Have you discovered the key components needed for your test case?
            4. Are you getting diminishing returns from continued exploration?
            
            Based on your reflection, end with either:
            - "CONTINUE: [reason why you need to keep exploring]"
            - "FINISH: [explanation of why you have enough information]"
            
            Be honest about whether continued exploration will be productive.
            Focus on finding files directly related to your test case.
            """
        )
    )

    # Check verbose setting
    if not state.config.verbose:
        console.print("🤔 Reflecting on inspection progress...")
        reflection_content = ""
        async for chunk in llm.astream(state.all_messages + [reflection_message]):
            if chunk.content:
                reflection_content += str(chunk.content)
        console.print("✅ Progress reflection completed")
        return reflection_content.strip()

    # Verbose mode - show live progress
    reflection_content = ""
    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.all_messages + [reflection_message]):
            if chunk.content:
                reflection_content += str(chunk.content)

                panel = Panel(
                    reflection_content,
                    title=f"🤔 Progress Reflection (After {exploration_attempts} Attempts)",
                    title_align="left",
                    border_style="yellow",
                )
                live.update(panel)

    return reflection_content.strip()


async def generate_inspection_report(state: TestAgentState, explorations: list[FileExplorationData]) -> str:
    """Generate a final project inspection report based on all explorations."""
    llm = state.create_llm()

    # Prepare exploration summary
    exploration_summary = "\n\n".join(
        [
            f"Exploration {i + 1}:\n"
            f"- Command: {exp.exploration_command[:200]}{'...' if len(exp.exploration_command) > 200 else ''}\n"
            f"- Success: {exp.exploration_success}\n"
            f"- Findings: {exp.exploration_output[:400]}{'...' if len(exp.exploration_output) > 400 else ''}"
            for i, exp in enumerate(explorations)
        ]
    )

    report_message = HumanMessage(
        textwrap.dedent(
            f"""\
            Based on the project file exploration below, generate a comprehensive project inspection report.
            
            Project exploration performed:
            {exploration_summary}
            
            The report should include:
            1. **Project Structure Overview**: Key directories and organization
            2. **Relevant Files for Test Case**: List of files directly related to the test case with brief descriptions
            3. **Key Components Found**: Important React components, services, or modules
            4. **Patterns and Conventions**: Coding patterns, file naming, project conventions observed
            5. **Dependencies and Technologies**: Key libraries and frameworks used
            6. **Test-Related Insights**: Existing test patterns, testing setup, relevant test files
            
            Format the report clearly with sections and bullet points.
            Focus on information that will help with writing effective tests.
            Include specific file paths and brief explanations of what each file contains.
            
            Example format:
            ## Project Structure Overview
            - src/components/ - React components
            - src/services/ - API and business logic
            
            ## Relevant Files for Test Case
            - src/components/LoginForm.tsx - Main login component with form validation
            - src/services/auth.js - Authentication API calls and token management
            
            ## Key Components Found
            - LoginForm component handles user authentication
            - AuthService manages login/logout operations
            
            Write a clear, structured project inspection report.
            """
        )
    )

    # Check verbose setting
    if not state.config.verbose:
        console.print("📋 Generating project inspection report...")
        report_content = ""
        async for chunk in llm.astream(state.all_messages + [report_message]):
            if chunk.content:
                report_content += str(chunk.content)
        console.print("✅ Project inspection report generated")
        return report_content

    # Verbose mode - show live progress
    report_content = ""
    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.all_messages + [report_message]):
            if chunk.content:
                report_content += str(chunk.content)

                panel = Panel(
                    report_content,
                    title=f"📋 Generating Project Inspection Report ({len(report_content)} chars)",
                    title_align="left",
                    border_style="green",
                )
                live.update(panel)

    return report_content
