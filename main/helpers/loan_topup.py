from main.models import Loan
from datetime import datetime

from pay.models import constant_env

# get_constant = constant_env()


def topup_view(phone):
    if constant_env().get("topup_anytime") == True:
        data = {"eligible": True, "message": ""}
        return data

    elif constant_env().get("topup_monthly") == True:
        get_user_loan = Loan.objects.filter(loan_status=True, phoneNumber=phone).last()
        if get_user_loan:
            if get_user_loan.is_over_30_days():
                data = {"eligible": True, "message": ""}
                return data

            else:
                if get_user_loan.loanAmount >= get_user_loan.elgible_amount:
                    data = {
                        "eligible": False,
                        "message": "END Sorry, you're not eligible for top-up at the moment",
                    }
                    return data

                else:
                    data = {"eligible": True, "message": ""}
                    return data

    else:
        get_user_loan = Loan.objects.filter(loan_status=True, phoneNumber=phone)
        if get_user_loan:
            for loan in get_user_loan:
                days_diff = datetime.today().date() - loan.dateOfDisbursement.date()

                if days_diff.days > 30:
                    if (
                        loan.paid_amount == 0.0
                        or loan.paid_amount == 0
                        or loan.paid_amount == None
                        or loan.paid_amount == ""
                    ):
                        data = {
                            "eligible": False,
                            "message": "END Sorry, you're not eligible for top-up at the moment",
                        }
                        return data

                    else:
                        data = {"eligible": True, "message": ""}
                        return data

                else:

                    data = {"eligible": True, "message": ""}
                    return data
        else:
            data = {"eligible": True, "message": ""}
            return data


def active_loan_check(phone):
    all_user_loans = Loan.objects.filter(loan_status=True, phoneNumber=phone)
    if all_user_loans:
        data = {"status": True, "message": "END sorry you've an active loan with us!"}
    else:
        processing_loans = Loan.objects.filter(
            loan_status=False, phoneNumber=phone, loan_comment="processing"
        )
        if processing_loans:
            data = {
                "status": True,
                "message": "END sorry you've an active loan with us!",
            }
        else:
            data = {"status": False, "message": ""}

    return data
