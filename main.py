import os
import json
import time
import requests
from dotenv import load_dotenv

# === Config ===
REQUEST_DELAY_SECONDS = 7
FAILED_LOG_PATH = "data/pdf_ones/failed_chunks_pdf.json"
SUCCESS_LOG_PATH = "data/pdf_ones/all_extracted_employees_pdf.json"
CHUNKS_FILE_PATH = "data/pdf_ones/employee_chunks_raw_pdf.json"

# === Load employee chunks ===
with open(CHUNKS_FILE_PATH, "r", encoding="utf-8") as f:
    employee_chunks = json.load(f)

# === Gemini API setup ===
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY in .env")

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
)
HEADERS = {"Content-Type": "application/json"}

# === Output containers ===
all_extracted = []
failed_chunks = []

# === Gemini extraction loop ===
for idx, chunk in enumerate(employee_chunks):
    if not any(word.startswith("Emp#") for word in chunk.split()) or "Net Pay" not in chunk:
        print(f"⚠️ Skipping likely header-only chunk #{idx+1}")
        continue

    prompt = f"""
You are a strict payroll data extractor.

From the raw payroll block below, extract values as a flat JSON using exactly the following keys.  
If a value is missing, set it to `null`. All keys must always be present.

Include both **Current** and **YTD** values for all applicable fields.

Also extract employee-level totals:
- "Total Deductions", "Total Taxes", and "Net Pay"

Earnings Field Format:
- All earning types (e.g., Regular, Sick, Holiday, Personal, Vac, Comp, Jury, etc.) follow this format:
  Hours | Rate | Current Amount | YTD Amount

Parsing Guidelines:
- If any value in this 4-part structure is missing, set it to null.
  - Example: "Sick |||263.52" means:
    "SickHrs": null, "SickAmt": null, "SickAmt_YTD": 263.52
  - Example: "Holiday | 8.00 | 200.00 |" means:
    "HolHrs": 8.0, "HolAmt": 200.0, "HolAmt_YTD": null
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

  "FWT": null, "FWT_YTD": null,
  "SS W/H": null, "SS W/H_YTD": null,
  "MC W/H": null, "MC W/H_YTD": null,
  "NY State Tax": null, "NY State Tax_YTD": null,
  "NY SDI": null, "NY SDI_YTD": null,
  "NY PFML":null, "NY PFML_YTD":null,

  "ER SS": null, "ER SS_YTD": null,
  "ER MC": null, "ER MC_YTD": null,
  "FUTA":null,   "FUTA_YTD":null,
  "NY SUTA":null, "NY SUTA_YTD":null,

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


    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        print(f"⏳ Sending employee #{idx+1}...")
        res = requests.post(GEMINI_URL, headers=HEADERS, json=body)
        res.raise_for_status()

        response_data = res.json()
        raw_output = response_data['candidates'][0]['content']['parts'][0]['text'].strip()

        # Clean up markdown fences if they exist
        if raw_output.startswith("```json"):
            raw_output = raw_output.removeprefix("```json").removesuffix("```").strip()
        elif raw_output.startswith("```"):
            raw_output = raw_output.removeprefix("```").removesuffix("```").strip()

        try:
            parsed = json.loads(raw_output)
            all_extracted.append(parsed)
            print(f"✅ Success for employee #{idx+1}")
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse failed for employee #{idx+1}: {e}")
            failed_chunks.append({
                "index": idx,
                "error": "parse_failed",
                "raw": raw_output,
                "input": chunk
            })

    except Exception as e:
        print(f"❌ Error for employee #{idx+1}: {e}")
        failed_chunks.append({
            "index": idx,
            "error": str(e),
            "input": chunk
        })

    time.sleep(REQUEST_DELAY_SECONDS)

# === Save output files ===
with open(SUCCESS_LOG_PATH, "w", encoding="utf-8") as f:
    json.dump(all_extracted, f, indent=2)
print(f"✅ Extracted data saved to: {SUCCESS_LOG_PATH}")

if failed_chunks:
    with open(FAILED_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(failed_chunks, f, indent=2)
    print(f"⚠️ Failed chunks saved to: {FAILED_LOG_PATH}")
else:
    print("🎉 No failed chunks. All data extracted successfully.")
