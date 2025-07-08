from playwright.sync_api import sync_playwright

def run_upload_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        
        # ✅ Load previously saved login state
        context = browser.new_context(storage_state="login_state.json")
        page = context.new_page()
        # ✅ Follow real redirect path to initialize session correctly
        print("➡️ Going to Launch Payroll via accountantsoffice.com")
        page.goto("https://www.accountantsoffice.com/AoCommon/Home/Launch/payroll")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(4000)

        # ✅ You’ll be redirected to payrollrelief with dropdown initialized
        page.screenshot(path="check_dropdown.png", full_page=True)

        # Optional: reload if dropdown didn’t load
        page.reload()
        page.wait_for_selector("select#ddlClients", timeout=10000)
        print("✅ Dropdown found!")

        # Now you can select the client, proceed with file upload, etc.

        browser.close()

if __name__ == "__main__":
    run_upload_bot()
    print("✅ Bot completed successfully!")