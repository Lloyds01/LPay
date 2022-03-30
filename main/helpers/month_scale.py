from pprint import pprint
from main.helpers.utils import utility
from web.models import USSD_Constant_Variable, constant_env


def scale_to_months(amount, months):

    # get_constant = constant_env()

    denominations = {}
    print("NET OFFER ---> ", amount)

    for i in range(1, months + 1):

        if i == 1:
            interest = constant_env().get(
                "loan_disk_one_month_interest"
            ) * constant_env().get("loan_duration")
            actual_interest = constant_env().get("loan_disk_one_month_interest")

        elif i == 2:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_two_month_post"
            )
            actual_interest = constant_env().get("loan_disk_two_month_post")

        elif i == 3:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_three_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_three_month_interets")

        elif i == 4:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_four_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_four_month_interets")

        elif i == 5:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_five_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_five_month_interets")

        elif i == 6:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_six_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_six_month_interets")

        elif i == 7:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_seven_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_seven_month_interets")

        elif i == 8:
            interest = constant_env().get("loan_duration") * constant_env().get(
                "loan_disk_eight_month_interets"
            )
            actual_interest = constant_env().get("loan_disk_eight_month_interets")

        loan_max = amount * i

        tenor = i
        net_offer = amount
        interest_rate = actual_interest / 100

        loan_offer = (net_offer * tenor) / (1 + (interest_rate * tenor))
        # Monthly
        hundred_percent = utility.currency_formatter(loan_offer * (100 / 100))

        eighty_percent = utility.currency_formatter(round(loan_offer * (87.5 / 100)))

        seventy_five_percent = utility.currency_formatter(
            round(loan_offer * (75 / 100))
        )

        sixty_two_percent = utility.currency_formatter(round(loan_offer * (62.5 / 100)))

        fifty_percent = utility.currency_formatter(round(loan_offer * (50 / 100)))

        thirty_seven_percent = utility.currency_formatter(
            round(loan_offer * (37.5 / 100))
        )

        twenty_five_percent = utility.currency_formatter(round(loan_offer * (25 / 100)))

        denominations[f"{i}-month"] = {
            100: hundred_percent,
            80: eighty_percent,
            75: seventy_five_percent,
            62: sixty_two_percent,
            50: fifty_percent,
            37: thirty_seven_percent,
            25: twenty_five_percent,
        }

    return denominations
