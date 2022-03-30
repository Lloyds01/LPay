from django.core.checks import messages
from django.conf import settings
from requests.models import Response
from rest_framework import response
from main.helpers import date_helpers
import requests
import hashlib  # import hashlib module
import datetime
import json
from dateutil.parser import parse
import pandas as pd
from functools import lru_cache


class Loan_Manager:

    base_url = "https://api-main.loandisk.com/"
    public_key = f"{settings.LOAN_DISK_PUBLICK_KEY}"
    branch_id = f"{settings.LOAN_DISK_BRANCH_ID}"
    api_key = "NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867"
    borrower_url = f"{base_url}{public_key}{branch_id}/borrower"
    loan_url = f"{base_url}{public_key}{branch_id}/loan"

    headers = {"Authorization": "Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867"}

    @lru_cache(maxsize=128)
    def borrower_api_call(self, **args):
        payload = args
        print("This is the borrower api call")

        print("supposed payload>>>>>>>>>>>>>>>>>>", payload)
        print("supposed self>>>>>>>>>>>>>>>>>", self)

        # response = requests.post(self.borrower_url, json=body, headers=self.headers)
        # data = response.json()

        # print("data from laon disk >>>>>>>>>>>>>>>>>>>>>>>>>>>>", data)
        # return data

    @lru_cache(maxsize=128)
    def loan_api_call(self, payload, headers):

        body = payload

        response = requests.post(self.loan_url, data=payload, headers=headers)
        data = response.json()
        print(">>>>>>>>>>>>>from direct response>>>>>>>>>>>")

        print(data)
        return data


base_url = "https://api-main.loandisk.com/"
public_key = f"{settings.LOAN_DISK_PUBLICK_KEY}"
branch_id = f"{settings.LOAN_DISK_BRANCH_ID}"
api_key = "NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867"
borrower_url = f"{base_url}/{public_key}/{branch_id}/borrower"
loan_url = f"{base_url}{public_key}{branch_id}/loan"

headers = {
    "Authorization": "Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867",
    "Content-Type": "application/json",
}


def borrower_api_call(
    currency,
    full_name,
    first_name,
    last_name,
    middle_name,
    company,
    id,
    n,
    m,
    phone,
    bvn,
    account,
    bankcode,
    bank,
    ministry,
):

    payload = {
        "borrower_country": currency,
        "borrower_fullname": full_name,
        "borrower_firstname": first_name,
        "borrower_lastname": last_name,
        "custom_field_5854": middle_name,
        "borrower_business_name": company,
        "borrower_unique_number": id,
        "borrower_gender": m,
        "borrower_title": n,
        "borrower_mobile": phone,
        "custom_field_5037": bvn,
        "custom_field_4220": account,
        "custom_field_4222": bankcode,
        "custom_field_4221": bank,
        "custom_field_6362": ministry,
    }

    payload = json.dumps(payload)

    url = f"https://api-main.loandisk.com/{settings.LOAN_DISK_PUBLICK_KEY}/{settings.LOAN_DISK_BRANCH_ID}/borrower"

    headers = {
        "Authorization": "Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text


def get_borrower_using_phone(phone):

    url = f"https://api-main.loandisk.com/{settings.LOAN_DISK_PUBLICK_KEY}/{settings.LOAN_DISK_BRANCH_ID}/borrower/borrower_mobile/{phone}"

    print(url)

    payload = {}
    headers = {
        "Authorization": "Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867",
        "Content-Type": "application/json",
        "Cookie": "AWSALBTG=bZfwQ3huDy9iYvEOOviOWjR/dWfwv8fMiOSVgCgclevStJO+kw+29pWpmoeGhh9O9up/E5VLXmpvEoS8hg9AePVl11mNXjoqLlcDnR+gROcdVlsLL+zJdaSLNYs4jj+Lk/3EcYolAwYy/rVIp4n3/rR+7WbgXEOseX8NuhWJ/LAl; AWSALBTGCORS=bZfwQ3huDy9iYvEOOviOWjR/dWfwv8fMiOSVgCgclevStJO+kw+29pWpmoeGhh9O9up/E5VLXmpvEoS8hg9AePVl11mNXjoqLlcDnR+gROcdVlsLL+zJdaSLNYs4jj+Lk/3EcYolAwYy/rVIp4n3/rR+7WbgXEOseX8NuhWJ/LAl; PHPSESSID=8evba1b49di360h7709nb9ppcf",
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()


def update_borrower_api_call(
    currency,
    full_name,
    first_name,
    last_name,
    middle_name,
    company,
    id,
    n,
    m,
    phone,
    bvn,
    account,
    bankcode,
    bank,
    ministry,
    borrower_id,
):

    payload = {
        "borrower_country": currency,
        "borrower_fullname": full_name,
        "borrower_firstname": first_name,
        "borrower_lastname": last_name,
        "custom_field_5854": middle_name,
        "borrower_business_name": company,
        "borrower_unique_number": id,
        "borrower_gender": m,
        "borrower_title": n,
        "borrower_mobile": phone,
        "custom_field_5037": bvn,
        "custom_field_4220": account,
        "custom_field_4222": bankcode,
        "custom_field_4221": bank,
        "custom_field_6362": ministry,
        "borrower_id": borrower_id,
    }

    payload = json.dumps(payload)

    url = f"https://api-main.loandisk.com/{settings.LOAN_DISK_PUBLICK_KEY}/{settings.LOAN_DISK_BRANCH_ID}/borrower"

    headers = {
        "Authorization": "Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867",
        "Content-Type": "application/json",
    }

    response = requests.request("PUT", url, headers=headers, data=payload)
    return response.text


def loan_disk_update_borrower(**args):
    payload_data = args
    payload = json.dumps(payload_data)

    url = f"https://api-main.loandisk.com/{settings.LOAN_DISK_PUBLICK_KEY}/{settings.LOAN_DISK_BRANCH_ID}/borrower"

    headers = {
        "Authorization": "Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867",
        "Content-Type": "application/json",
    }

    response = requests.request("PUT", url, headers=headers, data=payload)
    return response.text


def post_repayment(**args):
    payload_data = args
    payload = json.dumps(payload_data)

    url = f"https://api-main.loandisk.com/{settings.LOAN_DISK_PUBLICK_KEY}/{settings.LOAN_DISK_BRANCH_ID}/repayment"

    headers = {
        "Authorization": "Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text


def loan_disk_loan_update(**args):
    payload = args
    payload = json.dumps(payload)
    url = f"https://api-main.loandisk.com/{settings.LOAN_DISK_PUBLICK_KEY}/{settings.LOAN_DISK_BRANCH_ID}/loan"

    headers = {
        "Authorization": "Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867",
        "Content-Type": "application/json",
    }

    response = requests.request("PUT", url, headers=headers, data=payload)
    return response.text


def get_external_mandate_branch(mandate, phone):
    """
    This function check if the mandate pass in the parameter is found in the external branch
    """

    # get borrower using his phone

    url = f"https://api-main.loandisk.com/5797/16857/borrower/borrower_mobile/{phone}"

    payload = {}
    headers = {
        "Authorization": f"Basic NZaVE3RXR8WM7dgX9HKC664TKabRhp6pxDEdG867",
        "Content-Type": "application/json",
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    try:
        res = json.loads(response.text)
    except:
        res = response.text

    if type(res) == dict:

        try:
            if res["response"]["Results"]:
                loan_id = res["response"]["Results"][0][0]["borrower_id"]

                # fetch all the user external loan using his borrower id

                url = f"https://api-main.loandisk.com/5797/16857/loan/borrower/{loan_id}/from/1/count/50000"

                response = requests.request(
                    "GET", url, headers=headers, data=payload)

                try:
                    res = json.loads(response.text)
                except:
                    res = response.text

                if type(res) == dict:
                    if res["response"]["Results"]:
                        for ex_mandate in res["response"]["Results"][0]:
                            if ex_mandate["custom_field_5262"] == mandate:
                                data = {"found": True, "data": ex_mandate}
                                return data

                    else:
                        data = {"found": False}
                        return data

                else:
                    data = {"found": False}

                    return data

            else:
                data = {"found": False}

                return data
        except KeyError:

            data = {"found": False}

            return data
    else:
        data = {"found": False}

        return data
