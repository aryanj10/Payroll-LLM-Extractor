import pyotp
from dotenv import load_dotenv
load_dotenv()
TOTP_SECRET = os.getenv("TOTP_SECRET")
totp = pyotp.TOTP("VOQF25GTGDUFDDMG7WQEMOSRVTJHL6IY")
print("Your 6-digit 2FA code is:", totp.now())
