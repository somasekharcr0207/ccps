import re


def luhn_valid(number: str) -> bool:
    digits = [int(d) for d in number][::-1]
    total = sum(digits[0::2])
    for d in digits[1::2]:
        d *= 2
        total += d - 9 if d > 9 else d
    return total % 10 == 0


def detect_brand(number: str) -> str:
    if number.startswith("4"):
        return "VISA"
    if re.match(r"^(5[1-5]|2[2-7])", number):
        return "MASTERCARD"
    if re.match(r"^3[47]", number):
        return "AMEX"
    if re.match(r"^(6011|65|64[4-9])", number):
        return "DISCOVER"
    if re.match(r"^(60|65|81|82|508)", number):
        return "RUPAY"
    return "OTHER"


def mask_number(number: str) -> str:
    return "**** **** **** " + number[-4:]
