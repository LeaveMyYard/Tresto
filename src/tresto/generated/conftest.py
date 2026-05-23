"""Pytest configuration and fixtures for Tresto tests."""

from collections.abc import AsyncIterable

import pytest
from playwright.async_api import Browser, BrowserContext, Page, ViewportSize, async_playwright

import tresto


@pytest.fixture
async def browser() -> AsyncIterable[Browser]:
    """Create a browser instance for the test session."""
    browser_config = tresto.config.browser
    headless = bool(browser_config.headless) if browser_config is not None else True
    timeout = browser_config.timeout if browser_config is not None else 30000

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, timeout=timeout)

        try:
            yield browser
        finally:
            await browser.close()


@pytest.fixture
async def context(browser: Browser) -> AsyncIterable[BrowserContext]:
    """Create a new browser context for each test."""
    browser_config = tresto.config.browser
    viewport = None
    timeout = 30000
    if browser_config is not None:
        timeout = browser_config.timeout or timeout
        viewport = ViewportSize(width=browser_config.viewport.width, height=browser_config.viewport.height)

    try:
        context = await browser.new_context(viewport=viewport)
        context.set_default_timeout(timeout)
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
