"""Execution utilities for playwright and BeautifulSoup code."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from rich.console import Console
from rich.panel import Panel

from .models import InspectionResult, PlaywrightExecutionResult


def strip_markdown_code_fences(text: str) -> str:
    """Extract Python code from markdown fences."""
    pattern = re.compile(r"```\s*(?:python|py)?\s*\n([\s\S]*?)\n```", re.IGNORECASE)
    m = pattern.search(text)
    if m:
        return m.group(1).strip()
    pattern2 = re.compile(r"^```\s*\n?([\s\S]*?)\n?```\s*$", re.IGNORECASE)
    m2 = pattern2.match(text.strip())
    if m2:
        return m2.group(1).strip()
    return text.strip()


async def execute_playwright_code(
    code: str, 
    base_url: str | None = None, 
    headless: bool = True
) -> PlaywrightExecutionResult:
    """Execute playwright code and return result with page snapshot."""
    try:
        # Create a clean namespace for execution
        namespace: dict[str, Any] = {}
        
        # Execute the user code in the namespace (including their imports)
        exec(code, namespace)
        
        # Look for an async function to run (typically 'run' or 'main')
        async_func = namespace.get('run') or namespace.get('main')
        if not async_func or not callable(async_func):
            return PlaywrightExecutionResult(
                success=False, 
                error_message="No 'run' or 'main' async function found in the code"
            )
        
        # Execute with playwright context
        page_html = None
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Patch page.close() to prevent the model from closing the page
            original_close = page.close
            async def patched_close():
                # Do nothing - we need the page open for inspection
                pass
            page.close = patched_close
            
            if base_url:
                await page.goto(base_url)
            
            # Execute the user's function
            await async_func(page)
            
            # Capture page HTML for snapshot
            page_html = await page.content()
            
            # Restore original close method
            page.close = original_close
            
            await browser.close()
        
        return PlaywrightExecutionResult(success=True, page_html=page_html)
        
    except Exception as e:  # noqa: BLE001
        # Catch ALL exceptions and provide them as feedback to the model
        return PlaywrightExecutionResult(success=False, error_message=str(e))


def execute_soup_inspection_code(
    code: str, 
    soup: BeautifulSoup, 
    globals_dict: dict[str, Any]
) -> InspectionResult:
    """Execute inspection code with access to BeautifulSoup object and preserved globals."""
    
    try:
        # Capture print output
        output_lines: list[str] = []

        def capture_print(*args, **kwargs):
            # Convert args to strings and join them
            message = ' '.join(str(arg) for arg in args)
            output_lines.append(message)
        
        # Always add these required variables (overwrite if they exist)
        globals_dict = globals_dict | {
            'soup': soup,
            'BeautifulSoup': BeautifulSoup,
            'print': capture_print
        }
        
        # Execute the code
        exec(code, globals_dict)
        
        # Format output with rich styling (but don't expose rich to the model)
        formatted_output = _format_inspection_output(output_lines)
        
        return InspectionResult(success=True, output=formatted_output)
        
    except Exception as e:  # noqa: BLE001
        # Catch ALL exceptions and provide them as feedback to the model
        return InspectionResult(success=False, output="", error=str(e))


def _format_inspection_output(output_lines: list[str]) -> str:
    """Format inspection output with rich styling."""
    if not output_lines:
        return "Code executed successfully (no output)"
    
    # Join all output lines
    raw_output = '\n'.join(output_lines)
    
    # Create a nice panel for the output using rich
    try:
        console = Console(file=None, force_terminal=False, width=80)
        with console.capture() as capture:
            console.print(
                Panel(
                    raw_output,
                    title="🔍 Inspection Results",
                    title_align="left",
                    border_style="blue",
                    padding=(1, 2)
                )
            )
        
        # Return the captured rich output
        return capture.get()
    except Exception:  # noqa: BLE001
        # Fallback to plain text if rich formatting fails
        return raw_output 