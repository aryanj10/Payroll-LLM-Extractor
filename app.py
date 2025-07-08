import os
import json
import pandas as pd
from src.excel_raw_text_chunk import extract_employee_chunks
from src.send_chunk_llm import extract_payroll_with_gemini
from src.populate_csv_template import populate_csv_from_json

# === Paths ===
BASE_DIR = "Data"
INPUT_DIR = os.path.join(BASE_DIR, "input_files")
TEMPLATE_DIR = os.path.join(BASE_DIR, "CSV_Templates")
RAW_CHUNKS_PATH = os.path.join(BASE_DIR, "raw_chunks", "employee_chunks_raw.json")
EXTRACTED_JSON_PATH = os.path.join(BASE_DIR, "output", "LLM", "all_extracted_employees.json")
POPULATED_CSV_PATH = os.path.join(BASE_DIR, "output", "populated_files", "populated_output.csv")
FAILED_CHUNKS_PATH = os.path.join(BASE_DIR, "logs", "failed_chunks.json")

def log(msg):
    print(msg)

def main():
    # === Step 1: List input files ===
    excel_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".xlsx")]
    csv_templates = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".csv")]

    if not excel_files:
        print("❌ No Excel files found in input directory.")
        return
    if not csv_templates:
        print("❌ No CSV templates found in template directory.")
        return

    # === Step 2: Ask user to choose files ===
    print("Available Excel Payroll Registers:")
    for idx, f in enumerate(excel_files):
        print(f"{idx+1}. {f}")
    excel_index = int(input("Select Excel file (number): ")) - 1
    selected_excel = excel_files[excel_index]

    print("\nAvailable CSV Templates:")
    for idx, f in enumerate(csv_templates):
        print(f"{idx+1}. {f}")
    template_index = int(input("Select CSV template (number): ")) - 1
    selected_template = csv_templates[template_index]

    # === Step 3: Full Pipeline ===
    excel_path = os.path.join(INPUT_DIR, selected_excel)
    template_path = os.path.join(TEMPLATE_DIR, selected_template)

    log("🔍 Extracting employee chunks...")
    chunks = extract_employee_chunks(excel_path, output_path=RAW_CHUNKS_PATH)

    log("🧠 Sending chunks to LLM for JSON extraction...")
    extract_payroll_with_gemini(
        chunks_path=RAW_CHUNKS_PATH,
        success_path=EXTRACTED_JSON_PATH,
        failed_path=FAILED_CHUNKS_PATH,
        delay_seconds=7,
        
    )

    log("🧾 Populating CSV Template...")
    populate_csv_from_json(
        csv_path=template_path,
        json_path=EXTRACTED_JSON_PATH,
        output_csv=POPULATED_CSV_PATH
    )

    log("✅ All steps completed!")

    # === Optional Output Preview ===
    with open(EXTRACTED_JSON_PATH, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    print("\n📂 Sample Parsed JSON:")
    print(json.dumps(json_data[:1], indent=2))  # preview first record

    df = pd.read_csv(POPULATED_CSV_PATH, header=None)
    print("\n📄 Populated CSV Preview:")
    print(df.head())

    print(f"\n🎉 Files saved:\n- JSON: {EXTRACTED_JSON_PATH}\n- CSV: {POPULATED_CSV_PATH}")

if __name__ == "__main__":
    main()
