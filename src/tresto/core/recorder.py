"""Browser recording functionality for Tresto."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from rich.console import Console

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page

    from .config.main import TrestoConfig


console = Console()


class BrowserRecorder:
    """Records browser interactions for test generation."""

    def __init__(self, config: TrestoConfig, headless: bool = False) -> None:
        """Initialize the browser recorder."""
        self.config = config
        self.headless = headless
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.actions: list[dict[str, Any]] = []

    async def start_recording(self, url: str) -> dict[str, Any]:
        """Start recording browser interactions."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            console.print("[red]Error: Playwright not installed. Install with: pip install playwright[/red]")
            return {}

        async with async_playwright() as p:
            # Launch browser
            self.browser = await p.chromium.launch(
                headless=self.headless, args=["--disable-blink-features=AutomationControlled"]
            )

            # Create context
            self.context = await self.browser.new_context(
                viewport={
                    "width": self.config.browser.viewport["width"],
                    "height": self.config.browser.viewport["height"],
                },
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )

            # Create page
            self.page = await self.context.new_page()

            # Set up event listeners
            await self._setup_event_listeners()

            # Navigate to URL
            console.print(f"🌐 Navigating to: {url}")
            await self.page.goto(url)

            console.print("\n[bold green]Recording started![/bold green]")
            console.print("Perform your test actions in the browser...")
            console.print("Press [bold]Ctrl+C[/bold] in the terminal when done.\n")

            try:
                # Keep the browser open and wait for user to finish
                await self._wait_for_user_completion()
            except KeyboardInterrupt:
                console.print("\n[yellow]Recording stopped by user[/yellow]")

            return {
                "url": url,
                "actions": self.actions,
                "final_url": self.page.url if self.page else url,
                "page_title": await self.page.title() if self.page else "",
                "viewport": self.config.browser.viewport,
            }

    async def _setup_event_listeners(self) -> None:
        """Set up event listeners to capture user interactions."""
        if not self.page:
            return

        # Track navigation
        self.page.on("framenavigated", self._on_navigation)

        # Track clicks
        await self.page.add_init_script("""
            document.addEventListener('click', (event) => {
                const element = event.target;
                const rect = element.getBoundingClientRect();
                
                // Get various selector options
                const selectors = {
                    id: element.id,
                    className: element.className,
                    tagName: element.tagName.toLowerCase(),
                    textContent: element.textContent?.trim().substring(0, 50),
                    dataTestId: element.getAttribute('data-testid'),
                    ariaLabel: element.getAttribute('aria-label'),
                    xpath: getXPath(element)
                };
                
                window.trestoActions = window.trestoActions || [];
                window.trestoActions.push({
                    type: 'click',
                    timestamp: Date.now(),
                    selectors: selectors,
                    coordinates: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }
                });
            });
            
            // Track input changes
            document.addEventListener('input', (event) => {
                const element = event.target;
                if (element.tagName.toLowerCase() === 'input' || element.tagName.toLowerCase() === 'textarea') {
                    const selectors = {
                        id: element.id,
                        name: element.name,
                        type: element.type,
                        placeholder: element.placeholder,
                        dataTestId: element.getAttribute('data-testid'),
                        xpath: getXPath(element)
                    };
                    
                    window.trestoActions = window.trestoActions || [];
                    window.trestoActions.push({
                        type: 'input',
                        timestamp: Date.now(),
                        selectors: selectors,
                        value: element.value
                    });
                }
            });
            
            // Helper function to get XPath
            function getXPath(element) {
                if (element.id) return `//*[@id="${element.id}"]`;
                if (element.tagName === 'BODY') return '/html/body';
                
                let selector = element.tagName.toLowerCase();
                if (element.className) {
                    selector += '[@class="' + element.className + '"]';
                }
                
                let parent = element.parentElement;
                if (parent) {
                    return getXPath(parent) + '/' + selector;
                }
                return '/' + selector;
            }
        """)

    async def _on_navigation(self, frame: Any) -> None:
        """Handle page navigation events."""
        if self.page and frame == self.page.main_frame:
            self.actions.append(
                {
                    "type": "navigation",
                    "timestamp": asyncio.get_event_loop().time(),
                    "url": frame.url,
                    "title": await frame.title(),
                }
            )

    async def _wait_for_user_completion(self) -> None:
        """Wait for user to complete their actions."""
        while True:
            await asyncio.sleep(1)

            # Get recorded actions from browser
            if self.page:
                try:
                    browser_actions = await self.page.evaluate("() => window.trestoActions || []")
                    if browser_actions:
                        # Merge new actions
                        existing_count = len(self.actions)
                        new_actions = browser_actions[existing_count:]
                        self.actions.extend(new_actions)

                        # Clear processed actions
                        await self.page.evaluate("() => { window.trestoActions = []; }")
                except (OSError, RuntimeError, TimeoutError):
                    # Page might be navigating or closed
                    pass
