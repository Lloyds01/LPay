from pprint import pprint
from traceback import print_tb
from unittest import result
from celery import shared_task
from main.models import Borrower
from main.models import *
from main.helpers.utils import *
from main.helpers.loan_helpers import Remita_Manager
from main.helpers.utils import woven_payment_disbursment
from main.models import Woven_payout_payload
import uuid
from main.helpers.loan_processing_helper import *
from main.helpers.utils import *
from main.helpers.send_sms import *
from main.models import *
from main.helpers.loan_topup import topup_view
import datetime
import logging
from main.helpers.month_scale import scale_to_months
from web.models import constant_env
from main.helpers.loan_disk_helpers import get_borrower_using_phone
from main.helpers.loan_helpers import is_mandate_created


logging.basicConfig(filename="test.log", level=logging.DEBUG)

# num_of_loan_duration = constant_env()

from django.conf import settings


######## get constants
# get_constant = constant_env()

logging.basicConfig(filename="test.log", level=logging.DEBUG)


@shared_task(bind=True)
def test_func(self, object, phone_number, text, time):

    print("Task successfully received.!!", object, phone_number, text, time)

    borrower = Borrower.objects.filter(id=object)
    print(borrower)

    return {"Status": "Successful", "data": [object, phone_number, text, time]}


@shared_task(bind=True)
def add(self, x, y):

    print("Task successfully received.!!", x, y)

    return {"Status": "Successful", "data": [x, y]}


@shared_task(bind=True)
def dud_loan_processor(
    self, borrower_loan_choice_amount, payload, borrower_queryset, uuid_ref, channel
):

    # extract from here

    borrower_queryset = Borrower.objects.filter(id=borrower_queryset).first()
    reference = f"{uuid_ref}"
    payload["reference"] = reference
    load_num_fee = loan_fee(
        str(borrower_loan_choice_amount).replace("N", "").replace(",", "")
    )
    loan_amti = str(str(borrower_loan_choice_amount).replace("N", "")).replace(",", "")
    payload["amount"] = float(loan_amti.replace("N", "").replace(",", "")) - float(
        str(load_num_fee).replace("N", "").replace(",", "")
    )
    payload["beneficiary_nuban"] = borrower_queryset.acct_no
    payload["beneficiary_account_name"] = (borrower_queryset.borrower_fullname,)
    payload["source_account"] = settings.WOVEN_SOURCE_ACCOUNT
    payload["request_id"] = uuid.uuid4()
    payload["phone"] = borrower_queryset.borrower_phoneNumber

    Woven_payout_payload.objects.create(payload=payload)
    # return payload

    # ############### check the loan amount is greater than 3000 here

    if payload["amount"] < 1000:
        return_response = "END Sorry the loan amount is too low"
        return return_response

    else:

        # ############### check the loan amount is greater than 3000 end here

        # ############### posting loan to loan disk before  with processing  without manadate reference

        ran_data = ""
        digits = "0123456789"

        for i in range(0, 4):
            ran_data += random.choice(digits)

        loan_application_id = ""

        date_formate = datetime.datetime.now().date()
        date_formate = datetime.datetime.strptime(
            f"{date_formate}", "%Y-%m-%d"
        ).strftime("%d/%m/%Y")

        # calculation to post to laon disk here

        request_loan_amt = loan_amti.replace("N", "").replace(",", "")

        loan_interest_amt = 0

        borrower_qu = Borrower.objects.filter(
            borrower_id=borrower_queryset.borrower_id
        ).last()

        get_trans = Transaction.objects.filter(
            customer_phone=borrower_queryset.borrower_phoneNumber
        ).last()

        if not get_trans:
            return "No transaction found"

        if get_trans.loan_duration == 1:
            loan_interest_amt = constant_env().get("loan_disk_one_month_interest")

        elif get_trans.loan_duration == 2:
            loan_interest_amt = constant_env().get("loan_disk_two_month_post")

        elif get_trans.loan_duration == 3:
            loan_interest_amt = constant_env().get("loan_disk_three_month_interets")

        elif get_trans.loan_duration == 4:
            loan_interest_amt = constant_env().get("loan_disk_four_month_interets")

        elif get_trans.loan_duration == 5:
            loan_interest_amt = constant_env().get("loan_disk_five_month_interets")

        elif get_trans.loan_duration == 6:
            loan_interest_amt = constant_env().get("loan_disk_six_month_interets")

        elif get_trans.loan_duration == 7:
            loan_interest_amt = constant_env().get("loan_disk_seven_month_interets")

        elif get_trans.loan_duration == 8:
            loan_interest_amt = constant_env().get("loan_disk_eight_month_interets")

        interest_converter = (loan_interest_amt * get_trans.loan_duration) / 100

        get_date_now = datetime.datetime.now()
        total_col = (
            int(get_trans.amount) + int(get_trans.loan_fee)
        ) * interest_converter

        # get_interest = 0
        # if get_trans.loan_duration == 1:
        #     get_interest = one_interest_convert

        # elif get_trans.loan_duration == 2:
        #     get_interest = two_interest_convert

        repayent = loan_monthly_repayment_amt(
            request_loan_amt, get_trans.loan_duration, loan_interest_amt
        )
        repayent.replace("N", "").replace(",", "")
        repayent = repayent.replace("N", "").replace(",", "")

        total_repayent = total_loan_repayment_calculator(
            request_loan_amt, loan_interest_amt, get_trans.loan_duration
        )
        total_repayent = (
            total_repayent.replace("N", "")
            .replace(",", "")
            .replace("N", "")
            .replace(",", "")
        )

        ### get loan eligible payloads
        eligible_id = Eligible.objects.filter(
            phoneNumber=borrower_queryset.borrower_phoneNumber
        ).last()

        ###### get borrower eligible amount and save it to his loan
        elgible_amount = 0
        if borrower_queryset.borrower_eligibleOffer:
            elgible_amount = float(borrower_queryset.borrower_eligibleOffer)

        # posting to loan model  without manadate reference  ends here

        # Mandate reference request payload

        remita_payload = {
            "customerId": f'{borrower_queryset.borrower_remita_id.replace("r_","").replace(",", "")}',
            "authorisationCode": borrower_queryset.borrower_authorisationCode,
            "authorisationChannel": channel,
            "phoneNumber": f"{borrower_queryset.borrower_phoneNumber}",
            "accountNumber": f"{borrower_queryset.acct_no}",
            "currency": "NGN",
            "loanAmount": float(request_loan_amt),
            "collectionAmount": float(repayent),
            "dateOfDisbursement": datetime.datetime.now(),
            "dateOfCollection": datetime.datetime.now(),
            "totalCollectionAmount": total_repayent,
            "numberOfRepayments": get_trans.loan_duration,
        }

        mandate_request_payload = f"{remita_payload}"

        # saving mandate request payload to the model here
        Mandate_Request.objects.create(
            mandate_request_payload=mandate_request_payload,
            amount=int(request_loan_amt),
            phone_number=borrower_queryset.borrower_phoneNumber,
            borrower_name=borrower_queryset.borrower_fullname,
        )
        # saving mandate request payload to the model end here

        # request mandate reference from remita here
        remita_data = Remita_Manager.ref_payload(**remita_payload)
        remita_data = json.loads(remita_data)

        logging.debug(
            "remita mandate generated >>>>>>>>>>>>>>>>>>>>>>>>>>>>", remita_data
        )

        # request mandate reference from remita end here

        # loan duration
        dur = get_trans.loan_duration

        # loan product id for each month
        product_id = 0

        if dur == 1:
            product_id = float(constant_env().get("loan_disk_fedwk_one_month"))
        elif dur == 2:
            product_id = float(constant_env().get("loan_disk_fedwk_two_month"))
        elif dur == 3:
            product_id = float(constant_env().get("loan_disk_fedwk_three_month"))

        product_id = float(constant_env().get("loan_disk_fedwk_one_month"))

        # loan product interest for each month

        loan_product_interest = 0
        if dur == 1:
            loan_product_interest = constant_env().get("loan_disk_one_month_interest")
        elif dur == 2:
            loan_product_interest = constant_env().get("loan_disk_two_month_post")

        elif dur == 3:
            loan_product_interest = constant_env().get("loan_disk_three_month_interets")

        elif dur == 4:
            loan_product_interest = constant_env().get("loan_disk_four_month_interets")

        elif dur == 5:
            loan_product_interest = constant_env().get("loan_disk_five_month_interets")

        elif dur == 6:
            loan_product_interest = constant_env().get("loan_disk_six_month_interets")

        elif dur == 7:
            loan_product_interest = constant_env().get("loan_disk_seven_month_interets")

        elif dur == 8:
            loan_product_interest = constant_env().get("loan_disk_eight_month_interets")

        if remita_data["status"] == "success":

            mandateReference = remita_data["data"]["mandateReference"]
            mandateReference.replace("'", "").replace(",", "").replace(
                "(", ""
            ).replace(")", "")



             # update manadate reference  success status here
            update_mandate_ref = Mandate_Request.objects.filter(
                phone_number=borrower_queryset.borrower_phoneNumber
            ).last()
            update_mandate_ref.mandateReference = (mandateReference,)
            update_mandate_ref.status = True
            update_mandate_ref.remita_gen_response = remita_data
            update_mandate_ref.save()

            #########################
            ########## Confirm if we have this mandate already in our db
            #########################

            mandate_exists = Loan.objects.filter(
                mandateReference=mandateReference
            )

            if mandate_exists:
                return {"status": "mandate already exist"}
            
            ######################
            #### Local mandate check ends here
            ######################
            

            ############################################################################
            ############## check if
            ############## mandate was created for the amount and values tally on remita
            ############################################################################

            r_id = f'{borrower_queryset.borrower_remita_id.replace("r_","").replace(",", "")}'
            mandate_confirmed_on_remita = is_mandate_created(mandateReference, borrower_queryset.borrower_authorisationCode, r_id, float(request_loan_amt))
            
            if not mandate_confirmed_on_remita:
                """STOP LOAN DISBURSEMENTS IF ANY DISPARITY IN DISBURSEMENT DETAILS FROM REMITA"""

                return {"status": f"mandate confirmation error on remita -> {mandateReference}"}

            elif mandate_confirmed_on_remita:

                ##### celery
                get_loan_request = LoanRequestPassToCelery.objects.filter(
                    phone=borrower_queryset.borrower_phoneNumber
                ).last()
                if get_loan_request:
                    get_loan_request.mandate_open = True
                    get_loan_request.save()

                mandateReference = remita_data["data"]["mandateReference"]
                mandateReferencev = "".join(
                    e for e in mandateReference if e.isalnum() or e == " "
                )

               

                ############# save data to pending loan
                Pending_loan_record.objects.create(
                    phone=borrower_queryset.borrower_phoneNumber,
                    mandate=mandateReference,
                    payment_ref=payload["reference"],
                )


                #########################
                ########## create borrower on loan disk for this user
                #########################

                if borrower_queryset.exists_on_loandisk == False:

                    get_user_in_loandisk = get_borrower_using_phone(
                        borrower_queryset.borrower_phoneNumber
                    )
                    print(f"get_user_in_loan disk response {get_user_in_loandisk} \n\\n\n")

                    try:
                        if get_user_in_loandisk["error"]["message"] == "Not Found":

                            loans_diskdata = borrower_api_call(
                                "NG",
                                borrower_queryset.borrower_business_name,
                                borrower_queryset.borrower_firstname,
                                borrower_queryset.borrower_lastname,
                                borrower_queryset.borrower_middlename,
                                borrower_queryset.borrower_business_name,
                                borrower_queryset.borrower_remita_id,
                                "",
                                "",
                                borrower_queryset.borrower_phoneNumber,
                                borrower_queryset.bvn_no,
                                borrower_queryset.acct_no,
                                borrower_queryset.bank_code,
                                borrower_queryset.bank_name,
                                borrower_queryset.borrower_business_name,
                            )

                            try:
                                post_borrower_response = json.loads(loans_diskdata)
                                if post_borrower_response["response"]["borrower_id"]:
                                    borrower_id = post_borrower_response["response"][
                                        "borrower_id"
                                    ]
                                    borrower_queryset.borrower_id = borrower_id
                                    borrower_queryset.exists_on_loandisk = True
                                    borrower_queryset.save()
                            except KeyError:
                                pass
                            except Exception as e:
                                print(e)
                    except KeyError:
                        if get_user_in_loandisk["response"]["Results"]:
                            borrower_id = get_user_in_loandisk["response"]["Results"][0][0][
                                "borrower_id"
                            ]
                            borrower_queryset.borrower_id = borrower_id
                            borrower_queryset.exists_on_loandisk = True
                            borrower_queryset.save()

                p_loan = Loan.post_loan_to_loandisk(
                    product_id,
                    borrower_queryset.borrower_id,
                    loan_application_id,
                    float(borrower_loan_choice_amount.replace("N", "").replace(",", "")),
                    date_formate,
                    loan_product_interest,
                    dur,
                    dur,
                    borrower_queryset.bank_code,
                    borrower_queryset.acct_no,
                    borrower_queryset.bvn_no,
                    borrower_queryset.borrower_remita_id.replace("r_", "").replace(",", ""),
                    borrower_queryset.borrower_business_name,
                    borrower_queryset.borrower_business_name,
                    borrower_queryset.bank_name,
                    borrower_queryset.bank_name,
                )

                loandisk_post_response.objects.create(
                    phone=borrower_queryset.borrower_phoneNumber, pay_load_res=p_loan
                )

                print("post to loan disk response >>>>>>>>>>>>>>>>>>>>>>>>", p_loan)

                ############ after posting the loan to loan disk.save it to our local db
                Loan.objects.create(
                    customerId=borrower_queryset.borrower_remita_id,
                    authorisationCode=borrower_queryset.borrower_authorisationCode,
                    authorisationChannel=channel,
                    phoneNumber=borrower_queryset.borrower_phoneNumber,
                    accountNumber=borrower_queryset.acct_no,
                    currency="Naira",
                    loanAmount=float(get_trans.amount),
                    collectionAmount=float(get_trans.loan_fee),
                    dateOfDisbursement=get_date_now,
                    totalCollectionAmount=get_trans.amount + total_col,
                    numberOfRepayments=get_trans.loan_duration,
                    payement_reference=get_trans.ref_id,
                    loan_disk_id=p_loan["response"]["loan_id"],
                    eligible_id=eligible_id,
                    average_salary=eligible_id.average_salary,
                    loan_obligation=eligible_id.loan_obligation,
                    monthly_repayment=repayent,
                    elgible_amount=int(elgible_amount),
                    eligible_for_top_up=False,
                    is_topup=True if get_trans.topup == True else False,
                )

                loan_disk_id = p_loan["response"]["loan_id"]

                ###### updatte pending load
                get_pending_load_record = Pending_loan_record.objects.filter(
                    phone=borrower_queryset.borrower_phoneNumber
                ).last()

                if get_pending_load_record:
                    get_pending_load_record.posted_to_loan_disk = True
                    get_pending_load_record.save()

                liberty_loan_id = Loan.objects.filter(loan_disk_id=loan_disk_id).last()

                mandateReference = remita_data["data"]["mandateReference"]
                mandateReference.replace("'", "").replace(",", "").replace("(", "").replace(
                    ")", ""
                )

                # update manadate reference  success status here
                update_mandate_ref = Mandate_Request.objects.filter(
                    phone_number=borrower_queryset.borrower_phoneNumber
                ).last()
                update_mandate_ref.mandateReference = (mandateReference,)
                update_mandate_ref.loan_disk_id = p_loan["response"]["loan_id"]
                update_mandate_ref.status = True
                update_mandate_ref.remita_gen_response = remita_data
                update_mandate_ref.save()

                # update manadate reference success status end here

                # update manadate reference  on loan disk and loan id here

                dur = 0
                if get_trans.loan_duration == 1:
                    dur = 119290
                elif get_trans.loan_duration == 2:
                    dur = 119291
                elif get_trans.loan_duration == 3:
                    dur = 119292

                dur = 119290

                ############## detect if this loan is a topup loan or a new loan

                check_topup_loan_status = Loan.objects.filter(
                    phoneNumber=borrower_queryset.borrower_phoneNumber,
                    eligible_for_top_up=True,
                    loan_percentage_taken__lte=100,
                )

                if check_topup_loan_status.exists():
                    topup_status = "T"
                else:
                    topup_status = ""

                is_loan_tpup = "-topup" if get_trans.topup == True else ""
                loan_application_id = f"LXF-{loan_disk_id}-{liberty_loan_id.id}-{topup_status}-{channel}{is_loan_tpup}"
                loan = Loan.objects.filter(loan_disk_id=loan_disk_id).last()
                date_formate = datetime.datetime.now().date()
                date_formate = datetime.datetime.strptime(
                    f"{date_formate}", "%Y-%m-%d"
                ).strftime("%d/%m/%Y")

                # loan disk payload for update
                ####
                # percent salary as repayment
                ####
                perc_salaey_as_rep = (loan.monthly_repayment / loan.average_salary) * 100
                loan_disk_payload = {
                    "loan_product_id": f"{product_id}",
                    "borrower_id": f"{borrower_queryset.borrower_id}",
                    "loan_application_id": f"{loan_application_id}",
                    "loan_disbursed_by_id": "91595",
                    "loan_principal_amount": int(loan.loanAmount),
                    "loan_released_date": f"{date_formate}",
                    "loan_interest_method": "flat_rate",
                    "loan_interest_type": "percentage",
                    "loan_interest_period": "Month",
                    "loan_interest": loan_product_interest,
                    "loan_duration_period": "Months",
                    "loan_duration": get_trans.loan_duration,
                    "loan_payment_scheme_id": "3",
                    "loan_num_of_repayments": get_trans.loan_duration,
                    "loan_decimal_places": "round_up_to_five",
                    "loan_status_id": "8",
                    "custom_field_5262": f"{mandateReference}",
                    "custom_field_4181": f"{borrower_queryset.bank_code}",
                    "custom_field_4178": f"{borrower_queryset.acct_no}",
                    "custom_field_5261": f"{loan.dateOfCollection}",
                    "custom_field_4361": f"{borrower_queryset.bvn_no}",
                    "loan_fee_id_2746": 0,
                    "loan_fee_id_3915": 0,
                    "loan_fee_id_4002": 0,
                    "loan_fee_id_4003": 0,
                    "loan_fee_id_4004": 0,
                    "loan_fee_id_4005": 0,
                    "loan_fee_id_4006": 0,
                    "custom_field_5251": f'{borrower_queryset.borrower_remita_id.replace("r_","").replace(",", "")}',
                    "custom_field_4385": f"{borrower_queryset.borrower_business_name}",
                    "custom_field_6363": f"{borrower_queryset.borrower_business_name}",
                    "loan_id": loan.loan_disk_id,
                    "custom_field_4219": f"{borrower_queryset.bank_name}",
                    "custom_field_4221": f"{borrower_queryset.bank_name}",
                    "custom_field_11516": loan.loan_obligation,
                    "custom_field_11515": loan.average_salary,
                    "custom_field_11517": loan.monthly_repayment,
                    "custom_field_11518": perc_salaey_as_rep,
                }

                logging.debug("printing payload to be pas to loan disk")
                logging.debug(loan_disk_payload)
                logging.debug("printing payload to be pas to loan disk")
                logging.debug(loan_disk_payload)

                update_loaddisk = post_loan_to_loandisk(**loan_disk_payload)

                loandisk_post_response.objects.create(
                    phone=borrower_queryset.borrower_phoneNumber,
                    pay_load_res=update_loaddisk,
                )

                print("updated loan >>>>>>>>>>>>>>>>>>>>>>>>", update_loaddisk)

                # update manadate reference  on loan disk and loan id end here

                # update manadate reference  on loan model here

                gt_loan = Loan.objects.filter(loan_disk_id=loan_disk_id).last()
                gt_loan.mandateReference = mandateReference
                gt_loan.save()
                # update manadate reference  on loan model end here

                woven_payment_disbursment(**payload)

                send_loan_processing_sms(
                    borrower_queryset.borrower_phoneNumber,
                    borrower_queryset.borrower_fullname,
                )

                ######### get LoanRequestPassToCelery and update open
                get_loan_request = LoanRequestPassToCelery.objects.filter(
                    phone=borrower_queryset.borrower_phoneNumber
                ).last()
                if get_loan_request:
                    get_loan_request.mandate_open = True
                    get_loan_request.save()

                return "END Loan application has been sent for processing, you should receive a credit notification from your bank shortly"

            else:
                # loan_disk_id = p_loan['response']['loan_id']
                # liberty_loan_id = Loan.objects.filter(
                #     loan_disk_id=loan_disk_id)["id"]
                # mandateReference = remita_data['date']['mandateReference']

                # update manadate reference  success status here

                update_request_mandate = Mandate_Request.objects.filter(
                    phone_number=borrower_queryset.borrower_phoneNumber
                ).last()
                update_request_mandate.status = False
                update_request_mandate.remita_gen_response = remita_data
                update_request_mandate.save()

                return None


def create_transaction(
    source, customer, amount, ref, acct, phone, bank_code, loan_fee, duration
):
    """
    This function handles creation of transaction
    """
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

        logging.debug(f"{eligibileCheckers}")

        logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> done getting dommy data")

        if eligibileCheckers == None:
            response = "END Sorry this product is for salary earners only !!"
            return response
        else:
            pass

        eligibileAmountChecker = eligibileCheckers["eligible_amount"]
        # eligibileChecker = eligibileCheckers

        logging.debug(f"pass >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

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

        try:
            catched_ = Catched_Cookie.objects.filter(phone=borrower_phone_number).last()

            ###### if cache has passed 12 hours. if it passes 12 hours. clear the cache
            if catched_.clear_cache():
                raise ValueError("Cache cleard. please create new cache")

            ###### end of clear cache on

            if catched_.has_expired(borrower_phone_number):
                catched_.phone = ""
                catched_.save()
                raise ValueError("Cache has expired. allow new Remita call")

            if catched_:
                return {"message": "user already exist in cache"}
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
        else:
            eligiblechecker_error = catched_.message

        if catched_.user_eligibile_amount:
            eligibileChecker_ = catched_.user_eligibile_amount
            eligibileAmountChecker = float(eligibileChecker_)
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
            loan_cap if eligibileAmountChecker > loan_cap else eligibileAmountChecker
        )

        if eligibileAmountChecker == 0:

            check_non_borrowers_db = InEligible_borrowers.objects.filter(
                phone=borrower_phone_number
            ).last()
            if eligiblechecker_error != None:
                response = f"{eligiblechecker_error}"
                return response

            elif (
                eligibileChecker["message"] == "Customer not found, Customer not found"
            ):
                if not check_non_borrowers_db:
                    InEligible_borrowers.objects.create(
                        phone=borrower_phone_number, date=datetime.datetime.now()
                    )

                response = (
                    "END Sorry this loan product is availiable for civil servants! "
                )
                catched_.message = (
                    "END Sorry this loan product is availiable for civil servants only!"
                )
                catched_.save()
                return response

            elif eligibileChecker["message"] == "Inactive customer, Inactive customer":
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

            elif eligibileChecker["message"] == "No salaries in past 45 days, SUCCESS":
                response = (
                    "END Sorry this loan product is availiable for civil servants!"
                )
                catched_.message = (
                    "END Sorry this loan product is availiable for civil servants!"
                )
                catched_.save()
                return response

            elif eligibileChecker["message"] == "Ok, Unable to grant you loan":
                response = "END You're currently not eligible based on your current credit data. try again later"
                catched_.message = "END You're currently not eligible based on your current credit data. try again later"
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

            elif (
                eligibileChecker["message"]
                == "Error Processing Request, Error Processing Request"
            ):
                response = (
                    "END unable to process your request at this time. try again later"
                )
                catched_.message = (
                    "END unable to process your request at this time. try again later"
                )
                catched_.save()
                return response

            elif (
                eligibileChecker["message"]
                == "Customer not from coverage region, SUCCESS"
            ):
                response = "END Sorry cannot process eligibility from your region at this time please try again later"
                catched_.message = "END Sorry cannot process eligibility from your region at this time please try again later"
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
            catched_.user_eligibile_amount = eligibileCheckers["eligible_amount"]
            catched_.save()


@shared_task(bind=True)
def celery_process_eligible_loan(self, data):

    Main_Menu.liberty_loan(**data)
    print("Task successfully received.!!", data)

    return {"Status": "Successful", "data": data}


@shared_task(bind=True)
def celery_contact_sms(self, num):
    contact_sms(num)

    return {"message": "success"}


@shared_task(bind=True)
def celery_check_loan_balance(self, phone_number):
    num = utility.phone_num_pre_extractor(phone_number)

    ###### get user borrowers id from loan disk
    ######

    try:
        get_local_borrower = Borrower.objects.get(borrower_phoneNumber=num)

    except:
        get_local_borrower = None

    num_of_loans = 0
    user_local_loan_id = []
    user_local_loan_due_amt = 0
    user_local_loan_outstanding = 0
    user_local_paid_amt = 0

    user_local_loans = Loan.objects.filter(phoneNumber=num, loan_status=True)

    ######### get user libertytechx loan from loan disk using his loan_disk_borrower id
    if get_local_borrower:
        if get_local_borrower.exists_on_loandisk:
            get_user_liberty_techx_id = get_local_borrower.borrower_id

            ####### fetch the loan for this borrower using his id
            url = f"{settings.LOAN_DISK_BASE_URL}/5797/{settings.LOAN_DISK_BRANCH_ID}/loan/borrower/{get_user_liberty_techx_id}/from/1/count/90000"
            headers = {
                "Authorization": f"Basic {settings.LOAN_DISK_SEC_KEY}",
                "Content-Type": "application/json",
            }

            payload = {}

            response = requests.request("GET", url, headers=headers, data=payload)
            try:
                techx_loan_res = json.loads(response.text)
            except:
                techx_loan_res = response.text

            if type(techx_loan_res) == dict:
                if techx_loan_res["response"]["Results"]:
                    for i in techx_loan_res["response"]["Results"][0]:
                        if i["loan_status_id"] == 1 or i["loan_status_id"] == "1":
                            num_of_loans += 1
                            user_local_loan_id.append(i["loan_id"])
                            user_local_loan_due_amt += float(i["balance_amount"])
                            user_local_paid_amt += float(i["total_paid"])
                            user_local_loan_outstanding += (
                                user_local_loan_due_amt - user_local_paid_amt
                            )

    ######### loan disk libertyfedwk branch
    loan_disk_loan_id = []
    loan_disk_loan_due_amt = 0
    loan_disk_outstanding = 0
    loan_disk_paid_amt = 0
    loan_disk_fedwk_name = "user"

    ############### get borrower details on liberty fedwk branch using phone number
    url = f"{settings.LOAN_DISK_BASE_URL}/5797/{settings.LIBERTY_FEDWK_BRANCH_ID}/borrower/borrower_mobile/{num}"

    payload = {}

    headers = {
        "Authorization": f"Basic {settings.LOAN_DISK_SEC_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    borrower_id = None
    try:
        get_loan_disk_borrower = json.loads(response.text)
        if get_loan_disk_borrower["response"]["ReturnResults"] > 0:
            borrower_id = get_loan_disk_borrower["response"]["Results"][0][0][
                "borrower_id"
            ]

            print("borrower found on fed_wk branch \n\n\n\n")

    except Exception as e:
        print(e)

    #### get borrower loans using his borrowers id
    url = f"{settings.LOAN_DISK_BASE_URL}/5797/{settings.LIBERTY_FEDWK_BRANCH_ID}/loan/borrower/{borrower_id}/from/1/count/90000"
    headers = {
        "Authorization": f"Basic {settings.LOAN_DISK_SEC_KEY}",
        "Content-Type": "application/json",
    }

    payload = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    try:
        get_loandisk_loan = json.loads(response.text)

    except:
        get_loandisk_loan = response.text

    if type(get_loandisk_loan) == dict:
        if get_loandisk_loan["response"]["Results"]:
            for i in get_loandisk_loan["response"]["Results"][0]:
                if i["loan_status_id"] == 1 or i["loan_status_id"] == "1":
                    num_of_loans += 1
                    loan_disk_loan_id.append(i["loan_id"])
                    loan_disk_loan_due_amt += float(i["balance_amount"])
                    loan_disk_paid_amt += float(i["total_paid"])
                    loan_disk_outstanding += loan_disk_loan_due_amt - loan_disk_paid_amt
                    loan_disk_fedwk_name = i["borrower_firstname"]

            if get_local_borrower == None:
                one_balance_sms(
                    num,
                    loan_disk_fedwk_name,
                    num_of_loans,
                    loan_disk_loan_id,
                    loan_disk_paid_amt,
                    loan_disk_outstanding,
                    loan_disk_loan_due_amt,
                )
                return {"message": "message sent successfully"}
            else:
                two_balance_sms(
                    num,
                    get_local_borrower.borrower_firstname,
                    num_of_loans,
                    user_local_loan_id,
                    user_local_loan_due_amt,
                    user_local_paid_amt,
                    user_local_loan_outstanding,
                    loan_disk_loan_id,
                    loan_disk_loan_due_amt,
                    loan_disk_paid_amt,
                    loan_disk_outstanding,
                )

                return {"message": "message sent successfully"}

        else:
            if get_local_borrower == None:
                no_active_loan(num)
                return {"message": "message sent successfully"}

            else:
                one_balance_sms(
                    num,
                    get_local_borrower.borrower_firstname,
                    num_of_loans,
                    user_local_loan_id,
                    user_local_paid_amt,
                    user_local_loan_outstanding,
                    user_local_loan_due_amt,
                )

                return {"message": "message sent successfully"}

    else:
        if get_local_borrower == None:
            no_active_loan(num)
            return {"message": "message sent successfully"}

        else:
            one_balance_sms(
                num,
                get_local_borrower.borrower_firstname,
                num_of_loans,
                user_local_loan_id,
                user_local_paid_amt,
                user_local_loan_outstanding,
                user_local_loan_due_amt,
            )
            return {"message": "message sent successfully"}


@shared_task(bind=True)
def celery_add_borrower_to_loandisk(self):
    all_borrowers = Borrower.objects.filter(exists_on_loandisk=False).order_by("id")[
        :500
    ]
    responses = dict()

    for borrower in all_borrowers:
        loans_diskdata = borrower_api_call(
            "NG",
            borrower.borrower_business_name,
            borrower.borrower_firstname,
            borrower.borrower_lastname,
            borrower.borrower_middlename,
            borrower.borrower_business_name,
            borrower.borrower_remita_id,
            "",
            "",
            borrower.borrower_phoneNumber,
            borrower.bvn_no,
            borrower.acct_no,
            borrower.bank_code,
            borrower.bank_name,
            borrower.borrower_business_name,
        )

        try:
            post_borrower_response = json.loads(loans_diskdata)

            if isinstance(post_borrower_response["response"].get("Errors"), list):

                error = post_borrower_response["response"].get("Errors")[0]
                if "Unique Number is not unique." in error:

                    get_user_in_loandisk = get_borrower_using_phone(
                        borrower.borrower_phoneNumber
                    )
                    borrower_id = get_user_in_loandisk["response"]["Results"][0][0][
                        "borrower_id"
                    ]

                    borrower.borrower_id = borrower_id
                    borrower.exists_on_loandisk = True
                    borrower.save()
                    responses[borrower.borrower_phoneNumber] = {
                        "status": "added",
                        "err": None,
                        "id": borrower.borrower_remita_id,
                    }

            elif post_borrower_response["response"]["borrower_id"]:

                borrower_id = post_borrower_response["response"]["borrower_id"]
                borrower.borrower_id = borrower_id
                borrower.exists_on_loandisk = True
                borrower.save()
                responses[borrower.borrower_phoneNumber] = {
                    "status": "added",
                    "err": None,
                    "id": borrower.borrower_remita_id,
                }

        except Exception as e:
            responses[borrower.borrower_phoneNumber] = {
                "status": "failed",
                "err": str(e),
                "id": borrower.borrower_remita_id,
            }

    return {"status": "task finished running", "responses": responses}


@shared_task(bind=True)
def celery_save_outliers(self, data, phone):
    OutLiersLogs.objects.create(
        ratio=data.get("ratio"),
        low_lim=data.get("low_lim"),
        up_lim=data.get("up_lim"),
        max_val=data.get("max_val"),
        min_val=data.get("min_val"),
        segregation_ration=data.get("segregation_ratio"),
        multiplier=data.get("multiplier"),
        using=data.get("using"),
        salaries=data.get("salaries"),
        phone=phone,
    )

    return {"status": "saved outliers"}


@shared_task(bind=True)
def celery_update_loan_request_pass_to_celery(self, borrower_id):
    get_borrower = Borrower.objects.filter(id=borrower_id).first()

    ######### get LoanRequestPassToCelery and update open
    get_loan_request = LoanRequestPassToCelery.objects.filter(
        phone=get_borrower.borrower_phoneNumber
    ).last()

    if get_loan_request:
        get_loan_request.mandate_open = True
        get_loan_request.save()

    return {"status": "updated"}
