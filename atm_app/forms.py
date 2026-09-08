from decimal import Decimal

from django import forms


class LoginForm(forms.Form):
    """MODULE 4 / 13: card number + PIN entry."""

    card_number = forms.CharField(
        max_length=19,
        min_length=16,
        widget=forms.TextInput(attrs={
            "class": "atm-input", "placeholder": "1234 5678 9012 3456",
            "inputmode": "numeric", "autocomplete": "off", "autofocus": True,
            "data-card-number": "true",
        }),
    )
    pin = forms.CharField(
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(attrs={
            "class": "atm-input atm-pin", "placeholder": "••••",
            "inputmode": "numeric", "autocomplete": "off",
        }),
    )

    def clean_card_number(self):
        value = self.cleaned_data["card_number"].replace(" ", "")
        if not value.isdigit() or len(value) != 16:
            raise forms.ValidationError("Card number must contain 16 digits.")
        return value


    def clean_pin(self):
        value = self.cleaned_data["pin"]
        if not value.isdigit():
            raise forms.ValidationError("PIN must be numeric.")
        return value


class AmountForm(forms.Form):
    """Shared by Withdraw and Deposit (MODULE 16 / 18)."""

    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("1"),
        widget=forms.NumberInput(attrs={
            "class": "atm-input", "placeholder": "Enter amount", "step": "100", "min": "1",
        }),
    )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


class TransferForm(AmountForm):
    """MODULE 19: fund transfer needs a validated receiver account too."""

    beneficiary_account = forms.CharField(
        max_length=12,
        widget=forms.TextInput(attrs={"class": "atm-input", "placeholder": "Receiver account number"}),
    )


class ChangePinForm(forms.Form):
    """MODULE 20: current PIN + new PIN + confirmation."""

    current_pin = forms.CharField(
        min_length=4, max_length=4,
        widget=forms.PasswordInput(attrs={"class": "atm-input atm-pin", "placeholder": "Current PIN"}),
    )
    new_pin = forms.CharField(
        min_length=4, max_length=4,
        widget=forms.PasswordInput(attrs={"class": "atm-input atm-pin", "placeholder": "New PIN"}),
    )
    confirm_pin = forms.CharField(
        min_length=4, max_length=4,
        widget=forms.PasswordInput(attrs={"class": "atm-input atm-pin", "placeholder": "Confirm new PIN"}),
    )

    def clean(self):
        cleaned = super().clean()
        new_pin, confirm_pin = cleaned.get("new_pin"), cleaned.get("confirm_pin")
        if new_pin and not new_pin.isdigit():
            self.add_error("new_pin", "PIN must be numeric.")
        if new_pin and confirm_pin and new_pin != confirm_pin:
            self.add_error("confirm_pin", "New PIN and confirmation do not match.")
        return cleaned


class RegisterForm(forms.Form):
    """New Customer Registration form."""

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "atm-input", "placeholder": "Full Name", "autofocus": True}),
    )
    phone = forms.CharField(
        max_length=10,
        min_length=10,
        widget=forms.TextInput(attrs={"class": "atm-input", "placeholder": "10-digit Mobile Number", "inputmode": "numeric"}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "atm-input", "placeholder": "Email Address (optional)"}),
    )
    account_type = forms.ChoiceField(
        choices=[("SAVINGS", "Savings Account"), ("CURRENT", "Current Account")],
        widget=forms.Select(attrs={"class": "atm-input"}),
    )
    initial_deposit = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("500.00"),
        initial=Decimal("1000.00"),
        widget=forms.NumberInput(attrs={"class": "atm-input", "placeholder": "Initial Deposit (min ₹500)", "step": "100"}),
    )
    pin = forms.CharField(
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(attrs={"class": "atm-input atm-pin", "placeholder": "4-digit PIN", "inputmode": "numeric"}),
    )
    confirm_pin = forms.CharField(
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput(attrs={"class": "atm-input atm-pin", "placeholder": "Confirm 4-digit PIN", "inputmode": "numeric"}),
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain digits only.")
        return phone

    def clean_pin(self):
        pin = self.cleaned_data["pin"]
        if not pin.isdigit():
            raise forms.ValidationError("PIN must be 4 numeric digits.")
        return pin

    def clean(self):
        cleaned = super().clean()
        pin = cleaned.get("pin")
        confirm_pin = cleaned.get("confirm_pin")
        if pin and confirm_pin and pin != confirm_pin:
            self.add_error("confirm_pin", "PIN and Confirmation PIN do not match.")
        return cleaned

