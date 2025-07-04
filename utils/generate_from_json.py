import os
import json
from docx import Document
from utils.anchor_alignment import fill_template_with_data

def generate_from_json(json_path, template_path, output_path):
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    filled_doc = fill_template_with_data(template_path, data)
    filled_doc.save(output_path)
    print(f"✅ Generated: {output_path}")

if __name__ == "__main__":
    # Example usage
    json_input = "json/structured_example_resume.json"
    template = "templates/final_template.docx"
    output_docx = "outputs/generated_example_resume.docx"

    generate_from_json(json_input, template, output_docx)
