from datetime import datetime, timedelta
from django.core.mail import BadHeaderError, EmailMultiAlternatives
import os
from django.template.loader import get_template
import main
from django.db.models import Count


def mandate_failed(name, ministry, amount, laonfee, phone):
    """
    This function sends email to admin
    whenever loan has been disbursed and remita mandate fail to generate
    """

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(BASE_DIR, "templates/mandate_email.html")) as emailSend:
        feedback_message = emailSend.read()

    c = {
        "name": name,
        "ministry": ministry,
        "amount": amount,
        "phone": phone,
        "laonfee": laonfee,
    }

    subject = "Failed Mandate Generation"
    sender = "whispersms@gmail.com"
    recipients = [
        "libertyassured@gmail.com",
    ]

    message = EmailMultiAlternatives(
        subject=subject, body=feedback_message, from_email=sender, to=recipients
    )
    html_template = get_template("mandate_email.html").render(c)
    message.attach_alternative(html_template, "text/html")
    try:
        message.send()
    except BadHeaderError:
        pass


def woven_insufficient():
    """
    This function sends email to admin
    whenever woven payment becomes insufficient
    """

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(
        os.path.join(BASE_DIR, "templates/woven_insufficient_email.html")
    ) as emailSend:
        feedback_message = emailSend.read()

    c = {
        # "name": name,
        # "ministry": ministry,
        # "amount": amount,
        # "phone": phone,
        # "laonfee": laonfee
    }

    subject = "Woven Insufficient"
    sender = "whispersms@gmail.com"
    recipients = [
        "libertyassured@gmail.com",
    ]

    message = EmailMultiAlternatives(
        subject=subject, body=feedback_message, from_email=sender, to=recipients
    )
    html_template = get_template("woven_insufficient_email.html").render(c)
    message.attach_alternative(html_template, "text/html")
    try:
        message.send()
    except BadHeaderError:
        pass


def failed_to_post_to_loan_disk():
    """
    This function sends email to admin
    whenever woven payment becomes insufficient
    """

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(
        os.path.join(BASE_DIR, "templates/failed_post_to_loan_disk.html")
    ) as emailSend:
        feedback_message = emailSend.read()

    c = {
        # "name": name,
        # "ministry": ministry,
        # "amount": amount,
        # "phone": phone,
        # "laonfee": laonfee
    }

    subject = "Woven Insufficient"
    sender = "whispersms@gmail.com"
    recipients = [
        "libertyassured@gmail.com",
    ]

    message = EmailMultiAlternatives(
        subject=subject, body=feedback_message, from_email=sender, to=recipients
    )
    html_template = get_template("failed_post_to_loan_disk.html").render(c)
    message.attach_alternative(html_template, "text/html")
    try:
        message.send()
    except BadHeaderError:
        pass


def send_multi_email():
    """
    This function sends list of repeated transcation daily to admin
    """
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(BASE_DIR, "templates/multi_email.html")) as emailSend:
        feedback_message = emailSend.read()

    duplicate_emails = (
        main.models.Transaction.objects.values("customer_phone")
        .annotate(email_count=Count("customer_phone"))
        .filter(email_count__gt=1)
    )
    duplicate_objects = main.models.Transaction.objects.filter(
        created_at__date=yesterday,
        customer_phone__in=[item["customer_phone"] for item in duplicate_emails],
    )

    if duplicate_objects.exists():
        c = {"data_query": duplicate_objects}

        subject = "Multiple Disbursement"
        sender = "whispersms@gmail.com"
        recipients = [
            "libertyassured@gmail.com",
        ]

        message = EmailMultiAlternatives(
            subject=subject, body=feedback_message, from_email=sender, to=recipients
        )
        html_template = get_template("multi_email.html").render(c)
        message.attach_alternative(html_template, "text/html")
        try:
            message.send()
        except BadHeaderError:
            pass


def failed_to_stop_loan_on_remita(mandate):
    """
    This function sends email to admin
    whenever woven payment becomes insufficient
    """

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(
        os.path.join(BASE_DIR, "templates/failied_to_stop_mandate.html")
    ) as emailSend:
        feedback_message = emailSend.read()

    c = {
        # "name": name,
        # "ministry": ministry,
        # "amount": amount,
        # "phone": phone,
        "mandate": mandate
    }

    subject = "Failed Stop loan mandate"
    sender = "whispersms@gmail.com"
    recipients = [
        "libertyassured@gmail.com",
    ]

    message = EmailMultiAlternatives(
        subject=subject, body=feedback_message, from_email=sender, to=recipients
    )
    html_template = get_template("failied_to_stop_mandate.html").render(c)
    message.attach_alternative(html_template, "text/html")
    try:
        message.send()
    except BadHeaderError:
        pass


def send_negative_repayment():
    """
    This function sends list of repeated transcation daily to admin
    """

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(BASE_DIR, "templates/multi_email.html")) as emailSend:
        feedback_message = emailSend.read()

    get_user_loan = main.models.Loan.objects.all()

    query_data = []
    for i in get_user_loan:
        if i.paid_amount > i.loanAmount:
            get_borrower = main.models.Borrower.objects.filter(
                borrower_phoneNumber=i.phoneNumber
            ).last()
            query_data.append(
                {
                    "name": f"{get_borrower.borrower_fullname}",
                    "remita_id": f"{i.customerId}",
                    "mandate_ref": f"{i.mandateReference}",
                    "phone": i.phoneNumber,
                    "amount": i.loanAmount,
                    "paid_amount": i.paid_amount,
                }
            )

    if query_data:
        c = {"data_query": query_data}

        subject = "Multiple Disbursement"
        sender = "whispersms@gmail.com"
        recipients = [
            "libertyassured@gmail.com",
        ]

        message = EmailMultiAlternatives(
            subject=subject, body=feedback_message, from_email=sender, to=recipients
        )
        html_template = get_template("multi_email.html").render(c)
        message.attach_alternative(html_template, "text/html")
        try:
            message.send()
        except BadHeaderError:
            pass

    # if duplicate_objects.exists():
    #     c = {

    #     "data_query": duplicate_objects
    #     }

    #     subject = "Multiple Disbursement"
    #     sender = "whispersms@gmail.com"
    #     recipients = ["libertyassured@gmail.com",]

    #     message = EmailMultiAlternatives(
    #         subject=subject, body=feedback_message, from_email=sender, to=recipients)
    #     html_template = get_template(
    #         "multi_email.html").render(c)
    #     message.attach_alternative(html_template, "text/html")
    #     try:
    #         message.send()
    #     except BadHeaderError:
    #         pass
