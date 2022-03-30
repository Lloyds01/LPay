from django.core.mail import BadHeaderError, EmailMessage
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import get_template
import os


def insufficent_bal():
    """
    This function sends email to admin
    when wooven account balance becomes Insufficent
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(BASE_DIR, "main/template/email.html")) as emailSend:
        feedback_message = emailSend.read()

    subject = "Failed Disbursment"
    sender = "whispersms@gmail.com"
    recipients = []

    c = {"user": "user"}

    message = EmailMultiAlternatives(
        subject=subject, body=feedback_message, from_email=sender, to=recipients
    )

    html_template = get_template("email.html").render(c)

    message.attach_alternative(html_template, "text/html")

    try:
        message.send()
    except BadHeaderError:
        pass
