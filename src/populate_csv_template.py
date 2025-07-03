import csv
import json

def populate_csv_from_json(
    csv_path="NewBaltimo 532025 to 5162025.csv",
    json_path="all_extracted_employees.json",
    output_csv="populated_output.csv"
):
    # === Load JSON data ===
    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    json_map = {emp["Emp#"]: emp for emp in json_data}

    # === Load CSV as list of rows ===
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = list(csv.reader(f))

    # === Identify header rows (row 9 and 10 are index 8 and 9) ===
    header_row_1 = reader[8]
    header_row_2 = reader[9]

    # === Merge headers to get final column names ===
    final_headers = []
    for h1, h2 in zip(header_row_1, header_row_2):
        merged = f"{h1.strip()} {h2.strip()}".strip()
        final_headers.append(merged)

    # === Mapping: Human-readable to JSON key ===
    column_to_json_key = {
        "Emp Num": "Emp#",
        "Employee Name": "Name",
        "Regular Hours": "RegHrs",
        "Regular Amount": "RegAmt",
        "Vacation Hours": "VacHrs",
        "Vacation Amount": "VacAmt",
        "Holiday Hours": "HolHrs",
        "Holiday Amount": "HolAmt",
        "Overtime Hours": "OTHrs",
        "Overtime Amount": "OTAmt",
        "Sick Hours": "SickHrs",
        "Sick Amount": "SickAmt",
        "Personal Hours": "PersonalHrs",
        "Personal Amount": "PersonalAmt",
        "Deputy Clerk 1410 Hours": "Deputy Clerk Hrs",
        "Deputy Clerk 1410 Amount": "Deputy Clerk Amt",
        "Emergency Mgmt Amount": "Emergency Mgmt Amt",
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
        "Loan Repayment Amount": "Loan Repayment",
        "Medical Ins Amount": "Medical Ins",
        "Pre Tax SCP Amount": "Pre Tax SCP",
        "Union Dues Amount": "Union Dues",
        "Vision Ins Amount": "Vision Ins",
        "Net Amount": "Net Pay"
    }

    # === Build column index map ===
    header_index_map = {col: i for i, col in enumerate(final_headers)}

    # === Process and update rows starting from row 10 (index 9) onward ===
    for i in range(10, len(reader)):
        row = reader[i]
        emp_num_raw = row[0].strip()
        if emp_num_raw.isdigit():
            emp_num = emp_num_raw
            if emp_num in json_map:
                emp_json = json_map[emp_num]
                for col_name, json_key in column_to_json_key.items():
                    col_idx = header_index_map.get(col_name)
                    if col_idx is not None and json_key in emp_json:
                        val = emp_json[json_key]
                        if val is not None:
                            row[col_idx] = str(val)

    # === Write updated CSV ===
    with open(output_csv, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(reader)

    print(f"✅ Done. Populated data saved to: {output_csv}")
    return output_csv
