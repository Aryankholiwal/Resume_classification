import os
import json
from dotenv import load_dotenv
from ibm_watson_machine_learning.foundation_models import Model

# Load environment variables
load_dotenv()

IBM_API_KEY = os.getenv("IBM_API_KEY")
IBM_PROJECT_ID = os.getenv("IBM_PROJECT_ID")
IBM_URL = "https://us-south.ml.cloud.ibm.com"

if not IBM_API_KEY or not IBM_PROJECT_ID:
    raise ValueError("❌ IBM_API_KEY or IBM_PROJECT_ID not set. Please check your .env file.")

# === PROMPT TEMPLATE ===
PROMPT_TEMPLATE = """
You are a strict resume parser. Parse the resume below and return only a valid JSON structure.

===========================
GENERAL RULES
===========================
- Output must be syntactically valid JSON—no markdown, commentary, or notes.
- All keys and string values must be wrapped in double quotes.
- Always return every top-level key, even if empty or "Not Specified".
- Resume content may be in bullets, inline text, or tables—normalize accordingly.
- Ensure that EVERY company or employer listed is included in Employment History, even short-term roles or internships.
- DO NOT embed project descriptions inside Employment History (unless no Projects section exists).
- Distinguish EMPLOYERS (organizations the candidate worked for) from CLIENTS (end customers).
- Use fallback logic if a section is missing or unclear.

===========================
IMPORTANT RULES ABOUT EMPLOYMENT HISTORY AND PROJECTS
===========================
- In "Employment History", list every distinct employer and role, even if the role lasted only a few months.
- For each company:
  - Extract Role, Duration, and a short Description (high-level duties only).
  - Do NOT include detailed project descriptions.
- In "Projects", separately extract any detailed project information:
  - Project titles, technology stack, objectives, outcomes.
- Ensure NO duplication of text between Employment History and Projects.
- Under no circumstances should education details (such as degrees, universities, academic durations, or education descriptions) be placed in "Employment History".
- If there is no employment information at all:
  - Leave "Employment History" empty.
  - Do NOT move Education, Certifications, or Skills into "Employment History".
- Never list educational institutions (universities, colleges, schools) as employers in "Employment History".
- If an entry mentions degree names (e.g., "B.Tech", "Bachelor", "MSc", "PhD") or schooling, it must go ONLY under "Education".
- "Employment History" should include only organizations where the candidate was employed, interned, or contracted to perform professional work for compensation.
- Do not repeat them in "Employment History".
- Example:
Example:
- Input: "Amity University, Noida - B.Tech in Information Technology, 2022-2026"
  Correct: Under "Education"
  Incorrect: Under "Employment History"

- Input: "Infosys Limited - Software Developer, 2021-2023"
  Correct: Under "Employment History"

===========================
1. "Personal Details"
===========================
"Personal Details": {
  "Full Name": "...",
  "Email": "...",
  "Phone": "...",
  "Location": "..."
}

- Extract the candidate's full name, email, phone, and location.
- If missing, set as "Not Specified".

===========================
2. "Recent Employer"
===========================
- Most recent employer (not a client).
- Infer from Employment History.

===========================
3. "Job Title"
===========================
- Most recent valid job designation.

===========================
4. "Professional Summary"
===========================
- If present, extract it.
- If absent, generate a 2–4 line summary covering:
  - Years of experience
  - Technologies
  - Domain/industry
  - Highlights of work

===========================
5. "Employment History"
===========================
"Employment History": {
  "Company A": [
    {
      "Role": "...",
      "Duration": "...",
      "Description": "..."
    }
  ],
  "Company B": [...]
}

DO:
- Include all employers and all roles—full-time, internships, freelance.
- Accept bullet points, paragraphs, or tables.
- If missing, set as "Not Specified".


DO NOT:
- Use clients or technologies as company names.
- Repeat the same Role-Duration-Description under multiple companies.

===========================
6. "Skills"
===========================
"Skills": {
  "Hard Skill": [...],
  "Soft Skill": [...]
}

- Hard Skills: technologies, frameworks, tools.
- Soft Skills: interpersonal capabilities.

===========================
7. "Certifications"
===========================
[
  {
    "Certification Name": "...",
    "Field": "...",
    "Date": "..."
  }
]

===========================
8. "Education"
===========================
[
  {
    "Degree": "...",
    "Institution": "...",
    "Duration": "..."
  }
]

===========================
9. "Languages"
===========================
["English", "Hindi"]

===========================
10. "Projects"
===========================
[
  {
    "Title": "...",
    "Stack": "...",
    "Description": "..."
  }
]

DO:
- Extract from any dedicated Projects section or project mentions under Employment.
- Ensure no duplication with Employment History descriptions.

===========================
STRICT FINAL JSON FORMAT
===========================
{
  "Personal Details": {
    "Full Name": "...",
    "Email": "...",
    "Phone": "...",
    "Location": "..."
  },
  "Recent Employer": "...",
  "Job Title": "...",
  "Professional Summary": "...",
  "Employment History": {
    "Company A": [
      {
        "Role": "...",
        "Duration": "...",
        "Description": "..."
      }
    ]
  },
  "Skills": {
    "Hard Skill": ["..."],
    "Soft Skill": ["..."]
  },
  "Certifications": [
    {
      "Certification Name": "...",
      "Field": "...",
      "Date": "..."
    }
  ],
  "Education": [
    {
      "Degree": "...",
      "Institution": "...",
      "Duration": "..."
    }
  ],
  "Languages": ["English", "Hindi"],
  "Projects": [
    {
      "Title": "...",
      "Stack": "...",
      "Description": "..."
    }
  ]
}
===========================
EXAMPLE INPUT TEXT
===========================
Full name: John Smith
Email:john@example.com
Phone: 9473840788 
Experience: 5years as Software engineer
Skills: Python, JavaScript, AWS
Languages: English, Hindi

===========================
EXAMPLE JSON OUTPUT
===========================
{
  "Personal Details": {
  "Full Name":"John Smith",
  "Email"L"john@example.com",
  "Phone":"9473840788" 
  "Location": "not specified"
  },

  "Recent Employer": "Not Specified",
  "Job Title": "Software Engineer",
  "Professional Summary": "Software Engineer with 5 years of experience specializing in Python and AWS.",
  "Employment History": {
  "Company A": [
      {
        "Role": "...",
        "Duration": "...",
        "Description": "..."
      }
    ]
  },
  "Skills": {
    "Hard Skill": ["Python", "AWS", "JavaScript"],
    "Soft Skill": []
  },
  "Certifications": [],
  "Education": [],
  "Languages": ["English"],
  "Projects": []
}

===========================
Resume to Parse
===========================
<<<RESUME_START>>>
{text}
<<<RESUME_END>>>
""".strip()

def sanitize_json_output(raw):
    """
    Attempts to clean incomplete or messy JSON output.
    """
    cleaned = raw.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    lines = cleaned.splitlines()
    json_lines = []
    inside_json = False
    brace_balance = 0

    for line in lines:
        if not inside_json:
            if line.strip().startswith("{"):
                inside_json = True
                brace_balance = line.count("{") - line.count("}")
                json_lines.append(line)
        else:
            brace_balance += line.count("{") - line.count("}")
            json_lines.append(line)
            if brace_balance == 0:
                break

    if not json_lines:
        raise ValueError("❌ No JSON block found in output.")

    return "\n".join(json_lines).strip()

def extract_resume_info(text):
    """
    Calls IBM Granite model with the parsing prompt and returns structured JSON.
    """
    model_id = "ibm/granite-3-3-8b-instruct"

    model = Model(
        model_id=model_id,
        params={
            "decoding_method": "greedy",
            "max_new_tokens": 4096,
            "temperature": 0
        },
        credentials={
            "apikey": IBM_API_KEY,
            "url": IBM_URL
        },
        project_id=IBM_PROJECT_ID
    )

    prompt = PROMPT_TEMPLATE.replace("{text}", text)

    response = model.generate(prompt=prompt)

    generated_text = response.get("results", [{}])[0].get("generated_text", "")
    print("---- RAW GRANITE OUTPUT ----")
    print(generated_text)
    print("---- END ----")

    cleaned_json = sanitize_json_output(generated_text)

    try:
        data = json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON decode error: {e}")
        raise ValueError("❌ Failed to parse JSON. Please check the model output.")

    return data
