import os
import json
from utils.ibm_extractor import extract_resume_info
from extractors.pdf_extractor import extract_pdf_text
from extractors.docx_extractor import extract_docx_text
from utils.anchor_alignment import fill_template_with_data
from utils.excel_writer import append_to_excel
from utils.postprocessing import clean_extracted_data  # If you have this module

def main():
    input_folder = "resumes"
    template_path = "templates/final_template.docx"
    output_folder = "outputs"
    json_folder = "json"
    excel_path = "outputs/resume_summary.xlsx"

    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(json_folder, exist_ok=True)

    files = os.listdir(input_folder)
    if not files:
        print("⚠️ No resumes found in the 'resumes' folder.")
        return

    # Define Excel headers
    excel_headers = [
        "Full Name",
        "Email",
        "Phone",
        "Location",
        "Recent Employer",
        "Most Recent Job Title",
        "Professional Summary",
        "Total Years of Experience",
        "Technologies Worked On",
        "Technology Durations"
    ]

    for filename in files:
        if filename.startswith(".") or not (
            filename.lower().endswith(".pdf") or filename.lower().endswith(".docx")
        ):
            print(f"⏭️ Skipping unsupported or hidden file: {filename}")
            continue

        filepath = os.path.join(input_folder, filename)
        text = ""

        # Extract text (PDF)
        if filename.lower().endswith(".pdf"):
            print(f"🔍 Extracting text from PDF: {filename}")
            text = extract_pdf_text(filepath, ocr=False)

            if not text.strip():
                print("🟠 No text extracted from PDF, trying OCR...")
                text = extract_pdf_text(filepath, ocr=True)
                if text.strip():
                    print("🟢 OCR text extraction succeeded.")
                else:
                    print(f"❌ OCR also failed for {filename}. Skipping.")
                    continue

        # Extract text (DOCX)
        elif filename.lower().endswith(".docx"):
            print(f"🔍 Extracting text from DOCX: {filename}")
            text = extract_docx_text(filepath, ocr=False)

            if not text.strip():
                print("🟠 No text extracted from DOCX, trying OCR...")
                text = extract_docx_text(filepath, ocr=True)
                if text.strip():
                    print("🟢 OCR text extraction succeeded.")
                else:
                    print(f"❌ OCR also failed for {filename}. Skipping.")
                    continue

        if not text.strip():
            print(f"⚠️ Skipping empty or unreadable resume: {filename}")
            continue

        # Call IBM Granite
        print(f"📤 Sending text to IBM Granite Model → {filename}")
        try:
            extracted_data = extract_resume_info(text)
        except Exception as e:
            print(f"❌ Error extracting data from {filename}: {e}")
            continue

        if not extracted_data or not isinstance(extracted_data, dict):
            print(f"❌ No valid structured JSON returned for {filename}. Skipping.")
            continue

        # Optional: Clean up (if you have postprocessing)
        try:
            extracted_data = clean_extracted_data(extracted_data)
            print("🧹 Post-processing cleanup applied.")
        except Exception as e:
            print(f"⚠️ Post-processing failed for {filename}: {e}. Continuing without cleanup.")

        # Save JSON
        base_name = os.path.splitext(filename)[0]
        json_path = os.path.join(json_folder, f"{base_name}.json")
        try:
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(extracted_data, jf, indent=2, ensure_ascii=False)
            print(f"💾 Saved structured JSON: {json_path}")
        except Exception as e:
            print(f"❌ Failed to save JSON for {filename}: {e}")
            continue

        # Estimate technology durations (if you have such logic)
        try:
            from utils.tech_duration_estimator import estimate_technology_durations
            # Estimate technology durations
            technologies = extracted_data.get("Skills", {}).get("Hard Skill", [])
            tech_durations = estimate_technology_durations(
            extracted_data,
            technologies
        )

        except ImportError:
            tech_durations = "N/A"

        # Prepare Excel row
        personal = extracted_data.get("Personal Details", {})
        skills = extracted_data.get("Skills", {})
        tech_list = skills.get("Hard Skill", [])
        tech_durations_str = ", ".join(
            [f"{k}: {v}" for k, v in tech_durations.items()]
        ) if isinstance(tech_durations, dict) else "N/A"

        excel_row = [
            personal.get("Full Name", "Not Specified"),
            personal.get("Email", "Not Specified"),
            personal.get("Phone", "Not Specified"),
            personal.get("Location", "Not Specified"),
            extracted_data.get("Recent Employer", "Not Specified"),
            extracted_data.get("Job Title", "Not Specified"),
            extracted_data.get("Professional Summary", "Not Specified"),
            extracted_data.get("Total Years of Experience", "Not Specified"),
            ", ".join(tech_list) if tech_list else "Not Specified",
            tech_durations_str
        ]

        # Append to Excel
        try:
            append_to_excel(excel_path, excel_headers, excel_row)
            print(f"📊 Appended summary to Excel: {excel_path}")
        except Exception as e:
            print(f"⚠️ Could not append to Excel: {e}")

        # Fill Word template
        print("📝 Generating Word document...")
        try:
            doc = fill_template_with_data(template_path, extracted_data)
            docx_path = os.path.join(output_folder, f"{base_name}.docx")
            doc.save(docx_path)
            print(f"✅ Done: {docx_path}\n")
        except Exception as e:
            print(f"❌ Error generating DOCX for {filename}: {e}")

if __name__ == "__main__":
    main()
