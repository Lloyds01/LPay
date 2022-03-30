import imp
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Web_hoop, Web_otp, USSD_Constant_Variable

# Register your models here.
@admin.register(Web_hoop)
class Web_hoopAdmin(ImportExportModelAdmin):
    list_display = [
        "date",
        "channel",
        "phone_number",
        "hops",
        "status",
        "message",
        "duration",
        "updated_date",
    ]

    search_fields = ["phone_number"]


@admin.register(USSD_Constant_Variable)
class USSD_Constant_VariableeAdmin(ImportExportModelAdmin):
    list_display = [
        "loan_duration",
        "eligible_interest",
        "affordability_rate",
        "loan_disk_one_month_interest",
        "loan_disk_two_month_interets",
        "loan_disk_two_month_post",
        "loan_disk_three_month_interets",
        "loan_disk_four_month_interets",
        "loan_disk_pub_key",
        "loan_disk_branch_id",
        "loan_disk_fedwk_one_month",
        "loan_disk_fedwk_two_month",
        "loan_disk_fedwk_three_month",
        "loan_fee",
        "topup",
    ]

    search_fields = [
        "loan_duration",
        "eligible_interest",
        "affordability_rate",
        "loan_disk_one_month_interest",
        "loan_disk_two_month_interets",
        "loan_disk_two_month_post",
        "loan_disk_three_month_interets",
        "loan_disk_four_month_interets",
        "loan_disk_pub_key",
        "loan_disk_branch_id",
        "loan_disk_fedwk_one_month",
        "loan_disk_fedwk_two_month",
        "loan_disk_fedwk_three_month",
        "loan_fee",
    ]


admin.site.register(Web_otp)
