import os
import re
from datetime import datetime
from agent_project.agents import run_upload_bot  # 👈 Import your bot

BASE_DIR = "Extracted"  # Adjusted relative path from agent_project
CLIENT = "NewBaltimo"
client_folder = "NewBaltimore"

def convert_date_format(date_str):
    return datetime.strptime(date_str, "%m-%d-%Y").strftime("%m/%d/%Y")

def get_records_to_run():
    records = []
    for folder_name in os.listdir(BASE_DIR):
        folder_path = os.path.join(BASE_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue

        populated_csv_path = os.path.join(folder_path, "populated_output.csv")
        if not os.path.exists(populated_csv_path):
            continue

        match = re.match(rf"{client_folder}-(\d{{2}}-\d{{2}}-\d{{4}})_(\d{{2}}-\d{{2}}-\d{{4}})_(\d{{2}}-\d{{2}}-\d{{4}})", folder_name)
        if not match:
            continue

        start_date, end_date, pay_date = match.groups()
        pay_period = f"{convert_date_format(start_date)} - {convert_date_format(end_date)}"
        pay_date_fmt = convert_date_format(pay_date)

        records.append({
            "FILENAME": "populated_output.csv",
            "CLIENT": CLIENT,
            "PAY_PERIOD": pay_period,
            "PAY_DATE": pay_date_fmt,
            "FILE_PATH": os.path.abspath(populated_csv_path)
        })
    return records

if __name__ == "__main__":
    records = get_records_to_run()

    for rec in records:
        print(f"\n▶️ Running upload for: {rec['PAY_PERIOD']} → {rec['PAY_DATE']}")
        try:
            # 🔁 Dynamically assign values for the run
            os.environ["FILENAME"] = rec["FILENAME"]
            os.environ["CLIENT"] = rec["CLIENT"]
            os.environ["PAY_PERIOD"] = rec["PAY_PERIOD"]
            os.environ["PAY_DATE"] = rec["PAY_DATE"]
            os.environ["FILE_PATH"] = rec["FILE_PATH"]

            run_upload_bot()  # Playwright bot will read from env vars
        except Exception as e:
            print(f"❌ Failed for {rec['PAY_DATE']}: {e}")
