from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .serializers import (
    On_boarding_Serializer,
    Loan_payout_serializer,
    Web_session_decline_serializer,
    Payout_otp,
    Disburse_serializer,
    Resend_otp_serializer,
)
from main.models import (
    Borrower,
    Catched_Cookie,
    InEligible_borrowers,
    Loan,
    Re_Targeting,
    Liberty_USSD_Constant_Variable,
    Transaction,
    LoanRequestPassToCelery,
)
from datetime import datetime
from main.helpers.loan_topup import topup_view, active_loan_check
from django.conf import settings
from main.helpers.utils import nip_bank_search, full_name_split
import uuid
from pay.models import Web_hoop, Web_otp, USSD_Constant_Variable, constant_env
from main.helpers.loan_helpers import Remita_Manager
from main.helpers.month_scale import scale_to_months
from pay.send_sms import send_payout_otp
from django.utils import timezone
from main.tasks import dud_loan_processor
from main.helpers.send_sms import send_loan_processing_sms
from main.menu import create_transaction

# Create your views here.


# get constants
# get_constant = constant_env()


@method_decorator(csrf_exempt, name="dispatch")
class On_boarding_view(APIView):
    def post(self, request):
        serializer = On_boarding_Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data.get("phone")
        email = serializer.validated_data.get("email")

        is_top_up = None

        try:
            catched_ = Catched_Cookie.objects.get(phone=phone)
            # if cache has passed 12 hours. if it passes 12 hours. clear the cache
            if catched_.clear_cache():
                raise ValueError("Cache cleard. please create new cache")

            # end of clear cache on demand

            if catched_.has_expired(phone):
                catched_.phone = ""
                catched_.save()
                raise ValueError("Cache has expired. allow new Remita call")
        except:
            # logging.debug(f"{datetime.now()}")
            catched_ = Catched_Cookie.objects.create(
                phone=phone, date=datetime.now())

        eligibileAmountChecker = None
        eligibileChecker = None
        eligiblechecker_error = None

        ############################
        # entry of hops
        ############################
        Web_hoop.objects.create(
            channel="web",
            phone_number=phone,
            date=datetime.now(),
            updated_date=datetime.now(),
            hops=1,
            status="Incomplete",
        )

        get_web_hops = Web_hoop.objects.filter(phone_number=phone).last()

        if catched_.disburse == True and catched_.message == "":

            # user loan disbursement is still pending
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Please wait your disbursment is still processing",
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        elif catched_.message != None:
            eligiblechecker_error = catched_.message
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": str(eligiblechecker_error).replace("END", ""),
            }

            get_web_hops.updated_date = datetime.now()
            get_web_hops.status = "Success"
            get_web_hops.message = str(
                eligiblechecker_error).replace("END", "")
            get_web_hops.save()

            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        ################### top up logic ###############################
        if constant_env().get("topup") == True:
            check_topup = topup_view(phone)

            if check_topup:
                if check_topup["eligible"] == False:
                    response = check_topup["message"]
                    catched_.message = response
                    catched_.user_eligibile_amount = ""
                    catched_.save()

                    data = {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Sorry, you're not eligible for top-up at the moment",
                    }

                    get_web_hops.updated_date = datetime.now()
                    get_web_hops.status = "Success"
                    get_web_hops.message = (
                        "Sorry, you're not eligible for top-up at the moment"
                    )
                    get_web_hops.save()

                    return Response(data, status=status.HTTP_400_BAD_REQUEST)

                else:

                    if (
                        catched_.user_eligibile_amount == None
                        or catched_.user_eligibile_amount == ""
                    ):
                        eligibileCheckers = Borrower.get_eligible_amount(
                            phone=phone, channel="ussd"
                        )
                        eligibileAmountChecker = eligibileCheckers["eligible_amount"]
                        eligibileChecker = eligibileCheckers
                        catched_.user_eligibile_amount = eligibileCheckers[
                            "eligible_amount"
                        ]
                        catched_.save()

                        if eligibileCheckers == None:

                            data = {
                                "status": status.HTTP_400_BAD_REQUEST,
                                "message": "Sorry this product is for salary earners only",
                            }

                            get_web_hops.updated_date = datetime.now()
                            get_web_hops.status = "Success"
                            get_web_hops.message = (
                                "Sorry this product is for salary earners only"
                            )
                            get_web_hops.save()

                            return Response(data, status=status.HTTP_400_BAD_REQUEST)
                        else:

                            eligibileAmountChecker = eligibileCheckers[
                                "eligible_amount"
                            ]
                            eligibileChecker = eligibileCheckers
                            catched_.user_eligibile_amount = eligibileCheckers[
                                "eligible_amount"
                            ]
                            catched_.save()

                    else:
                        eligibileAmountChecker = int(
                            catched_.user_eligibile_amount)

            else:
                if (
                    catched_.user_eligibile_amount == None
                    or catched_.user_eligibile_amount == ""
                ):
                    eligibileCheckers = Borrower.get_eligible_amount(
                        phone=phone, channel="ussd"
                    )
                    eligibileAmountChecker = eligibileCheckers["eligible_amount"]
                    eligibileChecker = eligibileCheckers
                    catched_.user_eligibile_amount = eligibileCheckers[
                        "eligible_amount"
                    ]
                    catched_.save()

                    if eligibileCheckers == None:

                        data = {
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Sorry this product is for salary earners only",
                        }

                        return Response(data, status=status.HTTP_400_BAD_REQUEST)
                    else:

                        eligibileAmountChecker = eligibileCheckers["eligible_amount"]
                        eligibileChecker = eligibileCheckers
                        catched_.user_eligibile_amount = eligibileCheckers[
                            "eligible_amount"
                        ]
                        catched_.save()
                else:
                    eligibileAmountChecker = int(
                        catched_.user_eligibile_amount)

        else:
            check_for_active_loans = active_loan_check(phone)
            if check_for_active_loans["status"] == True:
                catched_.message = check_for_active_loans["message"]
                catched_.user_eligibile_amount = ""
                catched_.save()

                data = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Sorry you're not eligible. You've an active loan with us",
                }

                get_web_hops.updated_date = datetime.now()
                get_web_hops.status = "Success"
                get_web_hops.message = (
                    "Sorry you're not eligible. You've an active loan with us"
                )
                get_web_hops.save()

                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            if (
                catched_.user_eligibile_amount == None
                or catched_.user_eligibile_amount == ""
            ):
                eligibileCheckers = Borrower.get_eligible_amount(
                    phone=phone, channel="ussd"
                )

                eligibileAmountChecker = eligibileCheckers["eligible_amount"]
                eligibileChecker = eligibileCheckers
                catched_.user_eligibile_amount = eligibileCheckers["eligible_amount"]
                catched_.save()

                if eligibileCheckers == None:
                    data = {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Sorry this product is for salary earners only",
                    }

                    get_web_hops.updated_date = datetime.now()
                    get_web_hops.status = "Success"
                    get_web_hops.message = (
                        "Sorry this product is for salary earners only"
                    )
                    get_web_hops.save()

                    return Response(data, status=status.HTTP_400_BAD_REQUEST)

                else:
                    pass

                eligibileAmountChecker = eligibileCheckers["eligible_amount"]
                eligibileChecker = eligibileCheckers
                catched_.user_eligibile_amount = eligibileCheckers["eligible_amount"]
                catched_.save()

            else:
                eligibileAmountChecker = int(catched_.user_eligibile_amount)

        loan_cap = int(settings.LOAN_CAP)
        eligibileAmountChecker = (
            loan_cap if eligibileAmountChecker > loan_cap else eligibileAmountChecker
        )

        if eligibileAmountChecker == 0:
            check_non_borrowers_db = InEligible_borrowers.objects.filter(
                phone=phone
            ).last()
            if eligiblechecker_error != None:
                data = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": str(eligiblechecker_error).replace("END", ""),
                }

                get_web_hops.updated_date = datetime.now()
                get_web_hops.status = "Success"
                get_web_hops.message = str(
                    eligiblechecker_error).replace("END", "")
                get_web_hops.save()

                catched_.message = eligiblechecker_error
                catched_.save()

                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            elif (
                eligibileChecker["message"] == "Customer not found, Customer not found"
            ):
                if not check_non_borrowers_db:
                    InEligible_borrowers.objects.create(
                        phone=phone, date=datetime.now()
                    )

                data = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Sorry this loan product is availiable for civil servants only",
                }

                get_web_hops.updated_date = datetime.now()
                get_web_hops.status = "Success"
                get_web_hops.message = (
                    "Sorry this loan product is availiable for civil servants only"
                )
                get_web_hops.save()

                catched_.message = (
                    "END Sorry this loan product is availiable for civil servants only!"
                )
                catched_.save()

                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            elif eligibileChecker["message"] == "Inactive customer, Inactive customer":
                if not check_non_borrowers_db:
                    InEligible_borrowers.objects.create(
                        phone=phone, date=datetime.now()
                    )

                catched_.message = "END sorry unable to get salary information"
                catched_.save()

                data = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "sorry unable to get salary information",
                }

                get_web_hops.updated_date = datetime.now()
                get_web_hops.status = "Success"
                get_web_hops.message = "sorry unable to get salary information"
                get_web_hops.save()

                catched_.message = "END sorry unable to get salary information"
                catched_.save()

                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            elif (
                eligibileChecker["message"]
                == "Customer Is Currently Suspended, Customer Is Currently Suspended"
            ):
                catched_.message = "END You're currently not eligible based on your current credit data. try again later"
                catched_.save()

                data = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "You're currently not eligible based on your current credit data. try again later",
                }

                get_web_hops.updated_date = datetime.now()
                get_web_hops.status = "Success"
                get_web_hops.message = "You're currently not eligible based on your current credit data. try again later"
                get_web_hops.save()

                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            elif (
                eligibileChecker["message"]
                == "Error Processing Request, Error Processing Request"
            ):
                catched_.message = (
                    "END unable to process your request at this time. try again later"
                )
                catched_.save()

                data = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "unable to process your request at this time. try again later",
                }

                get_web_hops.updated_date = datetime.now()
                get_web_hops.status = "Success"
                get_web_hops.message = (
                    "unable to process your request at this time. try again later"
                )
                get_web_hops.save()

                return Response(data, status=status.HTTP_400_BAD_REQUEST)
            elif (
                eligibileChecker["message"]
                == "Customer not from coverage region, SUCCESS"
            ):
                catched_.message = "END Sorry cannot process eligibility, loans are not available to your employer at this time"
                catched_.save()

                data = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Sorry cannot process eligibility, loans are not available to your employer at this time",
                }

                get_web_hops.updated_date = datetime.now()
                get_web_hops.status = "Success"
                get_web_hops.message = "Sorry cannot process eligibility, loans are not available to your employer at this time"
                get_web_hops.save()

                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            else:
                if not check_non_borrowers_db:
                    InEligible_borrowers.objects.create(
                        phone=phone, date=datetime.now()
                    )

                catched_.message = "END sorry not eligible. try again later"
                catched_.save()
                data = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "sorry not eligible. try again later",
                }

                get_web_hops.updated_date = datetime.now()
                get_web_hops.status = "Success"
                get_web_hops.message = "sorry not eligible. try again later"
                get_web_hops.save()

                return Response(data, status=status.HTTP_400_BAD_REQUEST)

        borrower_object = Borrower.objects.filter(
            borrower_phoneNumber=phone).last()

        b = nip_bank_search(borrower_object.bank_code)
        ref = uuid.uuid1()

        loan_offer_limit = 1000

        if eligibileAmountChecker == 0:
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "You are not eligible for a loan offer, please check back next time",
            }

            get_web_hops.updated_date = datetime.now()
            get_web_hops.status = "Success"
            get_web_hops.message = (
                "You are not eligible for a loan offer, please check back next time"
            )
            get_web_hops.save()

            catched_.message = (
                "END You are not eligible for a loan offer, please check back next time"
            )
            catched_.save()

            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        elif eligibileAmountChecker < loan_offer_limit:
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "You are not eligible for a loan offer at this time, please check back later",
            }

            get_web_hops.updated_date = datetime.now()
            get_web_hops.status = "Success"
            get_web_hops.message = "You are not eligible for a loan offer at this time, please check back later"
            get_web_hops.save()

            catched_.message = "END You are not eligible for a loan offer at this time, please check back later"
            catched_.save()

            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        else:
            catched_.user_eligibile_amount = eligibileAmountChecker
            catched_.save()
            #########################
            # save user to re_targeting model db, just incase the issue doesn't take
            # the loan. we'll be sending him/her remindeer to come back and apply for his / her loan
            ########################
            get_user_targeting = Re_Targeting.objects.filter(
                phone_number=phone).last()
            if get_user_targeting:
                get_user_targeting.is_loan_taken = False
                get_user_targeting.updated_date = datetime.now()
                get_user_targeting.save()
            else:
                Re_Targeting.objects.create(
                    first_name=borrower_object.borrower_firstname,
                    last_name=borrower_object.borrower_lastname,
                    eligible_amount=eligibileAmountChecker,
                    phone_number=phone,
                )

            get_loan_duration = constant_env().get("loan_duration")

            eligibilities = scale_to_months(
                eligibileAmountChecker, get_loan_duration)

            data_list = []

            data = {
                "status": status.HTTP_200_OK,
                "loan_fee": constant_env().get("loan_fee"),
                "phone": phone,
                "data": data_list,
            }

            loan__num_count = 0

            loan_innterest_d = 0

            print(f"{eligibileAmountChecker} :::::::::::::::::::::::::::::::")

            for key, value in eligibilities.items():

                if int(key[0]) == 1:
                    loan_month_display = str(key).replace("-", " ")
                elif int(key[0]) > 1:
                    loan_month_display = (
                        str(key).replace("-", " ").replace("month", "months")
                    )

                if int(key[0]) == 1:
                    loan__num_count = "one_month"
                    loan_innterest_d = constant_env().get(
                        "loan_disk_one_month_interest"
                    )
                elif int(key[0]) == 2:
                    loan__num_count = "two_month"
                    loan_innterest_d = constant_env().get("loan_disk_two_month_post")
                elif int(key[0]) == 3:
                    loan__num_count = "three_month"
                    loan_innterest_d = constant_env().get(
                        "loan_disk_three_month_interets"
                    )

                elif int(key[0]) == 4:
                    loan__num_count = "four_month"
                    loan_innterest_d = constant_env().get(
                        "loan_disk_four_month_interets"
                    )

                elif int(key[0]) == 5:
                    loan__num_count = "five_month"
                    loan_innterest_d = constant_env().get(
                        "loan_disk_five_month_interets"
                    )

                elif int(key[0]) == 6:
                    loan__num_count = "six_month"
                    loan_innterest_d = constant_env().get(
                        "loan_disk_six_month_interets"
                    )

                elif int(key[0]) == 7:
                    loan__num_count = "five_month"
                    loan_innterest_d = constant_env().get(
                        "loan_disk_seven_month_interets"
                    )

                elif int(key[0]) == 8:
                    loan__num_count = "six_month"
                    loan_innterest_d = constant_env().get(
                        "loan_disk_eight_month_interets"
                    )

                data_list.append(
                    {
                        "duration": int(key[0]),
                        "interest": loan_innterest_d,
                        "amount": int(
                            str(value[100]).replace("N", "").replace(",", "")
                        ),
                    }
                )

            get_web_hops.updated_date = datetime.now()
            get_web_hops.status = "Incomplete"
            get_web_hops.message = f"one_month {eligibileAmountChecker}, two_month: {eligibileAmountChecker * 2}"
            get_web_hops.save()

            return Response(data, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class Loan_payout(APIView):
    def post(self, request):
        serializer = Loan_payout_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data.get("phone")
        amount = serializer.validated_data.get("amount")
        duration = serializer.validated_data.get("duration")

        get_user_hops = Web_hoop.objects.filter(phone_number=phone).last()

        get_user_hops.message = "Incomplete"
        get_user_hops.status = "OTP Gen"
        get_user_hops.hops += 1
        get_user_hops.updated_date = datetime.now()
        get_user_hops.save()

        get_borrower = Borrower.objects.filter(
            borrower_phoneNumber=phone).last()

        if get_borrower:
            request.session["phone"] = phone
            request.session["amount"] = amount
            request.session["duration"] = duration

            Web_otp.objects.update_or_create(
                phone=phone,
                amount=int(amount),
                loan_duration=int(duration),
                date=datetime.now(),
            )

            otp_code = Web_otp.objects.filter(phone=phone).last().code

            send_payout_otp(phone, otp_code,
                            get_borrower.borrower_firstname)

            data = {"status": status.HTTP_200_OK, "message": "OTP sent"}

            # save the hops
            get_user_hops.message = "success"
            get_user_hops.status = "otp sent"
            get_user_hops.updated_date = datetime.now()
            get_user_hops.save()

            return Response(data, status=status.HTTP_200_OK)

        else:
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "borrower not found",
            }

            # save the hops
            get_user_hops.message = "success"
            get_user_hops.status = "borrower not found. otp not sent"
            get_user_hops.updated_date = datetime.now()
            get_user_hops.save()

            return Response(data, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class Loan_payout_verification(APIView):
    def post(self, request):
        serializer = Payout_otp(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data.get("code")
        phone = serializer.validated_data.get("phone")

        now = timezone.now()

        # phone = request.session.get('phone')
        amount = request.session.get("amount")
        duration = request.session.get("duration")

        get_user_hops = Web_hoop.objects.filter(phone_number=phone).last()

        # save the hops
        get_user_hops.message = "Incomplete"
        get_user_hops.status = "otp verification"
        get_user_hops.hops += 1
        get_user_hops.updated_date = datetime.now()
        get_user_hops.save()

        get_code = Web_otp.objects.filter(phone=phone, code=code).last()

        if get_code:

            code_date = Web_otp.objects.filter(
                phone=phone, code=code).last().date
            diff = now - code_date

            if diff.days == 0 and diff.seconds < 420:
                usercode = Web_otp.objects.filter(
                    phone=phone, code=code).last().code
                user_otp = Web_otp.objects.filter(
                    phone=phone, code=code).last()
                if int(code) == usercode:

                    get_borrower = Borrower.objects.filter(
                        borrower_phoneNumber=phone
                    ).last()

                    if get_borrower:
                        b = nip_bank_search(get_borrower.bank_code)

                        try:
                            get_user_bank = b["bank_code"]
                        except:
                            get_user_bank = "None"

                        if get_user_bank == "None":
                            data = {
                                "status": status.HTTP_400_BAD_REQUEST,
                                "message": "Issue with bank name. please contact support",
                            }

                            # save the hops
                            get_user_hops.message = "Success"
                            get_user_hops.status = (
                                "Issue with bank name. please contact support"
                            )
                            get_user_hops.updated_date = datetime.now()
                            get_user_hops.save()

                            return Response(data, status=status.HTTP_400_BAD_REQUEST)

                        else:
                            data = {
                                "status": status.HTTP_200_OK,
                                "data": {
                                    "name": get_borrower.borrower_fullname,
                                    "bank": get_borrower.bank_name,
                                    "company": get_borrower.borrower_business_name,
                                    "account": get_borrower.acct_no,
                                    "phone": phone,
                                    "amount": user_otp.amount,
                                    "duration": user_otp.loan_duration,
                                },
                            }

                            # save the hops
                            get_user_hops.message = "Success"
                            get_user_hops.status = "otp verified"
                            get_user_hops.updated_date = datetime.now()
                            get_user_hops.save()

                            return Response(data, status=status.HTTP_200_OK)
                    else:
                        data = {
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Borrower not found !!!",
                        }

                        # save the hops
                        get_user_hops.message = "Success"
                        get_user_hops.status = "Borrower not found !!!"
                        get_user_hops.updated_date = datetime.now()
                        get_user_hops.save()

                        return Response(data, status=status.HTTP_400_BAD_REQUEST)

                else:
                    data = {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid otp!!!",
                    }

                    # save the hops
                    get_user_hops.message = "Success"
                    get_user_hops.status = "Invalid OTP !!!"
                    get_user_hops.updated_date = datetime.now()
                    get_user_hops.save()

                    return Response(data, status=status.HTTP_400_BAD_REQUEST)

            else:
                data = {"message": "code exipred. resend your otp"}

                # save the hops
                get_user_hops.message = "Success"
                get_user_hops.status = "code exipred. resend your otp"
                get_user_hops.updated_date = datetime.now()
                get_user_hops.save()

                return Response(data, status=status.HTTP_400_BAD_REQUEST)

        else:
            data = {"status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid otp!!!"}

            get_user_hops.message = "Success"
            get_user_hops.status = "Invalid otp"
            get_user_hops.updated_date = datetime.now()
            get_user_hops.save()

            return Response(data, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class Payment_disburse(APIView):
    def post(self, request):
        serializer = Disburse_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data.get("phone")
        amount = serializer.validated_data.get("amount")
        name = serializer.validated_data.get("name")
        account_number = serializer.validated_data.get("account_number")
        employer = serializer.validated_data.get("employer")
        bank = serializer.validated_data.get("bank")

        catched_ = Catched_Cookie.objects.get(phone=phone)

        if catched_.disburse == True and catched_.message == "":
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Please wait your disbursment is still processing",
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        """ATHA ADDED THIS CODE TO STOP PEOPLE FROM COMING BACK TOO QUICK AND CAUSING MULTIPLE DISBURSEMENTS."""

        latest_transactions = Transaction.objects.filter(
            customer_phone__icontains=phone
        ).last()

        def get_minutes_since(time: datetime) -> float:
            """RETURN MINUTES BETWEEN CURRENT TIME AND TIME PASSED AS ARGUMENT."""
            difference = timezone.now() - time

            return difference.total_seconds() / 60

        if (
            latest_transactions
            and get_minutes_since(latest_transactions.created_at) < 120
        ):
            """If transaction is less less than 2hrs then stop the user."""

            data = {
                "status": status.HTTP_409_CONFLICT,
                "message": "Please wait your transaction is still processing",
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        """########### END OF CODE ATHA ADDED ##########"""

        usercode = Web_otp.objects.filter(phone=phone, amount=amount).last()
        print(f"web otp {usercode} \n\n\n\n")

        if usercode == None or usercode == "":
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "phone number issue",
            }

            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        get_borrower = Borrower.objects.filter(
            borrower_phoneNumber=phone).last()

        get_user_hops = Web_hoop.objects.filter(phone_number=phone).last()

        # save the hops
        get_user_hops.message = "Incomplete"
        get_user_hops.status = "payment disbursed"
        get_user_hops.hops += 1
        get_user_hops.updated_date = datetime.now()
        get_user_hops.save()

        b = nip_bank_search(get_borrower.bank_code)

        print(f"borrower bank code {b} \n\n\n\n")

        try:
            get_user_bank = b["bank_code"]
        except:
            get_user_bank = "None"

        if get_user_bank == "None":
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Issue with bank name. please contact support",
            }

            # save the hops
            get_user_hops.message = "Success"
            get_user_hops.status = "Issue with bank name. please contact support"
            get_user_hops.updated_date = datetime.now()
            get_user_hops.save()

            usercode.delete()

            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        ref = uuid.uuid1()
        payload = {
            "beneficiary_nuban": f"{get_borrower.borrower_phoneNumber}",
            "beneficiary_bank_code": get_user_bank,
            "bank_code_scheme": "NIP",
            "currency_code": "NGN",
            "narration": "Loan disbursement",
            "callback_url": "",
        }

        catched_.disburse = True
        catched_.date = datetime.now()
        catched_.message = ""
        catched_.save()

        reference = f"Libty-{ref.hex}"
        load_num_fee = constant_env().get("loan_fee")

        trans_status = create_transaction(
            "woven",
            get_borrower.borrower_fullname,
            float(str(amount).replace("N", "").replace(",", "")),
            reference,
            get_borrower.acct_no,
            phone,
            get_borrower.bank_code,
            float(str(load_num_fee).replace("N", "").replace(",", "")),
            usercode.loan_duration,
        )

        if trans_status["status"] == False:
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": trans_status["message"],
            }

            catched_.disburse = False
            catched_.date = datetime.now()
            catched_.message = trans_status["message"]
            catched_.save()

            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        else:
            usercode.delete()

            dud_loan_processor(
                amount, payload, get_borrower.id, reference, "web")

            data = {
                "status": status.HTTP_200_OK,
                "message": "Loan application has been sent for processing, you should receive a credit notification from your bank shortly",
            }

            # save the hops
            get_user_hops.message = "Success"
            get_user_hops.status = "Loan application has been sent for processing, you should receive a credit notification from your bank shortly"
            get_user_hops.updated_date = datetime.now()
            get_user_hops.save()

            return Response(data, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class Web_session_decline(APIView):
    def post(self, request):
        serializer = Web_session_decline_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data.get("phone")

        get_user_hops = Web_hoop.objects.filter(phone_number=phone).last()

        if get_user_hops:

            get_user_hops.message = "Decline"
            get_user_hops.status = "Success"
            get_user_hops.updated_date = datetime.now()
            get_user_hops.save()

            data = {"status": status.HTTP_200_OK}
            return Response(data, status=status.HTTP_200_OK)

        else:
            data = {
                "status": status.HTTP_200_OK,
                "message": "no hops found for this user",
            }

            return Response(data, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class Resend_otp(APIView):
    def post(self, request):
        serializer = Resend_otp_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data.get("phone")

        get_borrower = Borrower.objects.filter(
            borrower_phoneNumber=phone).last()

        get_user_hops = Web_hoop.objects.filter(phone_number=phone).last()

        get_user_hops.message = "Incomplete"
        get_user_hops.status = "otp resend"
        get_user_hops.hops += 1
        get_user_hops.updated_date = datetime.now()
        get_user_hops.save()

        user_otp = Web_otp.objects.filter(phone=phone).last()

        if not user_otp:
            get_user_hops.message = "success"
            get_user_hops.status = "otp resend user phone not found"
            get_user_hops.updated_date = datetime.now()
            get_user_hops.save()

            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "user phone not found",
            }

            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()

        diff = now - user_otp.date

        data = {"status": status.HTTP_200_OK, "message": diff.seconds}

        print(f"code \n\n\n\n {user_otp.code}")

        if diff.days == 0:
            if diff.seconds < 420:
                get_user_hops.message = "success"
                get_user_hops.status = "please wait for 7 minutes. you'll get your otp"
                get_user_hops.updated_date = datetime.now()
                get_user_hops.save()

                data = {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "please wait for 7 minutes. you'll get your otp",
                }

                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            else:
                loan_duration = user_otp.loan_duration
                amount = user_otp.amount
                Web_otp.objects.filter(phone=phone).delete()
                Web_otp.objects.create(
                    phone=phone,
                    date=datetime.now(),
                    loan_duration=loan_duration,
                    amount=amount,
                )

                otp_code = Web_otp.objects.filter(phone=phone).last().code

                send_payout_otp(phone, otp_code,
                                get_borrower.borrower_firstname)

                get_user_hops.message = "success"
                get_user_hops.status = "otp resent"
                get_user_hops.updated_date = datetime.now()
                get_user_hops.save()

                data = {"status": status.HTTP_200_OK, "message": "otp sent"}

                return Response(data, status=status.HTTP_200_OK)

        else:
            get_user_hops.message = "success"
            get_user_hops.status = "your last otp has passed a day. generate new otp"
            get_user_hops.updated_date = datetime.now()
            get_user_hops.save()
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "your last otp has passed a day. generate new otp",
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
