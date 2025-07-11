import os
import json
import time
import requests
from dotenv import load_dotenv

# === Config ===
REQUEST_DELAY_SECONDS = 7
BASE_FOLDER = "Extracted"

# === Load Gemini API Key ===
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY in .env")

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
)
HEADERS = {"Content-Type": "application/json"}

# === Gemini Prompt Template ===
def build_prompt(chunk):
    return f"""
You are a strict payroll data extractor.

From the raw payroll block below, extract values as a flat JSON using exactly the following keys.  
If a value is missing, set it to `null`. All keys must always be present.

Include both **Current** and **YTD** values for all applicable fields.

Also extract employee-level totals:
- "Total Deductions", "Total Taxes", and "Net Pay"

Earnings Field Format:
- All earning types (e.g., Regular, Sick, Holiday, Personal, Vac, Comp, Jury, etc.) follow this format:
  Hours | Rate | Current Amount | YTD Amount | 

Parsing Guidelines:
- If any value in this 4-part structure is missing, set it to null.
- Field separators may include pipes (`|`), spaces, or tabs. Treat them all equivalently.
- Do not guess values. Set missing values to `null`.

Important Field Distinctions:
- "Vision Ins" and "Vision Insurance" are two different fields. Do not combine them.
- "Dental Ins" and "Dental Insurance" are also separate. Keep them distinct.

Here is the required structure:

{{
  "Emp#": null,
  "Name": null,

  "RegHrs": null, "Rate":null,"RegAmt": null, "RegAmt_YTD": null,
  "VacHrs": null, "VacAmt": null, "VacAmt_YTD": null,
  "HolHrs": null, "HolAmt": null, "HolAmt_YTD": null,
  "ReimbAmt": null, "ReimbAmt_YTD": null,
  "SickHrs": null, "SickAmt": null, "SickAmt_YTD": null,
  "OTHrs": null, "OTAmt": null, "OTAmt_YTD": null,
  "PersonalHrs": null, "PersonalAmt": null, "PersonalAmt_YTD": null,

  "Deputy Hrs": null, "Deputy Amt": null, "Deputy Amt_YTD": null,
  "Recor Hrs": null, "Recor Amt": null, "Recor Amt_YTD": null,
  "Comp Hrs": null, "Comp Amt": null, "Comp Amt_YTD": null,
  "Clerk Hrs": null, "Clerk Amt": null, "Clerk Amt_YTD": null,
  "Jury Hrs": null, "Jury Amt": null, "Jury Amt_YTD": null,
  "BRV Hrs": null, "BRV Amt": null, "BRV Amt_YTD": null,
  "OtherHrs": null, "OtherAmt": null, "OtherAmt_YTD": null,
  "Emergency Mgmt Hrs": null, "Emergency Mgmt Amt": null, "Emergency Mgmt Amt_YTD": null,
  "Retro Pay": null, "Retro Pay_YTD": null,
  "Deputy Supt Amt": null, "Deputy Supt Amt_YTD": null,
  "Supv Secretary Amt": null, "Supv Secretary Amt_YTD": null,
  "Assessor Hrs": null, "Assessor Amt": null, "Assessor Amt_YTD": null,
  "Codes Hrs": null, "Codes Amt": null, "Codes Amt_YTD": null,
  "Zoning Hrs": null, "Zoning Amt": null, "Zoning Amt_YTD": null,
  "Planning Hrs": null, "Planning Amt": null, "Planning Amt_YTD": null,
  "Collector Hrs": null, "Collector Amt": null, "Collector Amt_YTD": null,

  "FWT": null, "FWT_YTD": null,
  "SS W/H": null, "SS W/H_YTD": null,
  "MC W/H": null, "MC W/H_YTD": null,
  "NY State Tax": null, "NY State Tax_YTD": null,
  "NY SDI": null, "NY SDI_YTD": null,
  "NY PFML": null, "NY PFML_YTD": null,

  "ER SS": null, "ER SS_YTD": null,
  "ER MC": null, "ER MC_YTD": null,
  "FUTA": null, "FUTA_YTD": null,
  "NY SUTA": null, "NY SUTA_YTD": null,

  "414(h)": null, "414(h)_YTD": null,
  "457(b)": null, "457(b)_YTD": null,
  "Aflac": null, "Aflac_YTD": null,
  "Medical Ins": null, "Medical Ins_YTD": null,
  "Dental Ins": null, "Dental Ins_YTD": null,
  "Vision Ins": null, "Vision Ins_YTD": null,
  "Dental Insurance": null, "Dental Insurance_YTD": null,
  "Vision Insurance": null, "Vision Insurance_YTD": null,
  "Aflac Pre-Tax": null, "Aflac Pre-Tax_YTD": null,
  "Union Dues": null, "Union Dues_YTD": null,
  "Pre Tax SCP": null, "Pre Tax SCP_YTD": null,
  "Loan Repayment": null, "Loan Repayment_YTD": null,

  "Net Pay": null
}}

Rules:
- Only return valid **JSON**
- Use `null` if any value is not present
- No markdown, no explanation, no extra keys

Raw input:
{chunk}
""".strip()

# === Main Folder Loop ===
for folder in os.listdir(BASE_FOLDER):
    folder_path = os.path.join(BASE_FOLDER, folder)
    if not os.path.isdir(folder_path):
        continue

    input_json = os.path.join(folder_path, "employee_data.json")
    output_json = os.path.join(folder_path, "parsed_employee_data.json")
    failed_json = os.path.join(folder_path, "failed_chunks.json")
    skipped_json = os.path.join(folder_path, "skipped_chunks.json")

    if not os.path.exists(input_json):
        print(f"⚠️ Skipping {folder} (no employee_data.json)")
        continue

    print(f"\n📂 Processing folder: {folder}")
    with open(input_json, "r", encoding="utf-8") as f:
        employee_blocks = json.load(f)

    parsed_employees = []
    failed_chunks = []
    skipped_chunks = []

    for idx, emp in enumerate(employee_blocks):
        emp_id = emp.get("Emp#", f"unknown-{idx+1}")
        chunk = emp.get("Block", "")

        if "Net Pay" not in chunk:
            print(f"⚠️ Skipping Emp# {emp_id} — 'Net Pay' not found")
            skipped_chunks.append({"Emp#": emp_id, "Block": chunk})
            continue

        prompt = build_prompt(chunk)
        body = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            print(f"⏳ Sending Emp# {emp_id}...")
            res = requests.post(GEMINI_URL, headers=HEADERS, json=body)
            res.raise_for_status()

            raw_output = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            if raw_output.startswith("```json"):
                raw_output = raw_output.removeprefix("```json").removesuffix("```").strip()
            elif raw_output.startswith("```"):
                raw_output = raw_output.removeprefix("```").removesuffix("```").strip()

            parsed = json.loads(raw_output)
            parsed["Emp#"] = emp_id

            # Fallback name from first line of block if Gemini missed it
            if not parsed.get("Name"):
                parsed["Name"] = chunk.strip().split("\n")[0].strip()

            parsed_employees.append(parsed)
            print(f"✅ Parsed Emp# {emp_id}")

        except Exception as e:
            print(f"❌ Error for Emp# {emp_id}: {e}")
            failed_chunks.append({
                "Emp#": emp_id,
                "error": str(e),
                "raw_input": chunk
            })

        time.sleep(REQUEST_DELAY_SECONDS)

    # === Save outputs ===
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(parsed_employees, f, indent=2)
    print(f"💾 Saved parsed employees → {output_json}")

    if failed_chunks:
        with open(failed_json, "w", encoding="utf-8") as f:
            json.dump(failed_chunks, f, indent=2)
        print(f"⚠️ Saved failed chunks → {failed_json}")

    if skipped_chunks:
        with open(skipped_json, "w", encoding="utf-8") as f:
            json.dump(skipped_chunks, f, indent=2)
        print(f"🟡 Saved skipped chunks → {skipped_json}")
