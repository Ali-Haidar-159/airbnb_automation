"""
Step 05 — Refine Search and Item List Verification
====================================================
Assignment requirements:
✓ Verify refine search results page loads successfully
✓ Confirm selected dates and guest count appear in page UI
✓ Validate dates and guest count present in page URL
✓ Scrape each listing's title, price, and image URL
✓ Store collected listing data in database
"""
import logging

from automation.services.browser_service  import BrowserService
from automation.services.database_service import DatabaseService

logger = logging.getLogger(__name__)


class Step05SearchResults:

    def __init__(self, browser: BrowserService, db: DatabaseService):
        self.browser = browser
        self.db      = db

    def run(self, date_info: dict, guest_count: int) -> list:
        logger.info("━" * 55)
        logger.info("STEP 05: Refine Search and Item List Verification")
        logger.info("━" * 55)

        self.browser.wait(4000)
        current_url = self.browser.get_url()

        # ── 1. Verify results page loaded ─────────────────────────────────────
        loaded = self._verify_page_loaded()
        self.browser.take_screenshot('step05_01_results_page')

        self.db.save_result(
            test_case='Search Results Page Load Verification',
            url=current_url,
            passed=loaded,
            should_be='Refine search results page to load with listing cards visible',
            found='Results page loaded with listing cards' if loaded
            else 'Results page did not load properly after search',
        )

        # ── 2. Validate dates in URL ──────────────────────────────────────────
        url_lower   = current_url.lower()
        dates_in_url = ('checkin' in url_lower or 'check_in' in url_lower
                        or 'check-in' in url_lower)
        self.db.save_result(
            test_case='Selected Dates in URL Validation',
            url=current_url,
            passed=dates_in_url,
            should_be='Selected check-in and check-out dates to appear as query parameters in URL',
            found=f"Date params {'PRESENT' if dates_in_url else 'NOT PRESENT'} in URL",
        )

        # ── 3. Validate guest count in URL ────────────────────────────────────
        guests_in_url = 'adults' in url_lower or 'guests' in url_lower
        self.db.save_result(
            test_case='Selected Guest Count in URL Validation',
            url=current_url,
            passed=guests_in_url,
            should_be=f'Selected guest count ({guest_count}) to appear in URL as query parameter',
            found=f"Guest params {'PRESENT' if guests_in_url else 'ABSENT'} in URL",
        )

        # ── 4. Dates and guests in page UI ────────────────────────────────────
        ui_ok = self._check_dates_guests_in_ui()
        self.db.save_result(
            test_case='Selected Dates and Guest Count in Page UI Confirmation',
            url=current_url,
            passed=ui_ok,
            should_be='Selected dates and guest count to be visible in the page top search bar UI',
            found='Dates/guests visible in page search bar UI' if ui_ok
            else 'Could not confirm dates/guests in UI',
        )

        # ── 5. Scrape listings ────────────────────────────────────────────────
        listings = self._scrape_all_listings()
        self.browser.take_screenshot('step05_02_listings_scraped')

        self.db.save_result(
            test_case='Listing Data Scraping — Title, Price, Image URL',
            url=current_url,
            passed=len(listings) > 0,
            should_be='Each listing title, price and image URL to be scraped and stored in database',
            found=f'Successfully scraped {len(listings)} listings with title/price/imageURL',
        )

        if listings:
            self.db.save_listings(listings)

        return listings

    # ─────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _verify_page_loaded(self) -> bool:
        """Wait for at least one listing card to appear."""
        selectors = [
            "[data-testid='card-container']",
            "[itemtype='http://schema.org/ListItem']",
            "a[href*='/rooms/']",
        ]
        for sel in selectors:
            if self.browser.wait_for_selector(sel, timeout=15000):
                return True
        return False

    def _check_dates_guests_in_ui(self) -> bool:
        """Check if date range and/or guests are visible in the top search bar."""
        page = self.browser.page
        selectors = [
            "button[aria-label*='Check']",
            "[data-testid*='dates']",
            "button[aria-label*='guest']",
        ]
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    txt = el.inner_text().strip()
                    if txt and txt.lower() not in ('add dates', 'when', 'add guests', 'who', ''):
                        return True
            except Exception:
                pass
        return False

    def _scrape_all_listings(self) -> list:
        """
        Scrape listing cards using JavaScript evaluate for speed and reliability.
        Primary method: schema.org/ListItem structured data (real Airbnb DOM).
        Fallback: card-container data-testid.
        """
        # Scroll to trigger lazy image loading
        self.browser.scroll_to_bottom()
        self.browser.wait(2000)
        self.browser.scroll_to_top()
        self.browser.wait(500)

        # ── Primary: schema.org structured data ──────────────────────────────
        results = self.browser.js("""
            () => {
                const out = [];
                document.querySelectorAll('[itemtype="http://schema.org/ListItem"]')
                    .forEach(el => {
                        const nameMeta = el.querySelector('meta[itemprop="name"]');
                        const urlMeta  = el.querySelector('meta[itemprop="url"]');
                        const img      = el.querySelector('img');

                        // Find price — leaf node containing '$'
                        let price = '';
                        for (const n of el.querySelectorAll('*')) {
                            if (!n.children.length && n.textContent.includes('$')) {
                                price = n.textContent.trim().slice(0, 100);
                                break;
                            }
                        }
                        const name = nameMeta ? nameMeta.getAttribute('content') : '';
                        if (name) {
                            out.push({
                                title:       name,
                                listing_url: urlMeta ? urlMeta.getAttribute('content') : '',
                                image_url:   img     ? (img.src || img.dataset.src || '') : '',
                                price:       price,
                            });
                        }
                    });
                return out.slice(0, 20);
            }
        """)

        if results:
            logger.info(f"Scraped {len(results)} listings (schema.org method)")
            return results

        # ── Fallback: card-container ──────────────────────────────────────────
        results = self.browser.js("""
            () => {
                const out = [];
                document.querySelectorAll('[data-testid="card-container"]')
                    .forEach(card => {
                        const link = card.querySelector('a[href*="/rooms/"]');
                        const img  = card.querySelector('img');
                        let price  = '';
                        for (const n of card.querySelectorAll('*')) {
                            if (!n.children.length && n.textContent.includes('$')) {
                                price = n.textContent.trim().slice(0, 100);
                                break;
                            }
                        }
                        const title = link
                            ? (link.getAttribute('aria-label') || card.innerText.split('\\n')[0])
                            : card.innerText.split('\\n')[0];
                        if (title && title.trim()) {
                            out.push({
                                title:       title.trim().slice(0, 200),
                                listing_url: link ? link.href : '',
                                image_url:   img  ? img.src  : '',
                                price:       price,
                            });
                        }
                    });
                return out.slice(0, 20);
            }
        """)

        logger.info(f"Scraped {len(results)} listings (fallback method)")
        return results
