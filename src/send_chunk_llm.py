import os
import json
import time
import requests
from dotenv import load_dotenv

def extract_payroll_with_gemini(
    chunks_path="employee_chunks_raw.json",
    success_path="all_extracted_employees.json",
    failed_path="failed_chunks.json",
    delay_seconds=7,
    logger=print
):
    # === Load employee chunks ===
    with open(chunks_path, "r", encoding="utf-8") as f:
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
            logger(f"⚠️ Skipping likely header-only chunk #{idx+1}")
            continue

        prompt = f"""
You are a strict payroll data extractor.

From the raw payroll block below, extract values as a flat JSON using exactly the following keys.  
If a value is missing, set it to `null`. All keys must always be present.

Include both **Current** and **YTD** values for all applicable fields.

Also extract employee-level totals:
- "Total Gross", "Total Deductions", "Total Taxes", and "Net Pay"

Here is the required structure:

{{
  "Emp#": ...,
  "Name": ...,
  "Department": ...,

  "RegHrs": ..., "RegAmt": ..., "RegAmt_YTD": ...,
  "VacHrs": ..., "VacAmt": ..., "VacAmt_YTD": ...,
  "HolHrs": ..., "HolAmt": ..., "HolAmt_YTD": ...,
  "SickHrs": ..., "SickAmt": ..., "SickAmt_YTD": ...,
  "OTHrs": ..., "OTAmt": ..., "OTAmt_YTD": ...,
  "PersonalHrs": ..., "PersonalAmt": ..., "PersonalAmt_YTD": ...,
  "Deputy Clerk Hrs": ..., "Deputy Clerk Amt": ..., "Deputy Clerk Amt_YTD": ...,
  "OtherHrs": ..., "OtherAmt": ..., "OtherAmt_YTD": ...,
  Emergency Mgmt Hrs: ..., "Emergency Mgmt Amt": ..., "Emergency Mgmt Amt_YTD": ...,

  "FWT": ..., "FWT_YTD": ...,
  "SS W/H": ..., "SS W/H_YTD": ...,
  "MC W/H": ..., "MC W/H_YTD": ...,
  "SOCSEC": ..., "SOCSEC_YTD": ...,
  "MEDI": ..., "MEDI_YTD": ...,
  "NY State Tax": ..., "NY State Tax_YTD": ...,
  "NY SDI": ..., "NY SDI_YTD": ...,

  "ER SS": ..., "ER SS_YTD": ...,
  "ER MC": ..., "ER MC_YTD": ...,

  "414(h)": ..., "414(h)_YTD": ...,
  "457(b)": ..., "457(b)_YTD": ...,
  "Aflac": ..., "Aflac_YTD": ...,
  "Medical Ins": ..., "Medical Ins_YTD": ...,
  "Dental Ins": ..., "Dental Ins_YTD": ...,
  "Vision Ins": ..., "Vision Ins_YTD": ...,
  "Aflac Pre-Tax": ..., "Aflac Pre-Tax_YTD": ...,
  "Union Dues": ..., "Union Dues_YTD": ...,
  "Pre Tax SCP": ..., "Pre Tax SCP_YTD": ...,
"Loan Repayment": ..., "Loan Repayment_YTD": ...,

  "Total Hours": ...,
  "Total Earnings YTD":...,
  "Total Taxes Current": ...,
  "Total Taxes YTD": ...,
  Total Deductions YTD:...,
  "Total ER Taxes Cuurrent": ...,
  "Total ER Taxes YTD": ...,
  "Net Pay": ...
}}

Rules:
- Only return valid **JSON**
- Use `null` if any value is not present
- No markdown, no explanation, no extra keys

Raw input:
{chunk}
""".strip()


        body = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            print(f"⏳ Sending employee #{idx+1}...")
            logger(f"⏳ Sending employee #{idx+1}...")
            res = requests.post(GEMINI_URL, headers=HEADERS, json=body)
            res.raise_for_status()

            response_data = res.json()
            raw_output = response_data['candidates'][0]['content']['parts'][0]['text'].strip()

            if raw_output.startswith("```json"):
                raw_output = raw_output.removeprefix("```json").removesuffix("```").strip()
            elif raw_output.startswith("```"):
                raw_output = raw_output.removeprefix("```").removesuffix("```").strip()

            try:
                parsed = json.loads(raw_output)
                all_extracted.append(parsed)
                print(f"✅ Success for employee #{idx+1}")
                logger(f"✅ Success for employee #{idx+1}")
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parse failed for employee #{idx+1}: {e}")
                logger(f"⚠️ JSON parse failed for employee #{idx+1}: {e}")
                failed_chunks.append({
                    "index": idx,
                    "error": "parse_failed",
                    "raw": raw_output,
                    "input": chunk
                })

        except Exception as e:
            print(f"❌ Error for employee #{idx+1}: {e}")
            logger(f"❌ Error for employee #{idx+1}: {e}")
            failed_chunks.append({
                "index": idx,
                "error": str(e),
                "input": chunk
            })

        time.sleep(delay_seconds)

    # === Save output files ===
    with open(success_path, "w", encoding="utf-8") as f:
        json.dump(all_extracted, f, indent=2)
    print(f"✅ Extracted data saved to: {success_path}")
    logger(f"✅ Extracted data saved to: {success_path}")

    if failed_chunks:
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed_chunks, f, indent=2)
        print(f"⚠️ Failed chunks saved to: {failed_path}")
        logger(f"⚠️ Failed chunks saved to: {failed_path}")
    else:
        print("🎉 No failed chunks. All data extracted successfully.")
        logger("🎉 No failed chunks. All data extracted successfully.")
