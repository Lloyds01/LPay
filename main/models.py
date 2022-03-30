from datetime import datetime, date
from email import header
from hashlib import new
import imp
import json
from math import log
from os import pathsep
import os
from pickletools import long1
from pyexpat import model
from re import T
import re
from time import sleep
from typing import Tuple
from click import echo
from dateutil.parser import parser
from django.db import DatabaseError, models
from django.db.models import Avg
from django.db.models.expressions import Ref
from numpy import average, mod
from django.utils import timezone
import pandas as pd
from requests.api import get
from requests.models import Response
from .helpers import loan_helpers, date_helpers,loan_disk_helpers
from dateutil.parser import parse
from statistics import mean, median, mode
from main.helpers.utils import full_name_split
from main.helpers.loan_disk_helpers import (
    borrower_api_call,
    update_borrower_api_call,
    loan_disk_update_borrower,
    post_repayment,
)
import requests
from datetime import datetime
import logging
from main.helpers.utils import nip_bank_search
from main.helpers.send_sms import *
import random
import string
from django.conf import settings
import math
import csv

from web.models import constant_env

# get constant

# get_constant = constant_env()


def rounding_amt_up(value):

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


logging.basicConfig(filename="test.log", level=logging.DEBUG)

STATUS = (
    ("Incomplete", "Incomplete"),
    ("Sucess", "Sucess"),
    ("Failed", "Failed"),
)


def clear_catch(num):
    try:
        Catched_Cookie.objects.filter(phone__iexact=num).last().delete()
    except:
        pass


# Create your models here.

class Loan_Session(models.Model):
    service_code = models.CharField(max_length=300)
    phone_number = models.CharField(max_length=50)
    date = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=300)
    channel = models.CharField(max_length=300)
    network_code = models.CharField(max_length=100)
    status = models.CharField(max_length=300, choices=STATUS, null=True)
    cost = models.CharField(max_length=3000, null=True)
    duration = models.CharField(max_length=300, null=True)
    hops_count = models.CharField(max_length=300, null=True)
    input_text = models.CharField(max_length=300, null=True)
    last_app_response = models.CharField(max_length=500, null=True)
    error_message = models.CharField(max_length=400, null=True)

    def __str__(self) -> str:
        return f"{self.phone_number} - {self.service_code}"


class  Borrower(models.Model):
    borrower_remita_id = models.CharField(max_length=50, null=True, blank=True)
    borrower_phoneNumber = models.CharField(
        max_length=20,
        null=True,
        blank=True,
    )
    borrower_eligibleOffer = models.CharField(
        max_length=15, null=True, blank=True)
    borrower_authorisationCode = models.CharField(
        max_length=300, null=True, blank=True)
    borrower_channel = models.CharField(
        max_length=300, null=True, blank=True, default="ussd"
    )
    borrower_id = models.CharField(max_length=200, null=True, blank=True)
    borrower_country = models.CharField(max_length=200, null=True, blank=True)
    borrower_fullname = models.CharField(max_length=200, null=True, blank=True)
    borrower_firstname = models.CharField(
        max_length=200, null=True, blank=True)
    borrower_lastname = models.CharField(max_length=200, null=True, blank=True)
    borrower_middlename = models.CharField(
        max_length=200, null=True, blank=True)
    borrower_business_name = models.CharField(
        max_length=200, null=True, blank=True)
    borrower_gender = models.CharField(max_length=200, null=True, blank=True)
    borrower_mobile = models.CharField(max_length=200, null=True, blank=True)
    borrower_email = models.CharField(max_length=200, null=True, blank=True)
    borrower_dob = models.DateField(null=True, blank=True)
    borrower_address = models.CharField(max_length=300, null=True, blank=True)
    borrower_city = models.CharField(max_length=300, null=True, blank=True)
    borrower_province = models.CharField(max_length=300, null=True, blank=True)
    borrower_zipcode = models.CharField(max_length=300, null=True, blank=True)
    borrower_landline = models.CharField(max_length=300, null=True, blank=True)
    borrower_working_status = models.CharField(
        max_length=300, null=True, blank=True)
    borrower_description = models.TextField(null=True, blank=True)
    office_address = models.CharField(max_length=300, null=True, blank=True)
    nearest_busstop = models.CharField(max_length=300, null=True, blank=True)
    next_of_kin = models.CharField(max_length=300, null=True, blank=True)
    next_of_kin_phone = models.CharField(max_length=300, null=True, blank=True)
    occupation = models.CharField(max_length=300, null=True, blank=True)
    nationality = models.CharField(max_length=300, null=True, blank=True)
    marital_status = models.CharField(max_length=300, null=True, blank=True)
    ippis_no = models.CharField(max_length=300, null=True, blank=True)
    ministry = models.CharField(max_length=300, null=True, blank=True)
    acct_no = models.CharField(max_length=300, null=True, blank=True)
    bank_name = models.CharField(max_length=300, null=True, blank=True)
    bank_code = models.CharField(max_length=300, null=True, blank=True)
    branch_code = models.CharField(max_length=300, null=True, blank=True)
    bvn_no = models.CharField(max_length=300, null=True, blank=True)
    exists_on_loandisk = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.borrower_remita_id

    def phone_number(self):
        return self.borrower_phoneNumber

    def customer_id(self):
        return self.borrower_remita_id

    @staticmethod
    def fetch_average_salary(phone, channel):
        """This function collates and aggregates the last 6 salaries for a user from current date and returns the average"""

        start_date, end_date = date_helpers.Time_Manipulator.get_months_before(
            date.today()
        )

        average_salary = False
        data = None
        tries = 0
        no_of_tries = 4
        response = False
        while tries < no_of_tries or response:

            remita_manager = loan_helpers.Remita_Manager(phone)
            borrower_queryset = Borrower.objects.filter(
                borrower_phoneNumber=phone)
            data = remita_manager.salary_request()

            def user_ministry_is_banned(data: dict) -> bool:
                """CHECK IF A USER IS NOT FROM A BANNED LIST OF PARASTATALS.
                RETURN FALSE IF THE USER MINISTRY IS NOT BANNED ELSE RETURN TRUE"""

                banned_ministries = constant_env().get("banned_ministries")
                if banned_ministries == None or banned_ministries == "":
                    return False
                else:

                    try:
                        user_ministry = data.get("data", {}).get("companyName")

                        def mini_checker(keyword): return all(
                            [
                                word in user_ministry.lower()
                                for word in keyword.lower().split(",")
                            ]
                        )
                        ministry_check = list(
                            map(mini_checker, banned_ministries))

                        return any(ministry_check)
                    except:
                        return True

            if user_ministry_is_banned(data):

                return {
                    "amount": 0,
                    "message": "Customer not from coverage region",
                    "account number": data.get("accountNumber"),
                }

            try:
                response_code = int(data.get("responseCode"))

            except:
                response_code = 7801

            if not ((response_code >= 500) or (response_code < 509)):
                response = True

            print(
                "\nThis is the number of tries \n",
                tries,
                "\n this is the response",
                response,
                "\n and response code \n",
                response_code,
            )
            tries = tries + 1

        try:
            res_code = data.get("responseCode")
        except:
            res_code = 7801
        if res_code == "00":
            print("this is the intro loan disk api >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            names = full_name_split(
                data.get("data", {}).get("customerName", ""))
            first_name = names[0] if len(names) > 0 else ""
            last_name = names[1] if len(names) > 1 else ""
            middle_name = names[2] if len(names) > 2 else ""
            print("this is the intro loan disk api 1111 >>>>>>>>>>>>>>>>>>>>>>>>>>>>")

            if not borrower_queryset:
                print(
                    "this is the intro loan disk api 2222 >>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                )

                get_borrower_bank = nip_bank_search(
                    data.get("data", {}).get("bankCode", "")
                )

                try:
                    get_user_bank = get_borrower_bank["name"]
                except:
                    Bank_search_query.objects.create(
                        payload=nip_bank_search(
                            data.get("data", {}).get("bankCode", "")
                        )
                    )
                    get_user_bank = "None"

                Borrower.objects.create(
                    borrower_remita_id=f"r_{data.get('data', {}).get('customerId', '')}",
                    borrower_fullname=data.get(
                        "data", {}).get("customerName", ""),
                    borrower_firstname=first_name,
                    borrower_lastname=last_name,
                    borrower_middlename=middle_name,
                    borrower_phoneNumber=phone,
                    borrower_business_name=data.get(
                        "data", {}).get("companyName", ""),
                    bvn_no=data.get("data", {}).get("bvn", ""),
                    acct_no=data.get("data", {}).get("accountNumber", ""),
                    bank_code=data.get("data", {}).get("bankCode", ""),
                    borrower_authorisationCode=data.get("authorisationCode"),
                    bank_name=get_user_bank,
                    borrower_channel=channel,
                )

            else:
                get_borrower_bank = nip_bank_search(
                    data.get("data", {}).get("bankCode", "")
                )
                try:
                    get_user_bank = get_borrower_bank["name"]

                except:
                    Bank_search_query.objects.create(
                        payload=nip_bank_search(
                            data.get("data", {}).get("bankCode", "")
                        )
                    )
                    get_user_bank = "None"

                gt_borrower = borrower_queryset.last()
                gt_borrower.borrower_authorisationCode = data.get(
                    "authorisationCode")

                gt_borrower.borrower_remita_id = (
                    f"r_{data.get('data', {}).get('customerId', '')}"
                )
                gt_borrower.borrower_fullname = data.get("data", {}).get(
                    "customerName", ""
                )

                gt_borrower.borrower_firstname = first_name
                gt_borrower.borrower_lastname = last_name
                gt_borrower.borrower_middlename = middle_name
                gt_borrower.borrower_phoneNumber = phone
                gt_borrower.borrower_business_name = data.get("data", {}).get(
                    "companyName", ""
                )
                gt_borrower.bvn_no = data.get("data", {}).get("bvn", "")
                gt_borrower.acct_no = data.get(
                    "data", {}).get("accountNumber", "")

                gt_borrower.bank_code = data.get(
                    "data", {}).get("bankCode", "")
                gt_borrower.bank_name = "".join(
                    e for e in get_user_bank if e.isalnum() or e == " "
                )
                gt_borrower.borrower_channel = channel
                gt_borrower.save()

        else:
            print(
                {
                    "amount": 0,
                    "message": data.get("responseMsg"),
                    "account number": data.get("accountNumber"),
                }
            )

        salaries = remita_manager.get_last_six_salaries(start_date, end_date)

        has_recent_salary = remita_manager.has_gotten_salary_in_45_days().get(
            "response"
        )

        if has_recent_salary == True:

            # salaries = remita_manager.get_last_six_salaries(
            #     start_date, end_date)

            if len(salaries.get("amount")) >= 4:

                # this saves user eligibility to Liberty ussd eligible db
                # if Salary_History

                clean_salaries = salaries.get("amount")
                salary_list = remita_manager.remove_outliers(
                    list(clean_salaries.values()), phone
                )

                average_salary = mean(salary_list)

                Eligible.objects.create(
                    phoneNumber=phone,
                    bank_code=data.get("data", {}).get("bankCode", ""),
                    account_number=data.get("data", {}).get(
                        "accountNumber", ""),
                    Salary_history=data.get("data", {}).get(
                        "salaryPaymentDetails", "")
                    if data.get("data", {}).get("salaryPaymentDetails", "")
                    else "",
                    loan_history=data.get("data", {}).get(
                        "loanHistoryDetails", "")
                    if data.get("data", {}).get("loanHistoryDetails", "")
                    else "",
                    is_salary_45_days=True,
                    average_salary=average_salary if average_salary else 0,
                )

                return {
                    "amount": mean(salary_list),
                    "message": "Ok",
                    "account number": data.get("accountNumber"),
                }

            else:
                remita_manager = loan_helpers.Remita_Manager(phone)

                salary_list = remita_manager.check_salaries_in_165_days()

                if len(salary_list) > 4:

                    salary_list = remita_manager.remove_outliers(
                        salary_list, phone)

                    average_salary = mean(salary_list)

                    # median_salary = median(salary_list)

                    # average_salary = mean([average_salary,median_salary])

                    print("XXXXXXThe avearage salaries XXXXXXXXXXX")
                    print(average_salary)
                    print("XXXXXXXXXXXXXXXXXXXXXXXXXXXX")

                    # this saves user eligibility to Liberty ussd eligible db
                    try:
                        Eligible.objects.create(
                            phoneNumber=phone,
                            bank_code=data.get("data", {}).get("bankCode", ""),
                            account_number=data.get("data", {}).get(
                                "accountNumber", ""
                            ),
                            Salary_history=data.get("data", {}).get(
                                "salaryPaymentDetails", ""
                            )
                            if data.get("data", {}).get("salaryPaymentDetails", "")
                            else "",
                            loan_history=data.get("data", {}).get(
                                "loanHistoryDetails", ""
                            )
                            if data.get("data", {}).get("loanHistoryDetails", "")
                            else "",
                            average_salary=average_salary if average_salary else 0,
                            is_salary_45_days=True,
                            is_3_months_salary_in_5_months=True,
                        )
                    except:
                        pass

                    return {"amount": average_salary, "message": "ok"}
                else:

                    # this saves user eligibility to Liberty ussd eligible db
                    Eligible.objects.create(
                        phoneNumber=phone,
                        bank_code=data.get("data", {}).get("bankCode", ""),
                        account_number=data.get("data", {}).get(
                            "accountNumber", ""),
                        Salary_history=data.get("data", {}).get(
                            "salaryPaymentDetails", ""
                        )
                        if data.get("data", {}).get("salaryPaymentDetails", "")
                        else "",
                        loan_history=data.get("data", {}).get(
                            "loanHistoryDetails", "")
                        if data.get("data", {}).get("loanHistoryDetails", "")
                        else "",
                        is_salary_45_days=True,
                        average_salary=average_salary if average_salary else 0,
                    )

                return {"amount": 0, "message": "Not enough salaries in past 165 days"}
        else:
            # Eligible.objects.create(phoneNumber=phone, bank_code=data.get("data", {}).get("bankCode", ""),
            # account_number=data.get("data", {}).get("accountNumber", ""),
            # Salary_history=data.get("data", {}).get("salaryPaymentDetails", "")[0],
            # loan_history=data.get("data", {}).get("loanHistoryDetails", "")[0],
            # )
            return {
                "amount": average_salary,
                "message": "No salaries in past 45 days",
                "account number": data.get("accountNumber"),
            }

    @staticmethod
    def get_eligible_amount(phone, channel):

        interest = 0

        if constant_env().get("loan_duration") == 1:
            interest = constant_env().get(
                "loan_disk_one_month_interest"
            ) * constant_env().get("loan_duration")
            actual_interest = constant_env().get("loan_disk_two_month_post")

        elif constant_env().get("loan_duration") == 2:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_two_month_post"
            )
            actual_interest = constant_env().get("loan_disk_two_month_post")

        elif constant_env().get("loan_duration") == 3:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_three_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_three_month_interets")

        elif constant_env().get("loan_duration") == 4:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_four_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_four_month_interets")

        elif constant_env().get("loan_duration") == 5:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_five_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_five_month_interets")

        elif constant_env().get("loan_duration") == 6:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_six_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_six_month_interets")

        elif constant_env().get("loan_duration") == 7:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_seven_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_seven_month_interets")

        elif constant_env().get("loan_duration") == 8:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_eight_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_eight_month_interets")

        average_salary_response = Borrower.fetch_average_salary(
            phone=phone, channel=channel
        )
        print(f"{interest}>>>>>>>>>this is the average salary response>>>>>>>>>>")
        print(f"{constant_env().get('loan_duration')} lona durations \n\n\n")
        print(average_salary_response)
        print(">>>>>>>>>>>>>>>>>>>")
        logging.debug(
            f"avarage salary  >>>>>>>>>>>>>>>>>>>>>>>>>{average_salary_response}"
        )
        loan_response = Loan.get_sum_active_loans_from_remita(phone=phone)
        print(">>>>>>>>>this is the loan response>>>>>>>>>>")
        print(loan_response)
        print(">>>>>>>>>>>>>>>>>>>")

        # save users that has no salary in past 45 days to a db
        ##############

        # if average_salary_response['message'] == 'No salaries in past 45 days':
        #     get_user_in_past_45_days_db = No_Salary_Past_45_Days.objects.filter(phone=phone).last()
        #     if get_user_in_past_45_days_db:
        #         pass
        #     else:
        #         No_Salary_Past_45_Days.objects.create(
        #             phone = phone
        #         )

        if average_salary_response["message"] != "Customer not found":
            #################
            # Saved all eligibile dailed check
            ##############
            try:
                Dailed_Eligbile.objects.get(phone=phone)
            except:
                Dailed_Eligbile.objects.create(
                    phone=phone,
                    eligibility=average_salary_response.get("amount"),
                    remita_success_return=True,
                )

        eligible_amount = 0

        if average_salary_response.get("amount"):

            average_salary_response["amount"] = average_salary_response.get(
                "amount"
            ) * float(constant_env().get("affordability_rate"))

            if loan_response.get("amount") >= 0:

                ###########
                # save sum of loan response to eligible table
                ###########

                get_saved_eligible = Eligible.objects.filter(
                    phoneNumber=phone).last()

                get_saved_eligible.loan_obligation = loan_response.get(
                    "amount")
                get_saved_eligible.save()

                ###########
                # done saving sum of loan response to eligible table
                ###########

                print("..........remainder calculator.............")
                print(average_salary_response.get("amount"))
                remainder_after_deductions = average_salary_response.get(
                    "amount"
                ) - loan_response.get("amount")

                print(
                    f"reminder after deduction {remainder_after_deductions}\n\n\n")

                eligible_amount = round(
                    max([round(remainder_after_deductions), 0]))

                print(
                    f"eligible to be divided by the interest is {eligible_amount}")
                loan_offer = rounding_amt_up(
                    (eligible_amount / (interest + 100)) * 100)
                print(loan_offer)

                tenor = constant_env().get("loan_duration")
                net_offer = eligible_amount
                interest_rate = actual_interest / 100
                net_offer

                loan_offer = (net_offer * tenor) / \
                    (1 + (interest_rate * tenor))

                eligible_amount = int(net_offer)

        borrower = Borrower.objects.filter(borrower_phoneNumber=phone).last()

        if borrower:
            borrower.borrower_eligibleOffer = eligible_amount
            # SAVE BORROWER ELIGIBLE AMOUNT OF MONEY FOR LATER USE
            borrower.save()
        if average_salary_response.get("amount") > 0 and eligible_amount < 1:
            print(".......................")
            print(average_salary_response.get("amount"))
            print(eligible_amount)

            return {
                "eligible_amount": eligible_amount,  # Borrower is eligible to 15% of remainder
                "message": f"{average_salary_response.get('message')}, {'Unable to grant you loan'}",
                "account number": average_salary_response.get("accountNumber"),
            }
        else:

            # check if user was preciously added to no_salary_past_45_days and enable him as active to
            # avoid checking eligibility for him in cronjob section
            get_user_in_past_45_days_db = No_Salary_Past_45_Days.objects.filter(
                phone=phone
            ).last()

            if get_user_in_past_45_days_db:
                get_user_in_past_45_days_db.eligible = False
                get_user_in_past_45_days_db.save()

            save_user_eligible_amount = Eligible.objects.filter(
                phoneNumber=phone
            ).last()
            if save_user_eligible_amount:
                save_user_eligible_amount.eligible_amount = eligible_amount
                save_user_eligible_amount.save()

            return {
                "eligible_amount": eligible_amount,  # Borrower is eligible to 15% of remainder
                "message": f"{average_salary_response.get('message')}, {loan_response.get('message')}",
            }

    @staticmethod
    def create_borrower(
        borrower_remita_id,
        borrower_fullname,
        borrower_firstname,
        borrower_lastname,
        borrower_middlename,
        borrower_phoneNumber,
        borrower_business_name,
        bvn_no,
        acct_no,
        bank_code,
        borrower_authorisationCode,
        borrower_id,
        bank_name,
        channel,
    ):

        new_borrower = Borrower(
            borrower_remita_id=borrower_remita_id,
            borrower_fullname=borrower_fullname,
            borrower_firstname=borrower_firstname,
            borrower_lastname=borrower_lastname,
            borrower_middlename=borrower_middlename,
            borrower_phoneNumber=borrower_phoneNumber,
            borrower_business_name=borrower_business_name,
            bvn_no=bvn_no,
            acct_no=acct_no,
            bank_code=bank_code,
            borrower_authorisationCode=borrower_authorisationCode,
            borrower_id=borrower_id,
            bank_name=bank_name,
            borrower_channel=channel,
        )
        new_borrower.save()

        return new_borrower


class Salary_History(models.Model):

    customerId = models.CharField(max_length=50, null=True, blank=True)
    authorisationCode = models.CharField(max_length=100)
    authorisationChannel = models.CharField(max_length=20)
    phoneNumber = models.CharField(max_length=20)
    amount = models.DecimalField(decimal_places=2, max_digits=1000, null=True)
    paymentDate = models.DateField(null=True, blank=True)
    dateSaved = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.paymentDate)

    def __str__(self) -> str:
        return str(self.customerId)

    @staticmethod
    def populate(data, borrower):

        borrower_salaries = borrower.salary_history_set.all()
        values = map(
            lambda salary: (salary[0].strftime("%m-%Y"), salary[1]),
            borrower_salaries.values_list("paymentDate", "amount"),
        )
        paymentDates, payment_amounts = zip(*(values))

        salary_dates = [
            salary
            for salary in data.get("salaryPaymentDetails")
            if parse(salary.get("paymentDate")).strftime("%m-%Y") not in paymentDates
        ]

        new_salary_entries = [
            Salary_History(
                borrower=borrower,
                customerId=borrower.customerId,
                amount=salary_detail.get("amount"),
                paymentDate=parse(salary_detail.get("paymentDate")),
            )
            for salary_detail in salary_dates
        ]

        Salary_History.objects.bulk_create(new_salary_entries)


class Loan(models.Model):
    customerId = models.CharField(max_length=1000)
    authorisationCode = models.CharField(
        max_length=5000, null=True, blank=True)
    authorisationChannel = models.CharField(
        max_length=1000, null=True, blank=True)
    phoneNumber = models.CharField(max_length=200)
    accountNumber = models.CharField(max_length=200, null=True, blank=True)
    payement_reference = models.CharField(
        max_length=1000, blank=True, null=True)
    currency = models.CharField(max_length=100, blank=True, null=True)
    loanAmount = models.IntegerField(null=True, blank=True)
    collectionAmount = models.IntegerField(null=True, blank=True)
    elgible_amount = models.IntegerField(null=True, blank=True)
    dateOfDisbursement = models.DateTimeField(auto_now_add=True)
    dateOfCollection = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    totalCollectionAmount = models.IntegerField(null=True, blank=True)
    numberOfRepayments = models.IntegerField(null=True, blank=True)
    mandateReference = models.CharField(max_length=300, blank=True)
    loan_disk_id = models.CharField(max_length=300, null=True, blank=True)
    loan_status = models.BooleanField(default=False, null=True, blank=True)
    average_salary = models.FloatField(default=0.0)
    loan_obligation = models.FloatField(default=0.0)
    monthly_repayment = models.FloatField(default=0.0)
    loan_comment = models.CharField(
        max_length=300, null=True, blank=True, default="processing"
    )
    paid_amount = models.FloatField(null=True, blank=True, default=0)
    last_paid_amount = models.FloatField(null=True, blank=True)
    last_paid_date = models.DateTimeField(null=True, blank=True)
    outstanding_loan_bal = models.FloatField(null=True, blank=True)
    remita_loan_repayment_ref = models.CharField(
        max_length=700, null=True, blank=True)
    eligible_id = models.ForeignKey(
        "Eligible", on_delete=models.CASCADE, null=True, blank=True
    )
    repayment_id = models.CharField(max_length=700, null=True, blank=True)
    mandate_close = models.BooleanField(default=False, null=True, blank=True)
    repayment_count = models.IntegerField(null=True, blank=True)
    loan_percentage_taken = models.IntegerField(null=True, blank=True)
    eligible_for_top_up = models.BooleanField(
        default=False, null=True, blank=True)
    topup_eligible_amount = models.FloatField(null=True, blank=True)
    is_topup = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self) -> str:
        return self.customerId

    def mandate_reference(self):
        return self.mandateReference

    @classmethod
    def compare_with_remita(cls):

        loans = cls.objects.all()

        data = []
        file_data = pd.read_excel("./static/Get recent Mandate history.xlsx", sheet_name="Sheet1", dtype=str)
        print(file_data.head())


        data_header = [
            "First name",
            "Last name",
            "Phone",
            "Account",
            "Mandate",
            "Amount",
            "Outstanding",
            "Date",
            "Status",
            "Repayment",
            "Ministry",
            "Error",
        ]

        total_loans = len(file_data)
        for index, loan in iter(file_data.iterrows()):
            loan_target_mandate = loan.Mandate
            loan_objects = Loan.objects.filter(mandateReference = loan_target_mandate)
            print(loan_target_mandate, "Found >", loan_objects.count(), "objects")

            if not loan_objects.exists(): print("Not found"); continue;

            loan = loan_objects.first()
            loan_id = loan.customerId.replace("r_", "")

            try:
                response = loan_helpers.Remita_Manager.get_details_by_mandate(
                    loan_id, loan.authorisationCode, loan.mandateReference
                )
                loop_data = [
                    response["data"]["firstName"],
                    response["data"]["lastName"],
                    response["data"]["phoneNumber"],
                    response["data"]["salaryAccount"],
                    response["data"]["loanMandateReference"],
                    response["data"]["totalDisbursed"],
                    response["data"]["outstandingLoanBal"],
                    response["data"]["dateOfDisbursement"],
                    response["data"]["status"],
                    response["data"]["repayment"],
                    response["data"]["employerName"],
                    "-",
                ]

                data.append(loop_data)

                print(index, "of", total_loans, "")
            except Exception as e:
                loop_data = [
                    "-",
                    "-",
                    loan.phoneNumber,
                    "-",
                    loan.mandateReference,
                    loan.loanAmount,
                    loan.collectionAmount,
                    loan.dateOfDisbursement,
                    loan.loan_status,
                    loan.totalCollectionAmount,
                    "-",
                    f"{e}",
                ]

                print(f"error :::::::::::::::::::::::: {e}")

        with open("result2.csv", "w", encoding="UTF-8", newline="") as f:

            writer = csv.writer(f)

            # write the header
            writer.writerow(data_header)

            # write multiple rows
            writer.writerows(data)

    @staticmethod
    def get_sum_active_loans_from_remita(phone):

        total_active_loans = loan_helpers.Remita_Manager(
            phone).get_total_active_loans()

        return total_active_loans

    @staticmethod
    def get_approval(customerID, requested_loan_amount):

        borrower = Borrower.objects.filter(customerId=customerID)

        if borrower.exists():
            loan_offered = float(borrower[0].eligibleOffer)

        if loan_offered >= requested_loan_amount:
            return {"disbursementApproval": "OK", "message": "ok"}
        else:
            return {"disbursementApproval": "Invalid", "message": "Invalid Amount"}

    @staticmethod
    def create_Loan(
        customerId,
        authorisationCode,
        authorisationChannel,
        phoneNumber,
        accountNumber,
        currency,
        loanAmount,
        collectionAmount,
        dateOfDisbursement,
        dateOfCollection,
        totalCollectionAmount,
        numberOfRepayments,
        mandateReference,
        loan_disk_id,
        eligible_id,
    ):

        new_Loan = Loan(
            customerId=customerId,
            authorisationCode=authorisationCode,
            authorisationChannel=authorisationChannel,
            phoneNumber=phoneNumber,
            accountNumber=accountNumber,
            currency=currency,
            loanAmount=float(loanAmount),
            collectionAmount=float(collectionAmount),
            dateOfDisbursement=dateOfDisbursement,
            dateOfCollection=dateOfCollection,
            totalCollectionAmount=totalCollectionAmount,
            numberOfRepayments=numberOfRepayments,
            mandateReference=mandateReference,
            loan_disk_id=loan_disk_id,
            eligible_id=eligible_id,
        )

        new_Loan.save()

        return new_Loan

    @staticmethod
    def get_loandisk_id(borrower_phone_number):
        """
        This handles getting of borrower id from loan disk
        """
        url = f"https://api-main.loandisk.com/{settings.LOAN_DISK_PUBLICK_KEY}/{settings.LOAN_DISK_BRANCH_ID}/borrower/borrower_mobile/{borrower_phone_number}"

        headers = {
            "Authorization": "Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867",
            "Content-Type": "application/json",
        }

        print(borrower_phone_number, url)

        response = requests.request("GET", url, headers=headers)

        res = response.text
        print("\n\nThis is the borrower data retrieved from loan disk\n\n", res)
        get_loandisk = json.loads(res)
        return get_loandisk

    @staticmethod
    def post_loan_to_loandisk(
        loan_product_id,
        borrower_id,
        loan_application_id,
        loan_principal_amount,
        loan_released_date,
        loan_interest,
        loan_duration,
        loan_num_of_repayments,
        custom_field_4181,
        custom_field_4178,
        custom_field_4361,
        custom_field_5251,
        custom_field_4385,
        custom_field_6363,
        custom_field_4219,
        custom_field_4221,
    ):
        """
        This handles posting of loans to loan disk
        """
        url = f"https://api-main.loandisk.com/{settings.LOAN_DISK_PUBLICK_KEY}/{settings.LOAN_DISK_BRANCH_ID}/loan"
        payload = json.dumps(
            {
                "loan_product_id": f"{loan_product_id}",
                "borrower_id": f"{borrower_id}",
                "loan_application_id": f"{loan_application_id}",
                "loan_disbursed_by_id": "91595",
                "loan_principal_amount": loan_principal_amount,
                "loan_released_date": f"{loan_released_date}",
                "loan_interest_method": "flat_rate",
                "loan_interest_type": "percentage",
                "loan_interest_period": "Month",
                "loan_interest": loan_interest,
                "loan_duration_period": "Months",
                "loan_duration": loan_duration,
                "loan_payment_scheme_id": "3",
                "loan_num_of_repayments": loan_num_of_repayments,
                "loan_decimal_places": "round_up_to_five",
                "loan_status_id": "8",
                "custom_field_5262": "",
                "custom_field_4181": f"{custom_field_4181}",
                "custom_field_4178": f"{custom_field_4178}",
                "custom_field_5261": "",
                "custom_field_4361": f"{custom_field_4361}",
                "loan_fee_id_2746": 0,
                "loan_fee_id_3915": 0,
                "loan_fee_id_4002": 0,
                "loan_fee_id_4003": 0,
                "loan_fee_id_4004": 0,
                "loan_fee_id_4005": 0,
                "loan_fee_id_4006": 0,
                "custom_field_5251": f"{custom_field_5251}",
                "custom_field_4385": f"{custom_field_4385}",
                "custom_field_6363": f"{custom_field_6363}",
                "custom_field_4219": f"{custom_field_4219}",
                "custom_field_4221": f"{custom_field_4221}",
                # "custom_field_5262": mandate_ref
            }
        )

        headers = {
            "Authorization": "Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867",
            "Content-Type": "application/json",
        }

        logging.debug(
            f"payload that i'm posting to loan disk\n\n\nLoan Interest {loan_interest}"
        )

        # print("payload that i'm posting to loan disk")
        print(payload)
        logging.debug(payload)

        response = requests.request("POST", url, headers=headers, data=payload)

        res = response.text
        post_loandisk = json.loads(res)

        # print("here's loan disk response >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        logging.debug("here's loan disk response")
        # print(post_loandisk)
        # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        logging.debug(post_loandisk)
        borrower_qu = Borrower.objects.filter(borrower_id=borrower_id).last()
        try:
            if post_loandisk["error"]["code"] == "11":
                logging.debug("here's loan disk response error log 11")
                clear_catch(borrower_qu.borrower_phoneNumber)
                customer_retry_loan(
                    borrower_qu.borrower_phoneNumber, borrower_qu.borrower_firstname
                )
                return post_loandisk
            elif "maximum 22.5" in post_loandisk["response"]["Errors"][1]:
                clear_catch(borrower_qu.borrower_phoneNumber)
                customer_retry_loan(
                    borrower_qu.borrower_phoneNumber, borrower_qu.borrower_firstname
                )
                logging.debug("here's loan disk response Erros")
                return post_loandisk
            elif post_loandisk["response"]["Errors"]:
                clear_catch(borrower_qu.borrower_phoneNumber)
                customer_retry_loan(
                    borrower_qu.borrower_phoneNumber, borrower_qu.borrower_firstname
                )
                logging.debug("here's loan disk response Erros")
                return post_loandisk
        except KeyError:
            pass
        except:
            pass

        # try:
        #     if post_loandisk['error']['code'] == "11":
        #         logging.debug("here's loan disk response error log 11")
        #         return post_loandisk
        #     elif post_loandisk['response']['Errors']:
        #         logging.debug("here's loan disk response Erros")
        #         return post_loandisk
        # except KeyError:
        #     logging.debug("here's loan disk KeyErros")
        #     return post_loandisk
        # except:
        #     pass

        borrower_qu = Borrower.objects.filter(borrower_id=borrower_id).last()

        # get customer Transaction
        # get_trans = Transaction.objects.filter(
        #     customer_phone=borrower_qu.borrower_phoneNumber).last()

        logging.debug("\n\n\n\n\n\nTrans\n\n\\n\n\n\n\n\n")
        # save the loan to our own loan db after posting loan disk
        logging.debug(
            "before !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! passeed here>>>>>>>>>>>>>>>>>>>>>>>!!!!!!!!!!!!!!!!!!!!!"
        )
        # get_date_now = datetime.now()
        # total_col = (int(get_trans.amount) + int(get_trans.loan_fee)) * \
        #     int(float(settings.LOAN_DISK_LOAN_INTEREST_ONE) - round(float(settings.LOAN_DISK_LOAN_INTEREST_ONE))) if get_trans.loan_duration == 1 else (
        #         int(get_trans.amount) + int(get_trans.loan_fee)) * 0.35
        # logging.debug(f'{total_col}', "collections")

        # logging.debug(
        #     "passeed here>>>>>>>>>>>>>>>>>>>>>>>!!!!!!!!!!!!!!!!!!!!!")

        # logging.debug(f"{borrower_qu.borrower_remita_id}")
        # logging.debug(f"{total_col}")

        return post_loandisk

    def is_over_30_days(self) -> bool:
        diff = self.dateOfCollection - timezone.now()
        days = diff.days
        return days > 30


class Loan_History(models.Model):

    customerId = models.CharField(max_length=50, null=True, blank=True)
    authorisationCode = models.CharField(max_length=100)
    authorisationChannel = models.CharField(max_length=20)
    phoneNumber = models.CharField(max_length=20)
    loanProvider = models.CharField(max_length=20)
    loanAmount = models.DecimalField(
        decimal_places=2, max_digits=1000, null=True)
    outstandingAmount = models.DecimalField(
        decimal_places=2, max_digits=1000, null=True
    )
    loanDisbursementDate = models.DateField(null=True, blank=True)
    repaymentFreq = models.CharField(max_length=10)
    dateSaved = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.customerId)

    def loan_amount(self):
        return str(self.loanAmount)


def loan_disbursement(phone, validated_post):

    remita_manager = loan_helpers.Remita_Manager(phone)
    borrowe_query_set = Borrower.objects.filter(borrower_phoneNumber=phone)

    if borrowe_query_set.exists():
        data = remita_manager.loan_mandate_request(
            validated_post, borrowe_query_set[0])
        print("............................")
        print("...........................")
        print(data)

        if data.get("responseCode") == "00":
            eligible_id = Eligible.objects.filter(phoneNumber=phone).id
            loan = Loan.create_Loan(
                customerId=data.get("data", {}).get("customerId", ""),
                authorisationCode=borrowe_query_set[0].authorisationCode,
                authorisationChannel="USSD",
                phoneNumber=phone,
                accountNumber=data.get("data", {}).get("accountNumber", ""),
                currency=validated_post.get("currency"),
                loanAmount=validated_post.get("loanAmount"),
                collectionAmount=data.get("data", {}).get("amount", ""),
                dateOfDisbursement=validated_post.get("dateOfDisbursement"),
                dateOfCollection=validated_post.get("dateOfCollection"),
                totalCollectionAmount=validated_post.get(
                    "totalCollectionAmount"),
                numberOfRepayments=validated_post.get("numberOfRepayments"),
                mandateReference=data.get("data", {}).get(
                    "mandateReference", ""),
                eligible_id=eligible_id,
            )

            loan_query_set = Loan.objects.filter(phoneNumber=phone)
            mandateRef = loan_query_set[0].mandateReference
            print(">>>>>>>>>>the saved loan >>>>>>>>>>>")
            print(loan_query_set[0].mandateReference)
            print(loan_query_set[0].customerId)
            loan_query_set.update(mandateReference=mandateRef)

            Response = {
                "customerId": loan_query_set[0].customerId,
                "mandateReference": loan_query_set[0].mandateReference,
            }
            return Response
        else:
            Response = {"message": data.get("responseMsg")}
    else:
        Response = {"message": "Invalid user details"}

    return Response


class Eligible(models.Model):
    remita_id = models.CharField(max_length=600, null=True, blank=True)
    phoneNumber = models.CharField(max_length=20, null=True, blank=True)
    bank_code = models.CharField(max_length=700, null=True, blank=True)
    account_number = models.CharField(max_length=500, null=True, blank=True)
    Salary_history = models.TextField(null=True, blank=True)
    loan_history = models.TextField(null=True, blank=True)
    average_salary = models.FloatField(default=0.0)
    loan_obligation = models.FloatField(default=0.0)
    date_created = models.DateTimeField(
        auto_now_add=True, blank=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    is_salary_45_days = models.BooleanField(default=False)
    is_3_months_salary_in_5_months = models.BooleanField(default=False)
    eligible_amount = models.IntegerField(default=0)
    is_loan_taken = models.BooleanField(default=False)

    def __str__(self) -> str:
        return str(self.id)

    @staticmethod
    def create_new_eligible(request_payload, response_payload):

        # new_eligible_data = Eligible.create(
        #     remita_id="",
        #     phoneNumber="",
        #     bank_code="",
        #     account_number=,
        #     Salary_history=,
        #     loan_history=,
        #     is_salary_45_days=,
        #     is_3_months_salary_in_5_months=,

        # )
        # new_eligible_data.save()
        new_eligible_data = ""

        return new_eligible_data


class Approval(models.Model):
    authorisationCode = models.CharField(max_length=100, null=True, blank=True)
    authorisationChannel = models.CharField(
        max_length=20, null=True, blank=True)
    customerId = models.CharField(max_length=50)
    loanOffer = models.DecimalField(decimal_places=2, max_digits=1000)
    dateSaved = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.customerId


class Stop(models.Model):
    authorisationCode = models.CharField(max_length=100, null=True, blank=True)
    customerId = models.CharField(max_length=50)
    mandateReference = models.CharField(max_length=50)
    dateSaved = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.customerId


def stop_loan(mandateREf, validated_post):

    loan_query_set = Loan.objects.filter(mandateReference=mandateREf)
    print(">>>>>>the loan query returned from db<<<<<<<<<<<<<<<<")
    print(loan_query_set[0])
    authorisationCode = loan_query_set[0].authorisationCode
    print(">>>>>>>>The auth code return from the db>>>>>>>>>>>")
    print(authorisationCode)

    remita_manager = loan_helpers.Stop_Loan_Manager()
    data = remita_manager.stop_loan(validated_post, authorisationCode)
    print("//////////////////////////")
    print(data)

    if data.get("responseCode") == "00":

        customerID = data.get("data").get("customerId")
        print("--------------------------------------------------")
        print(customerID)

        Response = {
            "customerId": data.get("data").get("customerId"),
            "mandateReference": data.get("mandateReference"),
        }
        return Response
    else:
        Response = {"message": data.get("responseMsg")}

        return Response


class Catched_Cookie(models.Model):
    phone = models.CharField(max_length=300, null=True, blank=True)
    user_eligibile_amount = models.CharField(
        max_length=300, null=True, blank=True)
    disburse = models.BooleanField(default=False)
    date = models.DateTimeField(null=True, blank=True)
    message = models.CharField(max_length=500, null=True, blank=True)

    def has_expired(self, phone, max_age: int = 15) -> bool:
        """Check that catche cookie has not expired based on time created and current time (max_age->(minutes)
        Only for eligible users"""

        get_user_loans = Loan.objects.filter(phoneNumber=phone).last()

        if get_user_loans:
            if get_user_loans.loan_status == True:
                difference = timezone.now() - self.date
                is_eligible_user = (
                    True
                    if self.user_eligibile_amount != "0"
                    and self.user_eligibile_amount != "-"
                    else False
                )
                return (difference.total_seconds() / 60) > max_age and is_eligible_user

            elif (
                get_user_loans.loan_status == False
                and get_user_loans.loan_comment == "processing"
            ):
                return False

            else:
                difference = timezone.now() - self.date
                is_eligible_user = (
                    True
                    if self.user_eligibile_amount != "0"
                    and self.user_eligibile_amount != "-"
                    else False
                )
                return (difference.total_seconds() / 60) > max_age and is_eligible_user

        else:
            difference = timezone.now() - self.date
            is_eligible_user = (
                True
                if self.user_eligibile_amount != "0"
                and self.user_eligibile_amount != "-"
                else False
            )
            return (difference.total_seconds() / 60) > max_age and is_eligible_user

    def clear_cache(self):
        difference = timezone.now() - self.date
        if difference.total_seconds() / 3600 > 12:
            self.delete()

            return True

        else:
            return False

    def __str__(self) -> str:
        return str(self.phone)


class Transaction(models.Model):
    source = models.CharField(max_length=300)
    customer = models.CharField(max_length=600)
    customer_phone = models.CharField(max_length=300, null=True, blank=True)
    amount = models.IntegerField()
    ref_id = models.CharField(max_length=900)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_created=True, null=True, blank=True)
    disbursed = models.BooleanField(default=False)
    bank_code = models.CharField(max_length=300, null=True, blank=True)
    disbursed_expired = models.BooleanField(default=False)
    customer_account = models.CharField(max_length=300, null=True)
    source_ref = models.CharField(max_length=300, null=True, blank=True)
    loan_duration = models.IntegerField(null=True, blank=True)
    loan_fee = models.IntegerField(null=True, blank=True)
    woven_payout_status = models.CharField(
        max_length=100, blank=True, null=True)
    payout_retry_count = models.IntegerField(null=True, blank=True)
    verified = models.BooleanField(default=False)
    payment_payload = models.TextField(blank=True, null=True)
    topup = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.customer


class Loan_repayment(models.Model):
    mandate_ref = models.CharField(max_length=700, null=True, blank=True)
    customer_id = models.CharField(max_length=700, null=True, blank=True)
    autherization_code = models.CharField(
        max_length=700, null=True, blank=True)
    outstanding_loan_bal = models.FloatField(null=True, blank=True)
    last_amount_paid = models.FloatField(null=True, blank=True)
    total_disbursed = models.FloatField(null=True, blank=True)
    loan_status = models.CharField(
        max_length=700, null=True, blank=True, default="open"
    )
    paid_date = models.DateTimeField(
        null=True, blank=True, default="25-09-2021 12:30:30+0000"
    )
    remita_loan_repayment_ref = models.CharField(
        max_length=700, null=True, blank=True)
    eligible_id = models.ForeignKey(
        Eligible, on_delete=models.CASCADE, null=True, blank=True
    )
    loan_id = models.CharField(max_length=700, null=True, blank=True)
    repayment_id = models.CharField(max_length=700, null=True, blank=True)

    def __str__(self) -> str:
        return self.customer_id


class Repayment_check(models.Model):
    remita_customer_id = models.CharField(
        max_length=400, blank=True, null=True)
    first_name = models.CharField(max_length=400, blank=True, null=True)
    last_name = models.CharField(max_length=400, blank=True, null=True)
    phone_number = models.CharField(max_length=400, blank=True, null=True)
    loan_mandate_ref = models.CharField(max_length=400, blank=True, null=True)
    total_disbursed = models.FloatField(blank=True, null=True)
    outstanding_bal = models.FloatField(blank=True, null=True)
    employer_name = models.CharField(max_length=400, blank=True, null=True)
    salary_account = models.CharField(max_length=400, blank=True, null=True)
    authorixation_code = models.CharField(
        max_length=900, blank=True, null=True)
    salary_bank_code = models.CharField(max_length=400, blank=True, null=True)
    disbursement_account_bank = models.CharField(
        max_length=400, blank=True, null=True)
    disbursement_account = models.CharField(
        max_length=400, blank=True, null=True)
    transaction = models.FloatField(blank=True, null=True)
    deduction_date = models.DateTimeField(null=True, blank=True)
    repayment_status = models.CharField(max_length=400, blank=True, null=True)

    def __str__(self):
        return self.remita_customer_id


class InEligible_borrowers(models.Model):
    full_name = models.CharField(max_length=900, blank=True, null=True)
    phone = models.CharField(max_length=200, blank=True, null=True)
    date = models.DateTimeField(
        auto_now_add=False, default="2022-01-13 12:30:30+0000")

    def __str__(self) -> str:
        return self.phone


class Woven_statement(models.Model):
    mandate_id = models.CharField(max_length=50, null=True, blank=True)
    loan_id = models.CharField(max_length=50, null=True, blank=True)
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    charges = models.DecimalField(max_digits=5, decimal_places=2)
    transaction_type = models.CharField(max_length=7)
    payout_reference = models.CharField(max_length=100)
    narration = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=10)
    account_name = models.CharField(max_length=50)
    status = models.CharField(max_length=12)
    previous_balance = models.DecimalField(max_digits=11, decimal_places=2)
    new_balance = models.DecimalField(max_digits=11, decimal_places=2)
    created_date = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_created=True, null=True, blank=True)

    def __str__(self) -> str:
        return self.mandate_id

    @staticmethod
    def create_woven_debit_statement(request_payload, response_payload):

        new_woven_statement = Woven_statement.create(
            amount=request_payload["amount"],
            charges=10.00,
            transaction_type="Debit",
            payout_reference=response_payload["data"]["payout_reference"],
            narration=request_payload["narration"],
            bank_name=request_payload["beneficiary_bank_code"],
            account_number=request_payload["beneficiary_nuban"],
            account_name=request_payload["beneficiary_account_name"],
            status="response_payload['narration']",
            previous_balance=response_payload["data"]["payout_reference"],
            new_balance=response_payload["data"]["payout_reference"],
        )
        new_woven_statement.save()

        return new_woven_statement


class Mandate_Request(models.Model):
    mandate_request_payload = models.TextField()
    loan_disk_id = models.CharField(max_length=50, null=True, blank=True)
    amount = models.IntegerField()
    phone_number = models.CharField(max_length=20)
    mandateReference = models.CharField(max_length=100, null=True, blank=True)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_created=True, null=True, blank=True)
    borrower_name = models.CharField(max_length=1000, null=True, blank=True)
    request_count = models.IntegerField(default=1, null=True, blank=True)
    remita_gen_response = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return self.loan_disk_id


class Repayment_logs(models.Model):
    mandate_id = models.CharField(max_length=300, null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    repayment_amount = models.CharField(max_length=300, null=True, blank=True)
    phone = models.CharField(max_length=300, null=True, blank=True)
    repayment_attempts_log_id = models.ForeignKey(
        "Repayment_Attempt_logs", on_delete=models.CASCADE, null=True, blank=True
    )
    method = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self) -> str:
        return self.phone


class Repayment_Attempt_logs(models.Model):
    mandate_id = models.CharField(max_length=300, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    repayment_res = models.TextField()

    def __str__(self) -> str:
        return str(self.id)


class Repayment_Failed_Check(models.Model):
    phone = models.CharField(max_length=300, null=True, blank=True)
    remita_id = models.CharField(max_length=300, null=True, blank=True)
    mandate_ref = models.CharField(max_length=300, null=True, blank=True)
    autherization_code = models.CharField(
        max_length=700, null=True, blank=True)
    date = models.DateTimeField(
        auto_now=True, auto_now_add=False, blank=True, null=True
    )
    reason = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self) -> str:
        return self.phone


class Liberty_USSD_Constant_Variable(models.Model):
    loan_duration = models.IntegerField(default=1)
    eligible_interest = models.FloatField(null=True, blank=True)
    affordability_rate = models.FloatField(null=True, blank=True)
    loan_disk_one_month_interest = models.IntegerField(null=True, blank=True)
    loan_disk_two_month_interets = models.IntegerField(null=True, blank=True)
    loan_disk_two_month_post = models.FloatField(null=True, blank=True)
    loan_disk_three_month_interets = models.IntegerField(null=True, blank=True)
    loan_disk_four_month_interets = models.IntegerField(null=True, blank=True)
    loan_disk_pub_key = models.IntegerField(null=True, blank=True)
    loan_disk_branch_id = models.IntegerField(null=True, blank=True)
    loan_disk_fedwk_one_month = models.IntegerField(null=True, blank=True)
    loan_disk_fedwk_two_month = models.IntegerField(null=True, blank=True)
    loan_disk_fedwk_three_month = models.IntegerField(null=True, blank=True)
    loan_fee = models.IntegerField(null=True, blank=True)


class Woven_payout_payload(models.Model):
    payload = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.id)


class loandisk_post_response(models.Model):
    phone = models.CharField(max_length=300)
    pay_load_res = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.phone


class Re_Targeting(models.Model):
    first_name = models.CharField(max_length=400)
    last_name = models.CharField(max_length=400)
    eligible_amount = models.FloatField()
    loan_amount = models.FloatField(null=True, blank=True)
    phone_number = models.CharField(max_length=300)
    is_loan_taken = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now=True)
    aged = models.BooleanField(default=False)
    updated_date = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Marketing(models.Model):
    phone = models.CharField(max_length=300)
    name = models.CharField(max_length=500)
    eligible_amount = models.FloatField()
    active = models.BooleanField(default=False)
    aged = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class No_Salary_Past_45_Days(models.Model):
    phone = models.CharField(max_length=300)
    name = models.CharField(max_length=700, blank=True, null=True)
    ministry = models.CharField(max_length=900, blank=True, null=True)
    eligible = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.phone


class Bank_search_query(models.Model):
    payload = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.payload


class Loandisk_response_payload(models.Model):
    payload = models.TextField()
    date = models.DateTimeField(auto_now=True)


class Dailed_contact(models.Model):
    phone = models.CharField(max_length=300)
    date = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.phone


class Dailed_Eligbile(models.Model):
    phone = models.CharField(max_length=300)
    eligibility = models.CharField(max_length=300)
    remita_success_return = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now=True)
    loan = models.BooleanField(default=False)
    exclude = models.BooleanField(default=False)
    non_customers = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.phone


class Remita_in_eligible_future_customers(models.Model):
    phone = models.CharField(max_length=300)
    name = models.CharField(max_length=300)

    def __str__(self) -> str:
        return self.phone


class Remiat_failed_error_response(models.Model):
    phone = models.CharField(max_length=300)
    payload = models.TextField()
    date = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.phone


class Pending_loan_record(models.Model):
    phone = models.CharField(max_length=400)
    mandate = models.CharField(max_length=400)
    date = models.DateTimeField(auto_now=True)
    posted_to_loan_disk = models.BooleanField(default=False)
    payment_verified = models.BooleanField(default=False)
    amount = models.FloatField(default=0.0)
    payment_ref = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self) -> str:
        return self.phone


class OutLiersLogs(models.Model):
    ratio = models.IntegerField()
    using = models.CharField(max_length=500)
    max_val = models.FloatField()
    min_val = models.FloatField()
    salaries = models.CharField(max_length=150)
    low_lim = models.FloatField()
    up_lim = models.FloatField()
    segregation_ration = models.FloatField()
    multiplier = models.FloatField()
    phone = models.CharField(max_length=100, blank=True)
    date = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.id)


class LoanRequestPassToCelery(models.Model):
    phone = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now=True)
    payload = models.JSONField()
    loan_amt = models.FloatField()
    borrower_id = models.IntegerField()
    ref = models.CharField(max_length=400)
    channel = models.CharField(max_length=400)
    payment_disbursed = models.BooleanField(default=False)
    mandate_open = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.phone


class ManualCreatedMandate(models.Model):
    phone = models.CharField(max_length=100)
    amount = models.IntegerField()
    duration = models.IntegerField()
    mandate = models.CharField(max_length=300)
    date = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.phone


class SmsCampaign(models.Model):
    phone = models.CharField(max_length=100)
    name = models.CharField(max_length=300)
    eligible_amount = models.IntegerField()
    loan_amount = models.IntegerField()
    status = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.phone


class InfiniteCheckDB(models.Model):
    phone = models.CharField(max_length=100)
    remita_reponse = models.JSONField()
    elgible = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now=True)
    suspended = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.phone


class CreateMandateDB(models.Model):
    phone = models.CharField(max_length=400)
    amount = models.FloatField()
    salary_data = models.JSONField(blank=True, null=True)
    loan_data = models.JSONField(blank=True, null=True)
    salaries = models.TextField(blank=True, null=True)
    loan = models.TextField(blank=True, null=True)
    auth_code = models.CharField(max_length=300, blank=True, null=True)
    mandate = models.CharField(max_length=300, blank=True, null=True)
    mandate_created = models.BooleanField(default=False)
    mandate_close = models.BooleanField(default=False)
    remita_response = models.JSONField(blank=True, null=True)
    number_of_repayment = models.IntegerField(blank=True, null=True)
    remita_mandate_response = models.JSONField(blank=True, null=True)
    remainder_after_deduction = models.FloatField(blank=True, null=True)
    comment = models.CharField(max_length=300, blank=True)
    average_salary = models.FloatField(blank=True, null=True)
    dti = models.FloatField(blank=True, null=True)
    customer_suspended = models.BooleanField(default=False)
    customer_found = models.BooleanField(default=True)
    more_than_18_month = models.BooleanField(default=False)
    posted_to_loandisk = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.phone


class VeendhqLogin(models.Model):
    tx_jwt = models.TextField()
    x_jwt = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.x_jwt
