import random
from datetime import date
from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AmountForm, ChangePinForm, LoginForm, RegisterForm, TransferForm
from .models import Account, Card, Customer, Transaction


# ---------------------------------------------------------------------------
# MODULE 14: session-based "who is currently using the ATM" helper
# ---------------------------------------------------------------------------


def login_required_atm(view_func):
    """Custom guard (the ATM authenticates by card+PIN, not Django's User model)."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("account_id"):
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect("atm_app:login")
        return view_func(request, *args, **kwargs)

    return wrapper


def _current_account(request):
    return get_object_or_404(Account, pk=request.session["account_id"])


# ---------------------------------------------------------------------------
# MODULE 13: Login / Authentication
# ---------------------------------------------------------------------------


def _ensure_demo_card():
    try:
        if not Card.objects.filter(card_number="4111111111111111").exists():
            customer, _ = Customer.objects.get_or_create(
                customer_id="CUSTDEMO01",
                defaults={"name": "Ravi Kumar", "phone": "9876543210", "email": "ravi@example.com"}
            )
            account, _ = Account.objects.get_or_create(
                customer=customer,
                defaults={"account_number": "AC1000000001", "account_type": "SAVINGS", "balance": Decimal("50000.00"), "daily_withdrawal_limit": Decimal("25000.00")}
            )
            if not Card.objects.filter(card_number="4111111111111111").exists():
                card = Card(
                    card_number="4111111111111111",
                    account=account,
                    status="ACTIVE",
                    failed_attempts=0,
                    expiry_date=date(2030, 12, 31),
                )
                card.set_pin("1234")
                card.save()
    except Exception:
        pass


def login_view(request):
    _ensure_demo_card()
    if request.session.get("account_id"):
        return redirect("atm_app:dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        card_number = form.cleaned_data["card_number"]
        pin = form.cleaned_data["pin"]

        card = Card.objects.filter(card_number=card_number).select_related("account", "account__customer").first()

        # Deliberately vague error message -- never reveal *which* part was wrong (MODULE 13/27).
        generic_error = "Invalid card number or PIN."

        if card is None:
            messages.error(request, generic_error)
        elif card.status == "BLOCKED":
            messages.error(request, "This card is blocked due to repeated failed attempts. Visit your branch.")
        elif card.status == "EXPIRED" or card.expiry_date < date.today():
            messages.error(request, "This card has expired.")
        elif not card.check_pin(pin):
            card.register_failed_attempt()
            remaining = max(card.MAX_FAILED_ATTEMPTS - card.failed_attempts, 0)
            if card.status == "BLOCKED":
                messages.error(request, "Too many incorrect attempts. Card is now blocked.")
            else:
                messages.error(request, f"{generic_error} {remaining} attempt(s) remaining.")
        else:
            card.reset_failed_attempts()
            request.session["account_id"] = card.account_id
            request.session["customer_name"] = card.account.customer.name
            return redirect("atm_app:dashboard")

    return render(request, "atm_app/login.html", {"form": form})


@login_required_atm
def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out safely. Please take your card.")
    return redirect("atm_app:login")


def _generate_card_number():
    while True:
        card_num = "4" + "".join([str(random.randint(0, 9)) for _ in range(15)])
        if not Card.objects.filter(card_number=card_num).exists():
            return card_num


def register_view(request):
    """Register a new customer, account, and ATM card for login."""
    if request.session.get("account_id"):
        return redirect("atm_app:dashboard")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        name = form.cleaned_data["name"]
        phone = form.cleaned_data["phone"]
        email = form.cleaned_data["email"]
        account_type = form.cleaned_data["account_type"]
        initial_deposit = form.cleaned_data["initial_deposit"]
        pin = form.cleaned_data["pin"]

        with transaction.atomic():
            customer = Customer.objects.create(name=name, phone=phone, email=email)
            account = Account.objects.create(
                customer=customer,
                account_type=account_type,
                balance=initial_deposit,
            )
            card_number = _generate_card_number()
            expiry_date = date(date.today().year + 5, 12, 31)
            card = Card(
                card_number=card_number,
                account=account,
                expiry_date=expiry_date,
            )
            card.set_pin(pin)
            card.save()

            if initial_deposit > Decimal("0.00"):
                Transaction.objects.create(
                    account=account,
                    transaction_type="DEPOSIT",
                    amount=initial_deposit,
                    balance_after=initial_deposit,
                    status="SUCCESS",
                    remarks="Initial account deposit",
                )

        messages.success(request, "Account created successfully! Note down your Card Number and PIN to log in.")
        return render(
            request,
            "atm_app/register_success.html",
            {
                "customer": customer,
                "account": account,
                "card_number": card_number,
                "pin": pin,
            },
        )

    return render(request, "atm_app/register.html", {"form": form})



# ---------------------------------------------------------------------------
# MODULE 4: Dashboard (also serves as Balance Enquiry, MODULE 15)
# ---------------------------------------------------------------------------


@login_required_atm
def dashboard_view(request):
    account = _current_account(request)
    return render(request, "atm_app/dashboard.html", {"account": account})


# ---------------------------------------------------------------------------
# MODULE 16 / 17: Cash Withdrawal
# ---------------------------------------------------------------------------


@login_required_atm
def withdraw_view(request):
    account = _current_account(request)
    form = AmountForm(request.POST or None)
    result = None

    if request.method == "POST" and form.is_valid():
        amount = form.cleaned_data["amount"]

        with transaction.atomic():
            locked_account = Account.objects.select_for_update().get(pk=account.pk)

            if amount > locked_account.daily_withdrawal_limit:
                messages.error(request, f"Amount exceeds the per-transaction limit of ₹{locked_account.daily_withdrawal_limit}.")
            elif amount > locked_account.balance:
                messages.error(request, "Insufficient balance.")
                Transaction.objects.create(
                    account=locked_account, transaction_type="WITHDRAWAL", amount=amount,
                    balance_after=locked_account.balance, status="FAILED", remarks="Insufficient balance",
                )
            elif amount % 100 != 0:
                messages.error(request, "Amount must be in multiples of ₹100 (denomination rule).")
            else:
                locked_account.balance -= amount
                locked_account.save(update_fields=["balance"])
                Transaction.objects.create(
                    account=locked_account, transaction_type="WITHDRAWAL", amount=amount,
                    balance_after=locked_account.balance, status="SUCCESS",
                )
                result = {"amount": amount, "balance": locked_account.balance}
                account = locked_account

    return render(request, "atm_app/withdraw.html", {"account": account, "form": form, "result": result})


# ---------------------------------------------------------------------------
# MODULE 18: Cash Deposit
# ---------------------------------------------------------------------------


@login_required_atm
def deposit_view(request):
    account = _current_account(request)
    form = AmountForm(request.POST or None)
    result = None

    if request.method == "POST" and form.is_valid():
        amount = form.cleaned_data["amount"]
        with transaction.atomic():
            locked_account = Account.objects.select_for_update().get(pk=account.pk)
            locked_account.balance += amount
            locked_account.save(update_fields=["balance"])
            Transaction.objects.create(
                account=locked_account, transaction_type="DEPOSIT", amount=amount,
                balance_after=locked_account.balance, status="SUCCESS",
            )
            result = {"amount": amount, "balance": locked_account.balance}
            account = locked_account

    return render(request, "atm_app/deposit.html", {"account": account, "form": form, "result": result})


# ---------------------------------------------------------------------------
# MODULE 19 / 26: Fund Transfer (atomic — commit or rollback as ONE unit)
# ---------------------------------------------------------------------------


@login_required_atm
def transfer_view(request):
    account = _current_account(request)
    form = TransferForm(request.POST or None)
    result = None

    if request.method == "POST" and form.is_valid():
        amount = form.cleaned_data["amount"]
        beneficiary_number = form.cleaned_data["beneficiary_account"]

        if beneficiary_number == account.account_number:
            messages.error(request, "You cannot transfer money to your own account.")
        else:
            receiver = Account.objects.filter(account_number=beneficiary_number, status="ACTIVE").first()
            if receiver is None:
                messages.error(request, "Receiver account not found or inactive.")
            else:
                with transaction.atomic():
                    # Lock both rows in a stable order to avoid deadlocks.
                    ids = sorted([account.pk, receiver.pk])
                    locked = {a.pk: a for a in Account.objects.select_for_update().filter(pk__in=ids)}
                    sender_locked = locked[account.pk]
                    receiver_locked = locked[receiver.pk]

                    if amount > sender_locked.balance:
                        messages.error(request, "Insufficient balance.")
                        Transaction.objects.create(
                            account=sender_locked, transaction_type="TRANSFER_OUT", amount=amount,
                            balance_after=sender_locked.balance, counterparty_account=beneficiary_number,
                            status="FAILED", remarks="Insufficient balance",
                        )
                    else:
                        sender_locked.balance -= amount
                        receiver_locked.balance += amount
                        sender_locked.save(update_fields=["balance"])
                        receiver_locked.save(update_fields=["balance"])

                        Transaction.objects.create(
                            account=sender_locked, transaction_type="TRANSFER_OUT", amount=amount,
                            balance_after=sender_locked.balance, counterparty_account=beneficiary_number,
                            status="SUCCESS",
                        )
                        Transaction.objects.create(
                            account=receiver_locked, transaction_type="TRANSFER_IN", amount=amount,
                            balance_after=receiver_locked.balance, counterparty_account=sender_locked.account_number,
                            status="SUCCESS",
                        )
                        result = {"amount": amount, "balance": sender_locked.balance, "receiver": beneficiary_number}
                        account = sender_locked

    return render(request, "atm_app/transfer.html", {"account": account, "form": form, "result": result})


# ---------------------------------------------------------------------------
# MODULE 20: PIN Change
# ---------------------------------------------------------------------------


@login_required_atm
def change_pin_view(request):
    account = _current_account(request)
    card = account.card
    form = ChangePinForm(request.POST or None)
    success = False

    if request.method == "POST" and form.is_valid():
        if not card.check_pin(form.cleaned_data["current_pin"]):
            messages.error(request, "Current PIN is incorrect.")
        elif form.cleaned_data["current_pin"] == form.cleaned_data["new_pin"]:
            messages.error(request, "New PIN must be different from the current PIN.")
        else:
            card.set_pin(form.cleaned_data["new_pin"])
            card.save(update_fields=["pin_hash"])
            Transaction.objects.create(
                account=account, transaction_type="PIN_CHANGE", amount=Decimal("0.00"),
                balance_after=account.balance, status="SUCCESS", remarks="PIN changed successfully",
            )
            success = True

    return render(request, "atm_app/change_pin.html", {"account": account, "form": form, "success": success})


# ---------------------------------------------------------------------------
# MODULE 21: Mini Statement
# ---------------------------------------------------------------------------


@login_required_atm
def mini_statement_view(request):
    account = _current_account(request)
    recent_transactions = account.transactions.all()[:10]
    return render(request, "atm_app/mini_statement.html", {"account": account, "transactions": recent_transactions})
