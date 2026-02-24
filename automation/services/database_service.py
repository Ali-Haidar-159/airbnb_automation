"""
DatabaseService
===============
All database write operations in one place.
Comment format: "should be <expected>, found <actual>"
"""
import logging
from django.db import connection
from django.db.utils import ProgrammingError
from automation.models import (
    TestResult, ListingData, SuggestionData, NetworkLog, ConsoleLog
)

logger = logging.getLogger(__name__)

_VALID_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'}


class DatabaseService:
    @staticmethod
    def _ensure_table(model):
        table_name = model._meta.db_table
        existing_tables = set(connection.introspection.table_names())
        if table_name in existing_tables:
            return
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(model)
        logger.warning(
            "Missing table '%s' was auto-created at runtime. Run migrations to keep schema consistent.",
            table_name,
        )

    # ── Test results ──────────────────────────────────────────────────────────

    @staticmethod
    def save_result(
        test_case: str,
        url: str,
        passed: bool,
        should_be: str,
        found: str,
    ) -> TestResult:
        DatabaseService._ensure_table(TestResult)
        comment = f"should be {should_be}, found {found}"
        obj = TestResult.objects.create(
            test_case=test_case,
            url=url[:2048],
            passed=passed,
            comment=comment,
        )
        icon = '✅' if passed else '❌'
        logger.info(f"{icon} [{test_case}] {comment}")
        return obj

    # ── Suggestions ───────────────────────────────────────────────────────────

    @staticmethod
    def save_suggestions(texts: list, query: str):
        DatabaseService._ensure_table(SuggestionData)
        objs = [
            SuggestionData(text=t[:512], search_query=query[:255])
            for t in texts if t.strip()
        ]
        if objs:
            SuggestionData.objects.bulk_create(objs)
            logger.info(f"Saved {len(objs)} suggestions for '{query}'")

    # ── Listings ──────────────────────────────────────────────────────────────

    @staticmethod
    def save_listings(listings: list):
        DatabaseService._ensure_table(ListingData)
        objs = [
            ListingData(
                title=item.get('title', '')[:512],
                price=item.get('price', '')[:100],
                image_url=item.get('image_url', '')[:2048],
                listing_url=item.get('listing_url', '')[:2048],
            )
            for item in listings if item.get('title')
        ]
        if objs:
            try:
                ListingData.objects.bulk_create(objs)
            except ProgrammingError:
                # Handles cases where DB schema was changed outside Django migration state.
                DatabaseService._ensure_table(ListingData)
                ListingData.objects.bulk_create(objs)
            logger.info(f"Saved {len(objs)} listings")

    # ── Network logs ──────────────────────────────────────────────────────────

    @staticmethod
    def save_network_logs(logs: list):
        DatabaseService._ensure_table(NetworkLog)
        objs = []
        for log in logs:
            url = log.get('url', '')
            if not url or url.startswith('data:') or url.startswith('blob:'):
                continue
            method = log.get('method', 'GET').upper()
            if method not in _VALID_METHODS:
                method = 'GET'
            objs.append(NetworkLog(
                url=url,
                method=method,
                status_code=log.get('status_code'),
                resource_type=log.get('resource_type', '')[:50],
            ))
        if objs:
            NetworkLog.objects.bulk_create(objs, ignore_conflicts=True)
            logger.info(f"Saved {len(objs)} network logs")

    # ── Console logs ──────────────────────────────────────────────────────────

    @staticmethod
    def save_console_logs(logs: list):
        DatabaseService._ensure_table(ConsoleLog)
        level_map = {
            'LOG': 'INFO', 'INFO': 'INFO',
            'WARNING': 'WARNING', 'WARN': 'WARNING',
            'ERROR': 'ERROR', 'DEBUG': 'DEBUG',
        }
        objs = [
            ConsoleLog(
                level=level_map.get(log.get('level', 'INFO').upper(), 'INFO'),
                message=log.get('message', '')[:2000],
                source=log.get('source', '')[:512],
            )
            for log in logs
        ]
        if objs:
            ConsoleLog.objects.bulk_create(objs)
            logger.info(f"Saved {len(objs)} console logs")
