from datetime import datetime
import requests
import json
from main.models import VeendhqLogin
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from django.conf import settings


class Veendhq_api:
    def veendhq_login_script():
        """
        Veendhq login api script
        """

        url = "https://api.veendhq.com/login?x-tag=veend-setup"

        payload = json.dumps(
            {"email": settings.VEENDHQ_EMAIL, "password": settings.VEENDHQ_PASSWORD}
        )
        headers = {"Content-Type": "application/json"}

        response = requests.request("POST", url, headers=headers, data=payload)

        data = json.loads(response.text)

        if data["status"] == "success":
            v_login = VeendhqLogin.objects.all().last()
            if v_login:
                v_login.tx_jwt = data["data"]["tx_jwt"]
                v_login.x_jwt = data["data"]["x_jwt"]
                v_login.date = datetime.now()
                v_login.save()
            else:
                VeendhqLogin.objects.create(
                    tx_jwt=data["data"]["tx_jwt"], x_jwt=data["data"]["x_jwt"]
                )

    def veendhq_loan_search(mandate_ref):
        """
        veendhq loan search function
        """
        mandate_ref = str(mandate_ref)
        mandate_ref = mandate_ref.replace(".0", "")

        login_key = VeendhqLogin.objects.all().last()

        url = f"https://api.veendhq.com/findloans?remitaMandateReference={mandate_ref}&desc=true&populate=user"

        payload = {}
        headers = {"x-jwt": f"{login_key.x_jwt}"}

        response = requests.request("GET", url, headers=headers, data=payload)

        data = response.text

        try:
            data = json.loads(response.text)

            if data["status"] == "success":
                if data["data"][0]["status"] == "active":
                    data_res = {
                        "loan_id": data["data"][0]["loanId"],
                        "client_id": data["data"][0]["user"]["clientId"],
                        "loan_status": data["data"][0]["status"],
                        "outstanding_amount": data["data"][0]["totalOutstanding"],
                    }
                    return data_res

                elif data["data"][0]["status"] == "closed":
                    data_res = {
                        "loan_id": data["data"][0]["loanId"],
                        "client_id": data["data"][0]["user"]["clientId"],
                        "loan_status": data["data"][0]["status"],
                        "outstanding_amount": data["data"][0]["totalOutstanding"],
                    }

                    return data_res
            else:
                return None
        except:
            if response == "Unauthorized":
                return response
            else:
                return None

    def veendhq_loan_repayment(**args):
        """
        veendhq loan repayment
        """
        import json

        url = "https://api.veendhq.com/loan-actions?x-tag=1"

        payload = json.dumps(args)

        login_key = VeendhqLogin.objects.all().last()

        headers = {"x-jwt": f"{login_key.x_jwt}",
                   "Content-Type": "application/json"}

        response = requests.request("POST", url, headers=headers, data=payload)


class LendlotApi:
    def post_repayment(loan_id, amount):
        todays_date = datetime.now()
        url = f"https://liberty.lendlot.com/fineract-provider/api/v1/loans/{loan_id}/transactions/?command=repayment"

        amount = str(amount).replace(",", "")

        payload = json.dumps({
            "dateFormat": "dd MMMM yyyy",
            "locale": "en",
            "transactionAmount": float(amount),
            "transactionDate": f'{todays_date.day} {todays_date.strftime("%B")} {todays_date.year}'
        })
        headers = {
            'Authorization': f'Basic {settings.LENDLOT_KEY}',
            'Fineract-Platform-TenantId': 'liberty',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        try:
            return json.loads(response.text)
        except:
            return response.text
