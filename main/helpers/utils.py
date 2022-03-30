import logging
import math
from os import remove
import re
import json
from main.helpers.loan_helpers import *
from main.helpers.email_helper import insufficent_bal
from django.conf import settings
from statistics import mean
import main.models
from datetime import datetime, date
import uuid
import random
from main.helpers.bankdb import bankdb
from main.helpers.sendemail import woven_insufficient
from main.helpers.loan_disk_helpers import borrower_api_call, loan_disk_update_borrower
from main.helpers.date_helpers import *
from main.helpers.sendemail import *
import requests
import pytz

from pay.models import USSD_Constant_Variable, constant_env

get_constant = constant_env()


class utility:
    one_month_interest = 1.33
    two_month_interest = 1.45
    # deductible fees
    credit_assessment = 200
    processing_fee = 1  # one percent
    remita_call_charge = 120
    bvn_check_giro = 50
    processing_fee_giro = 1  # one percent
    remita_collection = 5.8  # 5.8 percent
    bank_charges = 80

    def percet_calculator(num, value):
        str_val = str(value)
        val_str = str(str_val.replace("N", "").replace(",", ""))
        val = int(val_str) * (num / 100)
        return val

    def currency_formatter(amount, round=True):

        if round:
            currency = f"{rounding_up(amount)}"
            currency = "N{:,}".format(int(currency))
        else:
            currency = "N{:,}".format(int(amount))

        return currency

    def one_month_repayment_calculator(self, *args):
        principal = args
        repayment_value = principal + self.percet_calculator(
            self.one_month_interest, principal
        )
        return repayment_value

    def two_month_repayment_calculator(self, principal):
        repayment_value = principal * self.percet_calculator(
            self.two_month_interest, principal
        )
        return repayment_value

    def loan_fee(self, principal):
        fee = (
            self.credit_assessment
            + self.remita_call_charge
            + self.bvn_check_giro
            + self.bank_charges
            + self.percet_calculator(self.processing_fee, principal)
            + self.percet_calculator(self.processing_fee_giro, principal)
            + self.percet_calculator(self.remita_collection, principal)
        )
        return fee

    def phone_num_pre_extractor(phone_number):
        number = None
        number = phone_number[4:] if len(phone_number) == 14 else phone_number[5:]
        new_contact = "0" + str(number)
        return new_contact

    def go_back_func(num):
        """
        use this function to take user back on ussd session
        """
        x = num.split("*")
        data = None
        while "0" in x:
            index_of_x = x.index("0")
            n_x = x.index("0") - 1
            x.pop(index_of_x)
            x.pop(n_x)
            data = "*".join(x)

        if data == None:
            data = "*".join(x)
            return data

        return data


def full_name_split(name):
    """
    This functions split and return user data in a list
    """
    names = name.split()
    return names


# constant global variable
one_month_interest = 1.33
two_month_interest = 1.45
# deductible fees
credit_assessment = 200
processing_fee = 1  # one percent
remita_call_charge = 120
bvn_check_giro = 50
processing_fee_giro = 1  # one percent
remita_collection = 5.8  # 5.8 percent
bank_charges = 80


def one_month_repayment_calculator(principal):
    num = str(principal)
    principal = num.replace("N", "")
    principal = int(principal.replace(",", ""))
    print("here's the principal we're getting and hitting us:, ", principal)
    f = principal + (principal * (0.22 * 1)) + int(loan_fee(principal))
    repayment_value = rounding_up(f)
    repayment_value = utility.currency_formatter(repayment_value)
    return repayment_value


def loan_monthly_repayment_amt(amt, dur, interest):
    interest = interest / 100
    if type(amt) == str:
        principal = amt.replace("N", "")
        principal = int(principal.replace(",", ""))

        repayment_value = ((1 + (interest * dur)) * principal) / dur
        repayment_value = utility.currency_formatter(repayment_value, False)
        return repayment_value
    elif type(amt) == int:
        principal = amt

        repayment_value = ((1 + (interest * dur)) * principal) / dur
        repayment_value = utility.currency_formatter(repayment_value, False)
        return repayment_value

    elif type(amt) == float:
        principal = amt

        repayment_value = ((1 + (interest * dur)) * principal) / dur
        repayment_value = utility.currency_formatter(repayment_value, False)
        return repayment_value


def two_loan_monthly_repayment_amt(amt, dur, interest):
    if type(amt) == str:
        principal = amt.replace("N", "")
        principal = int(principal.replace(",", ""))
        print("here's the principal we're getting and hitting us:, ", principal)
        f = principal + (principal * interest) + int(loan_fee(principal))
        frd = f / dur
        repayment_value = rounding_up(frd)
        repayment_value = utility.currency_formatter(repayment_value)
        return repayment_value


def two_month_repayment_calculator(principal):
    num = str(principal)
    principal = num.replace("N", "")
    principal = int(principal.replace(",", ""))

    two_month_interest_rate = int(constant_env().get("loan_disk_two_month_post")) / 100

    f = principal + (principal * two_month_interest_rate) + int(loan_fee(principal))
    repayment_value = rounding_up(f)
    repayment_value = utility.currency_formatter(repayment_value)
    return repayment_value


def total_loan_repayment_calculator(amt, interest, dur, round=True):
    interest = interest / 100
    principal_amt = str(amt).replace("N", "").replace(",", "")

    principal = float(principal_amt)
    repayment_value = (1 + (interest * dur)) * principal
    # repayment_value = rounding_up(repayment_value)
    repayment_value = utility.currency_formatter(repayment_value, False)
    return repayment_value


def loan_process_fee(principal):
    pi = int(principal)
    result = (processing_fee / 100) * pi
    return result


def processing_fee_giros(principal):
    pi = int(principal)
    result = (processing_fee_giro / 100) * pi
    return result


def remita_collect_fee(principal):
    pi = int(principal)
    result = (remita_collection / 100) * pi
    return result


def loan_fee(principal):
    # num = str(principal)
    # principal = num.replace("N", "")
    # principal = int(principal.replace(",", ""))
    # fee = credit_assessment + remita_call_charge + \
    #     bvn_check_giro + bank_charges + \
    #     loan_process_fee(principal) + \
    #     processing_fee_giros(principal) + \
    #     remita_collect_fee(principal)

    # fee = rounding_up(fee)
    # fee = utility.currency_formatter(fee)
    fee = 0
    return fee


def avg_salary(phone):
    from main.helpers.loan_helpers import Remita_Manager

    start_date, end_date = Time_Manipulator.get_months_before(date.today())

    average_salary = 0

    remita_manager = Remita_Manager(phone)
    data = remita_manager.salary_request()

    salaries = remita_manager.get_last_six_salaries(start_date, end_date)

    has_recent_salary = remita_manager.has_gotten_salary_in_45_days().get("response")

    if has_recent_salary == True:

        salaries = remita_manager.get_last_six_salaries(start_date, end_date)

        if len(salaries.get("amount")) >= 6:

            return {
                "amount": mean(salaries.get("amount").values()),
                "message": "Ok",
                "account number": data.get("accountNumber"),
            }

        else:
            remita_manager = Remita_Manager(phone)

            salary_list = remita_manager.check_salaries_in_165_days()

            if len(salary_list) > 4:

                average_salary = mean(salary_list)

                return {"amount": average_salary, "message": "ok"}
            else:

                return {"amount": 0, "message": "Not enough salaries in past 165 days"}
    else:
        return {
            "amount": average_salary,
            "message": "No salaries in past 45 days",
            "account number": data.get("accountNumber"),
        }


def get_sum_active_loans_from_remita_v1(phone):
    from main.helpers.loan_helpers import Remita_Manager

    total_active_loans = Remita_Manager(phone).get_total_active_loans()

    return total_active_loans


def cal_interest(i, p):
    """
    This function returns interest of a loan
    """
    if type(p) == str:
        value = p.replace("N", "").replace(",", "")
        data = i * int(value)
        return data

    elif type(p) == int:
        # value = p.replace("N", "").replace(",", "")
        data = i * int(p)
        return data


def remita_eligibility_check_v2(phone):
    """
    This function checks users eligibiity offer on remita using their phone
    number
    """

    interest = 1.33
    average_salary_response = avg_salary(phone=phone)
    loan_response = get_sum_active_loans_from_remita_v1(phone=phone)
    eligible_amount = 0

    print(average_salary_response)

    if average_salary_response.get("amount"):
        if loan_response.get("amount") >= 0:

            remainder_after_deductions = average_salary_response.get(
                "amount"
            ) - loan_response.get("amount")
            eligible_amount = rounding_up(
                max([rounding_up(remainder_after_deductions), 0]) * 0.85
            )
            loan_offer = eligible_amount / interest
            eligible_amount = loan_offer

    if average_salary_response.get("amount") > 0 and eligible_amount < 1:

        print("this  0 and eligible_amount < 1 going")

        return {
            "eligible_amount": eligible_amount,
            "message": f"{average_salary_response.get('message')}, {'Unable to grant you loan'}",
            "account number": average_salary_response.get("accountNumber"),
            "name": loan_response.get("user"),
            "ministry": loan_response.get("ministry"),
        }
    else:
        print(">>>>>>>>>>>>>>>>>")
        print("work in Jesus name")
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>")
        return {
            "eligible_amount": eligible_amount,
            "message": f"{average_salary_response.get('message')}, {loan_response.get('message')}",
            "account number": average_salary_response.get("accountNumber"),
            "name": loan_response.get("user"),
            "ministry": loan_response.get("ministry"),
        }


def send_eligible_sms(user, amount, phone):
    """
    This function sends sms to all eligible customers, telling them the amount that they're
    eligible for !!
    """

    currency = f"{math.floor(amount)}"
    currency = "N{:,}".format(int(currency))
    phone_num = phone[1:]
    phone_num = f"234{phone_num}"

    url = "https://whispersms.xyz//whisper/send_message/"
    senders_id = ""
    payload = json.dumps(
        {
            "contacts": f"{phone_num}",
            "sender_id": f"{senders_id}",
            "message": f"Hello {user}\n\nDo you know that you're eligible for {currency}",
            "send_date": f"{datetime.datetime.now().date()}",
            "priority_route": False,
            "campaign_name": "Promotion 1",
        }
    )
    headers = {
        "Authorization": f"Api_key{settings.WHISPER_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text


def woven_payment_disbursment(**args):
    """
    This function disburs payment using woven gateway

    """
    import logging

    logging.basicConfig(filename="test.log", level=logging.DEBUG)
    logging.debug("when payment is initiated: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")

    logging.debug(
        f"when payment is initiated: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< {args}"
    )

    url = "https://api.woven.finance/v2/api/payouts/request?command=initiate"

    data = args
    # acc_name = str(data["beneficiary_account_name"].replace("[","").replace("]", "").replace("(", "").replace(")","")).replace('"', "")
    dfw = f'{data["beneficiary_account_name"]}'
    acc_name = "".join(e for e in dfw if e.isalnum() or e == " ")

    payload = json.dumps(
        {
            "source_account": settings.WOVEN_SOURCE_ACCOUNT,
            "PIN": settings.WOVEN_PAYMENT_PIN,
            "beneficiary_account_name": acc_name,
            "beneficiary_nuban": data["beneficiary_nuban"],
            "beneficiary_bank_code": data["beneficiary_bank_code"],
            "bank_code_scheme": data["bank_code_scheme"],
            "currency_code": data["currency_code"],
            "narration": data["narration"],
            "callback_url": settings.WOVEN_CALL_BACK,
            "reference": data["reference"],
            "amount": data["amount"],
        }
    )

    # main.models.Woven_payout_payload.objects.create(
    #     payload = payload
    # )

    logging.debug(f"woven payload: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<{payload}")

    headers = {
        "api_secret": f"{settings.WOVEN_API_SECRET}",
        "requestId": f"{data['request_id']}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    res = json.loads(response.text)

    try:
        if (
            res["status"] == "success"
            or res["status"] == "SUCCESS"
            or res["status"] == "Success"
        ):
            logging.debug(f">>>>>>>>>>>>>>>>>>>>>> after payement {res}")
            trans = main.models.Transaction.objects.filter(
                ref_id=res["data"]["payout_reference"]
            ).last()
            trans.payment_payload = payload
            trans.save()
            logging.debug(
                f">>>>>>>>>>>>>>>>>>>>>> nothing is wrong {res['data']['unique_reference']}"
            )
            logging.debug(f">>>>>>>>>>>>>>>>>>>>>> filtered transactions {trans}")
            trans.source_ref = res["data"]["unique_reference"]
            trans.updated_at = datetime.now()
            trans.save()

            return None

        elif (
            res["status"] == "failed"
            or res["status"] == "FAILED"
            or res["status"] == "Failed"
        ):
            trans = main.models.Transaction.objects.filter(
                ref_id=res["data"]["payout_reference"]
            ).last()

            trans.source_ref = res["data"]["unique_reference"]
            trans.updated_at = datetime.now()
            trans.save()

            trans.source_ref = res["data"]["unique_reference"]
            trans.woven_payout_status = "FAILED"
            trans.updated_at = datetime.now()
            trans.save()
            return None

        elif (
            res["status"] == "pending"
            or res["status"] == "PENDING"
            or res["status"] == "Pending"
        ):
            trans = main.models.Transaction.objects.filter(
                ref_id=res["data"]["payout_reference"]
            ).last()

            trans.source_ref = res["data"]["unique_reference"]
            trans.woven_payout_status = "PENDING"
            trans.updated_at = datetime.now()
            trans.save()

            return None

        else:
            trans = main.models.Transaction.objects.filter(
                ref_id=res["data"]["payout_reference"]
            ).last()

            trans.source_ref = res["data"]["unique_reference"]
            trans.updated_at = datetime.now()
            trans.save()

    except KeyError:
        return None

    except Exception as e:
        logging.debug(f"error: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<{e}")


def woven_payment_verification(ref_id):
    import requests

    PAYMENT_REFERENCE_KEY = "unique_reference"
    SINGLE_PAYOUT_URL = "https://api.woven.finance/v2/api/transactions?"
    # PAYMENT_REFERENCE_KEY="payout_reference"

    url = f"{SINGLE_PAYOUT_URL}{PAYMENT_REFERENCE_KEY}={ref_id}"

    payload = {}
    headers = {"api_secret": f"{settings.WOVEN_API_SECRET}"}

    response = requests.request("GET", url, headers=headers, data=payload)

    data = response.text
    return data


def woven_list_trans_filter(ref_id):

    print(ref_id)

    PAYMENT_REFERENCE_KEY = "reference"
    LIST_PAYOUT_URL = "https://api.woven.finance/v2/api/merchant/payouts?"
    # PAYMENT_REFERENCE_KEY="payout_reference"

    url = f"{LIST_PAYOUT_URL}{PAYMENT_REFERENCE_KEY}={ref_id}"

    payload = {}
    headers = {"api_secret": f"{settings.WOVEN_API_SECRET}"}

    print(f"here's the url \n\n\n\n\n {url} \n\n\n\n\n {headers} \n\n\n\n\n")

    response = requests.request("GET", url, headers=headers, data=payload)

    data = response.text
    return data


def hash_val(self, raw_val, mode="512"):

    if mode == "512":

        enc = hashlib.sha512(raw_val.encode())

        return enc.hexdigest()

    elif mode == "md5":

        enc = hashlib.md5(raw_val.encode())

        return enc.hexdigest()


def post_loan_to_loandisk(**args):

    payload_data = args

    url = f"https://api-main.loandisk.com/{settings.LOAN_DISK_PUBLICK_KEY}/{settings.LOAN_DISK_BRANCH_ID}/loan"
    payload = json.dumps(
        {
            "loan_product_id": f"{payload_data['loan_product_id']}",
            "borrower_id": f"{payload_data['borrower_id']}",
            "loan_application_id": f"{payload_data['loan_application_id']}",
            "loan_disbursed_by_id": f"{payload_data['loan_disbursed_by_id']}",
            "loan_principal_amount": payload_data["loan_principal_amount"],
            "loan_released_date": f"{payload_data['loan_released_date']}",
            "loan_interest_method": f"{payload_data['loan_interest_method']}",
            "loan_interest_type": f"{payload_data['loan_interest_type']}",
            "loan_interest_period": f"{payload_data['loan_interest_period']}",
            "loan_interest": payload_data["loan_interest"],
            "loan_duration_period": f"{payload_data['loan_duration_period']}",
            "loan_duration": payload_data["loan_duration"],
            "loan_payment_scheme_id": f"{payload_data['loan_payment_scheme_id']}",
            "loan_num_of_repayments": payload_data["loan_num_of_repayments"],
            "loan_decimal_places": f"{payload_data['loan_decimal_places']}",
            "loan_status_id": f"{payload_data['loan_status_id']}",
            "custom_field_4361": f"{payload_data['custom_field_4361']}",
            "custom_field_5262": f"{payload_data['custom_field_5262']}",
            "custom_field_4181": f"{payload_data['custom_field_4181']}",
            "custom_field_4178": f"{payload_data['custom_field_4178']}",
            "custom_field_5261": f"{payload_data['custom_field_5261']}",
            "loan_fee_id_2746": payload_data["loan_fee_id_2746"],
            "loan_fee_id_3915": payload_data["loan_fee_id_3915"],
            "loan_fee_id_4002": payload_data["loan_fee_id_4002"],
            "loan_fee_id_4003": payload_data["loan_fee_id_4003"],
            "loan_fee_id_4004": payload_data["loan_fee_id_4004"],
            "loan_fee_id_4005": payload_data["loan_fee_id_4005"],
            "loan_fee_id_4006": payload_data["loan_fee_id_4006"],
            "custom_field_4385": f"{payload_data['custom_field_4385']}",
            "custom_field_6363": f"{payload_data['custom_field_6363']}",
            "custom_field_4219": f"{payload_data['custom_field_4219']}",
            "custom_field_4221": f"{payload_data['custom_field_4221']}",
            "loan_id": f"{payload_data['loan_id']}",
            "custom_field_11516": f"{payload_data['custom_field_11516']}",
            "custom_field_11515": f"{payload_data['custom_field_11515']}",
            "custom_field_11517": f"{payload_data['custom_field_11517']}",
            "custom_field_11518": f"{payload_data['custom_field_11518']}",
        }
    )
    headers = {
        "Authorization": "Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867",
        "Content-Type": "application/json",
    }

    response = requests.request("PUT", url, headers=headers, data=payload)
    print("put request for loan disk>>>>>>>>>>>>>>>>", response.text)
    return response.text


def retry_sms():
    """
    This function sends sms to customer that thier transaction has failed
    """
    date_formate = datetime.now().date()
    date_formate = datetime.strptime(f"{date_formate}", "%Y-%m-%d").strftime("%d-%m-%Y")

    import requests
    import json

    url = "{{baseurl}}/whisper/send_message/"

    payload = json.dumps(
        {
            "contacts": ["2348031346306", "2348031346306"],
            "sender_id": "LIBERTY",
            "message": "Hello\n\n Disbursement from Libertytech to your account failed54555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555556ewe3wq",
            "send_date": "30-12-2021 00:00",
            "priority_route": False,
            "campaign_name": "Promotion 1",
        }
    )
    headers = {
        "Authorization": "Api_key{{api-key}}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


def remita_demo_data(phone):
    data = [
        {
            "name": "Giwa Edmund",
            "phone": "08142392255",
            "bvn_no": "238942778474",
            "account_number": "2120978948",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "033",
        },
        {
            "name": "Idris Fatai",
            "phone": "08133828790",
            "bvn_no": "238942778474",
            "account_number": "0154365278",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "058",
        },
        {
            "name": "Taiwo Lawal",
            "phone": "08142392255",
            "bvn_no": "238942778474",
            "account_number": "2120978948",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "070",
        },
        {
            "name": "Babatunde Ebitanmi",
            "phone": "08186311099",
            "bvn_no": "238942778474",
            "account_number": "0111865000",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "058",
        },
        {
            "name": "Johnson Adeekolade",
            "phone": "07039583538",
            "bvn_no": "238942778474",
            "account_number": "0113121154",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "058",
        },
        {
            "name": "Oluseye Awoyemi",
            "phone": "08187138160",
            "bvn_no": "238942778474",
            "account_number": "0121435531",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "032",
        },
        {
            "name": "Johnson Abe",
            "phone": "08060290218",
            "bvn_no": "238942778474",
            "account_number": "0071960215",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "232",
        },
        {
            "name": "Faith Oni",
            "phone": "07084252217",
            "bvn_no": "238942778474",
            "account_number": "4141205019",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "050",
        },
        {
            "name": "Basirat Jaiyeola",
            "phone": "08103248171",
            "bvn_no": "238942778474",
            "account_number": "0225935456",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "058",
        },
        {
            "name": "Omololu Taiwo",
            "phone": "08035903088",
            "bvn_no": "238942778474",
            "account_number": "0470679037",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "214",
        },
        {
            "name": "Alaba Adesanya",
            "phone": "07060848123",
            "bvn_no": "238942778474",
            "account_number": "2152558851",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "033",
        },
        {
            "name": "Toluwalope Coast",
            "phone": "08132393438",
            "bvn_no": "238942778474",
            "account_number": "0137053309",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "058",
        },
        {
            "name": "Odunlami Francis",
            "phone": "07060900294",
            "bvn_no": "238942778474",
            "account_number": "2178489337",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "057",
        },
        {
            "name": "Oluwasegun Oloyede",
            "phone": "08102751337",
            "bvn_no": "238942778474",
            "account_number": "2103109695",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "033",
        },
        {
            "name": "Yetunde Igbene",
            "phone": "08051832508",
            "bvn_no": "238942778474",
            "account_number": "0128509930",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "058",
        },
        {
            "name": "Oritsetinmeyin Igbene",
            "phone": "09069090865",
            "bvn_no": "238942778474",
            "account_number": "1006448463",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 10000,
            "bank_code": "057",
        },
        {
            "name": "Eko Offem",
            "phone": "08117849057",
            "bvn_no": "238942778474",
            "account_number": "3022114306",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "011",
        },
        {
            "name": "Aishat Ibrahim",
            "phone": "08027742869",
            "bvn_no": "238942778474",
            "account_number": "33710849",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "221",
        },
        {
            "name": "Oluwafemi Kehinde",
            "phone": "08060164419",
            "bvn_no": "238942778474",
            "account_number": "0072514835",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "232",
        },
        {
            "name": "Abiodun Bello",
            "phone": "08020711088",
            "bvn_no": "238942778474",
            "account_number": "2086344829",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "057",
        },
        {
            "name": "Abisola Oluyole",
            "phone": "08068978064",
            "bvn_no": "238942778474",
            "account_number": "0109958191",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "058",
        },
        {
            "name": "Aregbesola Mohammed",
            "phone": "08022037097",
            "bvn_no": "238942778474",
            "account_number": "0114975505",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "058",
        },
        {
            "name": "Joseph Chinedu",
            "phone": "07039115243",
            "bvn_no": "238942778474",
            "account_number": "0094570183",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "044",
        },
        {
            "name": "Joseph Chinedu",
            "phone": "09018896698",
            "bvn_no": "238942778474",
            "account_number": "0094570183",
            "companyName": "Liberty tech",
            "borrower_remita_id": "",
            "eligible_amount": 5000,
            "bank_code": "044",
        },
    ]

    ran_data = ""
    digits = "0123456789"
    for i in range(0, 8):
        ran_data += random.choice(digits)

    for i in data:
        if i["phone"] == phone:
            borrower_queryset = main.models.Borrower.objects.filter(
                borrower_phoneNumber=phone
            ).last()
            names = full_name_split(i["name"])
            first_name = names[0] if len(names) > 0 else ""
            last_name = names[1] if len(names) > 1 else ""
            middle_name = names[2] if len(names) > 2 else ""
            bank_name = nip_bank_search(i["bank_code"])
            if borrower_queryset:

                # logging.debug(f"user bank name {bank_name['name']}")
                # borrower_queryset.borrower_remita_id = f"r_{ran_data}",
                # borrower_queryset.borrower_phoneNumber = i['phone'],
                # borrower_queryset.borrower_authorisationCode = "6038b422660f79dccbebe66d5f1a9557",
                # borrower_queryset.borrower_fullname = i.get('name'),
                # borrower_queryset.acct_no = i['account_number'],
                # borrower_queryset.bank_code = i['bank_code'],
                # borrower_queryset.borrower_lastname = last_name,
                # borrower_queryset.borrower_firstname = first_name,
                # borrower_queryset.bvn_no = i['bvn_no'],
                # borrower_queryset.borrower_middlename = middle_name,
                # borrower_queryset.save()
                # borrower_queryset.update(
                #     borrower_remita_id = f"r_{ran_data}",
                #     borrower_phoneNumber = i['phone'],
                #     borrower_authorisationCode = "6038b422660f79dccbebe66d5f1a9557",
                #     borrower_fullname = i.get('name'),
                #     acct_no = i['account_number'],
                #     bank_code = i['bank_code'],
                #     borrower_lastname = last_name,
                #     borrower_firstname = first_name,
                #     bvn_no = i['bvn_no'],
                #     borrower_middlename = middle_name,

                # )

                payload = {
                    "borrower_country": "NG",
                    "borrower_fullname": i["name"],
                    "borrower_firstname": first_name,
                    "borrower_lastname": last_name,
                    "custom_field_5854": middle_name,
                    "borrower_business_name": i["companyName"],
                    "borrower_unique_number": f"{ran_data}",
                    "borrower_gender": "",
                    "borrower_title": "",
                    "borrower_mobile": phone,
                    "borrower_email": "",
                    "custom_field_5037": i["bvn_no"],
                    "custom_field_4220": i["account_number"],
                    "custom_field_4222": i["bank_code"],
                    "custom_field_4221": bank_name["name"],
                    "borrower_id": borrower_queryset.borrower_id,
                }

                # loans_diskdata = loan_disk_update_borrower(**payload)
                # logging.debug(f"Here's the loand disk update response {loans_diskdata}")
                # loans_diskdata = json.loads(loans_diskdata)
                # print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                # print(loans_diskdata)
                # print("user loan disk id", loans_diskdata['response']['borrower_id'])

                # logging.debug(f"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< got here but village people came through")

                return {"eligible_amount": i["eligible_amount"], "message": ""}

            else:
                payload = {
                    "borrower_country": "NG",
                    "borrower_fullname": i["name"],
                    "borrower_firstname": first_name,
                    "borrower_lastname": last_name,
                    "custom_field_5854": middle_name,
                    "borrower_business_name": i["companyName"],
                    "borrower_unique_number": f"{ran_data}",
                    "borrower_gender": "",
                    "borrower_title": "",
                    "borrower_mobile": phone,
                    "borrower_email": "",
                    "custom_field_5037": i["bvn_no"],
                    "custom_field_4220": i["account_number"],
                    "custom_field_4222": i["bank_code"],
                    "custom_field_4221": bank_name["name"],
                }

                loans_diskdata = borrower_api_call(**payload)
                loans_diskdata = json.loads(loans_diskdata)
                print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                print(loans_diskdata)
                print("user loan disk id", loans_diskdata["response"]["borrower_id"])

                print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")

                main.models.Borrower.objects.create(
                    borrower_remita_id=f"r_{ran_data}",
                    borrower_phoneNumber=i["phone"],
                    borrower_authorisationCode="6038b422660f79dccbebe66d5f1a9557",
                    borrower_fullname=i["name"],
                    acct_no=i["account_number"],
                    bank_code=i["bank_code"],
                    borrower_lastname=last_name,
                    borrower_firstname=first_name,
                    bvn_no=i["bvn_no"],
                    borrower_middlename=middle_name,
                    borrower_id=loans_diskdata["response"]["borrower_id"],
                    bank_name=bank_name["name"],
                )
                return {"eligible_amount": i["eligible_amount"], "message": ""}


def nip_bank_search(num):
    """
    This function handles bank search using cbn bank code
    """
    num_data = str(num)

    bank = bankdb()
    for i in bank:
        if i["cbn_code"] == num_data:
            data = {
                "bank_code": i["bank_code"],
                "cbn_code": i["cbn_code"],
                "name": i["name"],
                "bank_short_name": i["bank_short_name"],
                "disabled_for_vnuban": i["disabled_for_vnuban"],
            }
            return data


def currency_remover(strtext):
    print(strtext)
    print(
        strtext.replace("N", "")
        .replace(",", "")
        .replace("'", "")
        .replace("{", "")
        .replace("}", "")
    )
    amount = (
        strtext.replace("N", "")
        .replace(",", "")
        .replace("'", "")
        .replace("{", "")
        .replace("}", "")
    )
    return int(amount)


def loan_disk_date_format():
    """
    This function handles form
    """

    date_formate = datetime.now().date()
    date_formate = datetime.strptime(f"{date_formate}", "%Y-%m-%d").strftime("%d/%m/%Y")
    return date_formate


def django_db_date_format(date_text):
    _date = date_text.split(" ")
    _date[-1] = _date[-1][:8]
    _date = " ".join(_date)
    date_formate = datetime.strptime(_date, "%d-%m-%Y %H:%M:%S").strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return date_formate


def rounding_up(value):

    if type(value) == float:
        new_value = int(math.ceil(value / 100.0)) * 100
        return new_value
    elif type(value) == str:
        value = int(value.replace("N", "").replace(",", ""))
        new_value = int(math.ceil(value / 100.0)) * 100
        return new_value

    elif type(value) == int:
        new_value = int(math.ceil(value / 100.0)) * 100
        return new_value


def percentage_loan_take(eligible_amt, loan_amt, ref_id, phone):
    get_loan = main.models.Loan.objects.filter(
        phoneNumber=phone, payement_reference=ref_id
    ).last()

    if get_loan:
        if get_loan.numberOfRepayments == 1:
            loan_monthly_interets = constant_env().get("loan_disk_one_month_interest")

        elif get_loan.numberOfRepayments == 2:
            loan_monthly_interets = constant_env().get("loan_disk_two_month_post")

        elif get_loan.numberOfRepayments == 3:
            loan_monthly_interets = constant_env().get("loan_disk_three_month_interets")

        elif get_loan.numberOfRepayments == 4:
            loan_monthly_interets = constant_env().get("loan_disk_four_month_interets")

        elif get_loan.numberOfRepayments == 5:
            loan_monthly_interets = constant_env().get("loan_disk_four_month_interets")

        elif get_loan.numberOfRepayments == 6:
            loan_monthly_interets = constant_env().get("loan_disk_four_month_interets")

        elif get_loan.numberOfRepayments == 7:
            loan_monthly_interets = constant_env().get("loan_disk_seven_month_interets")

        elif get_loan.numberOfRepayments == 8:
            loan_monthly_interets = constant_env().get("loan_disk_eight_month_interets")

        eligible_amt = rounding_up(eligible_amt)
        loan_amt = int(loan_amt)

        loan_monthly_repayment_amount = loan_monthly_repayment_amt(
            loan_amt, get_loan.numberOfRepayments, loan_monthly_interets
        )

        monthly_repyament = (
            str(loan_monthly_repayment_amount).replace("N", "").replace(",", "")
        )

        if int(monthly_repyament) <= int(eligible_amt):
            get_loan.eligible_for_top_up = True
            get_loan.topup_eligible_amount = int(eligible_amt) - int(monthly_repyament)
            get_loan.save()

        else:
            get_loan.eligible_for_top_up = False
            get_loan.save()


def diff_in_time(request_time):
    """
    This function takes datetime object and return the time difference beteen times
    """
    utc = pytz.UTC

    req_datetime = utc.localize(datetime.now())

    diff = req_datetime - request_time

    return diff.total_seconds() / 60
