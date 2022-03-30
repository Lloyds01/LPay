from django.urls import path
from .views import (
    On_boarding_view,
    Loan_payout,
    Loan_payout_verification,
    Web_session_decline,
    Resend_otp,
    Payment_disburse,
)

app_name = "app"


urlpatterns = [
    path("", On_boarding_view.as_view()),
    path("payout/", Loan_payout.as_view()),
    path("payout_verify/", Loan_payout_verification.as_view()),
    path("session_decline/", Web_session_decline.as_view()),
    path("resend_otp/", Resend_otp.as_view()),
    path("payment_disburse/", Payment_disburse.as_view()),
]
