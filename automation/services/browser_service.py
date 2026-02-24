"""
BrowserService
==============
Playwright browser wrapper.

ROOT CAUSE OF "REFRESH LOOP" BUG:
  Previous versions called page.reload() or page.goto() after clearing
  localStorage/cookies, which caused the page to navigate away and lose
  the user session — making it look like an infinite refresh.

THE FIX:
  1. Navigate to Airbnb with goto()
  2. Wait for page to load fully
  3. Clear storage ONLY with JavaScript (no navigation/reload at all)
  4. Continue with interactions on the same loaded page

This means the browser stays on the Airbnb homepage without any refresh.
"""
import logging

from playwright.sync_api import sync_playwright, Page, BrowserContext

logger = logging.getLogger(__name__)


class BrowserService:
    """
    Manages the Playwright browser lifecycle.
    Use as a context manager: `with BrowserService() as browser:`
    """

    def __init__(self, headless: bool = False, mobile: bool = False):
        self.headless       = headless
        self.mobile         = mobile

        self._pw:      object        = None
        self._browser: object        = None
        self._context: BrowserContext = None
        self.page:     Page           = None

        # Live log buffers — populated automatically by event listeners
        self.console_logs: list = []
        self.network_logs: list = []

    # ─────────────────────────────────────────────────────────────────────────
    # Context manager
    # ─────────────────────────────────────────────────────────────────────────

    def __enter__(self) -> 'BrowserService':
        self._pw = sync_playwright().start()

        self._browser = self._pw.chromium.launch(
            headless=self.headless,
            slow_mo=80,          # gives page JS time to settle between actions
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--lang=en-US',
                '--disable-extensions',
            ],
        )

        if self.mobile:
            # Bonus: iPhone 14 Pro emulation
            device        = self._pw.devices['iPhone 14 Pro']
            self._context = self._browser.new_context(**device, locale='en-US')
        else:
            self._context = self._browser.new_context(
                viewport={'width': 1440, 'height': 900},
                locale='en-US',
                user_agent=(
                    'Mozilla/5.0 (X11; Linux x86_64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/122.0.0.0 Safari/537.36'
                ),
            )

        # Hide the webdriver fingerprint
        self._context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        self.page = self._context.new_page()
        self.page.set_default_timeout(25_000)
        self.page.set_default_navigation_timeout(30_000)

        # Attach listeners — these fire automatically throughout the session
        self.page.on('console',  self._capture_console)
        self.page.on('response', self._capture_network)

        logger.info(f"Browser launched  headless={self.headless}  mobile={self.mobile}")
        return self

    def __exit__(self, *_):
        try:
            if self._context: self._context.close()
            if self._browser: self._browser.close()
            if self._pw:      self._pw.stop()
            logger.info("Browser closed cleanly")
        except Exception as e:
            logger.warning(f"Browser close warning: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Log capture listeners (attached in __enter__)
    # ─────────────────────────────────────────────────────────────────────────

    def _capture_console(self, msg):
        level_map = {
            'log': 'INFO', 'info': 'INFO',
            'warning': 'WARNING', 'error': 'ERROR', 'debug': 'DEBUG',
        }
        self.console_logs.append({
            'level':   level_map.get(msg.type, 'INFO'),
            'message': msg.text[:2000],
            'source':  '',
        })

    def _capture_network(self, response):
        url = response.url
        if url.startswith('data:') or url.startswith('blob:'):
            return
        method = response.request.method.upper()
        if method not in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'):
            method = 'GET'
        self.network_logs.append({
            'url':           url[:2048],
            'method':        method,
            'status_code':   response.status,
            'resource_type': response.request.resource_type,
        })

    # ─────────────────────────────────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────────────────────────────────

    def navigate(self, url: str):
        """Navigate to a URL and wait for DOM to be ready."""
        current = (self.page.url or "").rstrip("/")
        target = (url or "").rstrip("/")
        if current and current == target:
            logger.info(f"Skipped navigation to same URL: {url}")
            return
        self.page.goto(url, wait_until='domcontentloaded', timeout=30_000)
        self.page.wait_for_timeout(2000)          # extra settle time
        logger.info(f"Navigated to: {url}")

    def get_url(self) -> str:
        return self.page.url

    # ─────────────────────────────────────────────────────────────────────────
    # Storage clear  ← THE CRITICAL FIX
    # ─────────────────────────────────────────────────────────────────────────

    def clear_storage_no_reload(self, clear_web_storage: bool = False):
        """
        Clear cookies WITHOUT any page reload.
        Optionally clear local/session storage.
        This is the fix for the "refresh loop" bug.
        After this call the browser stays exactly where it is.
        """
        try:
            self._context.clear_cookies()
        except Exception:
            pass
        if clear_web_storage:
            try:
                self.page.evaluate("""
                    () => {
                        try { window.localStorage.clear(); } catch(e) {}
                        try { window.sessionStorage.clear(); } catch(e) {}
                    }
                """)
            except Exception:
                pass
        logger.info(
            "Storage cleared (no reload): cookies=%s web_storage=%s",
            True,
            clear_web_storage,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Popup dismissal
    # ─────────────────────────────────────────────────────────────────────────

    def dismiss_popups(self):
        """Try common popup/banner/modal close patterns."""
        candidates = [
            "button[aria-label='Close']",
            "button[aria-label='close']",
            "button:has-text('Accept all')",
            "button:has-text('Accept')",
            "button:has-text('Got it')",
            "button:has-text('Dismiss')",
            "button:has-text('Not now')",
            "button:has-text('Skip')",
            "button:has-text('No thanks')",
            "button:has-text('Close')",
            "[data-testid='modal-container'] button:first-child",
            "[data-testid='closeButton']",
        ]
        for sel in candidates:
            try:
                el = self.page.locator(sel).first
                if el.is_visible(timeout=1500):
                    el.click(timeout=1500)
                    self.page.wait_for_timeout(500)
                    logger.info(f"Popup dismissed: {sel}")
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────────────
    # Human-like typing
    # ─────────────────────────────────────────────────────────────────────────

    def type_like_human(self, locator, text: str):
        """
        Click the element, wait a moment, then type with 100ms delay per char.
        Simulates a real user typing.
        """
        locator.click()
        self.page.wait_for_timeout(600)
        locator.type(text, delay=100)   # Playwright's built-in per-char delay

    # ─────────────────────────────────────────────────────────────────────────
    # Screenshots disabled
    # ─────────────────────────────────────────────────────────────────────────

    def take_screenshot(self, name: str) -> str:
        """Screenshots are disabled by project configuration."""
        return ''

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def wait(self, ms: int):
        """Wait for a number of milliseconds."""
        self.page.wait_for_timeout(ms)

    def wait_for_selector(self, selector: str, timeout: int = 10_000) -> bool:
        """
        Wait for a selector to become visible.
        Returns True on success, False on timeout (no exception raised).
        """
        try:
            self.page.wait_for_selector(selector, state='visible', timeout=timeout)
            return True
        except Exception:
            return False

    def scroll_to_bottom(self):
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        self.page.wait_for_timeout(1500)

    def scroll_to_top(self):
        self.page.evaluate("window.scrollTo(0, 0)")
        self.page.wait_for_timeout(500)

    def js(self, script: str):
        """Run arbitrary JavaScript and return the result."""
        return self.page.evaluate(script)
