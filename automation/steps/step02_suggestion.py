"""
Step 02 — Search Auto-suggestion Verification
=============================================
Assignment requirements:
✓ Verify auto-suggestion list appears after typing
✓ Ensure suggestions are relevant to the location
✓ Confirm each suggestion shows Google Map icon + location text
✓ Capture and store all suggestion items in DB
✓ Randomly select one suggestion and click it
"""
import random
import logging

from automation.services.browser_service  import BrowserService
from automation.services.database_service import DatabaseService

logger = logging.getLogger(__name__)


class Step02AutoSuggestion:

    def __init__(self, browser: BrowserService, db: DatabaseService):
        self.browser = browser
        self.db      = db

    def run(self, search_query: str) -> bool:
        logger.info("━" * 55)
        logger.info("STEP 02: Search Auto-suggestion Verification")
        logger.info("━" * 55)

        current_url = self.browser.get_url()

        # ── 1. Wait for the suggestion dropdown ───────────────────────────────
        appeared = self._wait_for_dropdown()

        self.db.save_result(
            test_case='Auto-suggestion List Visibility',
            url=current_url,
            passed=appeared,
            should_be='Auto-suggestion dropdown to appear after typing location name into search field',
            found='Suggestion dropdown appeared with location options' if appeared
            else 'Suggestion dropdown did NOT appear after typing',
        )

        if not appeared:
            logger.warning("Dropdown not visible — skipping rest of Step 02")
            return False

        # ── 2. Collect all suggestion texts ──────────────────────────────────
        texts = self._collect_suggestion_texts()
        logger.info(f"Collected {len(texts)} suggestions: {texts[:3]}")

        # ── 3. Relevance check ────────────────────────────────────────────────
        words    = search_query.lower().split()
        relevant = any(
            any(word in s.lower() for word in words)
            for s in texts
        )
        self.db.save_result(
            test_case='Auto-suggestion Relevance Check',
            url=current_url,
            passed=relevant,
            should_be=f"Suggestions to be relevant to the entered search term '{search_query}'",
            found=f"{len(texts)} suggestions: {', '.join(texts[:4])}",
        )

        # ── 4. Google Map icon check ──────────────────────────────────────────
        has_icons = self._check_map_icons()
        # Format suggestion list like the assignment PDF screenshot shows
        numbered  = ', '.join(f"{i+1}. {t}" for i, t in enumerate(texts[:8]))
        self.db.save_result(
            test_case='Google Auto Suggestion List Availability Test',
            url=current_url,
            passed=has_icons,
            should_be=(
                f"suggested items: i. {search_query}, ii. {search_query} suggestions "
                f"with Google Map icon and location text"
            ),
            found=f"suggested items: {numbered}",
        )

        # ── 5. Store all suggestions in DB ────────────────────────────────────
        self.db.save_suggestions(texts, search_query)

        # ── 6. Click a random suggestion ──────────────────────────────────────
        clicked = self._click_random_suggestion()
        self.browser.wait(3000)

        self.db.save_result(
            test_case='Auto-suggestion Random Selection and Click',
            url=self.browser.get_url(),
            passed=clicked,
            should_be='Randomly selected suggestion item to be clicked and search flow to continue',
            found='Suggestion clicked — proceeding to date picker' if clicked
            else 'Failed to click any suggestion item',
        )

        return clicked

    # ─────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _wait_for_dropdown(self) -> bool:
        """Wait for the suggestion listbox/options to appear."""
        for sel in [
            "[role='listbox']",
            "[role='option']",
            "[data-testid='autocomplete-menu']",
        ]:
            if self.browser.wait_for_selector(sel, timeout=8000):
                return True
        return False

    def _collect_suggestion_texts(self) -> list:
        """Extract text from each suggestion option element."""
        page = self.browser.page
        for sel in (
            "[role='option']",
            "[role='listbox'] [role='option']",
            "[data-testid='autocomplete-menu'] li",
        ):
            try:
                items = page.locator(sel).all()
                texts = []
                for item in items:
                    try:
                        t = item.inner_text().strip().replace('\n', ' ')
                        if t:
                            texts.append(t[:200])
                    except Exception:
                        pass
                if texts:
                    return texts
            except Exception:
                pass
        return []

    def _check_map_icons(self) -> bool:
        """Check if suggestion items contain SVG map pin icons."""
        page = self.browser.page
        for sel in (
            "[role='option'] svg",
            "[role='option'] img",
            "[role='listbox'] svg",
        ):
            try:
                if page.locator(sel).count() > 0:
                    return True
            except Exception:
                pass
        return False

    def _click_random_suggestion(self) -> bool:
        """Click a randomly chosen item from the suggestion list."""
        page = self.browser.page
        try:
            options = page.locator("[role='option']").all()
            if not options:
                return False
            random.choice(options).click()
            return True
        except Exception:
            # Fallback — click the first option
            try:
                page.locator("[role='option']").first.click()
                return True
            except Exception as e:
                logger.warning(f"Suggestion click error: {e}")
                return False
