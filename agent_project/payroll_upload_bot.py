
from playwright.sync_api import sync_playwright
import pandas as pd
import time
import pyotp
import os

FILENAME = os.path.abspath("Data/output/populated_files/populated_output.csv")
CLIENT = 'NewBaltimo'
PAY_PERIOD = '07-07-2025 - 07-07-2025'
PAY_DATE = '07-07-2025'



def run_upload_bot():
    with sync_playwright() as p:
        # Use a persistent context to simulate a real browser session
        user_data_dir = "C:/Users/aryan/playwright_profile"
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            slow_mo=50,
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = context.pages[0] if context.pages else context.new_page()

        # Mask automation detection
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Step 1: Login
        page.goto("https://login.accountantsoffice.com/")
        page.fill('input[name="FirmCode"]', FIRMCODE)
        page.fill('input[name="UserName"]', USERNAME)
        page.fill('input[name="Password"]', PASSWORD)
        page.click('input[type="submit"]')

        # Step 2: Handle 2FA
        print("✅ Waiting for 2FA method screen...")
        page.wait_for_url("https://login.accountantsoffice.com/Auth/SendCode?returnUrl=/&firmCode=starb3966", timeout=15000)
        page.click('input[type="submit"][value="Select"]')

        page.wait_for_selector('input[name="Code"]', timeout=15000)
        print("✅ On 2FA input page")

        totp = pyotp.TOTP("VOQF25GTGDUFDDMG7WQEMOSRVTJHL6IY")
        code = totp.now()
        print("✅ Generated TOTP code:", code)
        page.fill('input[name="Code"]', code)
        page.click('text=Submit')

        # Post-login wait
        page.wait_for_url("https://www.accountantsoffice.com/AoCommon/")
        page.wait_for_timeout(3000)

        # Navigate to Payroll Launch manually (not via click)
        print("🔗 Navigating to Payroll Launch page...")
        page.goto("https://www.accountantsoffice.com/AoCommon/Home/Launch/payroll")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(4000)

        # Wait and manually search client
        page.fill("input[placeholder='Search client']", CLIENT)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)

        # Go to Payroll Entry
        page.goto("https://app.payrollrelief.com/Payroll/PayrollEntry")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Select "Prior" radio
        page.click("text=Prior")
        page.wait_for_timeout(1000)

        # Select Period and Date
        page.select_option("select#ddlPayrollPeriod", PAY_PERIOD)
        page.select_option("select#ddlPayDate", PAY_DATE)
        page.wait_for_timeout(1000)

        # Upload
        page.set_input_files('input[type="file"]', FILENAME)
        page.click("button:has-text('Submit')")
        print(f"✅ Upload completed for client: {CLIENT}")

        time.sleep(3)
        context.close()

if __name__ == "__main__":
    run_upload_bot()
