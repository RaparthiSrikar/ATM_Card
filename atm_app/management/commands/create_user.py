from datetime import date
from decimal import Decimal
import random

from django.core.management.base import BaseCommand
from atm_app.models import Customer, Account, Card, Transaction


class Command(BaseCommand):
    help = "Create a new ATM user (Customer, Account, Card) for login."

    def add_arguments(self, parser):
        parser.add_argument("--name", type=str, default="Rahul Verma", help="Customer Full Name")
        parser.add_argument("--phone", type=str, default="9988776655", help="10-digit phone number")
        parser.add_argument("--email", type=str, default="rahul@example.com", help="Customer Email")
        parser.add_argument("--balance", type=float, default=25000.0, help="Initial deposit balance")
        parser.add_argument("--pin", type=str, default="9999", help="4-digit PIN")

    def handle(self, *args, **options):
        name = options["name"]
        phone = options["phone"]
        email = options["email"]
        balance = Decimal(str(options["balance"]))
        pin = options["pin"]

        customer = Customer.objects.create(name=name, phone=phone, email=email)
        account = Account.objects.create(customer=customer, account_type="SAVINGS", balance=balance)

        while True:
            card_number = "4" + "".join([str(random.randint(0, 9)) for _ in range(15)])
            if not Card.objects.filter(card_number=card_number).exists():
                break

        card = Card(card_number=card_number, account=account, expiry_date=date(2030, 12, 31))
        card.set_pin(pin)
        card.save()

        if balance > Decimal("0.00"):
            Transaction.objects.create(
                account=account,
                transaction_type="DEPOSIT",
                amount=balance,
                balance_after=balance,
                status="SUCCESS",
                remarks="Initial account deposit",
            )

        self.stdout.write(self.style.SUCCESS(f"New User Created Successfully!"))
        self.stdout.write(f"Customer Name : {customer.name}")
        self.stdout.write(f"Account Number: {account.account_number}")
        self.stdout.write(f"Card Number   : {card_number}")
        self.stdout.write(f"PIN           : {pin}")
        self.stdout.write(f"Balance       : INR {balance:,.2f}")
