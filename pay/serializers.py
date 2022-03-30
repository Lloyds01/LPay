from rest_framework import serializers


class On_boarding_Serializer(serializers.Serializer):
    phone = serializers.CharField()
    email = serializers.CharField(required=False)


class Loan_payout_serializer(serializers.Serializer):
    phone = serializers.CharField()
    amount = serializers.IntegerField()
    duration = serializers.CharField()


class Web_session_decline_serializer(serializers.Serializer):
    phone = serializers.CharField()


class Payout_otp(serializers.Serializer):
    code = serializers.CharField()
    phone = serializers.CharField()


class Disburse_serializer(serializers.Serializer):
    name = serializers.CharField()
    account_number = serializers.CharField()
    bank = serializers.CharField()
    employer = serializers.CharField()
    amount = serializers.CharField()
    phone = serializers.CharField()


class Resend_otp_serializer(serializers.Serializer):
    phone = serializers.CharField()
