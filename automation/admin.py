from django.contrib import admin
from .models import TestResult, ListingData, SuggestionData, NetworkLog, ConsoleLog


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display   = ('id', 'test_case', 'passed', 'comment')
    list_filter    = ('passed',)
    search_fields  = ('test_case', 'comment')
    ordering       = ('-id',)
    list_per_page  = 50


@admin.register(ListingData)
class ListingDataAdmin(admin.ModelAdmin):
    list_display  = ('id', 'title', 'price', 'listing_url', 'scraped_at')
    search_fields = ('title',)
    ordering      = ('-scraped_at',)


@admin.register(SuggestionData)
class SuggestionDataAdmin(admin.ModelAdmin):
    list_display  = ('id', 'search_query', 'text', 'captured_at')
    search_fields = ('search_query', 'text')
    ordering      = ('-captured_at',)


@admin.register(NetworkLog)
class NetworkLogAdmin(admin.ModelAdmin):
    list_display  = ('id', 'method', 'status_code', 'resource_type', 'url', 'captured_at')
    list_filter   = ('method', 'status_code')
    ordering      = ('-captured_at',)


@admin.register(ConsoleLog)
class ConsoleLogAdmin(admin.ModelAdmin):
    list_display  = ('id', 'level', 'message', 'captured_at')
    list_filter   = ('level',)
    ordering      = ('-captured_at',)
