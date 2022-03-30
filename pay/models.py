from email.policy import default
from django.db import models
from datetime import datetime
from dateutil import relativedelta
from django.db.models.signals import pre_save
from .utils import unique_text_msg_code_generator
from numpy import mod

# Create your models here.
class Web_hoop(models.Model):
    channel = models.CharField(max_length=300)
    phone_number = models.CharField(max_length=300)
    date = models.DateTimeField(auto_now=True)
    hops = models.IntegerField()
    status = models.CharField(max_length=300)
    message = models.TextField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return self.phone_number

    @property
    def duration(self):
        if not self.updated_date:

            return "0s"
            if int(get_time) // 60 < 0:
                print(get_time)
                return f"{get_time}s"
            elif get_time // 60 > 0:
                return f"{get_time}m"
        else:
            get_time = (self.date - self.updated_date).total_seconds()
            if get_time // 60 < 0:
                return f"{get_time}s"
            elif get_time // 60 > 0:
                return f"{get_time}m"
            else:
                return f"{get_time}s"


class Web_otp(models.Model):
    phone = models.CharField(max_length=300)
    code = models.PositiveIntegerField()
    loan_duration = models.IntegerField(null=True, blank=True)
    amount = models.IntegerField(null=True, blank=True)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.phone) + ":" + str(self.code)


def pre_save_txt_msg_code(instance, sender, *args, **kwargs):   
    instance.code = unique_text_msg_code_generator(instance)


pre_save.connect(pre_save_txt_msg_code, sender=Web_otp)


class USSD_Constant_Variable(models.Model):
    loan_duration = models.IntegerField(default=1)
    eligible_interest = models.FloatField(null=True, blank=True)
    affordability_rate = models.FloatField(null=True, blank=True)
    loan_disk_one_month_interest = models.IntegerField(null=True, blank=True)
    loan_disk_two_month_interets = models.IntegerField(null=True, blank=True)
    loan_disk_two_month_post = models.FloatField(null=True, blank=True)
    loan_disk_three_month_interets = models.IntegerField(null=True, blank=True)
    loan_disk_four_month_interets = models.IntegerField(null=True, blank=True)
    loan_disk_five_month_interets = models.IntegerField(null=True, blank=True)
    loan_disk_six_month_interets = models.IntegerField(null=True, blank=True)
    loan_disk_seven_month_interets = models.IntegerField(null=True, blank=True)
    loan_disk_eight_month_interets = models.IntegerField(null=True, blank=True)
    loan_disk_pub_key = models.IntegerField(null=True, blank=True)
    loan_disk_branch_id = models.IntegerField(null=True, blank=True)
    loan_disk_fedwk_one_month = models.IntegerField(null=True, blank=True)
    loan_disk_fedwk_two_month = models.IntegerField(null=True, blank=True)
    loan_disk_fedwk_three_month = models.IntegerField(null=True, blank=True)
    loan_fee = models.IntegerField(null=True, blank=True)
    topup = models.BooleanField(default=False)
    topup_anytime = models.BooleanField(default=False)
    topup_monthly = models.BooleanField(default=False)
    banned_ministries = models.JSONField(null=True, blank=True)


def constant_env():
    get_constant = USSD_Constant_Variable.objects.all().last()

    data = {
        "loan_duration": get_constant.loan_duration,
        "eligible_interest": get_constant.eligible_interest,
        "affordability_rate": get_constant.affordability_rate,
        "loan_disk_one_month_interest": get_constant.loan_disk_one_month_interest,
        "loan_disk_two_month_post": get_constant.loan_disk_two_month_post,
        "loan_disk_three_month_interets": get_constant.loan_disk_three_month_interets,
        "loan_disk_four_month_interets": get_constant.loan_disk_four_month_interets,
        "loan_disk_five_month_interets": get_constant.loan_disk_five_month_interets,
        "loan_disk_six_month_interets": get_constant.loan_disk_six_month_interets,
        "loan_disk_seven_month_interets": get_constant.loan_disk_seven_month_interets,
        "loan_disk_eight_month_interets": get_constant.loan_disk_eight_month_interets,
        "loan_disk_pub_key": get_constant.loan_disk_pub_key,
        "loan_disk_branch_id": get_constant.loan_disk_branch_id,
        "loan_disk_fedwk_one_month": get_constant.loan_disk_fedwk_one_month,
        "loan_disk_fedwk_two_month": get_constant.loan_disk_fedwk_two_month,
        "loan_disk_fedwk_three_month": get_constant.loan_disk_fedwk_three_month,
        "loan_fee": get_constant.loan_fee,
        "topup": get_constant.topup,
        "topup_monthly": get_constant.topup_monthly,
        "topup_anytime": get_constant.topup_anytime,
        "banned_ministries": get_constant.banned_ministries,

    }

    # data = {"data": "data"}

    return data

# Create your models here.
class Retargeting_message_24_hours(models.Model):
    phone = models.CharField(max_length=300)
    date = models.DateTimeField(auto_now=True)
    message_template = models.CharField(max_length=500)

    def __str__(self) -> str:
        return super().__str__()


class Retargeting_message_three_days(models.Model):
    phone = models.CharField(max_length=300)
    date = models.DateTimeField(auto_now=True)
    message_template = models.CharField(max_length=500)

    def __str__(self) -> str:
        return super().__str__()


class Retargeting_message_fourteen_days(models.Model):
    phone = models.CharField(max_length=300)
    date = models.DateTimeField(auto_now=True)
    message_template = models.CharField(max_length=500)

    def __str__(self) -> str:
        return super().__str__()


class Retargeting_message_twenty_eight_days(models.Model):
    phone = models.CharField(max_length=300)
    date = models.DateTimeField(auto_now=True)
    message_template = models.CharField(max_length=500)

    def __str__(self) -> str:
        return super().__str__()
