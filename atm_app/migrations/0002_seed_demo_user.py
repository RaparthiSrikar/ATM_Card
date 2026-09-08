from datetime import date
from decimal import Decimal
from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_demo_user(apps, schema_editor):
    Customer = apps.get_model('atm_app', 'Customer')
    Account = apps.get_model('atm_app', 'Account')
    Card = apps.get_model('atm_app', 'Card')
    Transaction = apps.get_model('atm_app', 'Transaction')

    if not Card.objects.filter(card_number='4111111111111111').exists():
        customer = Customer.objects.create(
            customer_id='CUSTDEMO01',
            name='Ravi Kumar',
            phone='9876543210',
            email='ravi@example.com'
        )
        account = Account.objects.create(
            account_number='AC1000000001',
            customer=customer,
            account_type='SAVINGS',
            balance=Decimal('50000.00'),
            daily_withdrawal_limit=Decimal('25000.00')
        )
        card = Card.objects.create(
            card_number='4111111111111111',
            account=account,
            pin_hash=make_password('1234'),
            status='ACTIVE',
            failed_attempts=0,
            expiry_date=date(2030, 12, 31)
        )
        Transaction.objects.create(
            account=account,
            transaction_type='DEPOSIT',
            amount=Decimal('50000.00'),
            balance_after=Decimal('50000.00'),
            status='SUCCESS',
            remarks='Initial account deposit'
        )


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('atm_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_demo_user, reverse_func),
    ]
