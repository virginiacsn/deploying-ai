import requests
import json
import re
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "data" / "ct_database.jsonl"

def download_trials():
    trials = []
    params = {
        "query.cond": "cancer",
        "query.locn": "United States",
        "filter.overallStatus": "RECRUITING",
        "filter.advanced": "AREA[StudyType]INTERVENTIONAL",
        "fields": "NCTId,BriefTitle,Condition,EligibilityCriteria,MinimumAge,MaximumAge,Sex",
        "pageSize": 1000,
        }
    while len(trials) < 1000:
        r = requests.get(
            "https://clinicaltrials.gov/api/v2/studies", 
            params=params,
            ).json()
        trials.extend(r.get("studies", []))
        token = r.get("nextPageToken")
        if not token:
            break
        params["pageToken"] = token
    return trials

def split_eligibility(text):
    parts = re.split(r"\n\s*(?:key\s+)?exclusion\s+criteria\s*:?", text, maxsplit=1, flags=re.I)
    inclusion = re.sub(r"^\s*(?:key\s+)?inclusion\s+criteria\s*:?", "", parts[0], flags=re.I).strip()
    exclusion = parts[1].strip() if len(parts) > 1 else ""
    return inclusion, exclusion


if __name__ == "__main__":
    print("Creating clinical trials database...")

    trials = []
    for trial in download_trials():
        p = trial["protocolSection"]
        e = p.get("eligibilityModule", {})
        inclusion, exclusion = split_eligibility(e.get("eligibilityCriteria", ""))
        trials.append({
                "id": p["identificationModule"]["nctId"],
                "title": p["identificationModule"].get("briefTitle", ""),
                "conditions": p.get("conditionsModule", {}).get("conditions", []),
                "inclusion": inclusion,
                "exclusion": exclusion,
                "min_age": e.get("minimumAge"),
                "max_age": e.get("maximumAge"),
                "sex": e.get("sex", "ALL"),
            })

    with open(DATA_PATH, 'w') as f:
        for trial in trials:
            line = json.dumps(trial)
            f.write(line + "\n")

    print("Clinical trials database saved in ct_database.jsonl")
