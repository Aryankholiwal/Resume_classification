import subprocess
import json
import re
import unicodedata
from config import LLAMA_MODEL_NAME, PROMPT_TEMPLATE

MAX_DESCRIPTION_LENGTH = 1000  # prevent excessively long strings


def sanitize_llama_output(raw_output):
    raw_output = re.sub(r'^.*?{', '{', raw_output, flags=re.DOTALL)
    raw_output = raw_output.replace("“", '"').replace("”", '"').replace("`", '"')
    raw_output = re.sub(r'"([^"\n]+)\':', r'"\1":', raw_output)
    raw_output = re.sub(r'\}\s*"([A-Za-z])', r'},\n"\1', raw_output)
    raw_output = re.sub(r'\]\s*"([A-Za-z])', r'],\n"\1', raw_output)
    raw_output = re.sub(r',\s*(\}|\])', r'\1', raw_output)
    raw_output = re.sub(r'":\s*"([^"]*)$', r'": "Not Specified"', raw_output)
    open_braces = raw_output.count("{")
    close_braces = raw_output.count("}")
    if close_braces < open_braces:
        raw_output += "}" * (open_braces - close_braces)
    return raw_output.strip()


def is_valid_duration(text):
    if not text or not isinstance(text, str):
        return False
    patterns = [
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-–]*\d{2,4}",
        r"\d{4}\s*[-–to]+\s*(Present|\d{4})",
        r"\d{2}/\d{4}",
        r"Present|Current"
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def normalize(text):
    return unicodedata.normalize("NFKD", text or "").strip().lower()


def clean_employment_history(employment_data, project_titles=None):
    cleaned = {}
    seen_keys = set()
    for company, roles in employment_data.items():
        if not company or not isinstance(roles, list):
            continue
        company_name = company.strip()
        company_norm = normalize(company_name)
        if not re.search(r"[a-zA-Z]", company_name):
            continue
        valid_roles = []
        for role in roles:
            if not isinstance(role, dict):
                continue
            role_title = (role.get("Role") or "").strip()
            duration = (role.get("Duration") or "").strip()
            description = (role.get("Description") or "").strip()
            if not role_title and not duration:
                continue
            if not is_valid_duration(duration):
                duration = "Not Specified"
            if not description:
                description = "Not Specified"
            elif len(description) > MAX_DESCRIPTION_LENGTH:
                description = description[:MAX_DESCRIPTION_LENGTH] + "..."
            if project_titles:
                combined = normalize(role_title + " " + description)
                if any(pt in combined for pt in project_titles):
                    continue
            key = (company_norm, normalize(role_title), normalize(duration), normalize(description))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            valid_roles.append({
                "Role": role_title or "Not Specified",
                "Duration": duration,
                "Description": description
            })
        if valid_roles:
            cleaned[company_name] = valid_roles
    return cleaned


def clean_education(edu_list):
    cleaned = []
    for entry in edu_list:
        if not isinstance(entry, dict):
            continue
        degree = (entry.get("Degree") or "").strip()
        institution = (entry.get("Institution") or "").strip()
        duration = (entry.get("Duration") or "").strip()
        if degree and institution and len(degree) > 2 and len(institution) > 2:
            cleaned.append({
                "Degree": degree,
                "Institution": institution,
                "Duration": duration if duration else "Not Specified"
            })
    return cleaned


def extract_projects_from_employment(employment_data):
    project_verbs = [
        "developed", "designed", "implemented", "built", "engineered",
        "created", "led", "worked on", "integrated", "optimized"
    ]
    extracted_projects = []
    for company, roles in employment_data.items():
        for role in roles:
            desc = (role.get("Description") or "").strip()
            lines = desc.split("\n") if "\n" in desc else re.split(r'[.;]', desc)
            non_project_lines = []
            for line in lines:
                if any(verb in line.lower() for verb in project_verbs) and len(line.strip()) > 20:
                    extracted_projects.append({
                        "Title": f"{role.get('Role')} at {company}",
                        "Stack": "Not Specified",
                        "Description": line.strip()
                    })
                else:
                    non_project_lines.append(line.strip())
            role["Description"] = ". ".join(non_project_lines).strip() or "Not Specified"
    return extracted_projects


def extract_resume_info(text):
    context_prefix = (
        "<<BEGIN INSTRUCTIONS>>\n"
        "You are a strict JSON-only resume parser.\n"
        "- DO NOT include markdown, commentary, bullet points, or explanation.\n"
        "- Only respond with a syntactically valid JSON object.\n"
        "- Ensure Employment and Projects are separated.\n"
        "- Begin with '{' and end with '}'.\n"
        "- Extract ALL companies (do not merge multiple employers).\n"
        "- Disambiguate CLIENTS vs EMPLOYERS.\n"
        "- Handle tables and inline formats.\n"
        "<<END INSTRUCTIONS>>\n\n"
        "<<BEGIN RESUME>>\n"
        f"{text}\n"
        "<<END RESUME>>\n\n"
        "Now respond ONLY with the JSON data in the schema described above:"
    )

    full_prompt = f"{context_prefix}\n\n{PROMPT_TEMPLATE}"

    for attempt in range(2):
        try:
            result = subprocess.run(
                ["ollama", "run", LLAMA_MODEL_NAME],
                input=full_prompt,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            raw_output = result.stdout.strip()
            print("---- RAW LLaMA OUTPUT ----")
            print(raw_output[:1000])
            print("---- END ----")
            start_idx = raw_output.find("{")
            end_idx = raw_output.rfind("}")
            if start_idx == -1 or end_idx == -1:
                print("❌ No JSON found in output.")
                return {}
            json_block = raw_output[start_idx:end_idx + 1]
            cleaned_output = sanitize_llama_output(json_block)
            with open("json/last_raw_output.txt", "w", encoding="utf-8") as debug_file:
                debug_file.write(cleaned_output)
            data = json.loads(cleaned_output)

            if "Projects" not in data or not isinstance(data["Projects"], list):
                data["Projects"] = []
            data["Projects"] = [
                p for p in data["Projects"]
                if isinstance(p, dict) and p.get("Title") and p.get("Description")
            ]

            project_titles = {
                normalize(p.get("Title") or "")
                for p in data["Projects"]
                if isinstance(p, dict)
            }

            if "Employment History" in data:
                data["Employment History"] = clean_employment_history(
                    data["Employment History"], project_titles
                )
                extracted_proj = extract_projects_from_employment(data["Employment History"])
                data["Projects"].extend(extracted_proj)

            if not data.get("Employment History"):
                recent_employer = data.get("Recent Employer", "").strip()
                job_title = data.get("Job Title", "").strip()
                summary = data.get("Professional Summary", "").strip()
                if recent_employer and job_title:
                    fallback_entry = {
                        "Role": job_title,
                        "Duration": "Not Specified",
                        "Description": summary[:250] or "Not Specified"
                    }
                    data["Employment History"] = {
                        recent_employer: [fallback_entry]
                    }

            if "Education" in data and isinstance(data["Education"], list):
                data["Education"] = clean_education(data["Education"])

            return data

        except json.JSONDecodeError as e:
            print(f"⚠️ JSON decode error: {e}")
            if attempt == 0:
                print("🔁 Retrying once more...")
                continue
            return {}
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {}
