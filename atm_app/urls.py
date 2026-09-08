from django.urls import path

from . import views

app_name = "atm_app"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("withdraw/", views.withdraw_view, name="withdraw"),
    path("deposit/", views.deposit_view, name="deposit"),
    path("transfer/", views.transfer_view, name="transfer"),
    path("change-pin/", views.change_pin_view, name="change_pin"),
    path("mini-statement/", views.mini_statement_view, name="mini_statement"),
    path("logout/", views.logout_view, name="logout"),
]
