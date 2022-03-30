from django.conf import settings
import json
import requests


def sub_num(num):
    n = num[1:]
    n = "234" + str(n)
    return n


def send_payout_otp(num, otp, name):
    user_phone = sub_num(num) if len(num) == 11 else num.replace("+", "")

    url = "https://whispersms.xyz/transactional/send"

    payload = json.dumps(
        {
            "receiver": f"{user_phone}",
            "template": f"{settings.WEB_PAYOUT_OTP}",
            "place_holders": {"username": f"{name}", "otp": f"{otp}"},
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
