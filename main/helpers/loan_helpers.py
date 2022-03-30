from cmath import inf
from rest_framework.response import Response
from django.core.checks import messages
from requests.models import Response
from rest_framework import response
from main.helpers import date_helpers, send_sms
import requests
import hashlib  # import hashlib module
import json
from dateutil.parser import parse
import pandas as pd
from functools import lru_cache
import random
import requests
import json
from main.helpers.sendemail import *
from main.models import *
import redis
import logging
import datetime
import numpy as np

logging.basicConfig(filename="test.log", level=logging.DEBUG)
from main.helpers.utils import rounding_up, utility
from main.helpers.send_sms import send_eligiblity_sms
from django.conf import settings
import main

CACHE_SALARY_MAX_AGE = 600  # AGE IN SECONDS CURRENT => 6MINS (600SECS)


def cachedproperty(func):
    """Used on methods to convert them to methods that replace themselves
    with their return value once they are called."""

    def cache(*args):
        self = args[0]  # Reference to the class who owns the method
        funcname = func.__name__
        ret_value = func(self)
        setattr(self, funcname, ret_value)  # Replace the function with its value
        return ret_value  # Return the result of the function

    return property(cache)


class Remita_Manager:

    base_url = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/salary/history/ph"
    base_url2 = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/post/loan"
    base_url3 = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/stop/loan"
    merchant_id = "4197239218"
    api_key = "QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw"
    api_token = "K3B1RmlPWjVuNFJ4VlBuWnhNWGJ2L3FiaFlqbWVaK0VhU25lWWthc3QvTGlTQU5mOFdKZjVYMzUyRjdibnJmaw=="

    def __init__(self, phone) -> None:

        self.phone = phone
        self.request_id = self.hash_val(str(datetime.datetime.now()), "md5")

    def hash_val(self, raw_val, mode="512"):

        if mode == "512":

            enc = hashlib.sha512(raw_val.encode())

            return enc.hexdigest()

        elif mode == "md5":

            enc = hashlib.md5(raw_val.encode())

            return enc.hexdigest()

    @lru_cache(maxsize=None)
    def salary_request(self):

        body = {
            "authorisationCode": self.request_id,
            "phoneNumber": self.phone,
            "authorisationChannel": "USSD",
        }

        r = redis.Redis()
        key = json.dumps(
            {
                "phoneNumber": self.phone,
                "authorisationChannel": "USSD",
            }
        )

        data = r.get(key)

        if data:

            data_dict = json.loads(r.get(key))

            age = (datetime.datetime.now().timestamp()) - (
                data_dict.get("cache_created")
            )

            if age > CACHE_SALARY_MAX_AGE:
                r.delete(key)
                pass

            else:

                return data_dict

        headers = {
            "CONTENT-TYPE": "application/json",
            "API_KEY": "QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw",
            "MERCHANT_ID": "4197239218",
            "REQUEST_ID": self.request_id,
            "AUTHORIZATION": f"remitaConsumerKey=QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw, remitaConsumerToken={self.hash_val(self.api_key + self.request_id + self.api_token)}",
        }

        response = requests.post(self.base_url, json=body, headers=headers)

        try:

            data = response.json()

        except Exception as e:

            data = {
                "authorisationCode": False,
                "status": "failed",
                "message": response.text,
                "responseCode": 500,
            }

        data.update({"authorisationCode": body.get("authorisationCode")})
        print(">>>>>>>>>>>>>from direct response>>>>>>>>>>>")

        print(f"joe >>>>>>>>> response \n\n {data}")

        ################   save user with no salaries in no_sal,ary_past_45_days    #######################
        try:
            if data["data"]["salaryCount"] == "0" or data["data"]["salaryCount"] == 0:
                try:
                    get_user_w_no_salary = (
                        main.models.No_Salary_Past_45_Days.objects.get(phone=self.phone)
                    )
                except:
                    main.models.No_Salary_Past_45_Days.objects.create(
                        phone=self.phone,
                        name=data["data"]["customerName"],
                        ministry=data["data"]["companyName"],
                    )

                try:
                    get_eligible_dail = main.models.Dailed_Eligbile.objects.filter(
                        phone=self.phone
                    ).last()
                    get_eligible_dail.exclude = True
                    get_eligible_dail.save()
                except:
                    pass

        except:
            pass

        try:
            if data["responseMsg"] == "Customer not found":
                get_eligible_dail = main.models.Dailed_Eligbile.objects.filter(
                    phone=self.phone
                ).last()
                if get_eligible_dail:
                    get_eligible_dail.non_customers = True
                    get_eligible_dail.save()
        except:
            pass

        data["cache_created"] = datetime.datetime.now().timestamp()
        r.set(key, json.dumps(data))
        return data

    def remita_mandate_ref(self):
        print("finally gottend to remiat mandate ref")

        headers = {
            "CONTENT-TYPE": "application/json",
            "API_KEY": "QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw",
            "MERCHANT_ID": "4197239218",
            "REQUEST_ID": self.request_id,
            "AUTHORIZATION": f"remitaConsumerKey=QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw, remitaConsumerToken={self.hash_val(self.api_key + self.request_id + self.api_token)}",
        }

        return headers

    @staticmethod
    def remita_mandate_status(**args):
        url = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/loan/payment/history"

        payload = json.dumps(args)

        apiKey = settings.REMITA_API_KEY
        api_token = settings.REMITA_API_TOKEN
        merchant_id = settings.REMITA_MERCHANT_ID

        req_id = datetime.datetime.now()
        hash_keys = apiKey + str(req_id) + api_token
        apiHash = hashlib.sha512(hash_keys.encode()).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "API_KEY": apiKey,
            "MERCHANT_ID": merchant_id,
            "REQUEST_ID": f"{req_id}",
            "AUTHORIZATION": "remitaConsumerKey="
            + apiKey
            + ", remitaConsumerToken="
            + apiHash,
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        try:
            res = json.loads(response.text)

        except:
            res = response.text

        return res

    @staticmethod
    def ref_payload(**args):
        payload_data = args
        """
            This function generate mandate reference for a user from remita
        """

        # print(f"amount : {")
        # print(f"rounded amount : {round(payload_data['loanAmount'])}")

        loan_remita_amount = int(payload_data["loanAmount"])
        loan_remita_amount_total = payload_data["totalCollectionAmount"]
        loan_remita_amount_total = loan_remita_amount_total.replace("N", "").replace(
            ",", ""
        )
        print("remita payload >>>>>>>>>>>>>>>>>>>>", payload_data)
        date_formate = datetime.datetime.now().date()

        date_formate = datetime.datetime.now().date()
        collection_date = date_formate + datetime.timedelta(days=30)
        collection_date = datetime.datetime.strptime(
            f"{collection_date}", "%Y-%m-%d"
        ).strftime("%d-%m-%Y")

        date_disbursed = datetime.datetime.strptime(
            f"{date_formate}", "%Y-%m-%d"
        ).strftime("%d-%m-%Y")

        payload = json.dumps(
            {
                "customerId": f"{payload_data['customerId']}",
                "authorisationCode": f"{payload_data['authorisationCode']}",
                "authorisationChannel": f"{payload_data['authorisationChannel']}",
                "phoneNumber": f"{payload_data['phoneNumber']}",
                "accountNumber": f"{payload_data['accountNumber']}",
                "currency": f"{payload_data['currency']}",
                "loanAmount": f"{loan_remita_amount}",
                "collectionAmount": f"{payload_data['collectionAmount']}",
                "dateOfDisbursement": f"{date_disbursed} 10:16:18+0000",
                "dateOfCollection": f"{date_disbursed} 10:16:18+0000",
                "totalCollectionAmount": f"{loan_remita_amount_total}",
                "numberOfRepayments": payload_data["numberOfRepayments"],
            }
        )

        url = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/post/loan"
        ran_data = ""
        digits = "08068309988"
        for i in range(0, 11):
            ran_data += random.choice(digits)
        phone = digits
        remita_manager = Remita_Manager(phone)

        headers = remita_manager.remita_mandate_ref()

        print("posting to remita now >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        response = requests.request("POST", url, headers=headers, data=payload)

        borrower_queryset = main.models.Borrower.objects.filter(
            borrower_phoneNumber=payload_data["phoneNumber"]
        ).last()

        data = response.text
        return data

        total_number_og_try = 0
        return_res_mandate = json.loads(data)

        logging.debug(f"rmita mandate response >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>{data}")
        # while True:
        #     try:
        #         if return_res_mandate['status'] == "success":
        #             return response.text

        #         if total_number_og_try >= 5:
        #             mandate_failed(borrower_queryset.borrower_fullname, borrower_queryset.borrower_business_name,
        #                         payload_data['loanAmount'], 0, borrower_queryset.borrower_phoneNumber)
        #             return response.text
        #         else:
        #             date_formate = datetime.datetime.now().date()
        #             date_formate = datetime.datetime.strptime(f"{date_formate}", "%Y-%m-%d").strftime('%d-%m-%Y')
        #             payload = {
        #                 "customerId": f"{payload_data['customerId']}",
        #                 "authorisationCode": f"{payload_data['authorisationCode']}",
        #                 "authorisationChannel": f"{payload_data['authorisationChannel']}",
        #                 "phoneNumber": f"{payload_data['phoneNumber']}",
        #                 "accountNumber": f"{payload_data['accountNumber']}",
        #                 "currency": f"{payload_data['currency']}",
        #                 "loanAmount": payload_data['loanAmount'],
        #                 "collectionAmount": payload_data['collectionAmount'],
        #                 "dateOfDisbursement": f"{date_formate} 10:16:18+0000",
        #                 "dateOfCollection": f"{date_formate} 10:16:18+0000",
        #                 "totalCollectionAmount": payload_data['totalCollectionAmount'],
        #                 "numberOfRepayments": payload_data['numberOfRepayments']
        #             }

        #             Remita_Manager.ref_payload(**payload)
        #             total_number_og_try += 1
        #             continue

        #     except:
        #         pass

    def loan_mandate_request(self, validated_post, borrower):
        print("================================")
        print("The validated post")
        print(validated_post)

        print(")))))))))))))))))))))))))")
        print("The returning borrower deatils")
        print(borrower)

        data = (
            "{"
            + '\r\n  "customerId": "{}",\r\n  "authorisationCode": "{}",\r\n  "authorisationChannel": "{}",\
                \r\n  "phoneNumber": "{}",\r\n  "accountNumber": "{}",\r\n  "currency": "{}",\r\n  "loanAmount": {},\
                \r\n  "collectionAmount": {},\r\n  "dateOfDisbursement": "{}",\r\n  "dateOfCollection": "{}",\r\n  \
                "totalCollectionAmount": {},\r\n  "numberOfRepayments": 1\r\n'.format(
                str(validated_post.get("customerId")),
                str(borrower.authorisationCode),
                "USSD",
                str(borrower.phoneNumber),
                str(validated_post.get("accountNumber")),
                str(validated_post.get("currency")),
                float(validated_post.get("loanAmount")),
                float(validated_post.get("collectionAmount")),
                date_helpers.Time_Manipulator().convert_date_format(
                    str(validated_post.get("dateOfDisbursement"))
                ),
                date_helpers.Time_Manipulator().convert_date_format(
                    str(validated_post.get("dateOfCollection"))
                ),
                float(validated_post.get("totalCollectionAmount")),
                int(validated_post.get("numberOfRepayments")),
            )
            + "}"
        )

        headers = {
            "CONTENT-TYPE": "application/json",
            "API_KEY": "QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw",
            "MERCHANT_ID": "4197239218",
            "REQUEST_ID": self.request_id,
            "AUTHORIZATION": f"remitaConsumerKey=QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw, remitaConsumerToken={self.hash_val(self.api_key + self.request_id + self.api_token)}",
        }
        print(json.dumps(data))

        response = requests.post(self.base_url2, json=data, headers=headers)

        data = response.json()
        print("*****************************")
        print("body data")
        print(data)
        return data

    @staticmethod
    def get_details_by_mandate(remita_id, auth_code, mandate_ref):

        url = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/loan/payment/history"

        apiKey = settings.REMITA_API_KEY
        api_token = settings.REMITA_API_TOKEN
        merchant_id = settings.REMITA_MERCHANT_ID

        req_id = datetime.datetime.now()
        hash_keys = apiKey + str(req_id) + api_token
        apiHash = hashlib.sha512(hash_keys.encode()).hexdigest()

        payload = json.dumps(
            {
                "authorisationCode": auth_code,
                "customerId": remita_id,
                "mandateRef": mandate_ref,
            }
        )

        headers = {
            "Content-Type": "application/json",
            "API_KEY": apiKey,
            "MERCHANT_ID": merchant_id,
            "REQUEST_ID": f"{req_id}",
            "AUTHORIZATION": "remitaConsumerKey="
            + apiKey
            + ", remitaConsumerToken="
            + apiHash,
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()

    @staticmethod
    def stop_loan(authorisationCode, mandate_ref, user_id):
        # payload = json.dumps({
        #     "authorisationCode": f"{authorisationCode}",
        #     "customerId": "6038b422660f79dccbebe66d5f1a9557",
        #     "mandateReference": "mandate_ref"
        # })

        url = "https://remitademo.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/stop/loan"

        ran_data = ""
        digits = "08068309988"
        for i in range(0, 11):
            ran_data += random.choice(digits)
        phone = digits
        remita_manager = Remita_Manager(phone)

        headers = remita_manager.remita_mandate_ref()
        print(headers)

        body = (
            "{"
            + '\r\n  "customerId": "{}",\r\n  "authorisationCode": "{}",\r\n "manadateReference": {}\r\n'.format(
                str(user_id), str(authorisationCode), str(mandate_ref)
            )
            + "}"
        )
        print("The payload")
        print(body)
        response = requests.post(url, json=body, headers=headers)
        data = response.json()

        print(">>>>>>>>>>stop loan>>>>>>>>>>>")
        print(data)
        return data

        # print("remita payload data")
        # print(authorisationCode, user_id, mandate_ref)

        # response = requests.request("POST",url, headers=headers, json=payload)
        # data = response.json()

        # print('>>>>>>>>>>stop loan>>>>>>>>>>>')
        # print(data)
        # return data

    def get_last_six_salaries(self, start_date, end_date):

        salary_History = self.salary_request()
        # store the salary history as a variable for later use.
        self.salary_data = salary_History
        salary_data = salary_History.get("data")

        if salary_data:

            six_months = self.get_only_required_months(
                salary_data.get("salaryPaymentDetails"), start_date, end_date
            )

        else:

            six_months = False

        return {"message": salary_History.get("responseMsg"), "amount": six_months}

    def get_only_required_months(self, months, start_date, end_date):

        required_months = date_helpers.Time_Manipulator.generate_months_between_dates(
            start_date, end_date
        )

        print("////////////////this is the last six salary/////////////")
        print(months)
        print("////////////////////////////")

        try:
            salary_dates = {
                datetime.datetime.strptime(
                    salary.get("paymentDate"), "%d-%m-%Y %H:%M:%S+%f"
                ).strftime("%m-%Y"): int(float(salary.get("amount")))
                for salary in months
                if datetime.datetime.strptime(
                    salary.get("paymentDate"), "%d-%m-%Y %H:%M:%S+%f"
                ).strftime("%m-%Y")
                in required_months
            }
            print(salary_dates)
        except KeyError:
            salary_dates = None
            return salary_dates

        return salary_dates

    def get_total_active_loans(self):

        request_data = self.salary_request()
        user_data = request_data.get("data")

        if user_data:
            if request_data.get("responseCode") == "00" and (
                not (user_data.get("loanHistoryDetails") == None)
            ):

                loan_history = user_data.get("loanHistoryDetails")
                active_loans = list(
                    filter(lambda loan: loan.get("status") == "NEW", loan_history)
                )
                total_active_loan_value = sum(
                    [float(loan.get("repaymentAmount")) for loan in active_loans]
                )

                return {
                    "message": request_data.get("responseMsg"),
                    "amount": total_active_loan_value,
                    "user": request_data.get("data", {}).get("customerName", {}),
                    "ministry": request_data.get("data", {}).get("companyName", {}),
                }

            else:
                return {
                    "message": request_data.get("responseDescription"),
                    "amount": False,
                }

        else:
            return {"message": request_data.get("responseMsg"), "amount": False}

    def check_salaries_in_165_days(self):

        now = datetime.date.today()
        last165_days = now - datetime.timedelta(days=195)
        user_salaries = self.salary_request()

        if not user_salaries.get("data"):
            return []

        salaries = pd.DataFrame(user_salaries.get("data").get("salaryPaymentDetails"))

        salaries["paymentDate"] = pd.to_datetime(
            salaries["paymentDate"], dayfirst=True
        ).dt.date

        salaries["amount"] = salaries["amount"].astype("float64")

        salaries["paymentMonth"] = pd.to_datetime(
            salaries["paymentDate"], dayfirst=True
        ).dt.strftime("%Y-%m")
        salaries["paymentDate"] = pd.to_datetime(salaries["paymentDate"], dayfirst=True)

        # Remove JAN & DEC salaries
        salaries = salaries[
            ~(salaries["paymentDate"].dt.month.astype("str").str.contains("01|12"))
        ]

        # print(f"XXXXXXXsalaries XX{salaries}XXXXXXXXXX")

        # print(f"XXXXXXXMonthly total salaries XX{monthly_total_salaries}XXXXXXXXXX")
        # monthly_total_salaries['paymentDate'] = salaries.groupby("paymentMonth").min()[
        #     'paymentDate']
        # # print(salaries.groupby("paymentMonth").min())
        # salaries = monthly_total_salaries

        salaries.index = pd.DatetimeIndex(salaries.paymentDate)

        print(salaries)
        salaries = salaries.asfreq("D")

        all_salaries_in_165_days = salaries.loc[last165_days:now]
        non_null_values = all_salaries_in_165_days[
            all_salaries_in_165_days.amount.notnull()
        ]

        actual_salaries = non_null_values[["paymentDate", "amount"]].to_records(
            index=False
        )
        actual_salaries["amount"] = actual_salaries["amount"].astype("str")

        results = list(actual_salaries["amount"])
        salary_list = [float(i) for i in results]

        return salary_list

    def has_gotten_salary_in_45_days(self):

        now = datetime.date.today()
        salary_data = self.salary_request()
        #  or (salary_data.get("resonseCode") == "7801")

        if not (salary_data.get("responseCode") == "00"):

            return {
                "response_code": salary_data.get("responseCode"),
                "message": salary_data.get("responseMsg"),
                "response": False,
            }
        elif (
            salary_data.get("resonseCode") == "00"
            and salary_data.get("salaryCount") == None
        ):

            print(">>>>>>>>>>>>>checking if salary is available<<<<<<<<<<<<<<")
            print(salary_data.get("salaryCount"))
            return {
                "response_code": salary_data.get("responseCode"),
                "message": "Customer has no salary record",
                "response": False,
            }

        salaries = pd.DataFrame(
            self.salary_request().get("data").get("salaryPaymentDetails")
        )

        if salaries.empty:
            return {
                "response_code": 200,
                "message": "cannot fetch salary history data",
                "response": False,
            }
        else:
            sorted_salaries = pd.to_datetime(
                salaries["paymentDate"], dayfirst=True
            ).dt.date.sort_values()

            # print(">>>>>>>This part is runniingzzzzzzz oooooo>>>>>>>>>>")
            # print(last_salary)
            # print("XXXXXXXXXXXXXXXXXXXX")

            last_salary = sorted_salaries.iloc[-1]
            period_since_last_salary = (now - last_salary).days

            print(">>>>>>>This part is runniing oooooo>>>>>>>>>>")

            print(period_since_last_salary)

            print(">>>>>>>>>>>>>>>>>")

            if period_since_last_salary < 45:

                return {
                    "response_code": 200,
                    "message": salary_data.get("responseMsg"),
                    "response": True,
                }

            else:

                return {
                    "response_code": 200,
                    "message": salary_data.get("responseMsg"),
                    "response": False,
                }

    def user_has_accurate_bio_data(self):

        user_data = self.salary_request()

        required_data = ["accountNumber", "bankCode", "bvn", "customerName"]

        for key, value in user_data.get("data").items():

            if key in required_data:

                if value:

                    continue

                else:

                    return {"message": f"missing {key}", "status": False}
        else:

            return {"message": f"Accurate", "status": True}

    def active_loans(loan):
        if loan.get("status") == "NEW":
            return True
        else:
            False

    # @staticmethod
    # def remove_jan_dec_salary(data):

    #     correct_data = {date:salary for date, salary in data.items() if date.split("-")[0] not in ["01", "12"]}

    #     return correct_data

    @staticmethod
    def remove_outliers(data, phone):

        MULTIPLIER = 1.2
        SEGREGATION_RATIO = 35
        data = list(data)

        maximum = max(data)
        minimum = np.median(data)

        ratio = minimum / maximum * 100
        low_lim, up_lim = 0, 0
        print(ratio)

        if ratio > 35:

            up_lim = maximum

        else:

            Q1 = np.percentile(data, 25, interpolation="midpoint")
            Q2 = np.percentile(data, 50, interpolation="midpoint")
            Q3 = np.percentile(data, 75, interpolation="midpoint")

            print("Q1 25 percentile of the given data is, ", Q1)
            print("Q1 50 percentile of the given data is, ", Q2)
            print("Q1 75 percentile of the given data is, ", Q3)

            IQR = Q3 - Q1
            print("Interquartile range is", IQR)

            low_lim = Q1 - 1.5 * IQR
            up_lim = (
                Q3 + 1.5 * IQR
            ) * MULTIPLIER  # INCREMENT JUST 20% BIT TO ALLOW FOR CLOSE VALUES TO PASS THROUGH
            print("low_limit is", low_lim)
            print("up_limit is", up_lim)

        good_values = []

        for x in data:
            if x <= up_lim:
                good_values.append(x)
        print("good_values in the dataset is", good_values)
        from main.tasks import celery_save_outliers

        log_data = dict(
            ratio=ratio,
            low_lim=low_lim,
            up_lim=up_lim,
            max_val=maximum,
            min_val=minimum,
            segregation_ratio=SEGREGATION_RATIO,
            multiplier=MULTIPLIER,
            using="DIRECT MEAN" if ratio > SEGREGATION_RATIO else "IQR",
            salaries=str(data),
        )

        celery_save_outliers(log_data, phone)

        return good_values


class Stop_Loan_Manager:

    base_url = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/stop/loan"
    merchant_id = "4197239218"
    api_key = "QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw"
    api_token = "K3B1RmlPWjVuNFJ4VlBuWnhNWGJ2L3FiaFlqbWVaK0VhU25lWWthc3QvTGlTQU5mOFdKZjVYMzUyRjdibnJmaw=="

    def _init_(self) -> None:

        self.request_id = self.hash_val(str(datetime.datetime.now()), "md5")

    def hash_val(self, raw_val, mode="512"):

        if mode == "512":

            enc = hashlib.sha512(raw_val.encode())

            return enc.hexdigest()

        elif mode == "md5":

            enc = hashlib.md5(raw_val.encode())

            return enc.hexdigest()

    def stop_loan(self, user_id, mandate_ref, auth_code):
        req_id = self.hash_val(str(datetime.datetime.now()), "md5")
        headers = {
            "CONTENT-TYPE": "application/json",
            "API_KEY": "QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw",
            "MERCHANT_ID": "4197239218",
            "REQUEST_ID": req_id,
            "AUTHORIZATION": f"remitaConsumerKey=QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw, remitaConsumerToken={self.hash_val(self.api_key + req_id + self.api_token)}",
        }

        print("here'd the data", headers)

        body = (
            "{"
            + '\r\n  "customerId": "{}",\r\n  "authorisationCode": "{}",\r\n "manadateReference": {}\r\n'.format(
                str(user_id), str(auth_code), str(mandate_ref)
            )
            + "}"
        )
        print("The payload")
        print(body)
        response = requests.post(self.base_url, json=body, headers=headers)
        data = response.text
        return data

    def repay_loan(self, user_id, mandate_ref, auth_code):

        headers = {
            "CONTENT-TYPE": "application/json",
            "API_KEY": "QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw",
            "MERCHANT_ID": "4197239218",
            "REQUEST_ID": self.hash_val(str(datetime.datetime.now()), "md5"),
            "AUTHORIZATION": f'remitaConsumerKey=QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw, remitaConsumerToken={self.hash_val(self.api_key + self.hash_val(str(datetime.datetime.now()), "md5") + self.api_token)}',
        }

        url = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/loan/payment/history"

        body = (
            "{"
            + '\r\n  "customerId": "{}",\r\n  "authorisationCode": "{}",\r\n "manadateReference": {}\r\n'.format(
                str(user_id), str(auth_code), str(mandate_ref)
            )
            + "}"
        )
        print("The payload")
        print(body)
        response = requests.post(url, json=body, headers=headers)
        data = response.json()

        print(">>>>>>>>>>stop loan>>>>>>>>>>>")
        print(data)
        return data


class Loan_repayment_Manager:

    base_url = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/loan/payment/history"
    merchant_id = "4197239218"
    api_key = "QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw"
    api_token = "K3B1RmlPWjVuNFJ4VlBuWnhNWGJ2L3FiaFlqbWVaK0VhU25lWWthc3QvTGlTQU5mOFdKZjVYMzUyRjdibnJmaw=="

    def _init_(self) -> None:

        self.request_id = self.hash_val(str(datetime.datetime.now()), "md5")

    def hash_val(self, raw_val, mode="512"):

        if mode == "512":

            enc = hashlib.sha512(raw_val.encode())

            return enc.hexdigest()

        elif mode == "md5":

            enc = hashlib.md5(raw_val.encode())

            return enc.hexdigest()

    def repay_loan(self, user_id, mandate_ref, auth_code):

        import requests
        import json

        url = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/loan/payment/history"

        payload = json.dumps(
            {
                "authorisationCode": f"{auth_code}",
                "customerId": f"{user_id}",
                "mandateRef": f"{mandate_ref}",
            }
        )
        headers = {
            "Content-Type": "application/json",
            "MERCHANT_ID": "4197239218",
            "REQUEST_ID": "1637842683350",
            "AUTHORIZATION": "remitaConsumerKey=QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw, remitaConsumerToken=1efe16447b249e09a6949b7275c63998b93c4b2989414bb2f06e728660285b547ab01eccaf93d8048457d91dffa5d00713688758189724d3898723b38db01bcf",
            "Cookie": "b1pi=!k0HOGxbo5yFjLJsIlu33Bqk8Pd7kXG7mSk9mSRcI5kHmiT48qqpQdlQgHcPJ4oQU8ZeBxRbJGCWCjSg=",
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print("response", response.text, "\n\n")

        data = response.json()

        return data


class Remita_Stop_Loan_Manager:

    base_url = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/stop/loan"

    merchant_id = "4197239218"
    api_key = "QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw"
    api_token = "K3B1RmlPWjVuNFJ4VlBuWnhNWGJ2L3FiaFlqbWVaK0VhU25lWWthc3QvTGlTQU5mOFdKZjVYMzUyRjdibnJmaw=="

    def __init__(self, phone) -> None:

        self.phone = phone
        self.request_id = self.hash_val(str(datetime.datetime.now()), "md5")

    def hash_val(self, raw_val, mode="512"):

        if mode == "512":

            enc = hashlib.sha512(raw_val.encode())

            return enc.hexdigest()

        elif mode == "md5":

            enc = hashlib.md5(raw_val.encode())

            return enc.hexdigest()

    def stop_loan(self, user_id, mandate_ref, auth_code):

        headers = {
            "CONTENT-TYPE": "application/json",
            "API_KEY": "QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw",
            "MERCHANT_ID": "4197239218",
            "REQUEST_ID": self.request_id,
            "AUTHORIZATION": f"remitaConsumerKey=QzAwMDAxNjg1MDAxMjM0fEMwMDAwMTY4NTAw, remitaConsumerToken={self.hash_val(self.api_key + self.request_id + self.api_token)}",
        }

        print("here'd the data", headers)

        body = (
            "{"
            + '\r\n  "customerId": "{}",\r\n  "authorisationCode": "{}",\r\n "manadateReference": {}\r\n'.format(
                str(user_id), str(auth_code), str(mandate_ref)
            )
            + "}"
        )
        print("The payload")
        print(body)
        response = requests.post(self.base_url, json=body, headers=headers)
        data = response.text
        return data


def loan_eligibility_checker(phone):
    try:
        get_eligibility = Borrower.get_eligible_amount(
            phone=phone, channel="api endpoint"
        )
        get_borrower = Borrower.objects.filter(borrower_phoneNumber=phone).last()
        if get_borrower:
            if int(get_eligibility["eligible_amount"]) > 3000:
                eligible_amt = rounding_up(get_eligibility["eligible_amount"])
                eligible_amt = utility.currency_formatter(eligible_amt)
                send_eligiblity_sms(
                    get_borrower.borrower_phoneNumber,
                    eligible_amt,
                    get_borrower.borrower_firstname,
                )

    except:
        pass


def remita_close_mandate(mandate_id, auth_code, remita_id):

    apiKey = settings.REMITA_API_KEY
    api_token = settings.REMITA_API_TOKEN
    merchant_id = settings.REMITA_MERCHANT_ID

    req_id = datetime.datetime.now()
    hash_keys = apiKey + str(req_id) + api_token
    apiHash = hashlib.sha512(hash_keys.encode()).hexdigest()
    url = "https://login.remita.net/remita/exapp/api/v1/send/api/loansvc/data/api/v2/payday/stop/loan"

    payload = json.dumps(
        {
            "authorisationCode": str(auth_code),
            "customerId": str(remita_id),
            "mandateReference": str(mandate_id),
        }
    )
    print(payload)

    headers = {
        "Content-Type": "application/json",
        "API_KEY": apiKey,
        "MERCHANT_ID": merchant_id,
        "REQUEST_ID": f"{req_id}",
        "AUTHORIZATION": "remitaConsumerKey="
        + apiKey
        + ", remitaConsumerToken="
        + apiHash,
    }

    data = requests.request("POST", url, headers=headers, data=payload)

    return data.text


def is_mandate_created(mandate, auth, remita_id, amount) -> bool:
    payload = {
        "authorisationCode": f"{auth}",
        "customerId": f"{remita_id}",
        "mandateRef": f"{mandate}",
    }

    data = Remita_Manager.remita_mandate_status(**payload)

    if type(data) == dict:
        if data["data"]:
            return (
                data["data"]["status"] == "NEW"
                and data["data"]["totalDisbursed"] == amount
            )
