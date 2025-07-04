
def clean_extracted_data(data):
    """
    Cleans up the extracted data.
    - Removes Education entries accidentally placed inside Employment History.
    - Optionally dedupes or normalizes fields.
    """

    # Remove companies with education-like names in Employment History
    education_keywords = ["University", "College", "School", "Institute"]
    cleaned_employment = {}

    for company, roles in data.get("Employment History", {}).items():
        if any(keyword.lower() in company.lower() for keyword in education_keywords):
            continue  # skip this company
        cleaned_employment[company] = roles

    data["Employment History"] = cleaned_employment

    # Example: ensure empty sections are properly set
    if not data.get("Certifications"):
        data["Certifications"] = []

    if not data.get("Projects"):
        data["Projects"] = []

    return data
