"""Execution utilities for playwright and BeautifulSoup code."""

from __future__ import annotations

import argparse
import io
import shlex
import sys
from typing import Any

from bs4 import BeautifulSoup, NavigableString

# Content size limits to prevent overwhelming the agent
MAX_TEXT_LENGTH = 200  # For individual text nodes
MAX_FULL_TEXT_LENGTH = 300  # For complete text content extraction
MAX_ATTR_VALUE_LENGTH = 100  # For individual attribute values
MAX_ATTRS_TOTAL_LENGTH = 200  # For combined attributes string
MAX_VIEW_LENGTH = 2000  # For complete HTML views
MAX_SUGGESTIONS_LENGTH = 500  # For navigation suggestions


class _HtmlExplorationParser:
    """Custom argument parser for HTML exploration commands."""

    def __init__(self):
        """Initialize the parser with subcommands."""
        self.parser = argparse.ArgumentParser(
            prog="html_explorer",
            description="Interactive HTML exploration tool",
            add_help=False,  # We'll handle help manually
            exit_on_error=False,  # Don't exit, return error instead
        )

        # Create subcommands
        subparsers = self.parser.add_subparsers(dest="command", help="Available commands", required=True)

        # Show/view command
        show_parser = subparsers.add_parser("show", aliases=["view", "start"], help="Show collapsed HTML structure")
        show_parser.add_argument("--depth", type=int, default=2, help="Maximum depth to show (default: 2)")

        # Expand command
        expand_parser = subparsers.add_parser("expand", help="Expand specific element using CSS selector")
        expand_parser.add_argument(
            "selector",
            nargs="+",
            help="CSS selector for the element to expand (e.g., 'body', '#myid', '.class', '.parent .child')",
        )
        expand_parser.add_argument("--depth", type=int, default=3, help="Maximum depth to show (default: 3)")

        # Text command
        text_parser = subparsers.add_parser("text", help="Show text content of element")
        text_parser.add_argument("selector", nargs="+", help="CSS selector for the element (can contain spaces)")

        # Attrs command
        attrs_parser = subparsers.add_parser("attrs", help="Show attributes of element")
        attrs_parser.add_argument("selector", nargs="+", help="CSS selector for the element (can contain spaces)")

        # Finish command
        subparsers.add_parser("finish", aliases=["done", "complete"], help="Complete exploration and generate report")

        # Help command
        help_parser = subparsers.add_parser("help", aliases=["?"], help="Show detailed help information")
        help_parser.add_argument("subcommand", nargs="?", help="Show help for specific subcommand")

    def parse_command(self, command_str: str) -> tuple[argparse.Namespace | None, str | None]:
        """
        Parse command string and return (args, error_message).

        Returns:
            (args, None) on success
            (None, error_message) on parsing error
        """

        # Capture stderr to get error messages
        old_stderr = sys.stderr
        captured_stderr = io.StringIO()
        sys.stderr = captured_stderr

        try:
            # Split command into arguments, handling quoted strings
            args_list = shlex.split(command_str)

            # Parse the arguments
            args = self.parser.parse_args(args_list)
            return args, None

        except SystemExit:
            # argparse calls sys.exit on error, capture the error message
            error_msg = captured_stderr.getvalue()
            return None, error_msg.strip() if error_msg.strip() else "Invalid command format"

        except Exception as e:  # noqa: BLE001
            return None, f"Command parsing error: {e}"

        finally:
            sys.stderr = old_stderr


def _trim_content(content: str, max_length: int) -> str:
    """Trim content to specified length with ellipsis if needed."""
    if len(content) <= max_length:
        return content
    return content[:max_length] + "..."


def _generate_collapsed_html_view(soup: BeautifulSoup, max_depth: int = 2) -> str:
    """Generate a collapsed view of HTML showing only top-level structure."""
    view = _format_element_collapsed(soup, 0, max_depth)
    return _trim_content(view, MAX_VIEW_LENGTH)


def _format_element_collapsed(element: Any, current_depth: int, max_depth: int) -> str:
    """Format an element in collapsed view."""
    if isinstance(element, NavigableString):
        text = str(element).strip()
        if text:
            # Trim text to prevent overwhelming agent
            trimmed_text = text[:MAX_TEXT_LENGTH]
            if len(text) > MAX_TEXT_LENGTH:
                trimmed_text += "..."
            return f'{"  " * current_depth}📝 "{trimmed_text}"\n'
        return ""

    if not hasattr(element, "name") or element.name is None:
        return ""

    # Format tag opening with trimmed attributes
    attrs = []
    if hasattr(element, "attrs") and element.attrs:
        for key, value in element.attrs.items():
            if isinstance(value, list):
                value = " ".join(value)
            # Trim individual attribute values
            value_str = str(value)[:MAX_ATTR_VALUE_LENGTH]
            if len(str(value)) > MAX_ATTR_VALUE_LENGTH:
                value_str += "..."
            attrs.append(f'{key}="{value_str}"')

    # Trim total attributes length
    attrs_combined = " ".join(attrs)
    if len(attrs_combined) > MAX_ATTRS_TOTAL_LENGTH:
        attrs_combined = attrs_combined[:MAX_ATTRS_TOTAL_LENGTH] + "..."
    attrs_str = f" {attrs_combined}" if attrs_combined else ""

    indent = "  " * current_depth

    # Count children
    children = [
        child
        for child in element.children
        if hasattr(child, "name") or (isinstance(child, NavigableString) and str(child).strip())
    ]
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


# Create a global parser instance
_parser = _HtmlExplorationParser()


def execute_html_exploration(command: str, soup: BeautifulSoup) -> str | None:
    """Execute HTML exploration command and return formatted response."""

    # Clean up command string - sometimes models start with "command: "
    command = command.strip()

    if command.lower().startswith("command:"):
        command = command[len("command:") :].strip()

    # Parse the command using argparse
    args, error = _parser.parse_command(command)

    if error:
        # Handle parsing errors with helpful suggestions
        return (
            f"❌ Command parsing error: {error}\n\n"
            + "💡 Use 'help' to see available commands and syntax or 'finish' to finish the exploration."
        )

    # Execute based on parsed command
    if args.command in ["show", "view", "start"]:
        return _execute_show_command(soup, args.depth)

    if args.command == "expand":
        selector = " ".join(args.selector) if isinstance(args.selector, list) else args.selector
        return _execute_expand_command(soup, selector, args.depth)

    if args.command == "text":
        selector = " ".join(args.selector) if isinstance(args.selector, list) else args.selector
        return _execute_text_command(soup, selector)

    if args.command == "attrs":
        selector = " ".join(args.selector) if isinstance(args.selector, list) else args.selector
        return _execute_attrs_command(soup, selector)

    if args.command in ["finish", "done", "complete"]:
        return None

    if args.command in ["help", "?"]:
        return _execute_help_command(args.subcommand if hasattr(args, "subcommand") else None)

    return f"❓ Unknown command: {args.command!r}\nUse 'help' to see available commands."


def _execute_show_command(soup: BeautifulSoup, depth: int = 2) -> str:
    """Execute show/view/start command."""
    # Validate depth
    if depth < 1 or depth > 5:
        return "❌ Depth must be between 1 and 5"

    view = _generate_collapsed_html_view(soup, max_depth=depth)
    return (
        f"📄 HTML Structure ({depth} levels):\n\n{view}\n"
        + "💡 To explore deeper, try: 'expand body' or 'expand html' first"
    )


def _execute_expand_command(soup: BeautifulSoup, selector: str, depth: int = 3) -> str:
    """Execute expand command."""
    # Validate depth
    if depth < 1 or depth > 5:
        return "❌ Depth must be between 1 and 5"

    element = _find_element_by_css_selector(soup, selector)

    if element is None:
        suggestions = _get_navigation_suggestions(soup, selector)
        return (
            f"❌ Could not find element with selector: {selector}\n\n"
            + f"💡 Try these selectors instead:\n{suggestions}"
        )

    view = _format_element_collapsed(element, 0, max_depth=depth)
    trimmed_view = _trim_content(view, MAX_VIEW_LENGTH)
    return (
        f"📂 Expanded view of '{selector}' ({depth} levels):\n\n{trimmed_view}\n"
        + "💡 Use more specific selectors or try exploring children shown above"
    )


def _execute_text_command(soup: BeautifulSoup, selector: str) -> str:
    """Execute text command."""
    element = _find_element_by_css_selector(soup, selector)

    if element is None:
        suggestions = _get_navigation_suggestions(soup, selector)
        return (
            f"❌ Could not find element with selector: {selector}\n\n"
            + f"💡 Try these selectors instead:\n{suggestions}"
        )

    text_content = element.get_text(strip=True)
    trimmed_text = _trim_content(text_content, MAX_FULL_TEXT_LENGTH)

    if trimmed_text == "":
        return f"❌ Element '{selector}' has no text content"

    return f"📝 Text content of '{selector}':\n{trimmed_text}"


def _execute_attrs_command(soup: BeautifulSoup, selector: str) -> str:
    """Execute attrs command."""
    element = _find_element_by_css_selector(soup, selector)

    if element is None:
        suggestions = _get_navigation_suggestions(soup, selector)
        return (
            f"❌ Could not find element with selector: {selector}\n\n"
            + f"💡 Try these selectors instead:\n{suggestions}"
        )

    if hasattr(element, "attrs") and element.attrs:
        # Trim individual attribute values for display
        attrs_list = []
        for k, v in element.attrs.items():
            value_str = str(v)
            trimmed_value = _trim_content(value_str, MAX_ATTR_VALUE_LENGTH)
            attrs_list.append(f"  {k}: {trimmed_value}")

        attrs_str = "\n".join(attrs_list)
        # Trim overall attributes display
        trimmed_attrs = _trim_content(attrs_str, MAX_VIEW_LENGTH)
        return f"🏷️ Attributes of '{selector}':\n{trimmed_attrs}"
    return f"🏷️ Element '{selector}' has no attributes"


def _execute_help_command(subcommand: str | None = None) -> str:
    """Execute help command."""
    if subcommand:
        # Show help for specific subcommand
        help_text = {
            "show": """📄 Show Command:
Usage: show [--depth N]

Shows collapsed HTML structure.

Options:
  --depth N    Maximum depth to show (1-5, default: 2)

Examples:
  show
  show --depth 3
  view --depth 1""",
            "expand": """📂 Expand Command:  
Usage: expand <selector> [--depth N]

Expands specific element using CSS selector.

Arguments:
  selector     CSS selector for element (can contain spaces for descendant selectors)
  
Options:
  --depth N    Maximum depth to show (1-5, default: 3)

Examples:
  expand body
  expand "#main-content"
  expand .navbar --depth 2
  expand .MuiSnackbar-root .MuiAlert-message
  expand "div.container p.text" --depth 1""",
            "text": """📝 Text Command:
Usage: text <selector>

Shows text content of element.

Arguments:
  selector     CSS selector for element (can contain spaces for descendant selectors)

Examples:
  text body
  text h1
  text "#title"
  text .MuiSnackbar-root .MuiAlert-message
  text "div.container p.error" """,
            "attrs": """🏷️  Attrs Command:
Usage: attrs <selector>

Shows attributes of element.

Arguments:
  selector     CSS selector for element (can contain spaces for descendant selectors)

Examples:
  attrs body
  attrs input[type='text']
  attrs "#myform"
  attrs .container .form-group input
  attrs "div.widget button.submit" """,
        }

        if subcommand in help_text:
            return help_text[subcommand]

        return f"❌ No help available for '{subcommand}'\nUse 'help' to see all commands."

    # General help
    return """🔍 HTML Exploration Commands:

🔧 AVAILABLE COMMANDS:
• show [--depth N] - Show collapsed HTML structure  
• expand <selector> [--depth N] - Expand specific element
• text <selector> - Show text content of element
• attrs <selector> - Show attributes of element  
• finish - Complete exploration and generate report
• help [command] - Show help (optionally for specific command)

🎯 NAVIGATION STRATEGY:
1. Start with 'show' to see overall structure
2. Use 'expand body' to see body contents  
3. Then expand specific elements: 'expand "#id"' or 'expand ".class"'
4. Navigate step by step, don't guess deep paths

📝 CSS SELECTOR EXAMPLES:
• body - The body element
• #myid - Element with id="myid" 
• .myclass - Element with class="myclass"
• div - First div element
• form input - Input inside form
• .MuiSnackbar-root .MuiAlert-message - Nested Material-UI elements
• div.container p.error - Paragraph with class 'error' inside div with class 'container'

💡 MULTI-WORD SELECTORS: Descendant selectors with spaces work automatically!
💡 QUOTES OPTIONAL: Only needed for selectors with special shell characters."""


def _get_navigation_suggestions(soup: BeautifulSoup, failed_selector: str) -> str:
    """Get helpful navigation suggestions when a selector fails."""
    suggestions = []

    # Try to find common starting points
    body = soup.find("body")
    if body:
        # Get direct children of body with their attributes
        children = [child for child in body.children if hasattr(child, "name") and child.name]
        if children:
            suggestions.append("• expand body (to see body contents)")
            for child in children[:3]:  # Show first 3 children
                if hasattr(child, "attrs") and child.attrs:
                    if "id" in child.attrs:
                        suggestions.append(f"• expand #{child.attrs['id']} (by ID)")
                    if "class" in child.attrs:
                        classes = child.attrs["class"]
                        if isinstance(classes, list):
                            classes = classes[0]  # Take first class
                        suggestions.append(f"• expand .{classes} (by class)")
                # Always suggest the element name
                suggestions.append(f"• expand {child.name} (first {child.name} element)")

    # Look for common elements
    common_elements = ["form", "input", "button", "div", "span", "a"]
    for elem_name in common_elements:
        element = soup.find(elem_name)
        if element:
            suggestions.append(f"• expand {elem_name} (first {elem_name} found)")
            break

    # Look for elements with IDs
    elements_with_ids = soup.find_all(attrs={"id": True})
    suggestions.extend(
        [
            f"• expand #{elem.attrs['id']} (by ID)"
            for elem in elements_with_ids[:2]  # First 2 elements with IDs
            if hasattr(elem, "attrs") and "id" in elem.attrs
        ]
    )

    suggestions_list = suggestions[:6] if suggestions else ["• Try 'expand body' or 'show' to see structure"]
    suggestions_text = "\n".join(suggestions_list)
    return _trim_content(suggestions_text, MAX_SUGGESTIONS_LENGTH)
