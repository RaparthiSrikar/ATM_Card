import uuid
from decimal import Decimal

from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


class Customer(models.Model):
    """A bank customer. One customer -> one account (kept 1:1 to mirror the KT doc)."""

    customer_id = models.CharField(max_length=12, unique=True, editable=False)
    name = models.CharField(max_length=100)
    phone = models.CharField(
        max_length=10,
        validators=[RegexValidator(r"^\d{10}$", "Enter a valid 10-digit phone number.")],
    )
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.customer_id:
            self.customer_id = "CUST" + uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.customer_id})"


class Account(models.Model):
    """Banking account information. Balance is Decimal, never Float (MODULE 12)."""

    ACCOUNT_TYPES = [("SAVINGS", "Savings"), ("CURRENT", "Current")]
    STATUS_CHOICES = [("ACTIVE", "Active"), ("BLOCKED", "Blocked")]

    account_number = models.CharField(max_length=12, unique=True, editable=False)
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="account")
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default="SAVINGS")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")
    daily_withdrawal_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("25000.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = "AC" + uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.account_number} - {self.customer.name}"


class Card(models.Model):
    """ATM card tied to an account. PIN is hashed, never stored as plain text (MODULE 20)."""

    STATUS_CHOICES = [("ACTIVE", "Active"), ("BLOCKED", "Blocked"), ("EXPIRED", "Expired")]

    card_number = models.CharField(max_length=16, unique=True)
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="card")
    pin_hash = models.CharField(max_length=128)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    expiry_date = models.DateField()

    MAX_FAILED_ATTEMPTS = 3

    def set_pin(self, raw_pin: str):
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin: str) -> bool:
        return check_password(raw_pin, self.pin_hash)

    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    def register_failed_attempt(self):
        self.failed_attempts += 1
        if self.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            self.status = "BLOCKED"
        self.save(update_fields=["failed_attempts", "status"])

    def reset_failed_attempts(self):
        if self.failed_attempts:
            self.failed_attempts = 0
            self.save(update_fields=["failed_attempts"])

    def __str__(self):
        return f"Card ending {self.card_number[-4:]}"


class Transaction(models.Model):
    """Every financial operation is recorded here (MODULE 10 / 21 / 25)."""

    TRANSACTION_TYPES = [
        ("WITHDRAWAL", "Withdrawal"),
        ("DEPOSIT", "Deposit"),
        ("TRANSFER_OUT", "Transfer Out"),
        ("TRANSFER_IN", "Transfer In"),
        ("PIN_CHANGE", "PIN Change"),
    ]
    STATUS_CHOICES = [("SUCCESS", "Success"), ("FAILED", "Failed")]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=15, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    counterparty_account = models.CharField(max_length=12, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="SUCCESS")
    remarks = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} on {self.account.account_number}"
