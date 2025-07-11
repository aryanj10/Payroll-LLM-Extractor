import pyotp

totp = pyotp.TOTP("VOQF25GTGDUFDDMG7WQEMOSRVTJHL6IY")
print("Your 6-digit 2FA code is:", totp.now())
