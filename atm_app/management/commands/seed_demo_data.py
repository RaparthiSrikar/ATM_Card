from django.core.management.base import BaseCommand
from atm_app.models import Customer, Account, Card, Transaction


class Command(BaseCommand):
    help = "Clear demo data from database."

    def handle(self, *args, **options):
        t_count = Transaction.objects.all().delete()[0]
        c_count = Card.objects.all().delete()[0]
        a_count = Account.objects.all().delete()[0]
        cust_count = Customer.objects.all().delete()[0]
        self.stdout.write(self.style.SUCCESS(f"Cleared database: {cust_count} customers, {a_count} accounts, {c_count} cards, {t_count} transactions."))
