"""Project inspection cycle for codebase investigation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.panel import Panel

from .execution import execute_file_exploration_command
from .generation import (
    generate_file_exploration_command,
    generate_inspection_goals,
    generate_inspection_report,
    generate_progress_reflection,
)
from .models import FileExplorationData

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def _execute_file_exploration_cycle(
    state: TestAgentState, iteration_num: int, iteration_context: str
) -> tuple[str, str, bool]:
    """Execute the file exploration cycle until model decides to finish."""

    # Check if we already have a project inspection report
    existing_report = state.project_inspection_report
    if existing_report:
        console.print("📁 Found existing project inspection report")
        console.print(
            Panel(
                existing_report,
                title="📁 Existing Project Inspection Report",
                title_align="left",
                border_style="green",
                padding=(1, 2),
            )
        )
        return "existing_report", existing_report, True

    # Define inspection goals at the start
    console.print("🎯 Setting project inspection goals...")
    inspection_goals = await generate_inspection_goals(state)

    exploration_context = iteration_context
    exploration_attempt = 0
    exploration_history: list[str] = []  # Track exploration commands
    findings_history: list[str] = []  # Track what we've discovered
    MAX_EXPLORATION_ATTEMPTS = 50  # Smaller limit for file exploration
    REFLECTION_INTERVAL = 10  # Reflect every 10 attempts

    while exploration_attempt < MAX_EXPLORATION_ATTEMPTS:
        exploration_attempt += 1

        # Periodic reflection every 10 attempts
        if exploration_attempt > 1 and (exploration_attempt - 1) % REFLECTION_INTERVAL == 0:
            console.print(f"\n🤔 Time for progress reflection (after {exploration_attempt - 1} attempts)...")
            reflection = await generate_progress_reflection(
                state, inspection_goals, exploration_attempt - 1, findings_history
            )

            console.print(
                Panel(
                    reflection,
                    title=f"🤔 Progress Reflection (Attempt {exploration_attempt - 1})",
                    title_align="left",
                    border_style="yellow",
                    padding=(1, 2),
                )
            )

            # Check if model decided to finish based on reflection
            if "FINISH:" in reflection.upper():
                console.print("🏁 Model decided to finish based on reflection")
                final_output = f"Reflection after {exploration_attempt - 1} attempts:\n\n{reflection}"
                return reflection, final_output, True
            if "CONTINUE:" in reflection.upper():
                console.print("🔄 Model decided to continue exploration")
                continue_reason = reflection.split("CONTINUE:")[-1].strip()
                exploration_context = f"Continuing exploration because: {continue_reason}"

        if state.config.verbose:
            console.print(
                f"📁 Generating file exploration command (attempt {exploration_attempt}/{MAX_EXPLORATION_ATTEMPTS})..."
            )
        else:
            console.print(f"📁 Generating exploration (attempt {exploration_attempt}/{MAX_EXPLORATION_ATTEMPTS})...")

        # Generate exploration command
        exploration_command = await generate_file_exploration_command(state, exploration_context, exploration_history)

        # Extract the actual command
        command_lines = exploration_command.strip().split("\n")
        actual_command = ""

        for line in command_lines:
            line = line.strip()
            if line and not line.startswith("#"):
                if not actual_command:
                    actual_command = line
                    break

        if not actual_command:
            actual_command = "list ."  # Default command

        # Track the command
        exploration_history.append(actual_command)

        if state.config.verbose:
            console.print(f"🔧 Executing command: {actual_command}")
        else:
            console.print("🔧 Executing exploration...")

        exploration_result = execute_file_exploration_command(actual_command, Path.cwd())

        if exploration_result.success:
            console.print("✅ Exploration completed")

            # Track findings for reflection
            output_summary = (
                exploration_result.output[:100] + "..."
                if len(exploration_result.output) > 100
                else exploration_result.output
            )
            findings_history.append(f"Command '{actual_command}': {output_summary}")

            if state.config.verbose:
                console.print("📁 Exploration results:")
                console.print(
                    Panel(
                        exploration_result.output,
                        title="📁 File Exploration Results",
                        title_align="left",
                        border_style="blue",
                        padding=(1, 2),
                        expand=False,
                    )
                )

            # Check if model finished exploration
            output_text = exploration_result.output
            if "EXPLORATION_FINISHED" in output_text:
                console.print("🏁 Model finished exploration")
                final_output = f"Command: {actual_command}\n\n{output_text}"
                return exploration_command, final_output, True

            # Continue exploration
            console.print("🔄 Continuing exploration...")
            exploration_context = f"Last command: {actual_command}\nResult: {output_text}"
            continue

        console.print(f"❌ Exploration failed (attempt {exploration_attempt}): {exploration_result.error}")

        # Track failed attempts
        findings_history.append(f"FAILED Command '{actual_command}': {exploration_result.error}")

        # Update context for next attempt
        exploration_context = f"Previous exploration attempt failed with error: {exploration_result.error}\n\nPlease try a different command."

        continue

    # If we reach max attempts, force finish
    console.print(f"⚠️ Reached maximum exploration attempts ({MAX_EXPLORATION_ATTEMPTS}), finishing...")
    final_output = f"Exploration reached maximum attempts. Last command: {actual_command if 'actual_command' in locals() else 'none'}"
    return exploration_command if "exploration_command" in locals() else "list .", final_output, True


async def project_inspect_cycle(state: TestAgentState) -> TestAgentState:
    """
    Main project inspection cycle:
    1. Check if project inspection report already exists
    2. If not, model defines inspection goals
    3. Model explores project files systematically
    4. Model decides to continue or finish based on goals
    5. Generate final project inspection report
    6. Store report in file header (only this gets added to state.messages)

    Uses temporary_messages context manager to automatically clean up local context.
    """
    console.print("📁 Starting project inspection cycle...")

    with state.temporary_messages():
        iterations: list[FileExplorationData] = []
        iteration_context = ""

        # Single iteration for file exploration
        iteration_num = 1
        console.print("\n--- Project Inspection ---")

        # Execute file exploration cycle
        final_exploration_code, final_exploration_output, exploration_success = await _execute_file_exploration_cycle(
            state, iteration_num, iteration_context
        )

        # If we found an existing report, use it
        if final_exploration_code == "existing_report":
            console.print("✅ Using existing project inspection report")
            return state

        # Store exploration data
        exploration_data = FileExplorationData(
            exploration_command=final_exploration_code,
            exploration_success=exploration_success,
            exploration_output=final_exploration_output,
        )
        iterations.append(exploration_data)

        # Add exploration details to local messages for context
        state.local_messages.append(
            HumanMessage(
                content=f"Project inspection completed:\n"
                f"- File exploration: ✅ Success\n"
                f"- Exploration findings: {final_exploration_output[:300]}{'...' if len(final_exploration_output) > 300 else ''}"
            )
        )

        # Generate final project inspection report
        if state.config.verbose:
            console.print("📋 Generating project inspection report...")
        else:
            console.print("📋 Generating report...")
        project_report = await generate_inspection_report(state, iterations)

    # Outside the context manager - local_messages are now cleared
    # Add only the final report to messages and file header
    state.messages.append(HumanMessage(content="Model inspected the project files and generated the following report."))
    state.messages.append(HumanMessage(content=project_report))

    # Store the report in the file header
    state.project_inspection_report = project_report

    console.print("✅ Project inspection cycle completed")
    console.print(f"📊 Total explorations: {len(iterations)}")

    return state
