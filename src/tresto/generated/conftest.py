"""Pytest configuration and fixtures for Tresto tests."""

import pytest
from playwright.async_api import Browser, BrowserContext, async_playwright


@pytest.fixture(scope="session")
async def browser():
    """Create a browser instance for the test session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        yield browser
        await browser.close()


@pytest.fixture
async def context(browser: Browser):
    """Create a new browser context for each test."""
    context = await browser.new_context()
    yield context
    await context.close()


@pytest.fixture
async def page(context: BrowserContext):
    """Create a new page for each test."""
    page = await context.new_page()
    yield page
    await page.close()
