import pyotp

totp = pyotp.TOTP("")
print("Your 6-digit 2FA code is:", totp.now())
