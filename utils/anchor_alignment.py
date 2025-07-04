from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def fill_template_with_data(template_path, data):
    doc = Document(template_path)

    def insert_after_paragraph(paragraph, text_lines, alignment=None):
        """
        Insert a list of lines after a given paragraph.
        """
        for line in text_lines:
            new_p = OxmlElement("w:p")
            r = OxmlElement("w:r")
            t = OxmlElement("w:t")
            t.text = line
            r.append(t)
            new_p.append(r)

            if alignment == "right":
                pPr = OxmlElement("w:pPr")
                jc = OxmlElement("w:jc")
                jc.set(qn("w:val"), "right")
                pPr.append(jc)
                new_p.insert(0, pPr)

            paragraph._element.addnext(new_p)

    def format_value(value, anchor):
        """
        Convert a field value into a list of lines to insert.
        """
        if not value:
            return ["Not Specified"]

        # EMPLOYMENT HISTORY
        if anchor == "EMPLOYMENT HISTORY":
            lines = []
            if isinstance(value, dict):
                for company, roles in value.items():
                    lines.append(company)
                    for role in roles:
                        title = role.get("Role", "Not Specified").strip()
                        duration = role.get("Duration", "Not Specified").strip()
                        description = role.get("Description", "").strip()
                        lines.append(f"• {title} ({duration})")
                        if description:
                            lines.append(description)
            return lines

        # CERTIFICATIONS
        if anchor == "CERTIFICATIONS":
            lines = []
            if isinstance(value, list):
                for cert in value:
                    if isinstance(cert, dict):
                        name = cert.get("Certification Name", "Not Specified")
                        field = cert.get("Field", "Not Specified")
                        date = cert.get("Date", "Not Specified")
                        lines.append(f"{name} - {field} ({date})")
                    else:
                        lines.append(str(cert))
            return lines

        # EDUCATION
        if anchor == "EDUCATION":
            lines = []
            if isinstance(value, list):
                value = list(reversed(value))  # most recent first
                for edu in value:
                    degree = edu.get("Degree", "Not Specified")
                    duration = edu.get("Duration", "Not Specified")
                    inst = edu.get("Institution", "Not Specified")
                    lines.append(f"{degree} ({duration})")
                    lines.append(inst)
            return lines

        # LANGUAGES
        if anchor == "LANGUAGES":
            lines = []
            if isinstance(value, list):
                for lang in value:
                    if isinstance(lang, dict):
                        name = lang.get("Name", "Not Specified")
                        level = lang.get("Level", "Not Specified")
                        lines.append(f"- {name} ({level})")
                    else:
                        lines.append(f"- {lang}")
            return lines

        # Skills
        if isinstance(value, list):
            return [f"- {item}" for item in value]

        # Fallback for dicts
        if isinstance(value, dict):
            return [f"{k}: {v}" for k, v in value.items()]

        return [str(value) or "Not Specified"]

    def insert_below_anchor(anchor, value):
        """
        Locate the anchor text and insert formatted content below it.
        """
        found = False
        for para in doc.paragraphs:
            if anchor.lower() in para.text.strip().lower():
                lines = format_value(value, anchor)
                alignment = "right" if anchor.lower() == "recent employer" else None
                insert_after_paragraph(para, lines, alignment)
                found = True
                break
        if not found:
            print(f"⚠️ Anchor '{anchor}' not found in the template.")

    # Insert all fields
    insert_below_anchor("Recent Employer", data.get("Recent Employer", "Not Specified"))
    insert_below_anchor("Job Title", data.get("Job Title", "Not Specified"))
    insert_below_anchor("PROFESSIONAL SUMMARY", data.get("Professional Summary", "Not Specified"))
    insert_below_anchor("EMPLOYMENT HISTORY", data.get("Employment History", []))
    skills = data.get("Skills") or {}
    insert_below_anchor("Hard Skill", skills.get("Hard Skill", []))
    insert_below_anchor("Soft Skill", skills.get("Soft Skill", []))
    insert_below_anchor("CERTIFICATIONS", data.get("Certifications", []))
    insert_below_anchor("EDUCATION", data.get("Education", []))
    insert_below_anchor("LANGUAGES", data.get("Languages", []))

    return doc
