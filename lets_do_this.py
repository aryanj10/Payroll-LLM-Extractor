import os
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from tqdm import tqdm
import google.generativeai as genai

# === Config ===
MAX_WORKERS = 8
BASE_FOLDER = "Extracted"

# === Load Gemini API Key ===
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY in .env")

# === Initialize Gemini Client ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# === Retry Wrapper ===
@retry(wait=wait_exponential(min=2, max=15), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
def send_to_gemini(prompt):
    response = model.generate_content(prompt)
    raw_output = response.text.strip()
    if raw_output.startswith("```json"):
        raw_output = raw_output.removeprefix("```json").removesuffix("```").strip()
    elif raw_output.startswith("```"):
        raw_output = raw_output.removeprefix("```").removesuffix("```").strip()
    return json.loads(raw_output)

# === Prompt Template Function ===
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
 | Hours | Rate | Current Amount | YTD Amount |

Fallback Parsing Rules:
Each earnings line will follow exactly one of these 3 formats:

1. **Full format with 4 values**:  
   `Hours | Rate | Current Amount | YTD Amount`  
   → Assign all four values in order.

2. **Two values**:  
   `Current Amount | YTD Amount` (preceded by two empty separators)  
   → Assign to **Current Amount** and **YTD Amount**.  
   Set `Hours` and `Rate` = null.

3. **Single value at the end**:  
   `|||YTD Amount|`  
   → Assign to **YTD Amount**.  
   Set all others = null.

- Field separators may be pipes (`|`), tabs (`\t`), or multiple spaces — treat them all the same.

Field Name Disambiguation:
- "Vision Ins" and "Vision Insurance" are **distinct fields**.
- "Dental Ins" and "Dental Insurance" are **also distinct**.
- Similarly named fields must not be merged or inferred from each other.



Here is the required structure:

{{
  "Emp#": null,
  "Name": null,

  "RegHrs": null, "RegRate":null, "RegAmt": null, "RegAmt_YTD": null,
  "VacHrs": null, "VacRate":null, "VacAmt": null, "VacAmt_YTD": null,
  "HolHrs": null, "HolRate":null, "HolAmt": null, "HolAmt_YTD": null,
  "ReimbAmt": null, "ReimbAmt_YTD": null,
  "SickHrs": null, "SickRate":null, "SickAmt": null, "SickAmt_YTD": null,
  "OTHrs": null,   "OTRate":null,   "OTAmt": null,   "OTAmt_YTD": null,
  "PersonalHrs": null, "PersonalRate":null, "PersonalAmt": null, "PersonalAmt_YTD": null,

  "Deputy Hrs": null, "Deputy Rate":null, "Deputy Amt": null, "Deputy Amt_YTD": null,
  "Recor Hrs": null, "Recor Rate":null, "Recor Amt": null, "Recor Amt_YTD": null,
  "Comp Hrs": null, "Comp Rate":null, "Comp Amt": null, "Comp Amt_YTD": null,
  "Clerk Hrs": null, "Clerk Rate":null, "Clerk Amt": null, "Clerk Amt_YTD": null,
  "Jury Hrs": null, "Jury Rate":null, "Jury Amt": null, "Jury Amt_YTD": null,
  "BRV Hrs": null, "BRV Rate":null, "BRV Amt": null, "BRV Amt_YTD": null,
  "OtherHrs": null, "OtherRate":null, "OtherAmt": null, "OtherAmt_YTD": null,
  "Emergency Mgmt Hrs": null, "Emergency Mgmt Rate":null, "Emergency Mgmt Amt": null, "Emergency Mgmt Amt_YTD": null,
  "Retro Pay": null, "Retro Pay_YTD": null,
  "Deputy Supt Amt": null, "Deputy Supt Amt_YTD": null,
  "Supv Secretary Amt": null, "Supv Secretary Amt_YTD": null,
  "Assessor Hrs": null, "Assessor Rate":null, "Assessor Amt": null, "Assessor Amt_YTD": null,
  "Codes Hrs": null, "Code Rate":null, "Codes Amt": null, "Codes Amt_YTD": null,
  "Zoning Hrs": null, "Zoning Rate":null, "Zoning Amt": null, "Zoning Amt_YTD": null,
  "Planning Hrs": null, "Planning Rate":null, "Planning Amt": null, "Planning Amt_YTD": null,
  "Collector Hrs": null, "Collector Rate":null, "Collector Amt": null, "Collector Amt_YTD": null,

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
   
  "403(b) for EE": null, "403(b) for EE_YTD": null,
  "414(h)": null, "414(h)_YTD": null,
  "457(b)": null, "457(b)_YTD": null,
  "457(b) (50+)": null, "457(b) (50+)_YTD": null,
  "Aflac": null, "Aflac_YTD": null,
  "Child/Spousal Support": null, "Child/Spousal Support_YTD": null,
  "Colonial AC": null, "Colonial AC_YTD": null,
  "Colonial DB": null, "Colonial DB_YTD": null,
  "Medical Ins": null, "Medical Ins_YTD": null,
  "Medical Insurance": null, "Medical Insurance_YTD": null,
  "Dental Ins": null, "Dental Ins_YTD": null,
  "Vision Ins": null, "Vision Ins_YTD": null,
  "Dental Insurance": null, "Dental Insurance_YTD": null,
  "Vision Insurance": null, "Vision Insurance_YTD": null,
  "Aflac Pre-Tax": null, "Aflac Pre-Tax_YTD": null,
  "Union Dues": null, "Union Dues_YTD": null,
  "Pre Tax SCP": null, "Pre Tax SCP_YTD": null,
  "Roth 457(b)": null, "Roth 457(b)_YTD": null,
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

# === Parallel Chunk Processor ===
def process_employee(emp):
    emp_id = emp.get("Emp#", "unknown")
    chunk = emp.get("Block", "")
    if "Net Pay" not in chunk:
        return {"status": "skipped", "data": {"Emp#": emp_id, "Block": chunk}}
    try:
        prompt = build_prompt(chunk)
        parsed = send_to_gemini(prompt)
        parsed["Emp#"] = emp_id
        if not parsed.get("Name"):
            parsed["Name"] = chunk.strip().split("\n")[0].strip()
        return {"status": "success", "data": parsed}
    except Exception as e:
        return {"status": "failed", "data": {"Emp#": emp_id, "error": str(e), "raw_input": chunk}}

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

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_employee, emp) for emp in employee_blocks]
        for future in tqdm(as_completed(futures), total=len(futures), desc="🔄 Parsing"):
            result = future.result()
            if result["status"] == "success":
                parsed_employees.append(result["data"])
            elif result["status"] == "failed":
                failed_chunks.append(result["data"])
            else:
                skipped_chunks.append(result["data"])

    # Save Outputs
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
    print(f"✅ Completed processing folder: {folder}\n")
