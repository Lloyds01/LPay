import requests
import json
from django.conf import settings
import logging
from dateutil.tz import tzlocal
from main.helpers.utils import utility, remita_demo_data
import logging
import datetime
import main
from pay.models import (
    Retargeting_message_24_hours,
    Retargeting_message_three_days,
    Retargeting_message_fourteen_days,
    Retargeting_message_twenty_eight_days,
)

logging.basicConfig(filename="test.log", level=logging.DEBUG)


def sub_num(num):
    n = num[1:]
    n = "234" + str(n)
    return n


def send_retry_sms(num):
    url = "https://whispersms.xyz/whisper/send_message/"

    date_formate = datetime.datetime.now().date()
    date_formate = datetime.datetime.strptime(f"{date_formate}", "%Y-%m-%d").strftime(
        "%d-%m-%Y"
    )
    usr_phone = sub_num(num)

    payload = json.dumps(
        {
            "receiver": f"{usr_phone}",
            "template": settings.RETRY_SMS,
            "place_holders": {},
        }
    )

    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    requests.request("POST", url, headers=headers, data=payload)


def send_loan_processing_sms(num, username):
    url = "https://whispersms.xyz/api/send_message/"
    usr_phone = sub_num(num)

    payload = json.dumps(
        {
            "receiver": f"{usr_phone}",
            "template": settings.LOAN_PROCESSING_SMS,
            "place_holders": {"username": f"{username}"},
        }
    )

    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    res = requests.request("POST", url, headers=headers, data=payload)
    res = json.loads(res.text)
    


def send_retry_loan_sms(num, username):
    url = "https://whispersms.xyz/api/send_message/"

    usr_phone = sub_num(num)

    payload = json.dumps(
        {
            "receiver": f"{usr_phone}",
            "template": settings.FAILED_DISBURSEMENT_RETRY_SMS,
            "place_holders": {},
        }
    )
    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    res = requests.request("POST", url, headers=headers, data=payload)
    res = json.loads(res.text)


# sms ```` transaction route message
def loan_processing(num, username):
    usr_phone = sub_num(num)

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{usr_phone}",
            "template": f"{settings.LIBERTY_USSD_LOAN_PROCESSING_TEMPLATE_ID}",
            "place_holders": {"name": f"{username}"},
        }
    )
    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


def loan_bal_check(num, username, amt):
    usr_phone = sub_num(num)

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{usr_phone}",
            "template": f"{settings.LIBERTY_USSD_LOAN_BALANCE}",
            "place_holders": {"name": f"{username}", "loan_amount": f"{amt}"},
        }
    )
    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    res = json.loads(response.text)
    logging.debug(f"sms bal output >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")


def customer_retry_loan(num, username):
    usr_phone = sub_num(num)

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{usr_phone}",
            "template": f"{settings.FAILED_LOAN_DISK_RECORD}",
            "place_holders": {"name": f"{username}"},
        }
    )
    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    res = json.loads(response.text)


def contact_sms(num):
    user_phone = sub_num(num) if len(num) == 11 else num.replace("+", "")

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{user_phone}",
            "template": f"{settings.LIBERTY_ASSURED_CONTACT_INFO_TEMPLATE_ID}",
            "place_holders": {"name": "Joseph Chinedu"},
        }
    )
    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    res = json.loads(response.text)
   

def loan_eligibility_sms(num):
    usr_phone = sub_num(num)

    borrower_phone_number = utility.phone_num_pre_extractor(num)
    eligibileAmountChecker = None
    eligibileChecker = None
    eligiblechecker_error = None

    # eligibileCheckers = Borrower.get_eligible_amount(
    #     phone=borrower_phone_number)
    # eligibileAmountChecker = eligibileCheckers['eligible_amount']
    # eligibileChecker = eligibileCheckers
    # catched_.user_eligibile_amount = eligibileCheckers['eligible_amount']
    # catched_.save()

    ############### demo ####################
    logging.debug(
        f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> demmy data >>>>>>>>>>>>>>>>>>>"
    )
    eligibileCheckers = remita_demo_data(phone=borrower_phone_number)

    logging.debug(f"{eligibileCheckers}")

    logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> done getting dommy data")

    if eligibileCheckers == None:
        response = "END Sorry this product is for salary earners only !!"

    else:
        pass

    eligibileAmountChecker = eligibileCheckers["eligible_amount"]
    eligibileChecker = eligibileCheckers

    logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    check_user_loans = main.models.Loan.objects.filter(
        loan_status=True, loan_comment__iexact="open", phoneNumber=borrower_phone_number
    )
    logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> getting loan")
    count_loans = check_user_loans.count()
    logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> done counting loan gotten")

    logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> getting loan")

    if count_loans > 0:
        logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> user have active loan")
        response = "END You've an active loan"

    if eligibileAmountChecker == 0:
        if eligiblechecker_error != None:
            response = f"{eligiblechecker_error}"

        elif eligibileChecker["message"] == "Customer not found, Customer not found":

            response = "END Sorry this loan are availiable for civil servants! "

        elif eligibileChecker["message"] == "Inactive customer, Inactive customer":
            response = "END sorry unable to get salary information"

        else:
            response = "END sorry not eligible. try again later"

    else:
        logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> enteered else")
        borrower_queryset = main.models.Borrower.objects.filter(
            borrower_phoneNumber=borrower_phone_number
        ).last()
        two_month_loan_max = round(float(eligibileAmountChecker) * 2)
        two_month_loan_max = utility.currency_formatter(two_month_loan_max)
        logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> finished filteru=ing")

        url = "https://whispersms.xyz/transactional/send"

        payload = json.dumps(
            {
                "receiver": f"{usr_phone}",
                "template": f"{settings.ELIGIBLE_BORROWER}",
                "place_holders": {
                    "name": f"{borrower_queryset.borrower_firstname}",
                    "eligiblility_amout": f"{two_month_loan_max}",
                },
            }
        )
        headers = {
            "Authorization": f"Api_key {settings.WHISPER_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        res = json.loads(response.text)
        logging.debug(f"sms bal output >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")


def send_retargting_sms_with_eligible_amount(num, amount, name):
    user_phone = sub_num(num) if len(num) == 11 else num.replace("+", "")

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{user_phone}",
            "template": f"{settings.LIBERTY_ASSURED_RE_TARGETING_SMS_AFTER_24HOURS_TEMPLATE_ID}",
            "place_holders": {"username": f"{name}", "eligible_amount": f"{amount}"},
        }
    )

    print(payload)
    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    res = json.loads(response.text)

    ###### save the message in sms modle
    Retargeting_message_24_hours.objects.create(
        phone=num,
        message_template=settings.LIBERTY_ASSURED_RE_TARGETING_SMS_AFTER_24HOURS_TEMPLATE_ID,
    )
    print(res)


def send_retargting_sms(num, name, dur):
    user_phone = sub_num(num) if len(num) == 11 else num.replace("+", "")

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{user_phone}",
            "template": f"{settings.LIBERTY_ASSURED_RE_TARGET_SMS_TEMPLATE_ID}",
            "place_holders": {"username": f"{name}"},
        }
    )
    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    res = json.loads(response.text)

    if dur == 3 or dur == "3":
        Retargeting_message_three_days.objects.create(
            message_template=settings.LIBERTY_ASSURED_RE_TARGET_SMS_TEMPLATE_ID,
            phone=num,
        )

    elif dur == 14 or dur == "14":
        Retargeting_message_fourteen_days.objects.create(
            message_template=settings.LIBERTY_ASSURED_RE_TARGET_SMS_TEMPLATE_ID,
            phone=num,
        )

    elif dur == 28 or dur == "28":
        Retargeting_message_twenty_eight_days.objects.create(
            message_template=settings.LIBERTY_ASSURED_RE_TARGET_SMS_TEMPLATE_ID,
            phone=num,
        )

    logging.debug(f"sms bal output >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {res}")


def send_eligiblity_sms(num, amount, name):
    user_phone = sub_num(num) if len(num) == 11 else num.replace("+", "")

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{user_phone}",
            "template": f"{settings.LIBERTY_ASSURED_RE_TARGETING_SMS_AFTER_24HOURS_TEMPLATE_ID}",
            "place_holders": {"username": f"{name}", "eligible_amount": f"{amount}"},
        }
    )

    print(payload)
    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    res = json.loads(response.text)
    print(res)


def two_balance_sms(
    num,
    name,
    num_of_loans,
    loan_num,
    due_amt,
    total_paid_amt,
    outstanding,
    num2,
    due_amt2,
    total_paid_amt2,
    outstanding2,
):

    user_phone = sub_num(num) if len(num) == 11 else num.replace("+", "")

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{user_phone}",
            "template": f"{settings.TWO_LOAN_BALANCE}",
            "place_holders": {
                "username": f"{name}",
                "num": f"{num_of_loans}",
                "loan_num": f"{loan_num}",
                "due_amt": f"{outstanding}",
                "total_paid_amt": f"{total_paid_amt}",
                "num2": f"{num2}",
                "due_amt2": f"{outstanding2}",
                "total_paid_amt2": f"{total_paid_amt2}",
            },
        }
    )

    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text


def one_balance_sms(
    num, name, num_of_loans, loan_num, total_paid_amt, outstanding, due_amt
):

    user_phone = sub_num(num) if len(num) == 11 else num.replace("+", "")

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{user_phone}",
            "template": f"{settings.ONE_LOAN_BALANCE}",
            "place_holders": {
                "username": f"{name}",
                "num": f"{num_of_loans}",
                "loan_num": f"{loan_num}",
                "due_amt": f"{utility.currency_formatter(outstanding, False)}",
                "total_paid_amt": f"{utility.currency_formatter(total_paid_amt,False)}",
            },
        }
    )

    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text


def no_active_loan(num):

    user_phone = sub_num(num) if len(num) == 11 else num.replace("+", "")

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{user_phone}",
            "template": f"{settings.NO_ACTIVE_LOAN}",
            "place_holders": {},
        }
    )

    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text


def sms_to_correct_loan_func(num, name):

    user_phone = sub_num(num) if len(num) == 11 else num.replace("+", "")

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{user_phone}",
            "template": "d6b53358-b420-48f6-83be-7673912987ba",
            "place_holders": {"username": f"{name}"},
        }
    )

    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    try:
        return json.loads(response.text)
    except:
        return response.text


def sms_to_correct_trans_func(num):

    user_phone = sub_num(num) if len(num) == 11 else num.replace("+", "")

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{user_phone}",
            "template": "e8ca9b16-fa12-4767-acbd-37ff300b7a5d",
            "place_holders": {},
        }
    )

    headers = {
        "Authorization": f"Api_key {settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    try:
        return json.loads(response.text)
    except:
        return response.text
