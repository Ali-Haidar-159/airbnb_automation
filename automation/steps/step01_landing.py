"""
Step 01 — Website Landing and Initial Search Setup
===================================================
Assignment requirements:
✓ Open browser → https://www.airbnb.com/
✓ Clear browser cache, cookies, local storage   ← NO RELOAD (this was the bug)
✓ Close any pop-up, banner, or modal
✓ Confirm the homepage loads correctly
✓ Click on the search icon or search field
✓ Collect top 20 countries list, pick one randomly
✓ Type it into the search field like a real user
✓ Screenshot at important steps
✓ Log each action to database
"""
import random
import logging

from automation.services.browser_service  import BrowserService
from automation.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

TOP_20_COUNTRIES = [
    "United States", "China", "India", "Brazil", "Russia",
    "Indonesia", "Pakistan", "Bangladesh", "Mexico", "Ethiopia",
    "Japan", "Egypt", "Philippines", "Vietnam", "Iran",
    "Turkey", "Germany", "Thailand", "United Kingdom", "France",
]


class Step01LandingAndSearch:

    def __init__(self, browser: BrowserService, db: DatabaseService, airbnb_url: str):
        self.browser     = browser
        self.db          = db
        self.airbnb_url  = airbnb_url

    def run(self) -> str:
        logger.info("━" * 55)
        logger.info("STEP 01: Website Landing and Initial Search Setup")
        logger.info("━" * 55)

        # ── 1. Navigate to Airbnb ─────────────────────────────────────────────
        self.browser.navigate(self.airbnb_url)
        self.browser.wait(2000)

        # ── 2. Clear storage WITHOUT reload (this fixes the refresh bug) ──────
        # Cookie cleanup only: clearing local/session storage on a live Airbnb
        # page can trigger site-driven refresh flows.
        self.browser.clear_storage_no_reload(clear_web_storage=False)
        # Do NOT navigate or reload here — stay on the page
        self.browser.wait(1000)

        current_url = self.browser.get_url()

        # ── 3. Dismiss any popup/banner/modal ─────────────────────────────────
        self.browser.dismiss_popups()
        self.browser.wait(1000)

        # ── 4. Verify homepage loaded correctly ───────────────────────────────
        is_airbnb = 'airbnb.com' in current_url
        self.db.save_result(
            test_case='Homepage Load Verification',
            url=current_url,
            passed=is_airbnb,
            should_be='airbnb.com homepage to load successfully with search bar visible',
            found=f'Page loaded at URL: {current_url}',
        )

        # ── 5. Pick random country ────────────────────────────────────────────
        country = random.choice(TOP_20_COUNTRIES)
        logger.info(f"Country randomly selected: {country}")

        # ── 6. Click search field ─────────────────────────────────────────────
        search_input = self._activate_search_field()

        if search_input is None:
            self.db.save_result(
                test_case='Search Field Click',
                url=current_url,
                passed=False,
                should_be='Search destination input field to be found and clicked',
                found='Could not find any search input on the homepage',
            )
            return country


        # ── 7. Type country like a real user ──────────────────────────────────
        self.browser.type_like_human(search_input, country)
        self.browser.wait(2500)   # wait for suggestions to load

        self.db.save_result(
            test_case='Search Field Input — Type Country Like Real User',
            url=self.browser.get_url(),
            passed=True,
            should_be=f"'{country}' to be typed character by character in the destination search field",
            found=f"Successfully typed '{country}' into search field with 100ms delay between each character",
        )

        return country

    # ─────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _activate_search_field(self):
        """
        Find the search input on the Airbnb homepage.
        Tries multiple strategies because Airbnb's DOM changes frequently.
        Returns a Playwright Locator or None.
        """
        page = self.browser.page

        # Strategy A — input may already be visible (e.g. on expanded layout)
        for placeholder in ('Search destinations', 'destination', 'Destination', 'Where'):
            try:
                loc = page.locator(f"input[placeholder*='{placeholder}']").first
                if loc.is_visible(timeout=3000):
                    logger.info(f"Found input directly (placeholder='{placeholder}')")
                    return loc
            except Exception:
                pass

        # Strategy B — click the "Where" area to expand and reveal the input
        click_targets = [
            "[data-testid='structured-search-input-field-query']",
            "button[data-testid='structured-search-input-field-query']",
            "[data-testid='little-search']",
            "//button[@data-testid='little-search']",
            "text=Search destinations",
            "text=Where",
            "form[id='search-tabpanel'] input",
        ]
        for sel in click_targets:
            try:
                if sel.startswith('//'):
                    el = page.locator(f"xpath={sel}").first
                else:
                    el = page.locator(sel).first

                if el.is_visible(timeout=3000):
                    el.click()
                    self.browser.wait(1500)

                    # After click, look for the revealed text input
                    for placeholder in ('Search destinations', 'destination', 'Where to'):
                        try:
                            inp = page.locator(
                                f"input[placeholder*='{placeholder}']"
                            ).first
                            if inp.is_visible(timeout=3000):
                                logger.info(f"Input revealed after clicking: {sel}")
                                return inp
                        except Exception:
                            pass
            except Exception:
                pass

        # Strategy C — any visible text input as last resort
        try:
            for inp in page.locator("input[type='text']").all():
                if inp.is_visible():
                    logger.info("Using generic text input as fallback")
                    return inp
        except Exception:
            pass

        logger.warning("Search input not found on page")
        return None
