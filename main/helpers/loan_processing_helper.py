#  what this function does

#  1. Posting to loan disk
#  2. caching the loan request to session to stop multiple disbursement
#  3. posting to woven for disbursement_amt
#  4. posting to libertyloan database
#  5. Check if loan amount is greater than 3000
#  6. returns true ( response if the loan is processed for disbursement) to the borrower or false ( response if the loan is not processed for disbursement) to the borrower


from rest_framework import response
from django.http import HttpResponse
from main.models import *
from datetime import datetime

# from main.views import *
from django.conf import settings
from main.helpers.utils import *
from main.helpers.loan_helpers import Remita_Manager

from web.models import USSD_Constant_Variable, constant_env


# get_constant = constant_env()


def loan_processor(borrower_loan_choice_amount, payload, borrower_queryset, uuid_ref):

    # extract from here

    reference = f"Libty-{uuid_ref.hex}"
    payload["reference"] = reference
    load_num_fee = loan_fee(
        borrower_loan_choice_amount.replace("N", "").replace(",", "")
    )
    loan_amti = borrower_loan_choice_amount.replace("N", "").replace(",", "")
    payload["amount"] = float(loan_amti.replace("N", "").replace(",", "")) - float(
        str(load_num_fee).replace("N", "").replace(",", "")
    )
    payload["beneficiary_nuban"] = borrower_queryset.acct_no
    payload["beneficiary_account_name"] = borrower_queryset.borrower_fullname

    # ############### check the loan amount is greater than 3000 here

    if payload["amount"] < 3000:
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

        date_formate = datetime.now().date()
        date_formate = datetime.strptime(f"{date_formate}", "%Y-%m-%d").strftime(
            "%d/%m/%Y"
        )

        # loan product id for one month
        product_id = float(constant_env().get("loan_disk_fedwk_one_month"))

        # loan duration
        dur = 1

        # calculation to post to laon disk here

        request_loan_amt = loan_amti.replace("N", "").replace(",", "")

        # one_mon_total_collect = float(request_loan_amt) + (
        #     float(request_loan_amt) * (0.18 * 1)) + float(loan_fee(request_loan_amt))
        # two_mon_total_collect = float(
        #     request_loan_amt) + (float(request_loan_amt) * (0.35)) + float(loan_fee(request_loan_amt))

        repayent = loan_monthly_repayment_amt(request_loan_amt, 1, 0.22)
        repayent.replace("N", "").replace(",", "")
        repayent = repayent.replace("N", "").replace(",", "")

        total_repayent = one_month_repayment_calculator(borrower_loan_choice_amount)
        total_repayent.replace("N", "").replace(",", "")

        # posting to loan disk with processing  without manadate reference end here

        # posting to loan model without manadate reference here

        borrower_qu = Borrower.objects.filter(
            borrower_id=borrower_queryset.borrower_id
        ).last()

        get_trans = Transaction.objects.filter(
            customer_phone=borrower_qu.borrower_phoneNumber
        ).last()

        get_date_now = datetime.now()
        total_col = (
            (int(get_trans.amount) + int(get_trans.loan_fee)) * 0.18
            if constant_env().get("loan_duration") == 1
            else (int(get_trans.amount) + int(get_trans.loan_fee)) * 0.35
        )

        ### get loan eligible payloads
        eligible_id = Eligible.objects.filter(
            phoneNumber=borrower_qu.borrower_phoneNumber
        ).last()

        ###### get borrower eligible amount and save it to his loan
        elgible_amount = 0
        if borrower_qu.borrower_eligibleOffer:
            elgible_amount = float(borrower_qu.borrower_eligibleOffer)

        # posting to loan model  without manadate reference  ends here

        # Mandate reference request payload

        remita_payload = {
            "customerId": f'{borrower_queryset.borrower_remita_id.replace("r_","").replace(",", "")}',
            "authorisationCode": borrower_queryset.borrower_authorisationCode,
            "authorisationChannel": "USSD",
            "phoneNumber": f"{borrower_queryset.borrower_phoneNumber}",
            "accountNumber": f"{borrower_queryset.acct_no}",
            "currency": "NGN",
            "loanAmount": float(request_loan_amt),
            "collectionAmount": float(repayent),
            "dateOfDisbursement": datetime.now(),
            "dateOfCollection": datetime.now(),
            "totalCollectionAmount": total_repayent,
            "numberOfRepayments": 1,
        }
        mandate_request_payload = f"{remita_payload}"

        # saving mandate request payload to the model here
        Mandate_Request.objects.create(
            mandate_request_payload=mandate_request_payload,
            amount=int(request_loan_amt),
            phone_number=borrower_queryset.borrower_phoneNumber,
            borrower_name=borrower_qu.borrower_fullname,
        )
        # saving mandate request payload to the model end here

        # request mandate reference from remita here
        remita_data = Remita_Manager.ref_payload(**remita_payload)
        remita_data = json.loads(remita_data)

        print("remita mandate generated >>>>>>>>>>>>>>>>>>>>>>>>>>>>", remita_data)

        # request mandate reference from remita end here

        if remita_data["status"] == "success":

            p_loan = Loan.post_loan_to_loandisk(
                product_id,
                borrower_queryset.borrower_id,
                loan_application_id,
                float(borrower_loan_choice_amount.replace("N", "").replace(",", "")),
                date_formate,
                constant_env().get("loan_disk_one_month_interest")
                if dur == 1
                else constant_env().get(""),
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

            print("post to loan disk response >>>>>>>>>>>>>>>>>>>>>>>>", p_loan)

            ############ after posting the loan to loan disk.save it to our local db
            Loan.objects.create(
                customerId=borrower_qu.borrower_remita_id,
                authorisationCode=borrower_qu.borrower_authorisationCode,
                authorisationChannel=borrower_qu.borrower_channel,
                phoneNumber=borrower_qu.borrower_phoneNumber,
                accountNumber=borrower_qu.acct_no,
                currency="Naira",
                loanAmount=float(get_trans.amount),
                collectionAmount=float(get_trans.loan_fee),
                dateOfDisbursement=get_date_now,
                totalCollectionAmount=get_trans.amount + total_col,
                numberOfRepayments=constant_env().get("loan_duration"),
                payement_reference=get_trans.ref_id,
                loan_disk_id=p_loan["response"]["loan_id"],
                eligible_id=eligible_id,
                elgible_amount=int(elgible_amount),
            )

            loan_disk_id = p_loan["response"]["loan_id"]
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
            if constant_env().get("loan_duration") == 1:
                dur = 119290
            elif constant_env().get("loan_duration") == 2:
                dur = 119291
            elif constant_env().get("loan_duration") == 3:
                dur = 119292
            # loan disk payload for update
            loan_application_id = f"LXF-{loan_disk_id}-{liberty_loan_id.id}-USSD"
            loan = Loan.objects.filter(loan_disk_id=loan_disk_id).last()
            date_formate = datetime.now().date()
            date_formate = datetime.strptime(f"{date_formate}", "%Y-%m-%d").strftime(
                "%d/%m/%Y"
            )
            loan_disk_payload = {
                "loan_product_id": f"{dur}",
                "borrower_id": f"{borrower_queryset.borrower_id}",
                "loan_application_id": f"{loan_application_id}",
                "loan_disbursed_by_id": "91595",
                "loan_principal_amount": int(loan.loanAmount),
                "loan_released_date": f"{date_formate}",
                "loan_interest_method": "flat_rate",
                "loan_interest_type": "percentage",
                "loan_interest_period": "Month",
                "loan_interest": constant_env().get("loan_disk_one_month_interest")
                if constant_env().get("loan_duration") == 1
                else constant_env().get("loan_disk_two_month_post"),
                "loan_duration_period": "Months",
                "loan_duration": constant_env().get("loan_duration"),
                "loan_payment_scheme_id": "3",
                "loan_num_of_repayments": constant_env().get("loan_duration"),
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
            }

            logging.debug("printing payload to be pas to loan disk")
            logging.debug(loan_disk_payload)
            logging.debug("printing payload to be pas to loan disk")
            logging.debug(loan_disk_payload)

            update_loaddisk = post_loan_to_loandisk(**loan_disk_payload)

            print("updated loan >>>>>>>>>>>>>>>>>>>>>>>>", update_loaddisk)

            # update manadate reference  on loan disk and loan id end here

            # update manadate reference  on loan model here

            gt_loan = Loan.objects.filter(loan_disk_id=loan_disk_id).last()
            gt_loan.mandateReference = mandateReference
            gt_loan.save()
            # update manadate reference  on loan model end here

            # Woven disbursement  here
            woven_payment_disbursment(**payload)

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

            # update manadate reference success status end here

    # Extract stop here


# def dud_loan_processor(borrower_loan_choice_amount, payload, borrower_queryset, uuid_ref):

#     # extract from here

#     borrower_queryset = Borrower.objects.filter(id = borrower_queryset).first()
#     reference = f"Libty-{uuid_ref.hex}"
#     payload["reference"] = reference
#     load_num_fee = loan_fee(
#         borrower_loan_choice_amount.replace("N", "").replace(",", ""))
#     loan_amti = borrower_loan_choice_amount.replace("N", "").replace(",", "")
#     payload["amount"] = float(loan_amti.replace("N", "").replace(
#         ",", "")) - float(str(load_num_fee).replace("N", "").replace(",", ""))
#     payload["beneficiary_nuban"] = borrower_queryset.acct_no
#     payload["beneficiary_account_name"] = borrower_queryset.borrower_fullname

#     return payload

# ############### check the loan amount is greater than 3000 here

# if payload["amount"] < 3000:
#     return_response = "END Sorry the loan amount is too low"
#     return return_response

# else:

#  # ############### check the loan amount is greater than 3000 end here

#     # ############### posting loan to loan disk before  with processing  without manadate reference

#     ran_data = ''
#     digits = '0123456789'

#     for i in range(0, 4):
#         ran_data += random.choice(digits)

#     loan_application_id = ""

#     date_formate = datetime.now().date()
#     date_formate = datetime.strptime(
#         f"{date_formate}", "%Y-%m-%d").strftime('%d/%m/%Y')

#     # loan product id for one month
#     product_id = float(settings.ONE_MONTH_FEDWK)

#     # loan duration
#     dur = 1

#     # calculation to post to laon disk here

#     request_loan_amt = loan_amti.replace("N", "").replace(",", "")

#     # one_mon_total_collect = float(request_loan_amt) + (
#     #     float(request_loan_amt) * (0.18 * 1)) + float(loan_fee(request_loan_amt))
#     # two_mon_total_collect = float(
#     #     request_loan_amt) + (float(request_loan_amt) * (0.35)) + float(loan_fee(request_loan_amt))

#     repayent = loan_monthly_repayment_amt(
#         request_loan_amt, 1, 0.22)
#     repayent.replace("N", "").replace(",", "")
#     repayent = repayent.replace("N", "").replace(",", "")

#     total_repayent = one_month_repayment_calculator(
#         borrower_loan_choice_amount)
#     total_repayent.replace("N", "").replace(",", "")


#     # posting to loan disk with processing  without manadate reference end here

#     # posting to loan model without manadate reference here

#     borrower_qu = Borrower.objects.filter(
#         borrower_id=borrower_queryset.borrower_id).last()

#     get_trans = Transaction.objects.filter(
#         customer_phone=borrower_qu.borrower_phoneNumber).last()

#     get_date_now = datetime.now()
#     total_col = (int(get_trans.amount) + int(get_trans.loan_fee)) * \
#         0.18 if constant_env().get('loan_duration') == 1 else (
#             int(get_trans.amount) + int(get_trans.loan_fee)) * 0.35


#     ### get loan eligible payloads
#     eligible_id  = Eligible.objects.filter(phoneNumber = borrower_qu.borrower_phoneNumber).last()


#     ###### get borrower eligible amount and save it to his loan
#     elgible_amount = 0
#     if borrower_qu.borrower_eligibleOffer:
#         elgible_amount = float(borrower_qu.borrower_eligibleOffer)


#     # posting to loan model  without manadate reference  ends here

#     # Mandate reference request payload

#     remita_payload = {
#         "customerId": f'{borrower_queryset.borrower_remita_id.replace("r_","").replace(",", "")}',
#         "authorisationCode": borrower_queryset.borrower_authorisationCode,
#         "authorisationChannel": "USSD",
#         "phoneNumber": f"{borrower_queryset.borrower_phoneNumber}",
#         "accountNumber": f"{borrower_queryset.acct_no}",
#         "currency": "NGN",
#         "loanAmount": float(request_loan_amt),
#         "collectionAmount": float(repayent),
#         "dateOfDisbursement": datetime.now(),
#         "dateOfCollection": datetime.now(),
#         "totalCollectionAmount": total_repayent,
#         "numberOfRepayments": 1
#     }
#     mandate_request_payload = f"{remita_payload}"

#     # saving mandate request payload to the model here
#     Mandate_Request.objects.create(
#         mandate_request_payload=mandate_request_payload,
#         amount=int(request_loan_amt),
#         phone_number=borrower_queryset.borrower_phoneNumber,
#         borrower_name=borrower_qu.borrower_fullname
#     )
#     # saving mandate request payload to the model end here

#     # request mandate reference from remita here
#     remita_data = Remita_Manager.ref_payload(**remita_payload)
#     remita_data = json.loads(remita_data)

#     print("remita mandate generated >>>>>>>>>>>>>>>>>>>>>>>>>>>>", remita_data)

#     # request mandate reference from remita end here

#     if remita_data['status'] == "success":

#         p_loan = Loan.post_loan_to_loandisk(
#             product_id,
#             borrower_queryset.borrower_id,
#             loan_application_id,
#             float(borrower_loan_choice_amount.replace(
#                 "N", "").replace(",", "")),
#             date_formate,
#             constant_env().get('loan_disk_one_month_interest') if dur == 1 else constant_env().loan_disk_two_month_post,
#             dur,
#             dur,
#             borrower_queryset.bank_code,
#             borrower_queryset.acct_no,
#             borrower_queryset.bvn_no,
#             borrower_queryset.borrower_remita_id.replace(
#                 "r_", "").replace(",", ""),
#             borrower_queryset.borrower_business_name,
#             borrower_queryset.borrower_business_name,
#             borrower_queryset.bank_name,
#             borrower_queryset.bank_name


#         )

#         print("post to loan disk response >>>>>>>>>>>>>>>>>>>>>>>>", p_loan)


#         ############ after posting the loan to loan disk.save it to our local db
#         Loan.objects.create(
#             customerId=borrower_qu.borrower_remita_id,
#             authorisationCode=borrower_qu.borrower_authorisationCode,
#             authorisationChannel=borrower_qu.borrower_channel,
#             phoneNumber=borrower_qu.borrower_phoneNumber,
#             accountNumber=borrower_qu.acct_no,
#             currency="Naira",
#             loanAmount=float(get_trans.amount),
#             collectionAmount=float(get_trans.loan_fee),
#             dateOfDisbursement=get_date_now,
#             totalCollectionAmount=get_trans.amount + total_col,
#             numberOfRepayments=constant_env().get('loan_duration'),
#             payement_reference = get_trans.ref_id,
#             loan_disk_id=p_loan['response']['loan_id'],
#             eligible_id = eligible_id,
#             elgible_amount = int(elgible_amount)
#         )


#         loan_disk_id = p_loan['response']['loan_id']
#         liberty_loan_id = Loan.objects.filter(
#             loan_disk_id=loan_disk_id).last()

#         mandateReference = remita_data['data']['mandateReference']
#         mandateReference.replace("'", "").replace(
#             ",", "").replace("(", "").replace(")", "")

#         # update manadate reference  success status here
#         update_mandate_ref = Mandate_Request.objects.filter(phone_number=borrower_queryset.borrower_phoneNumber).last()
#         update_mandate_ref.mandateReference = mandateReference,
#         update_mandate_ref.loan_disk_id = p_loan['response']['loan_id']
#         update_mandate_ref.status = True
#         update_mandate_ref.remita_gen_response = remita_data
#         update_mandate_ref.save()

#         # update manadate reference success status end here

#         # update manadate reference  on loan disk and loan id here

#         dur = 0
#         if constant_env().get('loan_duration') == 1:
#             dur = 119290
#         elif constant_env().get('loan_duration') == 2:
#             dur = 119291
#         elif constant_env().get('loan_duration') == 3:
#             dur = 119292
#         # loan disk payload for update
#         loan_application_id = f"LXF-{loan_disk_id}-{liberty_loan_id.id}-USSD"
#         loan = Loan.objects.filter(loan_disk_id=loan_disk_id).last()
#         date_formate = datetime.now().date()
#         date_formate = datetime.strptime(
#             f"{date_formate}", "%Y-%m-%d").strftime('%d/%m/%Y')
#         loan_disk_payload = {
#             "loan_product_id": f"{dur}",
#             "borrower_id": f"{borrower_queryset.borrower_id}",
#             "loan_application_id": f"{loan_application_id}",
#             "loan_disbursed_by_id": "91595",
#             "loan_principal_amount": int(loan.loanAmount),
#             "loan_released_date": f"{date_formate}",
#             "loan_interest_method": "flat_rate",
#             "loan_interest_type": "percentage",
#             "loan_interest_period": "Month",
#             "loan_interest": constant_env().get('loan_disk_one_month_interest') if constant_env().get('loan_duration') == 1 else constant_env().loan_disk_two_month_post,
#             "loan_duration_period": "Months",
#             "loan_duration": constant_env().get('loan_duration'),
#             "loan_payment_scheme_id": "3",
#             "loan_num_of_repayments": constant_env().get('loan_duration'),
#             "loan_decimal_places": "round_up_to_five",
#             "loan_status_id": "8",
#             "custom_field_5262": f"{mandateReference}",
#             "custom_field_4181": f"{borrower_queryset.bank_code}",
#             "custom_field_4178": f"{borrower_queryset.acct_no}",
#             "custom_field_5261": f"{loan.dateOfCollection}",
#             "custom_field_4361": f"{borrower_queryset.bvn_no}",
#             "loan_fee_id_2746": 0,
#             "loan_fee_id_3915": 0,
#             "loan_fee_id_4002": 0,
#             "loan_fee_id_4003": 0,
#             "loan_fee_id_4004": 0,
#             "loan_fee_id_4005": 0,
#             "loan_fee_id_4006": 0,
#             "custom_field_5251": f'{borrower_queryset.borrower_remita_id.replace("r_","").replace(",", "")}',
#             "custom_field_4385": f"{borrower_queryset.borrower_business_name}",
#             "custom_field_6363": f"{borrower_queryset.borrower_business_name}",
#             "loan_id": loan.loan_disk_id,
#             "custom_field_4219": f"{borrower_queryset.bank_name}",
#             "custom_field_4221": f"{borrower_queryset.bank_name}"

#         }

#         logging.debug(
#             "printing payload to be pas to loan disk")
#         logging.debug(loan_disk_payload)
#         logging.debug("printing payload to be pas to loan disk")
#         logging.debug(loan_disk_payload)

#         update_loaddisk = post_loan_to_loandisk(**loan_disk_payload)

#         print("updated loan >>>>>>>>>>>>>>>>>>>>>>>>", update_loaddisk)

#         # update manadate reference  on loan disk and loan id end here

#         # update manadate reference  on loan model here

#         gt_loan = Loan.objects.filter(loan_disk_id=loan_disk_id).last()
#         gt_loan.mandateReference = mandateReference
#         gt_loan.save()
#         # update manadate reference  on loan model end here


#         # Woven disbursement  here
#         woven_payment_disbursment(**payload)

#         return "END Loan application has been sent for processing, you should receive a credit notification from your bank shortly"

#     else:
#         # loan_disk_id = p_loan['response']['loan_id']
#         # liberty_loan_id = Loan.objects.filter(
#         #     loan_disk_id=loan_disk_id)["id"]
#         # mandateReference = remita_data['date']['mandateReference']

#         # update manadate reference  success status here

#         update_request_mandate = Mandate_Request.objects.filter(phone_number=borrower_queryset.borrower_phoneNumber).last()
#         update_request_mandate.status = False
#         update_request_mandate.remita_gen_response = remita_data
#         update_request_mandate.save()


#         return None

# update manadate reference success status end here

# Extract stop here
