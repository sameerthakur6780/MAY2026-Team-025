import re

# 10 digits, no country code/leading zero -- matches Indian mobile numbers.
INDIAN_PHONE_REGEX = re.compile(r"^[6-9]\d{9}$")
INDIAN_PHONE_ERROR = "phone must be a valid 10-digit Indian mobile number (10 digits, starting with 6-9)"