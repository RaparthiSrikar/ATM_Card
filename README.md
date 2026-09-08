# ABC Bank — ATM Management System

A working, real-time ATM simulator built exactly to the module-wise KT
document you provided: **HTML → CSS → Bootstrap-style responsive layout →
JavaScript → Python → Django → SQL**. It isn't a mockup — every screen
reads and writes a real SQLite database through Django, with the same
validations, security rules, and transaction logic a real ATM needs.

![tech](https://img.shields.io/badge/stack-Django%20%7C%20SQLite%20%7C%20JS-2dd4bf)

## What it looks like

The UI is designed as a physical ATM kiosk, not a generic web form: a dark
machine housing frames a glowing terminal screen, the dashboard menu lines
up with labeled side-buttons (L1–L4 / R1–R4) the way a real ATM's bezel
works, and every action gets a matching animation — a card slides into the
slot on login, a short "processing…" spinner plays before each transaction,
cash notes animate out on a successful withdrawal, and results print onto
a receipt-style panel.

## 1. Prerequisites

- Python 3.10 or newer
- pip

# 2. Setup (step by step)

```bash
# 1. Unzip the project and move into it
cd atm_management_system

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the database tables
python manage.py migrate

# 5. Create a new user account via CLI (or register via web interface)
python manage.py create_user --name "John Doe" --phone "9876543210" --balance 50000 --pin "1234"

# 6. Run the development server
python manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser.

## 3. Creating & Managing Accounts

You can create new customer accounts in two ways:
1. **Web Interface**: Click `+ Open New Account & Get ATM Card` on the login page (`/register/`).
2. **Management Command**:
   ```bash
   python manage.py create_user --name "Name" --phone "10-digit-phone" --balance 25000 --pin "4-digit-pin"
   ```


## 4. Feature checklist (maps to the KT document's modules)

| Feature | Module(s) | Where it lives |
|---|---|---|
| Login (card + PIN) | 4, 13 | `views.login_view`, `templates/login.html` |
| Failed-attempt lockout | 13, 27 | `Card.register_failed_attempt` |
| Session management / auto-logout | 14 | `login_required_atm` decorator, `SESSION_COOKIE_AGE` in settings |
| Dashboard / Balance Enquiry | 4, 15 | `views.dashboard_view` |
| Cash Withdrawal + limits + denomination rule | 16, 17 | `views.withdraw_view` |
| Cash Deposit | 18 | `views.deposit_view` |
| Fund Transfer (atomic, rollback-safe) | 19, 26 | `views.transfer_view` (`transaction.atomic()`) |
| PIN Change (hashed, never plain text) | 20 | `views.change_pin_view`, `Card.set_pin` |
| Mini Statement | 21 | `views.mini_statement_view` |
| Logout / session clear | 14 | `views.logout_view` |
| Client-side validation | 7 | `static/js/atm.js` |
| Server-side validation (authoritative) | 7, 23 | `atm_app/forms.py` |
| Database design (Customer/Account/Card/Transaction) | 10, 11, 12 | `atm_app/models.py` |
| Security (CSRF, hashing, SQL injection safety via ORM) | 27 | Django defaults + `models.py` |
| Error handling | 28 | Each view's validation branches |

## 5. Project structure

```
atm_management_system/
├── manage.py
├── requirements.txt
├── atm_system/              # Django project (settings, root urls)
│   └── settings.py
└── atm_app/                 # The ATM application
    ├── models.py            # Customer, Account, Card, Transaction
    ├── forms.py              # LoginForm, AmountForm, TransferForm, ChangePinForm
    ├── views.py              # One view per ATM operation
    ├── urls.py
    ├── admin.py              # Registers models for /admin/
    ├── management/commands/
    │   └── seed_demo_data.py # Creates Ravi & Priya
    └── templates/atm_app/
        ├── base.html          # Kiosk shell, screen bezel, side buttons
        ├── login.html
        ├── dashboard.html
        ├── withdraw.html
        ├── deposit.html
        ├── transfer.html
        ├── change_pin.html
        └── mini_statement.html
static/
├── css/atm.css               # Full design system + animations
└── js/atm.js                 # Live clock, validation, animations
```

## 6. Security notes (Module 27, taken seriously)

- **PINs are hashed** with Django's `make_password`/`check_password` —
  never stored or logged as plain text.
- **Balances use `DecimalField`**, never floats, so money never suffers
  floating-point rounding errors.
- **Transfers are atomic**: `transaction.atomic()` with row-level locking
  (`select_for_update`) means a transfer either fully completes or fully
  rolls back — accounts can never end up half-updated.
- **Generic login errors**: a wrong card and a wrong PIN return the same
  message, so an attacker can't tell which one was wrong.
- **Lockout**: 3 failed PIN attempts blocks the card, even if a later
  attempt uses the correct PIN.
- **Session auto-expiry**: sessions time out after 5 minutes of
  inactivity (`SESSION_COOKIE_AGE` in `settings.py`) and are fully
  cleared on logout.
- **CSRF protection** is on by default for every form.
- All database access goes through the Django ORM, which parameterizes
  queries and avoids SQL injection.

## 7. Viewing the data directly

```bash
python manage.py createsuperuser
python manage.py runserver
# then visit http://127.0.0.1:8000/admin/
```

## 8. Customizing

- **Bank name / branding**: edit the `.bank-mark` block in
  `atm_app/templates/atm_app/base.html`.
- **Colors, fonts, animation timing**: everything is defined as CSS
  variables at the top of `static/css/atm.css`.
- **Withdrawal limit**: `Account.daily_withdrawal_limit` (per-account, so
  it's easy to demo different limits per customer).
- **Switch to MySQL/PostgreSQL**: change the `DATABASES` block in
  `atm_system/settings.py` to the appropriate backend and install the
  matching driver (`mysqlclient` or `psycopg`) — no other code changes
  needed, since all queries go through the Django ORM.

## 9. Before deploying anywhere real

This project is configured for **local development and training/demo
purposes**: `DEBUG = True` and the `SECRET_KEY` in `settings.py` are not
production-safe. If you ever deploy this beyond your own machine, set
`DEBUG = False`, move the secret key to an environment variable, set
`ALLOWED_HOSTS`, and put it behind a real WSGI/ASGI server (gunicorn,
uwsgi, etc.) instead of `manage.py runserver`.
