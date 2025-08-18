"""Execution utilities for playwright and BeautifulSoup code."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, NavigableString
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


def _generate_collapsed_html_view(soup: BeautifulSoup, max_depth: int = 2) -> str:
    """Generate a collapsed view of HTML showing only top-level structure."""
    return _format_element_collapsed(soup, 0, max_depth)


def _format_element_collapsed(element: Any, current_depth: int, max_depth: int) -> str:
    """Format an element in collapsed view."""
    if isinstance(element, NavigableString):
        text = str(element).strip()
        if text:
            return f"{'  ' * current_depth}📝 \"{text[:50]}{'...' if len(text) > 50 else ''}\"\n"
        return ""
    
    if not hasattr(element, 'name') or element.name is None:
        return ""
    
    # Format tag opening
    attrs = []
    if hasattr(element, 'attrs') and element.attrs:
        for key, value in element.attrs.items():
            if isinstance(value, list):
                value = ' '.join(value)
            attrs.append(f'{key}="{value}"')
    
    attrs_str = f" {' '.join(attrs)}" if attrs else ""
    indent = "  " * current_depth
    
    # Count children
    children = [child for child in element.children if hasattr(child, 'name') or (isinstance(child, NavigableString) and str(child).strip())]
    child_count = len(children)
    
    if current_depth >= max_depth and child_count > 0:
        # Show collapsed version
        return f"{indent}📁 <{element.name}{attrs_str}> [{child_count} children]\n"
    
    # Show expanded version
    result = f"{indent}📂 <{element.name}{attrs_str}>\n"
    
    for child in children:
        result += _format_element_collapsed(child, current_depth + 1, max_depth)
    
    return result


def _find_element_by_css_selector(soup: BeautifulSoup, selector: str) -> Any | None:
    """Find an element by CSS selector."""
    try:
        # Use BeautifulSoup's built-in CSS selector support
        return soup.select_one(selector)
    except Exception:  # noqa: BLE001
        return None


def execute_html_exploration(command: str, soup: BeautifulSoup) -> str:
    """Execute HTML exploration command and return formatted response."""
    command = command.strip().lower()
    
    if command.startswith(('show', 'view')) or command == 'start':
        # Show top-level collapsed view
        view = _generate_collapsed_html_view(soup, max_depth=2)
        return f"📄 HTML Structure (2 levels):\n\n{view}\n" + \
               "�� To explore deeper, try: 'expand body' or 'expand html' first"
    
    if command.startswith('expand '):
        # Expand specific element using CSS selector
        selector = command[7:].strip()  # Remove 'expand '
        element = _find_element_by_css_selector(soup, selector)
        
        if element is None:
            # Provide more helpful error message with suggestions
            suggestions = _get_navigation_suggestions(soup, selector)
            return f"❌ Could not find element with selector: {selector}\n\n" + \
                   f"💡 Try these selectors instead:\n{suggestions}"
        
        # Show expanded view of this element
        view = _format_element_collapsed(element, 0, max_depth=3)
        return f"📂 Expanded view of '{selector}' (3 levels):\n\n{view}\n" + \
               "💡 Use more specific selectors or try exploring children shown above"
    
    if command.startswith('text '):
        # Show text content of specific element
        selector = command[5:].strip()  # Remove 'text '
        element = _find_element_by_css_selector(soup, selector)
        
        if element is None:
            suggestions = _get_navigation_suggestions(soup, selector)
            return f"❌ Could not find element with selector: {selector}\n\n" + \
                   f"💡 Try these selectors instead:\n{suggestions}"
        
        text_content = element.get_text(strip=True)
        return f"📝 Text content of '{selector}':\n{text_content[:500]}{'...' if len(text_content) > 500 else ''}"
    
    if command.startswith('attrs '):
        # Show attributes of specific element
        selector = command[6:].strip()  # Remove 'attrs '
        element = _find_element_by_css_selector(soup, selector)
        
        if element is None:
            suggestions = _get_navigation_suggestions(soup, selector)
            return f"❌ Could not find element with selector: {selector}\n\n" + \
                   f"💡 Try these selectors instead:\n{suggestions}"
        
        if hasattr(element, 'attrs') and element.attrs:
            attrs_str = '\n'.join([f"  {k}: {v}" for k, v in element.attrs.items()])
            return f"🏷️ Attributes of '{selector}':\n{attrs_str}"
        return f"🏷️ Element '{selector}' has no attributes"
    
    if command in ['finish', 'done', 'complete']:
        return "🏁 EXPLORATION_FINISHED - Investigation complete, ready to generate report"
    
    if command in ['help', '?']:
        return """🔍 HTML Exploration Commands:
        
• show / view / start - Show collapsed HTML structure
• expand <css-selector> - Expand element (e.g., 'expand body')
• text <css-selector> - Show text content of element
• attrs <css-selector> - Show attributes of element
• finish - Complete exploration and generate report
• help - Show this help

🎯 NAVIGATION STRATEGY:
1. Start with 'show' to see overall structure
2. Use 'expand body' to see body contents
3. Then expand specific elements you see: 'expand #id' or 'expand .class'
4. Navigate step by step, don't guess deep paths

CSS Selector Examples:
• body - The body element
• #myid - Element with id="myid"
• .myclass - Element with class="myclass"
• div - First div element
• form - First form element
"""
    
    return f"❓ Unknown command: {command}\nUse 'help' to see available commands."


def _get_navigation_suggestions(soup: BeautifulSoup, failed_selector: str) -> str:
    """Get helpful navigation suggestions when a selector fails."""
    suggestions = []
    
    # Try to find common starting points
    body = soup.find('body')
    if body:
        # Get direct children of body with their attributes
        children = [child for child in body.children if hasattr(child, 'name') and child.name]
        if children:
            suggestions.append("• expand body (to see body contents)")
            for child in children[:3]:  # Show first 3 children
                if hasattr(child, 'attrs') and child.attrs:
                    if 'id' in child.attrs:
                        suggestions.append(f"• expand #{child.attrs['id']} (by ID)")
                    if 'class' in child.attrs:
                        classes = child.attrs['class']
                        if isinstance(classes, list):
                            classes = classes[0]  # Take first class
                        suggestions.append(f"• expand .{classes} (by class)")
                # Always suggest the element name
                suggestions.append(f"• expand {child.name} (first {child.name} element)")
    
    # Look for common elements
    common_elements = ['form', 'input', 'button', 'div', 'span', 'a']
    for elem_name in common_elements:
        element = soup.find(elem_name)
        if element:
            suggestions.append(f"• expand {elem_name} (first {elem_name} found)")
            break
    
    # Look for elements with IDs
    elements_with_ids = soup.find_all(attrs={'id': True})
    for elem in elements_with_ids[:2]:  # First 2 elements with IDs
        if hasattr(elem, 'attrs') and 'id' in elem.attrs:
            suggestions.append(f"• expand #{elem.attrs['id']} (by ID)")
    
    return '\n'.join(suggestions[:6]) if suggestions else "• Try 'expand body' or 'show' to see structure"


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


def execute_html_exploration_command(
    command: str, 
    soup: BeautifulSoup, 
    globals_dict: dict[str, Any]
) -> InspectionResult:
    """Execute HTML exploration command and return formatted result."""
    try:
        # Execute the exploration command
        result = execute_html_exploration(command, soup)
        
        return InspectionResult(success=True, output=result)
        
    except Exception as e:  # noqa: BLE001
        # Catch ALL exceptions and provide them as feedback to the model
        return InspectionResult(success=False, output="", error=str(e))
