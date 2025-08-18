"""Playwright iteration cycle for website investigation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup
from langchain_core.messages import SystemMessage
from rich.console import Console
from rich.panel import Panel

from .execution import execute_html_exploration_command, execute_playwright_code
from .generation import generate_html_exploration_command, generate_investigation_report, generate_playwright_code
from .models import IterationData

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def _execute_playwright_iteration(
    state: TestAgentState, 
    iteration_num: int, 
    iteration_context: str
) -> tuple[bool, str, IterationData]:
    """Execute a single playwright iteration (code generation + execution)."""
    if state.config.verbose:
        console.print("🤖 Generating playwright automation code...")
    playwright_code = await generate_playwright_code(state, iteration_context)
    
    if state.config.verbose:
        console.print("🚀 Executing playwright code...")
    else:
        console.print("🚀 Executing playwright automation...")
    playwright_result = await execute_playwright_code(
        playwright_code,
        base_url=state.config.project.base_url,
        headless=state.config.browser.headless if state.config.browser else True
    )
    
    if not playwright_result.success:
        console.print(f"❌ Playwright execution failed: {playwright_result.error_message}")
        
        # Add failed iteration to local messages for context
        state.local_messages.append(SystemMessage(
            content=f"Iteration {iteration_num}: Playwright execution failed with error: {playwright_result.error_message}"
        ))
        
        # Store failed iteration
        failed_iteration = IterationData(
            playwright_code=playwright_code,
            playwright_success=False,
            playwright_error=playwright_result.error_message,
            inspection_code="",
            inspection_success=False,
            inspection_output="",
            inspection_error=""
        )
        
        return False, f"Previous playwright execution failed: {playwright_result.error_message}", failed_iteration
    
    console.print("✅ Playwright code executed successfully")
    return True, playwright_result.page_html, IterationData(
        playwright_code=playwright_code,
        playwright_success=True,
        playwright_error=None,
        inspection_code="",  # Will be filled by inspection
        inspection_success=False,  # Will be updated
        inspection_output="",  # Will be updated
        inspection_error=None  # Will be updated
    )


async def _execute_inspection_cycle(
    state: TestAgentState,
    iteration_num: int,
    page_html: str,
    iteration_context: str
) -> tuple[str, str, bool]:
    """Execute the HTML exploration cycle until model decides to finish."""
    soup = BeautifulSoup(page_html, 'html.parser')
    
    inspection_context = iteration_context
    inspection_attempt = 0
    exploration_history: list[str] = []  # Track exploration commands
    MAX_EXPLORATION_ATTEMPTS = 150  # Prevent infinite loops
    
    while inspection_attempt < MAX_EXPLORATION_ATTEMPTS:
        inspection_attempt += 1
        if state.config.verbose:
            console.print(f"🔍 Generating exploration command (attempt {inspection_attempt}/{MAX_EXPLORATION_ATTEMPTS})...")
        else:
            console.print(f"🔍 Generating exploration (attempt {inspection_attempt}/{MAX_EXPLORATION_ATTEMPTS})...")
        
        # Generate exploration command
        exploration_command = await generate_html_exploration_command(
            state, inspection_context, exploration_history
        )
        
        # Extract the actual command (remove any extra text)
        command_lines = exploration_command.strip().split('\n')
        actual_command = ""
        
        for line in command_lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if not actual_command:  # Take the first non-comment line
                    actual_command = line
                    break
        
        if not actual_command:
            actual_command = "show"  # Default command
        
        # Track the command
        exploration_history.append(actual_command)
        
        if state.config.verbose:
            console.print(f"🔬 Executing command: {actual_command}")
        else:
            console.print("🔬 Executing exploration...")
            
        exploration_result = execute_html_exploration_command(
            actual_command, soup, {}  # No globals needed for commands
        )
        
        if exploration_result.success:
            console.print("✅ Exploration completed")
            if state.config.verbose:
                # Show full exploration results wrapped in a panel
                console.print("🔍 Exploration results:")
                console.print(Panel(
                    exploration_result.output,
                    title="🔍 HTML Exploration Results",
                    title_align="left",
                    border_style="blue",
                    padding=(1, 2),
                    expand=False
                ))
            
            # Check if model finished exploration
            output_text = exploration_result.output
            if "EXPLORATION_FINISHED" in output_text:
                console.print("🏁 Model finished exploration")
                final_output = f"Command: {actual_command}\n\n{output_text}"
                return exploration_command, final_output, True
            
            # Continue exploration
            console.print("🔄 Continuing exploration...")
            inspection_context = f"Last command: {actual_command}\nResult: {output_text}"
            continue
        
        console.print(f"❌ Exploration failed (attempt {inspection_attempt}): {exploration_result.error}")
        
        # Add failed exploration to local messages for context
        state.local_messages.append(SystemMessage(
            content=f"Iteration {iteration_num}, exploration attempt {inspection_attempt}: Failed with error: {exploration_result.error}"
        ))
        
        # Update context for next attempt
        inspection_context = f"Previous exploration attempt failed with error: {exploration_result.error}\n\nPlease try a different command."
        
        # Continue the inner loop to retry
        continue
    
    # If we reach max attempts, force finish
    console.print(f"⚠️ Reached maximum exploration attempts ({MAX_EXPLORATION_ATTEMPTS}), finishing...")
    final_output = f"Exploration reached maximum attempts. Last command: {actual_command if 'actual_command' in locals() else 'none'}"
    return exploration_command if 'exploration_command' in locals() else "show", final_output, True


def _check_iteration_decision(inspection_output: str) -> tuple[str, str]:
    """Check what the model decided based on inspection output."""
    if "FINISH" in inspection_output.upper():
        return "FINISH", "🏁 Model decided to finish investigation"
    if "CONTINUE" in inspection_output.upper():
        return "CONTINUE", "🔄 Model decided to continue investigation"
    return "CONTINUE", "⚠️ No clear decision from model, continuing..."


async def playwright_iterate_cycle(state: TestAgentState) -> TestAgentState:
    """
    Main playwright iteration cycle:
    1. Model writes playwright code
    2. Execute playwright code
    3. Model writes BeautifulSoup inspection code
    4. Execute inspection code and let model analyze the page
    5. If inspection fails, allow model to retry inspection
    6. Model decides to continue or finish
    7. Repeat until model decides to finish
    8. Generate final investigation report (only this gets added to state.messages)
    
    Uses temporary_messages context manager to automatically clean up local context.
    """
    console.print("🎭 Starting Playwright iteration cycle...")
    
    with state.temporary_messages():
        iterations: list[IterationData] = []
        iteration_context = ""
        
        while True:
            iteration_num = len(iterations) + 1
            console.print(f"\n--- Iteration {iteration_num} ---")
            
            # Execute playwright iteration
            success, result_data, iteration_data = await _execute_playwright_iteration(
                state, iteration_num, iteration_context
            )
            
            if not success:
                # Playwright failed, continue with next iteration
                iterations.append(iteration_data)
                iteration_context = result_data  # This is the error message
                continue
            
            # Playwright succeeded, result_data is page_html
            page_html = result_data
            
            # Execute inspection cycle
            final_inspection_code, final_inspection_output, inspection_success = await _execute_inspection_cycle(
                state, iteration_num, page_html, iteration_context
            )
            
            # Update iteration data with inspection results
            iteration_data.inspection_code = final_inspection_code
            iteration_data.inspection_success = inspection_success
            iteration_data.inspection_output = final_inspection_output
            iteration_data.inspection_error = None if inspection_success else "Unknown error"
            
            iterations.append(iteration_data)
            
            # Add successful iteration details to local messages for context
            state.local_messages.append(SystemMessage(
                content=f"Iteration {iteration_num} completed:\n"
                f"- Playwright code executed: ✅ Success\n"
                f"- Page inspection: ✅ Success\n"
                f"- Inspection findings: {final_inspection_output[:300]}{'...' if len(final_inspection_output) > 300 else ''}"
            ))
            
            # Check if model decided to finish
            decision, message = _check_iteration_decision(final_inspection_output)
            console.print(message)
            
            if decision == "FINISH":
                break
            iteration_context = final_inspection_output
            continue
        
        # Generate final investigation report (this happens within the context manager)
        if state.config.verbose:
            console.print("📋 Generating final investigation report...")
        else:
            console.print("📋 Generating report...")
        investigation_report = await generate_investigation_report(state, iterations)
    
    # Outside the context manager - local_messages are now cleared
    # Add only the final report to messages (not the iteration details)
    state.messages.append(SystemMessage(
        content="Model investigated the website using playwright automation and generated the following report."
    ))
    state.messages.append(SystemMessage(content=investigation_report))
    
    console.print("✅ Playwright iteration cycle completed")
    console.print(f"📊 Total iterations: {len(iterations)}")
    
    return state 