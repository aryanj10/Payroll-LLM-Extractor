import os
import json
import pandas as pd
import streamlit as st
from src.excel_raw_text_chunk import extract_employee_chunks
from src.send_chunk_llm import extract_payroll_with_gemini
from src.populate_csv_template import populate_csv_from_json
import sys
import io


# === Paths ===
BASE_DIR = "Data"
INPUT_DIR = os.path.join(BASE_DIR, "input_files")
TEMPLATE_DIR = os.path.join(BASE_DIR, "CSV_Templates")
RAW_CHUNKS_PATH = os.path.join(BASE_DIR, "raw_chunks", "employee_chunks_raw.json")
EXTRACTED_JSON_PATH = os.path.join(BASE_DIR, "output", "LLM", "all_extracted_employees.json")
POPULATED_CSV_PATH = os.path.join(BASE_DIR, "output","populated_files", "populated_output.csv")

st.set_page_config(page_title="Payroll Processor", layout="wide")
st.title("📋 Automated Payroll Parser")

# === Step 1: Select input files ===
st.header("1️⃣ Select Payroll Register and Template")
excel_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".xlsx")]
csv_templates = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".csv")]

selected_excel = st.selectbox("Choose Payroll Register (.xlsx)", excel_files)
selected_template = st.selectbox("Choose CSV Template", csv_templates)
    # === Capture logs ===
log_placeholder = st.empty()
log_lines = []

def log(msg):
    print(msg)  # Optional: also logs to terminal
    log_lines.append(msg)
    log_placeholder.text("\n".join(log_lines))


# === Step 2: Run Full Pipeline ===
if st.button("🚀 Run Payroll Processing"):
    excel_path = os.path.join(INPUT_DIR, selected_excel)
    template_path = os.path.join(TEMPLATE_DIR, selected_template)

    log("🔍 Extracting employee chunks...")
    chunks = extract_employee_chunks(excel_path, output_path=RAW_CHUNKS_PATH)

    log("🧠 Sending chunks to LLM for JSON extraction...")
    extract_payroll_with_gemini(
        chunks_path=RAW_CHUNKS_PATH,
        success_path=EXTRACTED_JSON_PATH,
        failed_path=os.path.join(BASE_DIR, "logs", "failed_chunks.json"),
        delay_seconds=7,
        logger=log
    )

    log("🧾 Populating CSV Template...")
    populate_csv_from_json(
        csv_path=template_path,
        json_path=EXTRACTED_JSON_PATH,
        output_csv=POPULATED_CSV_PATH
    )

    log("✅ All steps completed!")

    # === Display JSON ===
    with open(EXTRACTED_JSON_PATH, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    st.subheader("📂 Parsed Employee JSON")
    st.dataframe(pd.json_normalize(json_data))

    # === Display Populated CSV ===
    st.subheader("📄 Populated CSV Output")
    df = pd.read_csv(POPULATED_CSV_PATH, header=None)
    st.dataframe(df)

    # === Downloads ===
    st.download_button("⬇️ Download JSON", json.dumps(json_data, indent=2), file_name="extracted_employees.json", mime="application/json")
    st.download_button("⬇️ Download CSV", data=df.to_csv(index=False, header=False), file_name="populated_output.csv", mime="text/csv")
    st.success("All files processed successfully! 🎉")
