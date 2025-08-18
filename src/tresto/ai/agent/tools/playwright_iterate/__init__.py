"""Playwright iteration cycle for website investigation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup
from langchain_core.messages import SystemMessage
from rich.console import Console

from .execution import execute_playwright_code, execute_soup_inspection_code
from .generation import generate_investigation_report, generate_playwright_code, generate_soup_inspection_code
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
    console.print("🤖 Generating playwright automation code...")
    playwright_code = await generate_playwright_code(state, iteration_context)
    
    console.print("🚀 Executing playwright code...")
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
    """Execute the inspection cycle until model decides to finish."""
    soup = BeautifulSoup(page_html, 'html.parser')
    
    inspection_context = iteration_context
    inspection_attempt = 0
    inspection_globals: dict[str, Any] = {}  # Preserve globals across inspection attempts
    
    while True:
        inspection_attempt += 1
        console.print(f"🔍 Generating page inspection code (attempt {inspection_attempt})...")
        inspection_code = await generate_soup_inspection_code(state, inspection_context, inspection_globals)
        
        console.print("🔬 Executing inspection code...")
        inspection_result = execute_soup_inspection_code(inspection_code, soup, inspection_globals)
        
        if inspection_result.success:
            console.print("✅ Page inspection completed")
            console.print(f"🔍 Inspection findings:\n{inspection_result.output[:200]}{'...' if len(inspection_result.output) > 200 else ''}")
            
            # Check if model wants to continue or finish inspection attempts
            if "FINISH" in inspection_result.output.upper():
                console.print("🏁 Model decided to finish inspection attempts")
                return inspection_code, inspection_result.output, True
            if "CONTINUE" in inspection_result.output.upper():
                console.print("🔄 Model decided to continue inspection attempts")
                inspection_context = inspection_result.output
                continue
            console.print("⚠️ No clear decision from model in inspection, assuming finished")
            return inspection_code, inspection_result.output, True
        
        console.print(f"❌ Inspection failed (attempt {inspection_attempt}): {inspection_result.error}")
        
        # Add failed inspection to local messages for context
        state.local_messages.append(SystemMessage(
            content=f"Iteration {iteration_num}, inspection attempt {inspection_attempt}: Failed with error: {inspection_result.error}"
        ))
        
        # Update context for next inspection attempt
        inspection_context = f"Previous inspection attempt failed with error: {inspection_result.error}\n\nPlease fix the code and try again."
        
        # Continue the inner loop to retry inspection
        continue


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
        console.print("📋 Generating final investigation report...")
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