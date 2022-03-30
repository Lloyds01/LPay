import random


def random_text_msg_digit_code_generator():
    digits = "0123456789"
    result = ""
    for i in range(0, 6):
        result += random.choice(digits)

    return result


def unique_text_msg_code_generator(instance):
    new_txt_msg_code = random_text_msg_digit_code_generator()

    Klass = instance.__class__

    qs_exists = Klass.objects.filter(code=new_txt_msg_code).exists()
    if qs_exists:
        return unique_text_msg_code_generator(instance)
    return new_txt_msg_code


def confirm_requested_amount(amount, duration):
    pass
