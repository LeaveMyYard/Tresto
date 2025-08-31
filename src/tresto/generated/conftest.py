"""Pytest configuration and fixtures for Tresto tests."""

from collections.abc import AsyncIterable

import pytest
from playwright.async_api import Browser, BrowserContext, Page, async_playwright


@pytest.fixture
async def browser() -> AsyncIterable[Browser]:
    """Create a browser instance for the test session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        try:
            yield browser
        finally:
            await browser.close()


@pytest.fixture
async def context(browser: Browser) -> AsyncIterable[BrowserContext]:
    """Create a new browser context for each test."""
    try:
        context = await browser.new_context()
        yield context
    finally:
        await context.close()


@pytest.fixture
async def page(context: BrowserContext) -> AsyncIterable[Page]:
    """Create a new page for each test."""
    page = await context.new_page()
    try:
        yield page
    finally:
        await page.close()
