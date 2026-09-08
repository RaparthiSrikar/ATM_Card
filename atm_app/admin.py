from django.contrib import admin

from .models import Account, Card, Customer, Transaction


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "name", "phone", "email", "created_at")
    search_fields = ("customer_id", "name", "phone")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("account_number", "customer", "account_type", "balance", "status")
    list_filter = ("account_type", "status")
    search_fields = ("account_number", "customer__name")


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("card_number", "account", "status", "failed_attempts", "expiry_date")
    list_filter = ("status",)
    search_fields = ("card_number",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("account", "transaction_type", "amount", "balance_after", "status", "timestamp")
    list_filter = ("transaction_type", "status")
    date_hierarchy = "timestamp"
