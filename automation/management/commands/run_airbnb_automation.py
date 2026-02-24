"""
run_airbnb_automation
=====================
Django Management Command — Entry point for the full Airbnb automation.

Usage:
    python manage.py run_airbnb_automation              # visible browser
    python manage.py run_airbnb_automation --headless   # no window
    python manage.py run_airbnb_automation --mobile     # iPhone 14 Pro
    python manage.py run_airbnb_automation --mobile --headless

═══════════════════════════════════════════════════════════════
CRITICAL FIX — Why os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] is here
═══════════════════════════════════════════════════════════════
Playwright's sync_playwright() starts a background thread to manage
the browser event loop. Django 4.x treats any thread it didn't create
as an "async context" and raises:
  SynchronousOnlyOperation: You cannot call this from an async context

Setting DJANGO_ALLOW_ASYNC_UNSAFE=true BEFORE importing anything from
Django disables this safety guard for this management command only.
This is the officially documented workaround for sync Playwright + Django.
═══════════════════════════════════════════════════════════════
"""

# ─── MUST BE THE VERY FIRST CODE — before any Django ORM imports ─────────────
import os
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
# ─────────────────────────────────────────────────────────────────────────────

import sys
import logging

from django.core.management.base import BaseCommand
from django.conf                  import settings

from automation.services.browser_service   import BrowserService
from automation.services.database_service  import DatabaseService
from automation.steps.step01_landing       import Step01LandingAndSearch
from automation.steps.step02_suggestion    import Step02AutoSuggestion
from automation.steps.step03_datepicker    import Step03DatePicker
from automation.steps.step04_guestpicker   import Step04GuestPicker
from automation.steps.step05_results       import Step05SearchResults
from automation.steps.step06_details       import Step06ListingDetails

# ─── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(name)s  %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Run the full Airbnb end-to-end automation journey '
        'using Python Playwright and Django.'
    )

    # ─────────────────────────────────────────────────────────────────────────
    # CLI arguments
    # ─────────────────────────────────────────────────────────────────────────

    def add_arguments(self, parser):
        parser.add_argument(
            '--headless',
            action='store_true',
            default=False,
            help='Run Chromium in headless mode (no browser window). Default: visible.',
        )
        parser.add_argument(
            '--mobile',
            action='store_true',
            default=False,
            help='[BONUS] Emulate iPhone 14 Pro mobile device.',
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Entry point
    # ─────────────────────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        headless   = options['headless']
        mobile     = options['mobile']
        target_url = settings.AIRBNB_URL

        self.stdout.write(self.style.SUCCESS(
            f"\n{'═' * 62}\n"
            f"  🏠  Airbnb End-to-End Automation\n"
            f"  Framework : Python Playwright + Django\n"
            f"  Mode      : {'📱 Mobile (iPhone 14 Pro)' if mobile else '🖥  Desktop (1440×900)'}\n"
            f"  Browser   : {'Headless (no window)' if headless else 'Visible window'}\n"
            f"  Target    : {target_url}\n"
            f"{'═' * 62}\n"
        ))

        db = DatabaseService()

        # Log session start
        db.save_result(
            test_case='Automation Session Start',
            url=target_url,
            passed=True,
            should_be='Playwright browser to launch and Airbnb URL to be reachable',
            found=f"Session started — "
                  f"{'Mobile' if mobile else 'Desktop'} | "
                  f"{'Headless' if headless else 'Visible'}",
        )

        try:
            with BrowserService(headless=headless, mobile=mobile) as browser:
                self._run_journey(browser, db, target_url)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n⚠  Stopped by user (Ctrl+C).'))
            db.save_result(
                test_case='Automation Session End',
                url=target_url,
                passed=False,
                should_be='All 6 steps to complete successfully',
                found='Keyboard interrupt — user stopped the automation',
            )

        except Exception as exc:
            logger.error(f"Unhandled error: {exc}", exc_info=True)
            db.save_result(
                test_case='Automation Session End',
                url=target_url,
                passed=False,
                should_be='All 6 steps to complete without error',
                found=f'Automation crashed: {str(exc)[:250]}',
            )
            self.stdout.write(self.style.ERROR(f'\n❌  Automation failed: {exc}'))
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # Journey runner — executes all 6 steps in sequence
    # ─────────────────────────────────────────────────────────────────────────

    def _run_journey(
        self,
        browser:    BrowserService,
        db:         DatabaseService,
        target_url: str,
    ):
        def header(n: int, title: str):
            self.stdout.write(self.style.HTTP_INFO(
                f"\n┌{'─' * 60}┐\n"
                f"│  Step {n:02d} — {title:<50}│\n"
                f"└{'─' * 60}┘"
            ))

        # ── Step 01 ───────────────────────────────────────────────────────────
        header(1, 'Website Landing and Initial Search Setup')
        country = Step01LandingAndSearch(browser, db, target_url).run()
        self.stdout.write(self.style.SUCCESS(f"  ✓  Country randomly selected: {country}"))

        # ── Step 02 ───────────────────────────────────────────────────────────
        header(2, 'Search Auto-suggestion Verification')
        s2_ok = Step02AutoSuggestion(browser, db).run(country)
        self.stdout.write(self.style.SUCCESS(
            f"  {'✓  Suggestion clicked' if s2_ok else '⚠  Suggestion had issues — continuing'}"
        ))

        # ── Step 03 ───────────────────────────────────────────────────────────
        header(3, 'Date Picker Interaction')
        dates = Step03DatePicker(browser, db).run()
        self.stdout.write(self.style.SUCCESS(
            f"  ✓  Check-in  date : {dates.get('checkin',  'N/A')}\n"
            f"  ✓  Check-out date : {dates.get('checkout', 'N/A')}"
        ))

        # ── Step 04 ───────────────────────────────────────────────────────────
        header(4, 'Guest Picker Interaction')
        guests = Step04GuestPicker(browser, db).run()
        self.stdout.write(self.style.SUCCESS(f"  ✓  Total guests added: {guests}"))

        # ── Step 05 ───────────────────────────────────────────────────────────
        header(5, 'Refine Search and Item List Verification')
        listings = Step05SearchResults(browser, db).run(dates, guests)
        self.stdout.write(self.style.SUCCESS(f"  ✓  Listings scraped: {len(listings)}"))

        # ── Step 06 ───────────────────────────────────────────────────────────
        header(6, 'Item Details Page Verification')
        details = Step06ListingDetails(browser, db).run(listings)
        self.stdout.write(self.style.SUCCESS(
            f"  ✓  Title   : {details.get('title',    'N/A')[:55]}\n"
            f"  ✓  Subtitle: {details.get('subtitle', 'N/A')[:55]}\n"
            f"  ✓  Images  : {len(details.get('image_urls', []))} gallery images"
        ))

        # ── Save console & network logs collected throughout the session ───────
        self.stdout.write(self.style.HTTP_INFO("\n  Saving monitoring logs..."))
        if browser.console_logs:
            db.save_console_logs(browser.console_logs)
            self.stdout.write(self.style.SUCCESS(
                f"  ✓  Console logs : {len(browser.console_logs)} entries saved"
            ))
        if browser.network_logs:
            db.save_network_logs(browser.network_logs)
            self.stdout.write(self.style.SUCCESS(
                f"  ✓  Network logs : {len(browser.network_logs)} entries saved"
            ))

        # ── Log session end ───────────────────────────────────────────────────
        db.save_result(
            test_case='Automation Session End',
            url=browser.get_url(),
            passed=True,
            should_be='All 6 automation steps to complete and all data stored in database',
            found=(
                f"Complete — country={country} | "
                f"checkin={dates.get('checkin')} | "
                f"checkout={dates.get('checkout')} | "
                f"guests={guests} | "
                f"listings={len(listings)} | "
                f"title={details.get('title', '')[:40]}"
            ),
        )

        self._print_final_summary()

    # ─────────────────────────────────────────────────────────────────────────
    # Final summary
    # ─────────────────────────────────────────────────────────────────────────

    def _print_final_summary(self):
        from automation.models import TestResult
        total  = TestResult.objects.count()
        passed = TestResult.objects.filter(passed=True).count()
        failed = total - passed

        self.stdout.write(self.style.SUCCESS(
            f"\n{'═' * 62}\n"
            f"  ✅  AUTOMATION COMPLETE\n"
            f"{'─' * 62}\n"
            f"  Total Test Cases : {total}\n"
            f"  Passed  ✅       : {passed}\n"
            f"  Failed  ❌       : {failed}\n"
            f"{'─' * 62}\n"
            f"  📁  Screenshots saved in : ./screenshots/\n"
            f"  🌐  Admin panel at       : http://127.0.0.1:8000/admin/\n"
            f"{'═' * 62}\n"
        ))
