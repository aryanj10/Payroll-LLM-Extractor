from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os
import pyotp
import re

FILENAME = 'populated_output.csv'
CLIENT = 'NewBaltimo'
PAY_PERIOD = '06/02/2025 - 06/08/2025'
PAY_DATE = '06/13/2025'
FILE_PATH = f"{FILENAME}"



#USER_DATA_DIR = os.path.abspath("chrome_profile")

def run_upload_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(
        channel="chrome",
        headless=False,
        slow_mo=50,
        args=[
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
            "--disable-features=SameSiteByDefaultCookies"
        ]
    )

        context = browser.new_context(
        viewport=None,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        locale="en-US"
    )

        context.set_extra_http_headers({
        "Accept-Language": "en-US,en;q=0.9"
    })

        page = context.new_page()
        # Step 1: Login
        page.goto("https://login.accountantsoffice.com/")
        page.fill('input[name="FirmCode"]', FIRMCODE)
        page.fill('input[name="UserName"]', USERNAME)
        page.fill('input[name="Password"]', PASSWORD)
        page.click('input[type="submit"]')  # Adjust if needed

        
        # After login submit
        print("✅ Waiting for 2FA method screen...")
        page.wait_for_url("https://login.accountantsoffice.com/Auth/SendCode?returnUrl=/&firmCode=starb3966", timeout=15000)
        print("✅ 2FA method screen detected. Waiting for 'Select' button...")
        page.click('input[type="submit"][value="Select"]')

# Now wait for code input
        page.wait_for_selector('input[name="Code"]', timeout=15000)
        print("✅ On 2FA input page")

# Generate and fill code
        totp = pyotp.TOTP("secret")  # Replace with your actual secret
        code = totp.now()
        print("✅ Generated TOTP code:", code)
        page.fill('input[name="Code"]', code)
        page.click('text=Submit')
        
        # Wait for dashboard to load
        page.wait_for_url("https://www.accountantsoffice.com/AoCommon/")
        print("✅ Logged in successfully. Redirecting to Payroll Launch...")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        # Step 2: Go to Payroll Launch
        # Wait for the sidebar link and click it
        print("🖱️ Clicking 'Payroll Relief' in sidebar...")
        #page.wait_for_selector("text=Payroll Relief", timeout=10000)
        # Do the real DOM click with mouse events
        payroll_link = page.query_selector('a[title="Payroll Relief"]')
        page.evaluate("el => el.click()", payroll_link)

        print(f"➡️ Navigating directly to Payroll Relief:")
        page.wait_for_url(re.compile(r".*payrollrelief\.com.*"), timeout=15000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        page.screenshot(path="after_payroll_click.png")
        print("✅ Clicked 'Payroll Relief'. Redirecting to Payroll Launch...")
    

        
        print("🔽 Selecting client using Select2 dropdown...")
        page.click("span.select2-selection--single")
        page.keyboard.type(CLIENT)
        page.wait_for_timeout(1000)
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle")
        page.wait_for_url(re.compile(r".*payrollrelief\.com.*"), timeout=15000)
        page.wait_for_timeout(2000)

        print("➡️ Navigating to ListEntryPrior...")
        page.goto("https://app.payrollrelief.com/Payroll/ListEntryPrior")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        print("✅ Navigated to ListEntryPrior page.")
        # Step 5: Select Prior
        options = page.locator("div#payrollSelector select option").all_inner_texts()
        print("🔍 Payroll dropdown options:", options)

        page.select_option("div#payrollSelector select", label=f"Prior")
        print(f"✅ Selected Prior payroll for date")



        # Step 6: Select Pay Period & Date
        # Step 6: Fill Pay Period Begin, End and Pay Date
        period_start, period_end = PAY_PERIOD.split(" - ")

# Fill Period Begin
        page.fill('input#PeriodBegin', period_start)
        page.keyboard.press("Tab")
        # Fill Period End
        # Wait for page reload / PeriodEnd input to become ready
        #page.wait_for_selector('input#PeriodEnd', state='visible')
        page.wait_for_timeout(4000)  # optional extra wait to ensure value reset

# Fill Period End
        page.fill('input#PeriodEnd', period_end)
        page.keyboard.press("Tab")
        page.wait_for_timeout(4000)
# Select Pay Date
        page.fill('input#PayDate', PAY_DATE)
        page.keyboard.press("Tab")
        print(f"✅ Filled Pay Period: {PAY_PERIOD} and Pay Date: {PAY_DATE}")
        page.wait_for_timeout(4000)
        # Step 7: Upload File

        print("📤 Uploading file:", FILE_PATH)
        page.click('button#importPayroll')
        

        print("📥 Upload modal detected. Uploading file...")

# Wait for the modal input to appear
        page.wait_for_selector('input[type="file"][name="files[]"]', state='attached', timeout=5000)
        page.set_input_files('input[type="file"][name="files[]"]', FILE_PATH)

        page.wait_for_timeout(2000)
        print("✅ File uploaded into modal:", FILE_PATH)
        page.screenshot(path="after_upload_click.png")
        page.pause()
        page.screenshot(path="after_upload_click.png")
        page.wait_for_timeout(2000)
        print("📤 Clicked Upload button.")

        # Step 8: Submit (adjust selector)
        #page.click("button:has-text('Submit')")
        
        print("✅ Upload completed for:", CLIENT)
        page.pause()

        time.sleep(3)
        context.close()
        browser.close()
        


if __name__ == "__main__":
    run_upload_bot()