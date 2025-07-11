from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os
import pyotp
import re
import json
from dotenv import load_dotenv
#FILENAME = 'populated_output.csv'
#CLIENT = 'NewBaltimo'
#PAY_PERIOD = '06/02/2025 - 06/08/2025'
#PAY_DATE = '06/13/2025'
#FILE_PATH = f"{FILENAME}"
load_dotenv()

FIRMCODE = os.getenv("FIRMCODE")
USERNAME = os.getenv("USERID")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")

print("🔐 Using credentials:"
      f"\nFIRMCODE: {FIRMCODE}"
      f"\nUSERNAME: {USERNAME}")
#USER_DATA_DIR = os.path.abspath("chrome_profile")

def login_and_navigate(page):
    print("🔐 Logging in...")
    page.goto("https://login.accountantsoffice.com/")
    page.fill('input[name="FirmCode"]', FIRMCODE)
    page.fill('input[name="UserName"]', USERNAME)
    page.fill('input[name="Password"]', PASSWORD)
    page.click('input[type="submit"]')

    page.wait_for_url("https://login.accountantsoffice.com/Auth/SendCode?returnUrl=/&firmCode=starb3966", timeout=1500)
    page.click('input[type="submit"][value="Select"]')

    page.wait_for_selector('input[name="Code"]', timeout=15000)
    totp = pyotp.TOTP(TOTP_SECRET)
    code = totp.now()
    print("✅ TOTP code:", code)
    page.fill('input[name="Code"]', code)
    page.click('text=Submit')

    page.wait_for_url("https://www.accountantsoffice.com/AoCommon/")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    payroll_link = page.query_selector('a[title="Payroll Relief"]')
    page.evaluate("el => el.click()", payroll_link)
    page.wait_for_url(re.compile(r".*payrollrelief\.com.*"))
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

def select_client(page, client):
    print("🔽 Selecting client...")
    page.click("span.select2-selection--single")
    page.keyboard.type(client)
    page.wait_for_timeout(1000)
    page.keyboard.press("Enter")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

def fill_payroll_period(page, pay_period, pay_date):
    print("📅 Filling pay period...")
    page.goto("https://app.payrollrelief.com/Payroll/ListEntryPrior")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    page.select_option("div#payrollSelector select", label="Prior")
    page.fill('input#PayDate', pay_date)
    page.keyboard.press("Tab")

    period_start, period_end = pay_period.split(" - ")
    page.fill('input#PeriodBegin', period_start)
    page.keyboard.press("Tab")
    page.wait_for_timeout(4000)
    page.fill('input#PeriodEnd', period_end)
    page.keyboard.press("Tab")
    page.wait_for_timeout(4000)

def upload_csv(page, file_path):
    print(f"📤 Uploading file: {file_path}")
    page.click('button#importPayroll')
    page.wait_for_selector('input[type="file"][name="files[]"]', timeout=5000)
    page.set_input_files('input[type="file"][name="files[]"]', file_path)
    page.wait_for_timeout(2000)
    page.wait_for_selector("text=File: populated_output.csv", timeout=10000)

    ok_button = page.locator(
        'div[role="dialog"][aria-describedby="uploadDialog"]:has-text("File:") button.btn.btn-primary:has-text("OK")'
    )
    ok_button.wait_for(state="visible", timeout=10000)
    ok_button_handle = ok_button.element_handle()
    page.wait_for_function("btn => !btn.disabled", arg=ok_button_handle)
    ok_button.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(10000)

def trigger_review(page):
    print("🖱️ Clicking Review button...")
    page.click('button.btn.btn-primary:has-text("Review")')
    print("✅ Review triggered. Waiting 10 seconds...")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(10000)

"""def fill_federal_and_ny_tax_info(page, file_path):
    print("💰 Filling Federal and New York tax info...")
    page.goto("https://app.payrollrelief.com/Compliance/AdditionalPayments")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    folder = os.path.dirname(file_path)
    json_path = os.path.join(folder, "tax_info.json")
    with open(json_path, "r") as f:
        tax_data = json.load(f)

    for state_label, key in [("Federal", "Federal Withholding & FICA Tax"), ("New York", "NY Tax Withholding")]:
        tax_entry = tax_data.get(key)
        if not tax_entry:
            print(f"⚠️ Skipping {state_label} — no data found.")
            continue

        print(f"🔽 Selecting '{state_label}' from dropdown...")
        page.select_option('select.form-control', label=state_label)
        page.wait_for_timeout(2000)

        inputs = page.locator('tbody tr td input[type="text"]')
        if inputs.count() < 3:
            raise Exception(f"❌ Could not find all 3 input fields for {state_label}")

        # Fill the fields
        inputs.nth(0).fill(tax_entry["Debit Date"])
        inputs.nth(1).fill(tax_entry["Due Date"])
        page.keyboard.press("Tab")
        inputs.nth(2).fill(str(tax_entry["Amount"]))
        page.keyboard.press("Tab")
        page.wait_for_timeout(2000)
        print(f"✅ {state_label} tax info filled.")
        

    # === Optional Save ===
    page.click('button:has-text("Save")')
    page.wait_for_timeout(2000)
    # print("✅ Saved all tax entries.")
"""
def fill_federal_and_ny_tax_info(page, file_path):
    print("💰 Filling Federal and New York tax info...")
    page.goto("https://app.payrollrelief.com/Compliance/AdditionalPayments")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    folder = os.path.dirname(file_path)
    json_path = os.path.join(folder, "tax_info.json")
    with open(json_path, "r") as f:
        tax_data = json.load(f)

    tax_keys = [("Federal", "Federal Withholding & FICA Tax"), ("New York", "NY Tax Withholding")]

    for idx, (state_label, key) in enumerate(tax_keys):
        tax_entry = tax_data.get(key)
        if not tax_entry:
            print(f"⚠️ Skipping {state_label} — no data found.")
            continue

        print(f"🔽 Selecting '{state_label}' for row {idx + 1}...")

        # Select the row: nth tax entry (0-based)
        row = page.locator("#paymentsTable > tbody > tr").nth(idx)
        row.wait_for()

        # Select Federal/State dropdown (1st <select>)
        state_dropdown = row.locator("select").nth(0)
        state_dropdown.select_option(label=state_label)
        page.wait_for_timeout(500)

        # Ensure 3 input fields exist: Period End, Payment Date, Amount
        inputs = row.locator("input.form-control")
        if inputs.count() < 3:
            raise Exception(f"❌ Could not find all 3 input fields for {state_label} in row {idx + 1}")

        # Fill Period End Date (debit)
        inputs.nth(0).fill(tax_entry["Debit Date"])
        # Fill Payment Date (due)
        inputs.nth(1).fill(tax_entry["Due Date"])
        # Fill Amount
        inputs.nth(2).fill(str(tax_entry["Amount"]))

        page.wait_for_timeout(1000)
        print(f"✅ {state_label} tax info filled.")

    page.click('button:has-text("Save")')
    page.wait_for_timeout(2000)
    print("✅ Saved all tax entries.")


# === Main Bot Runner ===
def run_upload_bot():
    FILENAME = os.environ["FILENAME"]
    CLIENT = os.environ["CLIENT"]
    PAY_PERIOD = os.environ["PAY_PERIOD"]
    PAY_DATE = os.environ["PAY_DATE"]
    FILE_PATH = os.environ["FILE_PATH"]

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome", headless=False, slow_mo=50,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            locale="en-US"
        )
        context.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
        page = context.new_page()

        login_and_navigate(page)
        #select_client(page, CLIENT)
        #fill_payroll_period(page, PAY_PERIOD, PAY_DATE)
        #upload_csv(page, FILE_PATH)
        #trigger_review(page)
        #fill_federal_and_ny_tax_info(page, FILE_PATH)
        #print(f"✅ Completed run for client {CLIENT}")
        time.sleep(3)
        context.close()
        browser.close()
if __name__ == "__main__":
    run_upload_bot()