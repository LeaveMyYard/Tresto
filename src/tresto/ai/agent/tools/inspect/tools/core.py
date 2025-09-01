"""Execution utilities for playwright and BeautifulSoup code."""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, NavigableString

# Content size limits to prevent overwhelming the agent
MAX_TEXT_LENGTH = 200  # For individual text nodes
MAX_FULL_TEXT_LENGTH = 300  # For complete text content extraction
MAX_ATTR_VALUE_LENGTH = 100  # For individual attribute values
MAX_ATTRS_TOTAL_LENGTH = 200  # For combined attributes string
MAX_VIEW_LENGTH = 2000  # For complete HTML views
MAX_SUGGESTIONS_LENGTH = 500  # For navigation suggestions


def trim_content(content: str, max_length: int) -> str:
    """Trim content to specified length with ellipsis if needed."""
    if len(content) <= max_length:
        return content
    return content[:max_length] + "..."


def find_element_by_css_selector(soup: BeautifulSoup, selector: str) -> Any | None:
    """Find an element by CSS selector."""
    try:
        # Use BeautifulSoup's built-in CSS selector support
        return soup.select_one(selector)
    except Exception:  # noqa: BLE001
        return None


def generate_collapsed_html_view(soup: BeautifulSoup, max_depth: int = 2) -> str:
    """Generate a collapsed view of HTML showing only top-level structure."""
    view = format_element_collapsed(soup, 0, max_depth)
    return trim_content(view, MAX_VIEW_LENGTH)


def format_element_collapsed(element: Any, current_depth: int, max_depth: int) -> str:
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
        result += format_element_collapsed(child, current_depth + 1, max_depth)

    return result


def get_navigation_suggestions(soup: BeautifulSoup, failed_selector: str) -> str:
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
    return trim_content(suggestions_text, MAX_SUGGESTIONS_LENGTH)
