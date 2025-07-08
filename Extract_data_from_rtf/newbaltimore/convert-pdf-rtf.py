import os
import subprocess
import re

PDF_DIR = "./pdf_files"
RTF_DIR = "./rtf_files"
os.makedirs(RTF_DIR, exist_ok=True)

def sanitize_filename(name):
    return re.sub(r'[^\w\-]', '_', name)

def convert_with_soffice(pdf_path, output_dir):
    try:
        subprocess.run([
            "soffice",
            "--headless",
            "--convert-to", "rtf",
            pdf_path,
            "--outdir", output_dir
        ], check=True)
        print(f"✅ Converted: {os.path.basename(pdf_path)}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {pdf_path} — {e}")

for file in os.listdir(PDF_DIR):
    if file.lower().endswith(".pdf"):
        input_path = os.path.join(PDF_DIR, file)
        convert_with_soffice(input_path, RTF_DIR)
