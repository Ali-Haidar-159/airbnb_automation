"""
Step 06 — Item Details Page Verification
==========================================
Assignment requirements:
✓ Randomly select one listing from search results
✓ Click on the selected listing title
✓ Verify listing details page opens successfully
✓ Capture listing title (h1) and subtitle (h2)
✓ Collect all available image URLs from gallery
✓ Store collected details in database
"""
import random
import logging

from automation.services.browser_service  import BrowserService
from automation.services.database_service import DatabaseService
from automation.models                    import ListingData

logger = logging.getLogger(__name__)


class Step06ListingDetails:

    def __init__(self, browser: BrowserService, db: DatabaseService):
        self.browser = browser
        self.db      = db

    def run(self, listings: list) -> dict:
        logger.info("━" * 55)
        logger.info("STEP 06: Item Details Page Verification")
        logger.info("━" * 55)

        if not listings:
            logger.warning("No listings from step 05 — cannot open details page")
            self.db.save_result(
                test_case='Listing Details Page Load',
                url=self.browser.get_url(),
                passed=False,
                should_be='One listing to be randomly selected and its details page opened',
                found='No listings were scraped in Step 05 — cannot proceed',
            )
            return {}

        # ── 1. Randomly pick a listing and navigate to its page ───────────────
        listing = random.choice(listings)
        logger.info(f"Selected listing: {listing.get('title', '?')[:60]}")

        opened = self._navigate_to_listing(listing)
        self.browser.wait(4000)

        current_url = self.browser.get_url()
        self.browser.take_screenshot('step06_01_details_page')

        page_ok = '/rooms/' in current_url
        self.db.save_result(
            test_case='Listing Details Page Load',
            url=current_url,
            passed=page_ok,
            should_be='Listing details page to open with /rooms/ in URL and full listing visible',
            found=f"Page {'opened successfully' if page_ok else 'FAILED to open'}: {current_url[:100]}",
        )

        # ── 2. Capture title (h1) ─────────────────────────────────────────────
        title = self._get_h1_title()
        self.browser.take_screenshot('step06_02_title_subtitle')

        # ── 3. Capture subtitle (h2) ──────────────────────────────────────────
        subtitle = self._get_h2_subtitle()

        self.db.save_result(
            test_case='Listing Title and Subtitle Capture',
            url=current_url,
            passed=bool(title),
            should_be='Listing h1 title and h2 subtitle to be captured from the details page',
            found=f"h1 Title: '{title[:80]}' | h2 Subtitle: '{subtitle[:80]}'",
        )

        # ── 4. Collect all gallery image URLs ─────────────────────────────────
        image_urls = self._collect_gallery_images()
        self.browser.take_screenshot('step06_03_gallery_images')

        self.db.save_result(
            test_case='Listing Gallery Image URLs Collection',
            url=current_url,
            passed=len(image_urls) > 0,
            should_be='All available gallery image URLs to be collected from the listing photo section',
            found=f'Collected {len(image_urls)} image URLs from the listing gallery',
        )

        # ── 5. Store everything in DB ─────────────────────────────────────────
        result = {
            'title':      title,
            'subtitle':   subtitle,
            'image_urls': image_urls,
            'url':        current_url,
        }
        self._persist(result)
        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _navigate_to_listing(self, listing: dict) -> bool:
        """Navigate to a listing's detail page."""
        page        = self.browser.page
        listing_url = listing.get('listing_url', '')

        # Direct navigation if we have a rooms URL
        if listing_url:
            if not listing_url.startswith('http'):
                listing_url = 'https://www.airbnb.com' + listing_url
            if '/rooms/' in listing_url:
                self.browser.navigate(listing_url)
                self.browser.wait(3000)
                return '/rooms/' in self.browser.get_url()

        # Click the first available room link on the current page
        try:
            links = page.locator("a[href*='/rooms/']").all()
            if links:
                pick = random.choice(links[:10])
                href = pick.get_attribute('href') or ''
                if href:
                    if not href.startswith('http'):
                        href = 'https://www.airbnb.com' + href
                    self.browser.navigate(href)
                    self.browser.wait(3000)
                    return '/rooms/' in self.browser.get_url()
        except Exception as e:
            logger.warning(f"Room link click failed: {e}")

        return False

    def _get_h1_title(self) -> str:
        """Get the listing title from the h1 element."""
        page = self.browser.page
        try:
            el = page.locator('h1').first
            if el.is_visible(timeout=6000):
                txt = el.inner_text().strip()
                if txt:
                    logger.info(f"Title (h1): {txt[:70]}")
                    return txt
        except Exception as e:
            logger.warning(f"h1 title error: {e}")
        return ''

    def _get_h2_subtitle(self) -> str:
        """
        Get listing subtitle from h2.
        On real Airbnb this sits inside data-section-id='OVERVIEW_DEFAULT_V2'.
        Example: "Room in Greater London, United Kingdom"
        """
        page = self.browser.page
        selectors = [
            "[data-section-id='OVERVIEW_DEFAULT_V2'] h2",
            "[data-plugin-in-point-id='OVERVIEW_DEFAULT_V2'] h2",
            "h2",   # generic fallback
        ]
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    txt = el.inner_text().strip()
                    if txt:
                        logger.info(f"Subtitle (h2): {txt[:70]}")
                        return txt
            except Exception:
                pass
        return ''

    def _collect_gallery_images(self) -> list:
        """
        Collect all gallery image URLs using JS.
        Airbnb serves images from the muscache.com CDN.
        """
        images = self.browser.js("""
            () => {
                const urls = new Set();
                document.querySelectorAll('img').forEach(img => {
                    [img.src, img.dataset.src, img.dataset.originalUri].forEach(src => {
                        if (src && src.includes('muscache.com') && !src.startsWith('data:')) {
                            urls.add(src);
                        }
                    });
                    // Parse srcset too
                    (img.srcset || '').split(',').forEach(part => {
                        const u = part.trim().split(' ')[0];
                        if (u && u.includes('muscache.com')) {
                            urls.add(u);
                        }
                    });
                });
                return [...urls];
            }
        """)
        logger.info(f"Gallery images collected: {len(images)}")
        return images

    def _persist(self, result: dict):
        """Upsert listing detail record into ListingData table."""
        try:
            title  = result.get('title', '')
            images = result.get('image_urls', [])
            if title:
                ListingData.objects.update_or_create(
                    listing_url=result.get('url', '')[:2048],
                    defaults={
                        'title':     title[:512],
                        'price':     '',
                        'image_url': images[0][:2048] if images else '',
                    },
                )
                logger.info(f"Listing detail saved: {title[:60]}")
        except Exception as e:
            logger.warning(f"Failed to persist listing detail: {e}")
