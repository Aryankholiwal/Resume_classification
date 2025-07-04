from collections import defaultdict
from dateutil import parser

def parse_duration(duration_text):
    """
    Convert 'Jan 2019 – Mar 2022' into number of months.
    Returns (start_date, end_date, months).
    """
    if not duration_text or "–" not in duration_text:
        return None, None, 0

    try:
        start_str, end_str = [x.strip() for x in duration_text.split("–", 1)]
        start_date = parser.parse(start_str, fuzzy=True)
        end_date = parser.parse(end_str, fuzzy=True)
        delta = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        delta = max(delta, 1)
        return start_date, end_date, delta
    except Exception:
        return None, None, 0

def estimate_technology_durations(extracted_data, technologies):
    """
    Estimates duration per technology based on Employment History.
    Returns a dict mapping technology to total duration in months (approx).
    """
    employment_history = extracted_data.get("Employment History", {})
    durations = {}

    for tech in technologies:
        durations[tech] = 0

    for company, roles in employment_history.items():
        for role in roles:
            duration_text = role.get("Duration", "")
            description = role.get("Description", "").lower()

            # Heuristic: if tech mentioned in description, add dummy duration (e.g., 12 months)
            for tech in technologies:
                if tech.lower() in description:
                    durations[tech] += 12  # or your calculation logic

    return durations

