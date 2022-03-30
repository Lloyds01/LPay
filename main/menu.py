from rest_framework import response
from django.http import HttpResponse
import uuid

# from main.views import *
import logging
from main.helpers.loan_processing_helper import *
from main.tasks import dud_loan_processor, celery_update_loan_request_pass_to_celery
from main.helpers.utils import *
from main.helpers.send_sms import *
from main.models import *
from main.helpers.loan_topup import topup_view, active_loan_check
import datetime
import logging
from main.helpers.month_scale import scale_to_months
from pay.models import USSD_Constant_Variable, constant_env

# from celery_tasks import print_logger, queued_loan_processor, show_details

logging.basicConfig(filename="test.log", level=logging.DEBUG)

# constant_env() = constant_env()


def create_transaction(
    source, customer, amount, ref, acct, phone, bank_code, loan_fee, duration
):
    """
    This function handles creation of transaction
    """

    #### check if ther user has a loan and determine if this transaction should be a topup
    trans_is_topup = None
    if constant_env().get("topup") == True:
        check_user_loan = Loan.objects.filter(phoneNumber=phone, loan_status=True)
        if check_user_loan:
            trans_is_topup = True

    ######## check transaction before creating new transaction
    get_trans = Transaction.objects.filter(
        customer_phone=phone, created_at__date=datetime.date.today()
    ).order_by("-created_at")
    if get_trans:
        print(
            f"Here's get trans query object {get_trans.values('created_at')} \n\n\n\n"
        )

        print(f"Here's get trans query object {get_trans.first().created_at}")

        print(f"date time difference {diff_in_time(get_trans.first().created_at)}")

        print(f"{datetime.datetime.now()}\n\n\n")

        print(f"{get_trans.first().amount}  {get_trans.first().created_at} \n\n\n")

        hours_since_last_trans = diff_in_time(get_trans.first().created_at)

        if get_trans.count() > 2:
            data = {
                "status": False,
                "message": "END You've exhusted your transaction for today",
            }
            return data

        elif hours_since_last_trans < 2:
            data = {
                "status": False,
                "message": "END Sorry you've a recent transaction. kindly try again in next two hours",
            }
            return data

    if trans_is_topup == True:

        Transaction.objects.create(
            source=source,
            customer=customer,
            amount=amount,
            ref_id=ref,
            customer_account=acct,
            customer_phone=phone,
            bank_code=bank_code,
            loan_duration=duration,
            loan_fee=loan_fee,
            topup=True,
        )

        data = {"status": True, "message": ""}
        return data
    else:
        Transaction.objects.create(
            source=source,
            customer=customer,
            amount=amount,
            ref_id=ref,
            customer_account=acct,
            customer_phone=phone,
            bank_code=bank_code,
            loan_duration=duration,
            loan_fee=loan_fee,
        )

        data = {"status": True, "message": ""}
        return data


class Main_Menu:
    def back_func(num):
        """
        use this function to take user back on ussd session
        """
        x = num.split("*")
        response = None
        while "0" in x:
            index_of_x = x.index("0")
            n_x = x.index("0") - 1
            x.pop(index_of_x)
            x.pop(n_x)
            response = "*".join(x)

        if response == None:
            response = "*".join(x)
            return response

        return response

    def check_loan_bal(**args):
        data = args
        text = data["text"]
        session_id = data["session_id"]
        network_code = data["network_code"]
        phone_number = data["phone_number"]
        service_code = data["service_code"]
        borrower_phone_number = utility.phone_num_pre_extractor(phone_number)

        eligibileAmountChecker = None
        eligibileChecker = None
        eligiblechecker_error = None

        eligibileCheckers = Borrower.get_eligible_amount(
            phone=borrower_phone_number, channel="ussd"
        )
        eligibileAmountChecker = eligibileCheckers["eligible_amount"]
        eligibileChecker = eligibileCheckers

        ############### demo ####################
        # logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> demmy data >>>>>>>>>>>>>>>>>>>")
        # eligibileCheckers =  remita_demo_data(
        #     phone=borrower_phone_number)

        if eligibileCheckers == None:
            response = "END Sorry this product is for salary earners only !!"
            return response
        else:
            pass

        eligibileAmountChecker = eligibileCheckers["eligible_amount"]
        # eligibileChecker = eligibileCheckers

        check_user_loans = Loan.objects.filter(
            loan_status=True,
            loan_comment__iexact="open",
            phoneNumber=borrower_phone_number,
        )
        print(
            f"pass >>>>>>>>>>>\n \n>>This is number of loans borrower has {check_user_loans.count()}>>>\n\n>>>>>>>>>>>>>>>>>>> getting loan"
        )
        count_loans = check_user_loans.count()
        logging.debug(
            f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> done counting loan gotten"
        )

        logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> getting loan")

        if count_loans > 0:
            logging.debug(
                f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> user have active loan"
            )
            response = "END You've an active loan"
            return response

        if eligibileAmountChecker == 0:
            response = "END You don't have any outstanding loan with us"
            return response

        else:
            logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> enteered else")
            get_user_loan = Loan.objects.filter(
                loan_status=True,
                loan_comment__iexact="open",
                phoneNumber=borrower_phone_number,
            ).last()
            borrower_queryset = Borrower.objects.filter(
                borrower_phoneNumber=borrower_phone_number
            ).last()
            two_month_loan_max = round(float(eligibileAmountChecker) * 2)
            two_month_loan_max = utility.currency_formatter(two_month_loan_max)
            logging.debug(
                f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> finished filteru=ing"
            )

            if get_user_loan:
                logging.debug(
                    f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> user has an active loan"
                )
                remita_ref = get_user_loan.mandateReference.replace("r_", "")
                get_user_repayment = Loan_repayment.objects.filter(
                    mandate_ref=remita_ref
                ).last()
                if get_user_loan.paid_amount:
                    amt = utility.currency_formatter(
                        float(get_user_loan.loanAmount)
                        - float(get_user_loan.paid_amount)
                    )
                    loan_bal_check(
                        borrower_phone_number, borrower_queryset.borrower_firstname, amt
                    )
                    response = f"END Hello {borrower_queryset.borrower_firstname} Your loan balance is {amt}\n\n An sms loan balance has been sent to your phone"
                    return response
                else:

                    amt = utility.currency_formatter(get_user_loan.loanAmount)
                    loan_bal_check(
                        borrower_phone_number, borrower_queryset.borrower_firstname, amt
                    )
                    response = f"END Hello {borrower_queryset.borrower_firstname} Your loan balance is {amt}\n\n An sms loan balance has been sent to your phone"
                    return response
            else:
                response = "END You don't have an active loan"
                return response

    def main_menu():
        response = "CON Welcome to Liberty tech \n"
        response += "1. Get a loan \n"
        response += "2. Get balance \n"
        response += "3. Register your e-bank \n"
        response += "4. Contact us"

        return response

    def liberty_loan(**args):
        """
        Liberty loan function
        """
        data = args
        text = data["text"]
        session_id = data["session_id"]
        network_code = data["network_code"]
        phone_number = data["phone_number"]
        service_code = data["service_code"]
        borrower_phone_number = utility.phone_num_pre_extractor(phone_number)
        get_loandisk_hit = ""

        get_borrower_active_loan = Loan.objects.filter(
            phoneNumber=borrower_phone_number, loan_status=True
        )

        try:
            get_dailed = Dailed_contact.objects.get(phone=borrower_phone_number)
        except:
            ##### saved dauled contacts
            Dailed_contact.objects.create(phone=phone_number)

        try:
            Loan_Session.objects.get(session_id=session_id)
        except:
            Loan_Session.objects.create(
                phone_number=borrower_phone_number,
                service_code=service_code,
                network_code=network_code,
            )
        else:
            pass

        try:

            catched_ = Catched_Cookie.objects.filter(phone=borrower_phone_number).last()

            ###### if cache has passed 12 hours. if it passes 12 hours. clear the cache
            if catched_.clear_cache():
                raise ValueError("Cache cleard. please create new cache")

            ###### end of clear cache on demand

            if catched_.has_expired(borrower_phone_number):
                catched_.phone = ""
                catched_.save()
                raise ValueError("Cache has expired. allow new Remita call")

        except:

            # logging.debug(f"{datetime.datetime.now()}")
            catched_ = Catched_Cookie.objects.create(
                phone=borrower_phone_number, date=datetime.datetime.now()
            )

        go_back = "0"
        eligibileAmountChecker = None
        eligibileChecker = None
        eligiblechecker_error = None

        if catched_.disburse == True and catched_.message == "":
            response = "END Please wait your disbursment is still processing"
            return HttpResponse(response)

        elif catched_.message != None:
            response = catched_.message
            return response

        if catched_.user_eligibile_amount:
            eligibileChecker_ = catched_.user_eligibile_amount
            eligibileAmountChecker = float(eligibileChecker_)

        ################### top up logic ###############################

        ################ creating different hops for topup and none topup ###############################
        ################                                                  ###############################

        if constant_env().get("topup") == True:
            check_topup = topup_view(borrower_phone_number)

            if check_topup:
                if check_topup["eligible"] == False:
                    response = check_topup["message"]
                    return response
                else:
                    if (
                        catched_.user_eligibile_amount == None
                        or catched_.user_eligibile_amount == ""
                    ):
                        eligibileCheckers = Borrower.get_eligible_amount(
                            phone=borrower_phone_number, channel="ussd"
                        )
                        eligibileAmountChecker = eligibileCheckers["eligible_amount"]
                        eligibileChecker = eligibileCheckers
                        catched_.user_eligibile_amount = eligibileCheckers[
                            "eligible_amount"
                        ]
                        catched_.save()

                        if eligibileCheckers == None:
                            response = (
                                "END Sorry this product is for salary earners only !!"
                            )

                            return response
                        else:
                            pass

                        eligibileAmountChecker = eligibileCheckers["eligible_amount"]
                        eligibileChecker = eligibileCheckers
                        catched_.user_eligibile_amount = eligibileCheckers[
                            "eligible_amount"
                        ]
                        catched_.save()
                    else:
                        eligibileAmountChecker = int(catched_.user_eligibile_amount)

            else:

                eligibileCheckers = Borrower.get_eligible_amount(
                    phone=borrower_phone_number, channel="ussd"
                )
                eligibileAmountChecker = eligibileCheckers["eligible_amount"]
                eligibileChecker = eligibileCheckers
                catched_.user_eligibile_amount = eligibileCheckers["eligible_amount"]
                catched_.save()

                if eligibileCheckers == None:
                    response = "END Sorry this product is for salary earners only !!"

                    return response
                else:
                    pass

                eligibileAmountChecker = eligibileCheckers["eligible_amount"]
                eligibileChecker = eligibileCheckers
                catched_.user_eligibile_amount = eligibileCheckers["eligible_amount"]
                catched_.save()

            ####### eligibility ammount capping
            loan_cap = int(settings.LOAN_CAP)
            eligibileAmountChecker = (
                loan_cap
                if eligibileAmountChecker > loan_cap
                else eligibileAmountChecker
            )

            if eligibileAmountChecker == 0:
                check_non_borrowers_db = InEligible_borrowers.objects.filter(
                    phone=borrower_phone_number
                ).last()
                if eligiblechecker_error != None:
                    response = f"{eligiblechecker_error}"
                    return response

                elif (
                    eligibileChecker["message"]
                    == "Customer not found, Customer not found"
                ):
                    if not check_non_borrowers_db:
                        InEligible_borrowers.objects.create(
                            phone=borrower_phone_number, date=datetime.datetime.now()
                        )

                    response = "END Sorry this loan product is availiable for civil servants only! "
                    catched_.message = "END Sorry this loan product is availiable for civil servants only!"
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "Inactive customer, Inactive customer"
                ):
                    if not check_non_borrowers_db:
                        InEligible_borrowers.objects.create(
                            phone=borrower_phone_number, date=datetime.datetime.now()
                        )

                    response = "END sorry unable to get salary information"
                    catched_.message = "END sorry unable to get salary information"
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "Customer Is Currently Suspended, Customer Is Currently Suspended"
                ):
                    response = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.message = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "No salaries in past 45 days, Customer not found"
                ):
                    response = (
                        "END Sorry this loan product is availiable for civil servants!"
                    )
                    catched_.message = (
                        "END Sorry this loan product is availiable for civil servants!"
                    )
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "No salaries in past 45 days, SUCCESS"
                ):
                    response = (
                        "END Sorry this loan product is availiable for civil servants!"
                    )
                    catched_.message = (
                        "END Sorry this loan product is availiable for civil servants!"
                    )
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "No salaries in past 45 days, Customer Is Currently Suspended"
                ):
                    response = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.message = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.save()
                    return response

                elif eligibileChecker["message"] == "Customer Is Currently Suspended":
                    response = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.message = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.save()
                    return response

                elif eligibileChecker["message"] == "Ok, Unable to grant you loan":
                    response = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.message = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "Error Processing Request, Error Processing Request"
                ):
                    response = "END unable to process your request at this time. try again later"
                    catched_.message = "END unable to process your request at this time. try again later"
                    catched_.save()
                    return response
                elif (
                    eligibileChecker["message"]
                    == "Customer not from coverage region, SUCCESS"
                ):
                    response = "END Sorry cannot process eligibility, loans are not available to your employer at this time"
                    catched_.message = "END Sorry cannot process eligibility, loans are not available to your employer at this time"
                    catched_.save()
                    return response
                else:
                    if not check_non_borrowers_db:
                        InEligible_borrowers.objects.create(
                            phone=borrower_phone_number, date=datetime.datetime.now()
                        )

                    response = "END Sorry cannot process eligibility at this time please try again later"
                    catched_.message = "END Sorry cannot process eligibility at this time please try again later"
                    catched_.save()
                    return response

            else:
                data = "*".join(text)
                text = utility.go_back_func(data)

                borrower_queryset = Borrower.objects.filter(
                    borrower_phoneNumber=borrower_phone_number
                )

                if not borrower_queryset.exists():
                    # make salary request
                    remita_manager = loan_helpers.Remita_Manager(borrower_phone_number)
                    borrower_queryset = Borrower.objects.filter(
                        borrower_phoneNumber=borrower_phone_number
                    )
                    data = remita_manager.salary_request()

                borrower_queryset = borrower_queryset.last()

                b = nip_bank_search(borrower_queryset.bank_code)

                try:
                    get_user_bank = b["bank_code"]
                except:
                    get_user_bank = "None"

                ref = uuid.uuid1()
                payload = {
                    "beneficiary_nuban": f"{borrower_queryset.borrower_phoneNumber}",
                    "beneficiary_bank_code": get_user_bank,
                    "bank_code_scheme": "NIP",
                    "currency_code": "NGN",
                    "narration": "Loan disbursement",
                    "callback_url": "",
                }

                if text == "1":
                    response = "CON Liberty Assured can collect my data from 3rd party, deduct my salary at source and debit account linked to me for repayments \n"
                    response += "1. Accept \n"
                    response += "2. Decline"

                elif text == "1*1":
                    ######### topup new view ################

                    if constant_env().get("topup") == True:
                        if get_borrower_active_loan:
                            response = f"CON Hello {borrower_queryset.borrower_firstname} You're coming in for a topup \n"
                            response += "1. Accept \n"
                            response += "2. Decline"
                        else:
                            response = f"CON Hello {borrower_queryset.borrower_firstname} You may now proceed\n"
                            response += "1. Accept \n"
                            response += "2. Decline"
                    else:
                        response = f"CON Hello {borrower_queryset.borrower_firstname} You may now proceed\n"
                        response += "1. Accept \n"
                        response += "2. Decline"

                elif text == "1*1*2":
                    response = (
                        "END Thank you. visit libertyassured.com for more details"
                    )

                elif text == "1*1*2":
                    response = (
                        "END Thank you. visit libertyassured.com for more details"
                    )

                ########################## top up block  ############################
                # #######################                ############################
                # #########################              ###############################

                elif text == "1*1*1":

                    loan_offer_limit = 1000

                    check_user_loans = Loan.objects.filter(
                        loan_status=True,
                        loan_comment__iexact="open",
                        phoneNumber=borrower_phone_number,
                    )
                    count_loans = check_user_loans.count()

                    # if count_loans > 0:
                    #     response = "END You've an active loan"
                    #     return response

                    if eligibileAmountChecker == 0:
                        response = "END You are not eligible for a loan offer, please check back next time"

                    elif eligibileAmountChecker < loan_offer_limit:
                        logging.debug(
                            f"this's the eligible amount {eligibileAmountChecker}"
                        )
                        response = "END You are not eligible for a loan offer at this time, please check back later"
                    else:
                        # creating two elegibility amount checker functions one for a month and the other for 2months loan
                        response = f"CON Select a loan offer:\n"

                        ############### show customers one month eligibility only when they're eligible for loan topup
                        top_loan_checker = Loan.objects.filter(
                            loan_status=True, phoneNumber=borrower_phone_number
                        ).last()

                        # num_months = int(settings.LOAN_DURATION)

                        eligibilities = scale_to_months(
                            eligibileAmountChecker,
                            constant_env().get("loan_duration"),
                        )

                        #########################
                        ####### save user to re_targeting model db, just incase the issue doesn't take
                        ######## the loan. we'll be sending him/her remindeer to come back and apply for his / her loan
                        ########################
                        get_user_targeting = Re_Targeting.objects.filter(
                            phone_number=borrower_phone_number
                        ).last()
                        if get_user_targeting:
                            get_user_targeting.is_loan_taken = False
                            get_user_targeting.updated_date = datetime.datetime.now()
                            get_user_targeting.save()

                        else:
                            Re_Targeting.objects.create(
                                first_name=borrower_queryset.borrower_firstname,
                                last_name=borrower_queryset.borrower_lastname,
                                eligible_amount=eligibileAmountChecker,
                                phone_number=borrower_phone_number,
                            )

                        index_numbering = 1
                        for key, value in reversed(list(eligibilities.items())):

                            if int(key[0]) == 1:
                                loan_month_display = str(key).replace("-", " ")
                            elif int(key[0]) > 1:
                                loan_month_display = (
                                    str(key)
                                    .replace("-", " ")
                                    .replace("month", "months")
                                )

                            no_index = (key).replace("month", "").replace("-", "")
                            ## index numbering
                            response += (
                                ""
                                if int(no_index) == 2
                                else f"{index_numbering}. up to {utility.currency_formatter(value[100])} for {loan_month_display}\n"
                            )
                            index_numbering += 1

                        # if top_loan_checker:

                        #     response += f"1. up to {utility.currency_formatter(one_month_loan_max)} for 1 month\n"
                        # else:
                        #     response += f"1. up to {utility.currency_formatter(one_month_loan_max)} for 1 month\n2. up to {utility.currency_formatter(two_month_loan_max)} for 2 months"
                        # response += f"2. up to {utility.currency_formatter(two_month_loan_max)} for 2 months"

                elif text == "1*1*2":
                    response = "END Thank your. you can also use our\nour web app: libertyassured.com"

                elif (
                    "1*1*1*" in text
                    and int(text[-1]) <= constant_env().get("loan_duration")
                    and len(text) == 7
                ):

                    re_index_num = 0
                    if int(text[-1]) == 1:
                        re_index_num = "6"

                    elif int(text[-1]) == 2:
                        re_index_num = "5"
                    elif int(text[-1]) == 3:
                        re_index_num = "4"

                    elif int(text[-1]) == 4:
                        re_index_num = "3"
                    elif int(text[-1]) == 5:
                        return "END Invalid command"

                    elif int(text[-1]) == 6:
                        re_index_num = "1"

                    eligibilities = scale_to_months(
                        eligibileAmountChecker, constant_env().get("loan_duration")
                    )
                    print(
                        f"eligibilties: >>>>>>>>>>>>> {eligibilities[f'{text[-1]}-month']}"
                    )
                    response = f"CON Select a Loan Amount:\n"
                    response += (
                        f"1.{eligibilities[f'{re_index_num }-month'][100]}\n"
                        if currency_remover(
                            eligibilities[f"{re_index_num }-month"][100]
                        )
                        >= 3000
                        else ""
                    )  # 100%
                    response += (
                        f"2.{eligibilities[f'{re_index_num }-month'][80]}\n"
                        if currency_remover(eligibilities[f"{re_index_num }-month"][80])
                        >= 3000
                        else ""
                    )  # 87.5%
                    response += (
                        f"3.{eligibilities[f'{re_index_num }-month'][75]}\n"
                        if currency_remover(eligibilities[f"{re_index_num }-month"][75])
                        >= 3000
                        else ""
                    )  # 75%
                    response += (
                        f"4.{eligibilities[f'{re_index_num }-month'][62]}\n"
                        if currency_remover(eligibilities[f"{re_index_num }-month"][62])
                        >= 3000
                        else ""
                    )  # 62.5%
                    response += (
                        f"5.{eligibilities[f'{re_index_num }-month'][50]}\n"
                        if currency_remover(eligibilities[f"{re_index_num }-month"][50])
                        >= 3000
                        else ""
                    )  # 50%
                    response += (
                        f"6.{eligibilities[f'{re_index_num }-month'][37]}\n"
                        if currency_remover(eligibilities[f"{re_index_num }-month"][37])
                        >= 3000
                        else ""
                    )  # 37.5%
                    response += (
                        f"7.{eligibilities[f'{re_index_num }-month'][25]}\n"
                        if int(
                            currency_remover(
                                eligibilities[f"{re_index_num }-month"][25]
                            )
                        )
                        >= 3000
                        else ""
                    )  # 25%
                    response += f"{go_back}. back"

                    print(response)

                elif (
                    "1*1*1*" in text
                    and int(text[6]) <= constant_env().get("loan_duration")
                    and len(text) == 9
                ):

                    print(f"text \n\n\n {text} {text[6]}\n\n\n")

                    split_text_input = text.split("*")

                    re_index_num = 0
                    if int(split_text_input[3]) == 1:
                        re_index_num = "6"

                    elif int(split_text_input[3]) == 2:
                        re_index_num = "5"
                    elif int(split_text_input[3]) == 3:
                        re_index_num = "4"

                    elif int(split_text_input[3]) == 4:
                        re_index_num = "3"
                    elif int(split_text_input[3]) == 5:
                        return "END Invalid command"

                    elif int(split_text_input[3]) == 6:
                        re_index_num = "1"

                    percentages_map = {1: 100, 2: 80, 3: 75, 4: 62, 5: 50, 6: 37, 7: 25}

                    eligibilities = scale_to_months(
                        eligibileAmountChecker, constant_env().get("loan_duration")
                    )

                    x_index = int(re_index_num)
                    loan_percentage_required = eligibilities[f"{x_index}-month"]
                    loan_amount = loan_percentage_required[
                        percentages_map[int(text[-1])]
                    ]

                    ############### total_loan_repayment
                    total_loan_repayment = 0
                    if x_index == 1:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_one_month_interest"),
                            1,
                        )
                    elif x_index == 2:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_two_month_post"),
                            2,
                        )
                    elif x_index == 3:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_three_month_interets"),
                            3,
                        )

                    elif x_index == 4:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_four_month_interets"),
                            4,
                        )

                    elif x_index == 5:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_four_month_interets"),
                            5,
                        )

                    elif x_index == 6:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_four_month_interets"),
                            6,
                        )

                    elif x_index == 7:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_four_month_interets"),
                            7,
                        )

                    elif x_index == 8:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_eight_month_interets"),
                            8,
                        )

                    ########### loan monthly repayment
                    loan_monthly_interest = 0

                    if x_index == 1:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_one_month_interest"
                        )

                    elif x_index == 2:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_two_month_post"
                        )

                    elif x_index == 3:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_three_month_interets"
                        )

                    elif x_index == 4:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_four_month_interets"
                        )

                    elif x_index == 5:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_four_month_interets"
                        )

                    elif x_index == 6:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_four_month_interets"
                        )

                    elif x_index == 7:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_seven_month_interets"
                        )

                    elif x_index == 8:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_eight_month_interets"
                        )

                    loan_monthly_repayment_amount = loan_monthly_repayment_amt(
                        loan_amount, int(re_index_num), loan_monthly_interets
                    )
                    #########

                    ##### Total repayment {total_loan_repayment}.\n
                    ###############3

                    response = f"CON Loan amt: {loan_amount}.\nTenure: {re_index_num }\nMonthly payment: {loan_monthly_repayment_amount}   \nLoan Fee: {loan_fee(loan_amount)}.\nT&C Libertyng.com\n\n"
                    response += f"1. Confirm & agree\n"
                    response += f"2.Decline\n"
                    response += f"{go_back}. back"

                elif (
                    "1*1*1*" in text
                    and int(text[6]) <= constant_env().get("loan_duration")
                    and len(text) == 11
                    and int(text[-1]) == 1
                ):

                    split_text_input = text.split("*")

                    re_index_num = 0
                    if int(split_text_input[3]) == 1:
                        re_index_num = "6"

                    elif int(split_text_input[3]) == 2:
                        re_index_num = "5"
                    elif int(split_text_input[3]) == 3:
                        re_index_num = "4"

                    elif int(split_text_input[3]) == 4:
                        re_index_num = "3"
                    elif int(split_text_input[3]) == 5:
                        return "END Invalid command"

                    elif int(split_text_input[3]) == 6:
                        re_index_num = "1"

                    percentages_map = {1: 100, 2: 80, 3: 75, 4: 62, 5: 50, 6: 37, 7: 25}

                    eligibilities = scale_to_months(
                        eligibileAmountChecker, constant_env().get("loan_duration")
                    )
                    split_text_input = text.split("*")
                    x_index = int(re_index_num)
                    loan_percentage_required = eligibilities[f"{x_index}-month"]

                    loan_amount = loan_percentage_required[
                        percentages_map[int(text[-3])]
                    ]

                    if float(
                        str(loan_amount).replace("N", "").replace(",", "")
                    ) >= float(settings.MAX_LOAN_CAP):
                        response = "END Please contanct support for further assistance"
                        return response

                    # For restricting borrower from borrowing loan multiple time within 12hrs
                    # x = datetime.datetime.now()
                    catched_.disburse = True
                    catched_.date = datetime.datetime.now()
                    catched_.message = ""
                    catched_.save()
                    # y = datetime.now()
                    # print_logger.delay(x,y,"Hop6cache ")

                    # x = datetime.datetime.now()
                    reference = f"Libty-{ref.hex}"
                    load_num_fee = loan_fee(
                        str(loan_amount).replace("N", "").replace(",", "")
                    )
                    y = datetime.datetime.now()
                    # print_logger.delay(x,y,"Loan Fee ")

                    # x = datetime.datetime.now()
                    trans_status = create_transaction(
                        "woven",
                        borrower_queryset.borrower_fullname,
                        float(str(loan_amount).replace("N", "").replace(",", "")),
                        reference,
                        borrower_queryset.acct_no,
                        borrower_phone_number,
                        borrower_queryset.bank_code,
                        float(str(load_num_fee).replace("N", "").replace(",", "")),
                        duration=int(re_index_num),
                    )

                    if trans_status["status"] == False:
                        catched_.disburse = False
                        catched_.date = datetime.datetime.now()
                        catched_.message = trans_status["message"]
                        catched_.save()
                        return trans_status["message"]

                    else:

                        # print_logger.delay(x,y,"Woven ")
                        # Loan processing for one month loan here

                        # x = datetime.datetime.now()
                        borrower_loan_choice_amount = (
                            str(loan_amount).replace("N", "").replace(",", "")
                        )
                        y = datetime.datetime.now()
                        # print_logger.delay(x,y,"ONE MONTH PAY ")

                        # x = datetime.datetime.now()
                        # loan_processor(borrower_loan_choice_amount, payload, borrower_queryset, ref)

                        dud_loan_processor.delay(
                            borrower_loan_choice_amount,
                            payload,
                            borrower_queryset.id,
                            reference,
                            "ussd",
                        )

                        LoanRequestPassToCelery.objects.create(
                            payload=payload,
                            phone=borrower_phone_number,
                            loan_amt=float(borrower_loan_choice_amount),
                            borrower_id=borrower_queryset.id,
                            ref=reference,
                            channel="ussd",
                        )

                        y = datetime.datetime.now()
                        # print_logger.delay(x,y,"SEND LOAN MESSAGE ")
                        response = "END Loan application has been sent for processing, you should receive a credit notification from your bank shortly"
                        return response

                    # Loan processing for one month loan end here

                elif (
                    "1*1*1*" in text
                    and int(text[4]) <= constant_env().get("loan_duration")
                    and len(text) == 11
                    and int(text[-1]) == 2
                ):
                    response = (
                        "END Thank you. visit libertyassured.com for more details"
                    )

                else:
                    response = "END Invalid command"

                return response

        else:
            """
            This block of condition show different hops when topup is not turned on
            """

            check_for_active_loans = active_loan_check(borrower_phone_number)

            if check_for_active_loans["status"] == True:
                catched_.message = check_for_active_loans["message"]
                catched_.user_eligibile_amount = ""
                catched_.save()
                return check_for_active_loans["message"]

            if (
                catched_.user_eligibile_amount == None
                or catched_.user_eligibile_amount == ""
            ):
                eligibileCheckers = Borrower.get_eligible_amount(
                    phone=borrower_phone_number, channel="ussd"
                )

                eligibileAmountChecker = eligibileCheckers["eligible_amount"]
                eligibileChecker = eligibileCheckers
                catched_.user_eligibile_amount = eligibileCheckers["eligible_amount"]
                catched_.save()

                if eligibileCheckers == None:
                    response = "END Sorry this product is for salary earners only !!"

                    return response
                else:
                    pass

                eligibileAmountChecker = eligibileCheckers["eligible_amount"]
                eligibileChecker = eligibileCheckers
                catched_.user_eligibile_amount = eligibileCheckers["eligible_amount"]
                catched_.save()

            else:
                eligibileAmountChecker = int(catched_.user_eligibile_amount)

            ####### eligibility ammount capping
            loan_cap = int(settings.LOAN_CAP)
            eligibileAmountChecker = (
                loan_cap
                if eligibileAmountChecker > loan_cap
                else eligibileAmountChecker
            )

            if eligibileAmountChecker == 0:
                check_non_borrowers_db = InEligible_borrowers.objects.filter(
                    phone=borrower_phone_number
                ).last()
                if eligiblechecker_error != None:
                    response = f"{eligiblechecker_error}"
                    return response

                elif (
                    eligibileChecker["message"]
                    == "Customer not found, Customer not found"
                ):
                    if not check_non_borrowers_db:
                        InEligible_borrowers.objects.create(
                            phone=borrower_phone_number, date=datetime.datetime.now()
                        )

                    response = "END Sorry this loan product is availiable for civil servants only! "
                    catched_.message = "END Sorry this loan product is availiable for civil servants only!"
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "Inactive customer, Inactive customer"
                ):
                    if not check_non_borrowers_db:
                        InEligible_borrowers.objects.create(
                            phone=borrower_phone_number, date=datetime.datetime.now()
                        )

                    response = "END sorry unable to get salary information"
                    catched_.message = "END sorry unable to get salary information"
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "Customer Is Currently Suspended, Customer Is Currently Suspended"
                ):
                    response = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.message = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "No salaries in past 45 days, Customer not found"
                ):
                    response = (
                        "END Sorry this loan product is availiable for civil servants!"
                    )
                    catched_.message = (
                        "END Sorry this loan product is availiable for civil servants!"
                    )
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "No salaries in past 45 days, SUCCESS"
                ):
                    response = (
                        "END Sorry this loan product is availiable for civil servants!"
                    )
                    catched_.message = (
                        "END Sorry this loan product is availiable for civil servants!"
                    )
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "No salaries in past 45 days, Customer Is Currently Suspended"
                ):
                    response = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.message = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.save()
                    return response

                elif eligibileChecker["message"] == "Customer Is Currently Suspended":
                    response = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.message = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.save()
                    return response

                elif eligibileChecker["message"] == "Ok, Unable to grant you loan":
                    response = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.message = "END You're currently not eligible based on your current credit data. try again later"
                    catched_.save()
                    return response

                elif (
                    eligibileChecker["message"]
                    == "Error Processing Request, Error Processing Request"
                ):
                    response = "END unable to process your request at this time. try again later"
                    catched_.message = "END unable to process your request at this time. try again later"
                    catched_.save()
                    return response
                elif (
                    eligibileChecker["message"]
                    == "Customer not from coverage region, SUCCESS"
                ):
                    response = "END Sorry cannot process eligibility, loans are not available to your employer at this time"
                    catched_.message = "END Sorry cannot process eligibility, loans are not available to your employer at this time"
                    catched_.save()
                    return response
                else:
                    if not check_non_borrowers_db:
                        InEligible_borrowers.objects.create(
                            phone=borrower_phone_number, date=datetime.datetime.now()
                        )

                    response = "END Sorry cannot process eligibility at this time please try again later"
                    catched_.message = "END Sorry cannot process eligibility at this time please try again later"
                    catched_.save()
                    return response

            else:
                data = "*".join(text)
                text = utility.go_back_func(data)

                borrower_queryset = Borrower.objects.filter(
                    borrower_phoneNumber=borrower_phone_number
                )

                if not borrower_queryset.exists():
                    # make salary request
                    remita_manager = loan_helpers.Remita_Manager(borrower_phone_number)
                    borrower_queryset = Borrower.objects.filter(
                        borrower_phoneNumber=borrower_phone_number
                    )
                    data = remita_manager.salary_request()

                borrower_queryset = borrower_queryset.last()

                b = nip_bank_search(borrower_queryset.bank_code)

                try:
                    get_user_bank = b["bank_code"]
                except:
                    get_user_bank = "None"

                ref = uuid.uuid1()
                payload = {
                    "beneficiary_nuban": f"{borrower_queryset.borrower_phoneNumber}",
                    "beneficiary_bank_code": get_user_bank,
                    "bank_code_scheme": "NIP",
                    "currency_code": "NGN",
                    "narration": "Loan disbursement",
                    "callback_url": "",
                }

                if text == "1":
                    response = "CON Liberty Assured can collect my data from 3rd party, deduct my salary at source and debit account linked to me for repayments \n"
                    response += "1. Accept \n"
                    response += "2. Decline"

                elif text == "1*2":
                    response = (
                        "END Thank you. visit libertyassured.com for more details"
                    )

                elif text == "1*1":

                    loan_offer_limit = 1000

                    check_user_loans = Loan.objects.filter(
                        loan_status=True,
                        loan_comment__iexact="open",
                        phoneNumber=borrower_phone_number,
                    )
                    count_loans = check_user_loans.count()

                    # if count_loans > 0:
                    #     response = "END You've an active loan"
                    #     return response

                    if eligibileAmountChecker == 0:
                        response = "END You are not eligible for a loan offer, please check back next time"

                    elif eligibileAmountChecker < loan_offer_limit:
                        logging.debug(
                            f"this's the eligible amount {eligibileAmountChecker}"
                        )
                        response = "END You are not eligible for a loan offer at this time, please check back later"
                    else:
                        # creating two elegibility amount checker functions one for a month and the other for 2months loan
                        response = f"CON Select a loan offer:\n"

                        ############### show customers one month eligibility only when they're eligible for loan topup
                        top_loan_checker = Loan.objects.filter(
                            loan_status=True, phoneNumber=borrower_phone_number
                        ).last()

                        # num_months = int(settings.LOAN_DURATION)

                        eligibilities = scale_to_months(
                            eligibileAmountChecker,
                            constant_env().get("loan_duration"),
                        )

                        #########################
                        ####### save user to re_targeting model db, just incase the issue doesn't take
                        ######## the loan. we'll be sending him/her remindeer to come back and apply for his / her loan
                        ########################
                        get_user_targeting = Re_Targeting.objects.filter(
                            phone_number=borrower_phone_number
                        ).last()
                        if get_user_targeting:
                            get_user_targeting.is_loan_taken = False
                            get_user_targeting.updated_date = datetime.datetime.now()
                            get_user_targeting.save()

                        else:
                            Re_Targeting.objects.create(
                                first_name=borrower_queryset.borrower_firstname,
                                last_name=borrower_queryset.borrower_lastname,
                                eligible_amount=eligibileAmountChecker,
                                phone_number=borrower_phone_number,
                            )

                        index_numbering = 1
                        for key, value in reversed(list(eligibilities.items())):

                            if int(key[0]) == 1:
                                loan_month_display = str(key).replace("-", " ")
                            elif int(key[0]) > 1:
                                loan_month_display = (
                                    str(key)
                                    .replace("-", " ")
                                    .replace("month", "months")
                                )

                            no_index = (key).replace("month", "").replace("-", "")
                            ## index numbering
                            response += (
                                ""
                                if int(no_index) == 2
                                else f"{index_numbering}. up to {utility.currency_formatter(value[100])} for {loan_month_display}\n"
                            )
                            index_numbering += 1

                        # if top_loan_checker:

                        #     response += f"1. up to {utility.currency_formatter(one_month_loan_max)} for 1 month\n"
                        # else:
                        #     response += f"1. up to {utility.currency_formatter(one_month_loan_max)} for 1 month\n2. up to {utility.currency_formatter(two_month_loan_max)} for 2 months"
                        # response += f"2. up to {utility.currency_formatter(two_month_loan_max)} for 2 months"

                elif (
                    "1*1*" in text
                    and int(text[-1]) <= constant_env().get("loan_duration")
                    and len(text) == 5
                ):

                    re_index_num = 0
                    if int(text[-1]) == 1:
                        re_index_num = "6"

                    elif int(text[-1]) == 2:
                        re_index_num = "5"
                    elif int(text[-1]) == 3:
                        re_index_num = "4"

                    elif int(text[-1]) == 4:
                        re_index_num = "3"
                    elif int(text[-1]) == 5:
                        return "END Invalid command"

                    elif int(text[-1]) == 6:
                        re_index_num = "1"

                    eligibilities = scale_to_months(
                        eligibileAmountChecker, constant_env().get("loan_duration")
                    )
                    print(
                        f"eligibilties: >>>>>>>>>>>>> {eligibilities[f'{text[-1]}-month']}"
                    )
                    response = f"CON Select a Loan Amount:\n"
                    response += (
                        f"1.{eligibilities[f'{re_index_num }-month'][100]}\n"
                        if currency_remover(
                            eligibilities[f"{re_index_num }-month"][100]
                        )
                        >= 3000
                        else ""
                    )  # 100%
                    response += (
                        f"2.{eligibilities[f'{re_index_num }-month'][80]}\n"
                        if currency_remover(eligibilities[f"{re_index_num }-month"][80])
                        >= 3000
                        else ""
                    )  # 87.5%
                    response += (
                        f"3.{eligibilities[f'{re_index_num }-month'][75]}\n"
                        if currency_remover(eligibilities[f"{re_index_num }-month"][75])
                        >= 3000
                        else ""
                    )  # 75%
                    response += (
                        f"4.{eligibilities[f'{re_index_num }-month'][62]}\n"
                        if currency_remover(eligibilities[f"{re_index_num }-month"][62])
                        >= 3000
                        else ""
                    )  # 62.5%
                    response += (
                        f"5.{eligibilities[f'{re_index_num }-month'][50]}\n"
                        if currency_remover(eligibilities[f"{re_index_num }-month"][50])
                        >= 3000
                        else ""
                    )  # 50%
                    response += (
                        f"6.{eligibilities[f'{re_index_num }-month'][37]}\n"
                        if currency_remover(eligibilities[f"{re_index_num }-month"][37])
                        >= 3000
                        else ""
                    )  # 37.5%
                    response += (
                        f"7.{eligibilities[f'{re_index_num }-month'][25]}\n"
                        if int(
                            currency_remover(
                                eligibilities[f"{re_index_num }-month"][25]
                            )
                        )
                        >= 3000
                        else ""
                    )  # 25%
                    response += f"{go_back}. back"

                    print(response)

                elif (
                    "1*1*" in text
                    and int(text[6]) <= constant_env().get("loan_duration")
                    and len(text) == 7
                ):

                    print(f"text \n\n\n {text} {text[6]}\n\n\n")

                    split_text_input = text.split("*")

                    re_index_num = 0
                    if int(split_text_input[2]) == 1:
                        re_index_num = "6"

                    elif int(split_text_input[2]) == 2:
                        re_index_num = "5"
                    elif int(split_text_input[2]) == 3:
                        re_index_num = "4"

                    elif int(split_text_input[2]) == 4:
                        re_index_num = "3"
                    elif int(split_text_input[2]) == 5:
                        return "END Invalid command"

                    elif int(split_text_input[2]) == 6:
                        re_index_num = "1"

                    percentages_map = {1: 100, 2: 80, 3: 75, 4: 62, 5: 50, 6: 37, 7: 25}

                    eligibilities = scale_to_months(
                        eligibileAmountChecker, constant_env().get("loan_duration")
                    )

                    x_index = int(re_index_num)
                    loan_percentage_required = eligibilities[f"{x_index}-month"]
                    loan_amount = loan_percentage_required[
                        percentages_map[int(text[-1])]
                    ]

                    ############### total_loan_repayment
                    total_loan_repayment = 0
                    if x_index == 1:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_one_month_interest"),
                            1,
                        )
                    elif x_index == 2:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_two_month_post"),
                            2,
                        )
                    elif x_index == 3:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_three_month_interets"),
                            3,
                        )

                    elif x_index == 4:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_four_month_interets"),
                            4,
                        )

                    elif x_index == 5:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_four_month_interets"),
                            5,
                        )

                    elif x_index == 6:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_four_month_interets"),
                            6,
                        )

                    elif x_index == 7:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_four_month_interets"),
                            7,
                        )

                    elif x_index == 8:
                        total_loan_repayment = total_loan_repayment_calculator(
                            loan_amount,
                            constant_env().get("loan_disk_eight_month_interets"),
                            8,
                        )

                    ########### loan monthly repayment
                    loan_monthly_interest = 0

                    if x_index == 1:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_one_month_interest"
                        )

                    elif x_index == 2:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_two_month_post"
                        )

                    elif x_index == 3:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_three_month_interets"
                        )

                    elif x_index == 4:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_four_month_interets"
                        )

                    elif x_index == 5:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_four_month_interets"
                        )

                    elif x_index == 6:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_four_month_interets"
                        )

                    elif x_index == 7:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_seven_month_interets"
                        )

                    elif x_index == 8:
                        loan_monthly_interets = constant_env().get(
                            "loan_disk_eight_month_interets"
                        )

                    loan_monthly_repayment_amount = loan_monthly_repayment_amt(
                        loan_amount, int(re_index_num), loan_monthly_interets
                    )
                    #########

                    ##### Total repayment {total_loan_repayment}.\n
                    ###############3

                    response = f"CON Loan amt: {loan_amount}.\nTenure: {re_index_num }\nMonthly payment: {loan_monthly_repayment_amount}   \nLoan Fee: {loan_fee(loan_amount)}.\nT&C Libertyng.com\n\n"
                    response += f"1. Confirm & agree\n"
                    response += f"2.Decline\n"
                    response += f"{go_back}. back"

                elif (
                    "1*1*" in text
                    and int(text[6]) <= constant_env().get("loan_duration")
                    and len(text) == 9
                    and int(text[-1]) == 1
                ):

                    split_text_input = text.split("*")

                    re_index_num = 0
                    if int(split_text_input[2]) == 1:
                        re_index_num = "6"

                    elif int(split_text_input[2]) == 2:
                        re_index_num = "5"
                    elif int(split_text_input[2]) == 3:
                        re_index_num = "4"

                    elif int(split_text_input[2]) == 4:
                        re_index_num = "3"
                    elif int(split_text_input[2]) == 5:
                        return "END Invalid command"

                    elif int(split_text_input[2]) == 6:
                        re_index_num = "1"

                    percentages_map = {1: 100, 2: 80, 3: 75, 4: 62, 5: 50, 6: 37, 7: 25}

                    eligibilities = scale_to_months(
                        eligibileAmountChecker, constant_env().get("loan_duration")
                    )
                    split_text_input = text.split("*")
                    x_index = int(re_index_num)

                    loan_percentage_required = eligibilities[f"{x_index}-month"]

                    loan_amount = loan_percentage_required[
                        percentages_map[int(text[-3])]
                    ]

                    if float(
                        str(loan_amount).replace("N", "").replace(",", "")
                    ) >= float(settings.MAX_LOAN_CAP):
                        response = "END Please contanct support for further assistance"
                        return response

                    # For restricting borrower from borrowing loan multiple time within 12hrs
                    # x = datetime.datetime.now()
                    catched_.disburse = True
                    catched_.date = datetime.datetime.now()
                    catched_.message = ""
                    catched_.save()
                    # y = datetime.now()
                    # print_logger.delay(x,y,"Hop6cache ")

                    # x = datetime.datetime.now()
                    reference = f"Libty-{ref.hex}"
                    load_num_fee = loan_fee(
                        str(loan_amount).replace("N", "").replace(",", "")
                    )
                    y = datetime.datetime.now()
                    # print_logger.delay(x,y,"Loan Fee ")

                    # x = datetime.datetime.now()
                    trans_status = create_transaction(
                        "woven",
                        borrower_queryset.borrower_fullname,
                        float(str(loan_amount).replace("N", "").replace(",", "")),
                        reference,
                        borrower_queryset.acct_no,
                        borrower_phone_number,
                        borrower_queryset.bank_code,
                        float(str(load_num_fee).replace("N", "").replace(",", "")),
                        duration=int(re_index_num),
                    )

                    if trans_status["status"] == False:
                        catched_.disburse = False
                        catched_.date = datetime.datetime.now()
                        catched_.message = trans_status["message"]
                        catched_.save()
                        return trans_status["message"]

                    else:

                        # print_logger.delay(x,y,"Woven ")
                        # Loan processing for one month loan here

                        # x = datetime.datetime.now()
                        borrower_loan_choice_amount = (
                            str(loan_amount).replace("N", "").replace(",", "")
                        )
                        # y = datetime.datetime.now()
                        # # print_logger.delay(x,y,"ONE MONTH PAY ")

                        # # x = datetime.datetime.now()
                        # # loan_processor(borrower_loan_choice_amount, payload, borrower_queryset, ref)

                        dud_loan_processor.delay(
                            borrower_loan_choice_amount,
                            payload,
                            borrower_queryset.id,
                            reference,
                            "ussd",
                        )

                        LoanRequestPassToCelery.objects.create(
                            payload=payload,
                            phone=borrower_phone_number,
                            loan_amt=float(borrower_loan_choice_amount),
                            borrower_id=borrower_queryset.id,
                            ref=reference,
                            channel="ussd",
                        )

                        y = datetime.datetime.now()
                        # print_logger.delay(x,y,"SEND LOAN MESSAGE ")
                        response = "END Loan application has been sent for processing, you should receive a credit notification from your bank shortly"
                        return response

                    # Loan processing for one month loan end here

                elif (
                    "1*1*" in text
                    and int(text[4]) <= constant_env().get("loan_duration")
                    and len(text) == 9
                    and int(text[-1]) == 2
                ):
                    response = (
                        "END Thank you. visit libertyassured.com for more details"
                    )

                else:
                    response = "END Invalid command"

                return response
