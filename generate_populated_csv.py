import csv
import json
import os
import re

from datetime import datetime

BASE_DIR = "Extracted"
TEMPLATE_DIR = "Data/CSV_Templates"


def extract_payroll_dates_from_folder(folder_name):
    match = re.match(r"(.+)-(\d{2}-\d{2}-\d{4})_(\d{2}-\d{2}-\d{4})_(\d{2}-\d{2}-\d{4})", folder_name)
    if not match:
        raise ValueError("❌ Folder name format must be: ClientName-MM-DD-YYYY_MM-DD-YYYY_MM-DD-YYYY")

    client = match.group(1)
    
    def format_date(date_str):
        dt = datetime.strptime(date_str, "%m-%d-%Y")
        return f"{dt.month}/{dt.day}/{dt.year}"  # removes leading zeros

    start = format_date(match.group(2))
    end = format_date(match.group(3))
    pay_date = format_date(match.group(4))

    return {
        "ClientName": client,
        "PayPeriod": f"{start} to {end}",
        "PayDate": pay_date,
        "PaySchedule": "Prior"
    }
def find_matching_template(client_name):
    for f in os.listdir(TEMPLATE_DIR):
        if f.lower().startswith(client_name.lower()) and f.endswith(".csv"):
            return os.path.join(TEMPLATE_DIR, f)
    return None

def populate_csv(folder_name):
    folder_path = os.path.join(BASE_DIR, folder_name)
    json_path = os.path.join(folder_path, "parsed_employee_data.json")
    output_csv = os.path.join(folder_path, "populated_output.csv")
    pay_info = extract_payroll_dates_from_folder(folder_name)

    template_csv = find_matching_template(pay_info["ClientName"])
    if not template_csv:
        raise FileNotFoundError(f"❌ No CSV template found for client '{pay_info['ClientName']}' in {TEMPLATE_DIR}")

    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    json_map = {emp["Emp#"]: emp for emp in json_data}

    # Load CSV template
    with open(template_csv, newline='', encoding='utf-8') as f:
        reader = list(csv.reader(f))

    # Inject Pay Info
    for row in reader:
        if "Pay Period:" in row[0]:
            row[2] = pay_info["PayPeriod"]
        elif "Pay Schedule:" in row[0]:
            row[2] = pay_info["PaySchedule"]
        elif "Pay Date:" in row[0]:
            row[2] = pay_info["PayDate"]

    header_row_1 = reader[8]
    header_row_2 = reader[9]
    final_headers = [f"{h1.strip()} {h2.strip()}".strip() for h1, h2 in zip(header_row_1, header_row_2)]
    header_index_map = {col: i for i, col in enumerate(final_headers)}

    column_to_json_key = {
        "Emp Num": "Emp#",
        #"Employee Name": "Name",
        "Regular Hours": "RegHrs",
        "Regular Amount": "RegAmt",
        "Vacation Hours": "VacHrs",
        "Vacation Amount": "VacAmt",
        "Holiday Hours": "HolHrs",
        "Holiday Amount": "HolAmt",
        "Reimbursement Amount": "ReimbAmt",
        "Overtime Hours": "OTHrs",
        "Overtime Amount": "OTAmt",
        "Sick Hours": "SickHrs",
        "Sick Amount": "SickAmt",
        "Personal Hours": "PersonalHrs",
        "Personal Amount": "PersonalAmt",
        "Deputy Clerk 1410 Hours": "Deputy Hrs",
        "Deputy Clerk 1410 Amount": "Deputy Amt",
        "Records 1460 Hours": "Recor Hrs",
        "Records 1460 Amount": "Recor Amt",
        "Comp Time Hours": "Comp Hrs",
        "Comp Time Amount": "Comp Amt",
        "Office worker Hours": "Clerk Hrs",
        "Office worker Amount": "Clerk Amt",
        "Jury Duty Hours": "Jury Hrs",
        "Jury Duty Amount": "Jury Amt",
        "Emergency Mgmt Amount": "Emergency Mgmt Amt",
        "Bereavement Hours": "BRV Hrs",
        "Bereavement Amount": "BRV Amt",
        "Federal Tax": "FWT",
        "Soc.Sec. Tax": "SS W/H",
        "Medicare Tax": "MC W/H",
        "NY State Tax": "NY State Tax",
        "NY SDI Tax": "NY SDI",
        "414(H) Amount": "414(h)",
        "457(b) Amount": "457(b)",
        "Aflac Amount": "Aflac",
        "Aflac Pre-Tax Amount": "Aflac Pre-Tax",
        "Dental Ins Amount": "Dental Ins",
        "Dental Insurance Amount": "Dental Insurance",
        "Loan Repayment Amount": "Loan Repayment",
        "Medical Ins Amount": "Medical Ins",
        "Medical Insurance Amount": "Medical Insurance",
        "Pre Tax SCP Amount": "Pre Tax SCP",
        "Union Dues Amount": "Union Dues",
        "Vision Ins Amount": "Vision Ins",
        "Vision Insurance Amount": "Vision Insurance",
        "Net Amount": "Net Pay"
    }

    for i in range(10, len(reader)):
        row = reader[i]
        emp_num = row[0].strip()
        if emp_num.isdigit() and emp_num in json_map:
            emp_json = json_map[emp_num]
            for col_name, json_key in column_to_json_key.items():
                col_idx = header_index_map.get(col_name)
                if col_idx is not None and json_key in emp_json:
                    val = emp_json[json_key]
                    if val is not None:
                        try:
                            # Clean comma and convert to float
                            cleaned_val = float(str(val).replace(",", "").strip())
                            row[col_idx] = str(cleaned_val)
                        except ValueError:
                            row[col_idx] = str(val)

    # Save
    with open(output_csv, "w", newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(reader)

    print(f"✅ Done: {output_csv}")

# Just change this one line:


def should_process_folder(folder_name):
    folder_path = os.path.join(BASE_DIR, folder_name)
    failed_path = os.path.join(folder_path, "failed_chunks.json")
    return not os.path.exists(failed_path)

def main():
    folders = sorted(os.listdir(BASE_DIR))  # sorted for consistency
    for folder in folders:
        folder_path = os.path.join(BASE_DIR, folder)
        if os.path.isdir(folder_path):
            if should_process_folder(folder):
                try:
                    print(f"🔄 Processing: {folder}")
                    populate_csv(folder)
                except Exception as e:
                    print(f"❌ Error in {folder}: {e}")
            else:
                print(f"⏭️ Skipped {folder} (failed_chunks.json exists)")

if __name__ == "__main__":
    main()