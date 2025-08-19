"""Code generation utilities for playwright iteration."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, Any

from langchain_core.messages import SystemMessage
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.syntax import Syntax

from .execution import strip_markdown_code_fences

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState

    from .models import IterationData


console = Console()


async def generate_playwright_code(state: TestAgentState, iteration_context: str = "") -> str:
    """Generate playwright code using LLM."""
    llm = state.create_llm()
    
    context_prompt = f"\nContext from previous iteration:\n{iteration_context}" if iteration_context else ""
    
    generate_message = SystemMessage(
        textwrap.dedent(
            f"""\
            Generate Python playwright code for browser automation.
            Include all necessary imports at the top of your code.
            The code should define an async function called 'run' that takes a 'page' parameter.
            Write only the code, nothing else.
            Make sure the code is executable and follows playwright async patterns.
            {context_prompt}
            
            IMPORTANT GUIDELINES:
            - DO NOT call page.close() - the page will be used for inspection after your code runs
            - Start with minimal steps to reach the uncertain state you want to investigate
            - Focus on getting to a specific page state rather than complete user flows
            - Use this iteration to explore selectors, forms, buttons, and page structure
            - If you're unsure about selectors, write simple navigation code to get to the right page first
            
            Available imports you can use:
            - from playwright.async_api import expect (for assertions)
            - import asyncio (if needed)
            - Any other standard Python libraries
            
            Example structure:
            ```python
            from playwright.async_api import expect
            
            async def run(page):
                # Start simple - get to the page you want to investigate
                await page.goto("https://example.com/login")
                
                # Perform minimal steps to reach the state of interest
                await page.fill("#username", "test")
                await page.fill("#password", "test")
                await page.click("button[type='submit']")
                
                # Don't close the page - we'll inspect it next!
                # The page state will be captured for BeautifulSoup inspection
            ```
            """
        )
    )
    
    # Check verbose setting
    if not state.config.verbose:
        console.print("🤖 Generating playwright automation code...")
        # Generate without showing progress
        ai_content = ""
        async for chunk in llm.astream(state.all_messages + [generate_message]):
            if chunk.content:
                ai_content += chunk.content
        console.print("✅ Playwright code generated")
        return strip_markdown_code_fences(ai_content)
    
    # Verbose mode - show live progress
    ai_content = ""
    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.all_messages + [generate_message]):
            if chunk.content:
                ai_content += chunk.content
                
                # Show preview of generated code
                preview_code = strip_markdown_code_fences(ai_content)
                syntax = Syntax(
                    preview_code or "# Generating playwright code...",
                    "python",
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True,
                    background_color="default",
                )
                
                panel = Panel(
                    syntax,
                    title=f"🎭 Generating Playwright Code ({len(ai_content)} chars)",
                    title_align="left",
                    border_style="blue",
                )
                live.update(panel)
    
    return strip_markdown_code_fences(ai_content)


async def generate_soup_inspection_code(
    state: TestAgentState, 
    iteration_context: str = "", 
    globals_dict: dict[str, Any] | None = None
) -> str:
    """Generate BeautifulSoup inspection code using LLM."""
    llm = state.create_llm()
    
    context_prompt = f"\nContext from previous action:\n{iteration_context}" if iteration_context else ""
    
    # Format globals information
    globals_info = ""
    if globals_dict:
        globals_list = []
        for key, value in globals_dict.items():
            # Show type and a preview of the value
            value_preview = str(value)[:50]
            if len(str(value)) > 50:
                value_preview += "..."
            globals_list.append(f"  {key}: {type(value).__name__} = {value_preview}")
        
        if globals_list:
            globals_info = "\n\nAvailable variables from previous inspection attempts:\n" + "\n".join(globals_list)
    
    inspect_message = SystemMessage(
        textwrap.dedent(
            f"""\
            Generate Python code to inspect the current web page using BeautifulSoup.
            You have access to a 'soup' variable that contains the parsed HTML.
            You can also add any imports you need at the top.
            Write code that explores the page structure and extracts useful information.
            Use print() statements to output your findings.
            {context_prompt}{globals_info}
            
            IMPORTANT FEATURES:
            - Variables you define will be preserved across inspection attempts
            - You can build upon previous findings by reusing saved variables
            - Your output will be automatically formatted for better readability
            
            Available variables:
            - soup: BeautifulSoup object of the current page
            - BeautifulSoup: The BeautifulSoup class (already imported)
            
            Available imports you can add:
            - import re (for regular expressions)
            - from bs4 import BeautifulSoup (already available)
            - Any other standard Python libraries
            
            Write code to inspect the page and decide what to do next.
            At the end, print either "CONTINUE" or "FINISH" based on your findings.
            
            Example with variable preservation:
            ```python
            # Save findings for later use (will persist across attempts)
            if 'page_analysis' not in globals():
                page_analysis = {{}}
            
            # Analyze forms
            forms = soup.find_all('form')
            page_analysis['forms_count'] = len(forms)
            
            for i, form in enumerate(forms):
                inputs = form.find_all('input')
                print(f"Form {{i+1}}: {{len(inputs)}} inputs")
                for inp in inputs:
                    print(f"  - {{inp.get('name', 'unnamed')}}: {{inp.get('type', 'text')}}")
            
            print("CONTINUE")
            ```
            """
        )
    )
    
    # Check verbose setting
    if not state.config.verbose:
        console.print("🔍 Generating page inspection code...")
        # Generate without showing progress
        ai_content = ""
        async for chunk in llm.astream(state.all_messages + [inspect_message]):
            if chunk.content:
                ai_content += chunk.content
        console.print("✅ Inspection code generated")
        return strip_markdown_code_fences(ai_content)
    
    # Verbose mode - show live progress
    ai_content = ""
    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.all_messages + [inspect_message]):
            if chunk.content:
                ai_content += chunk.content
                
                # Show preview of generated code
                preview_code = strip_markdown_code_fences(ai_content)
                syntax = Syntax(
                    preview_code or "# Generating inspection code...",
                    "python",
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True,
                    background_color="default",
                )
                
                panel = Panel(
                    syntax,
                    title=f"🔍 Generating Inspection Code ({len(ai_content)} chars)",
                    title_align="left",
                    border_style="yellow",
                )
                live.update(panel)
    
    return strip_markdown_code_fences(ai_content)


async def generate_investigation_report(state: TestAgentState, iterations: list[IterationData]) -> str:
    """Generate a final investigation report based on all iterations."""
    llm = state.create_llm()
    
    # Prepare iteration summary
    iteration_summary = "\n\n".join([
        f"Iteration {i+1}:\n"
        f"- Playwright action: {it.playwright_code[:200]}{'...' if len(it.playwright_code) > 200 else ''}\n"
        f"- Action success: {it.playwright_success}\n"
        f"- Playwright error: {it.playwright_error if it.playwright_error else 'None'}\n"
        f"- Page inspection: {it.inspection_code[:200]}{'...' if len(it.inspection_code) > 200 else ''}\n"
        f"- Inspection success: {it.inspection_success}\n"
        f"- Inspection findings: {it.inspection_output[:300]}{'...' if len(it.inspection_output) > 300 else ''}"
        for i, it in enumerate(iterations)
    ])
    
    report_message = SystemMessage(
        textwrap.dedent(
            f"""\
            Based on the playwright automation investigation below, generate a comprehensive report.
            
            Investigation iterations performed:
            {iteration_summary}
            
            The report should include:
            1. Summary of what was investigated
            2. Key findings about the web application structure and functionality
            3. Notable elements found (forms, buttons, navigation, etc.)
            4. Any issues or errors encountered
            5. Recommendations for test automation
            6. Overall assessment of the application's testability
            7. Exact HTML examples of elements required for testing (collapsed format, without unrelated children/parents) - include specific selectors, attributes, and structure needed for automation
            
            For section 7, provide concrete HTML examples like:
            ```html
            <form id="login-form" class="auth-form">
                <div class="notifications-container">
                    ... <!-- This can be removed, as it is not relevant for initial goal -->
                </div>
                <input type="email" name="email" placeholder="Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit" class="btn-primary">Login</button>
            </form>
            ```
            
            Include the most reliable selectors for each element (ID, class, data attributes, etc.).
            
            Write a clear, structured investigation report.
            """
        )
    )
    
    # Check verbose setting
    if not state.config.verbose:
        console.print("📋 Generating investigation report...")
        # Generate without showing progress
        report_content = ""
        async for chunk in llm.astream(state.all_messages + [report_message]):
            if chunk.content:
                report_content += chunk.content
        console.print("✅ Investigation report generated")
        return report_content
    
    # Verbose mode - show live progress
    report_content = ""
    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.all_messages + [report_message]):
            if chunk.content:
                report_content += chunk.content
                
                panel = Panel(
                    report_content,
                    title=f"📋 Generating Investigation Report ({len(report_content)} chars)",
                    title_align="left",
                    border_style="green",
                )
                live.update(panel)
    
    return report_content 


async def generate_html_exploration_command(
    state: TestAgentState, 
    iteration_context: str = "", 
    exploration_history: list[str] | None = None
) -> str:
    """Generate HTML exploration command using LLM."""
    llm = state.create_llm()
    
    context_prompt = f"\nContext from previous action:\n{iteration_context}" if iteration_context else ""
    
    # Format exploration history
    history_info = ""
    if exploration_history:
        history_str = '\n'.join([f"  {i+1}. {cmd}" for i, cmd in enumerate(exploration_history[-5:])])  # Last 5 commands
        history_info = f"\n\nRecent exploration commands:\n{history_str}"
    
    explore_message = SystemMessage(
        textwrap.dedent(
            f"""\
            You are exploring an HTML page structure using interactive commands with CSS selectors.
            Issue ONE command at a time to investigate the page systematically.
            {context_prompt}{history_info}
            
            AVAILABLE COMMANDS:
            • show - Show collapsed HTML structure (start here)
            • expand <css-selector> - Expand element step by step
            • text <css-selector> - Show text content of element
            • attrs <css-selector> - Show attributes of element
            • finish - Complete exploration and generate report
            • help - Show command help
            
            🎯 PROGRESSIVE NAVIGATION STRATEGY:
            1. Start with 'show' to see the overall structure
            2. Use 'expand body' to see what's in the body
            3. Expand specific elements you can see: 'expand #root', 'expand .login-form'
            4. Navigate step-by-step - don't guess deep nested paths
            5. Use IDs and classes when available: '#id', '.class'
            6. Use simple element names: 'form', 'input', 'button'
            
            AVOID:
            • Complex nested selectors like 'body > div:nth-child(1) > div > form'
            • Guessing element positions without seeing them first
            • Deep paths before exploring intermediate levels
            
            PREFER:
            • Simple selectors: 'body', '#root', '.container', 'form'
            • Step-by-step exploration: expand what you can see
            • Use specific IDs/classes shown in the previous results
            
            YOUR TASK:
            Write ONE exploration command. Navigate progressively and use 'finish' when you have enough information.
            """
        )
    )
    
    # Check verbose setting
    if not state.config.verbose:
        console.print("🔍 Generating exploration command...")
        # Generate without showing progress
        ai_content = ""
        async for chunk in llm.astream(state.all_messages + [explore_message]):
            if chunk.content:
                ai_content += chunk.content
        console.print("✅ Exploration command generated")
        return ai_content.strip()
    
    # Verbose mode - show live progress
    ai_content = ""
    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.all_messages + [explore_message]):
            if chunk.content:
                ai_content += chunk.content
                
                panel = Panel(
                    ai_content,
                    title=f"🔍 Generating Exploration Command ({len(ai_content)} chars)",
                    title_align="left",
                    border_style="yellow",
                )
                live.update(panel)
    
    return ai_content.strip() 


async def generate_investigation_goals(state: TestAgentState) -> str:
    """Generate investigation goals for the playwright exploration cycle."""
    llm = state.create_llm()
    
    goals_message = SystemMessage(
        textwrap.dedent(
            """\
            You are about to start exploring a web page using playwright automation and HTML inspection.
            Before beginning exploration, you need to define clear investigation goals.
            
            YOUR TASK:
            Define 1-2 specific investigation goals for this web page exploration.
            
            Example goals:
            • "Find what is the html structure of the login container"
            • "What sidebar elements are there after login"
            
            Write your investigation goals clearly, one per line.
            Be specific about what you want to learn about this web application.
            """
        )
    )
    
    # Check verbose setting
    if not state.config.verbose:
        console.print("🎯 Defining investigation goals...")
        # Generate without showing progress
        goals_content = ""
        async for chunk in llm.astream(state.all_messages + [goals_message]):
            if chunk.content:
                goals_content += chunk.content
        console.print("✅ Investigation goals defined")
        return goals_content.strip()
    
    # Verbose mode - show live progress
    goals_content = ""
    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.all_messages + [goals_message]):
            if chunk.content:
                goals_content += chunk.content
                
                panel = Panel(
                    goals_content,
                    title="🎯 Defining Investigation Goals",
                    title_align="left",
                    border_style="cyan",
                    padding=(1, 2),
                )
                live.update(panel)
    
    return goals_content.strip()


async def generate_progress_reflection(
    state: TestAgentState, 
    investigation_goals: str,
    exploration_attempts: int,
    recent_findings: list[str]
) -> str:
    """Generate a reflection on progress toward investigation goals."""
    llm = state.create_llm()
    
    findings_summary = '\n'.join([f"- {finding}" for finding in recent_findings[-10:]])  # Last 10 findings
    
    reflection_message = SystemMessage(
        textwrap.dedent(
            f"""\
            You have been exploring a web page for {exploration_attempts} attempts.
            Time to reflect on your progress toward your investigation goals.
            
            YOUR ORIGINAL INVESTIGATION GOALS:
            {investigation_goals}
            
            RECENT EXPLORATION FINDINGS:
            {findings_summary}
            
            YOUR TASK:
            Reflect on your progress and decide whether to continue or finish exploration.
            
            Think verbosely about:
            1. Which goals have you accomplished or made progress on?
            2. What important information are you still missing?
            3. Have you discovered the key elements needed for testing?
            4. Are you getting diminishing returns from continued exploration?
            5. If some required elements could not be found, despite that they should be there, consider the case where this element is flaky and if it is logical to finish with information that this exact element is not stable and to try to search for another way of conducting the test
            
            Based on your reflection, end with either:
            - "CONTINUE: [reason why you need to keep exploring]"
            - "FINISH: [explanation of why you have enough information]"
            
            Be honest about whether continued exploration will be productive.
            """
        )
    )
    
    # Check verbose setting
    if not state.config.verbose:
        console.print("🤔 Reflecting on investigation progress...")
        # Generate without showing progress
        reflection_content = ""
        async for chunk in llm.astream(state.all_messages + [reflection_message]):
            if chunk.content:
                reflection_content += chunk.content
        console.print("✅ Progress reflection completed")
        return reflection_content.strip()
    
    # Verbose mode - show live progress
    reflection_content = ""
    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.all_messages + [reflection_message]):
            if chunk.content:
                reflection_content += chunk.content
                
                panel = Panel(
                    reflection_content,
                    title=f"🤔 Progress Reflection (After {exploration_attempts} Attempts)",
                    title_align="left",
                    border_style="yellow",
                )
                live.update(panel)
    
    return reflection_content.strip() 