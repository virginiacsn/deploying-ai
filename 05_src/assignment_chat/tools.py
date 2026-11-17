from langchain.tools import tool

import chromadb
from assignment_chat.embedding import COLLECTION_NAME, CHROMA_PATH, SRC_DIR, embedding_function
from pydantic import BaseModel, Field
from typing import Literal, Optional

from dotenv import load_dotenv

import requests
import xml.etree.ElementTree as ET

load_dotenv(SRC_DIR / ".env")
load_dotenv(SRC_DIR / ".secrets")

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = chroma_client.get_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function
)



class PatientData(BaseModel):
    age: int | None = Field(None, description="Patient age in years")
    sex: Literal["FEMALE", "MALE"] | None = None
    clinical_info: str = Field(description="Clinical information")

class ClinicalTrial(BaseModel):
    id: str
    title: str = Field(description="Full clinical trial title")
    condition: str = Field(description="List of conditions the clinical trial is for")
    inclusion: str = Field(description="Inclusion criteria")
    exclusion: str = Field(description="Exclusion criteria")


@tool(parse_docstring=True)
def get_matching_trials(patient: PatientData, n_results: int = 3) -> list[ClinicalTrial]:
    """Search for clinical trials a patient could be eligible for.

    Use this when the user describes a patient (a clinical note, a description, or a
    patient or caregiver describing themselves or a relative). The database only contains
    recruiting interventional cancer trials in the United States. Trials are pre-filtered
    by age and sex, then ranked by similarity to the clinical information, so every result
    still needs its inclusion and exclusion criteria checked against the patient.

    Args:
        patient: Patient age, sex and clinical information extracted from the user's message.
        n_results: Number of trials to retrieve. Use the number the user asks for, otherwise 3.

    Returns:
        Trials with id, title, conditions, inclusion and exclusion criteria.
        An empty list if no trial matches the age and sex filters.
    """

    context_data = get_context(patient, collection, n_results)
    matching_trials = []
    if not context_data:
        return matching_trials
    for item in context_data:
        trial = ClinicalTrial(
            id=item.get('id', 'N/A'),
            title=item.get('title', 'N/A'),
            condition=item.get('condition', 'N/A'),
            inclusion=item.get('inclusion', 'N/A'),
            exclusion=item.get('exclusion', 'N/A'),
        )
        matching_trials.append(trial)
    return matching_trials


def get_context_data(query: str, collection: chromadb.api.models.Collection, n_results: int,
                     where: dict = None):
    kwargs = dict(query_texts=[query], n_results=n_results)
    if where:
        kwargs['where'] = where
    results = collection.query(**kwargs)
    context_data = []
    for idx in range(len(results['ids'][0])):
        details = dict(results['metadatas'][0][idx])
        details['id'] = results['ids'][0][idx]
        context_data.append(details)
    return context_data


def get_context(patient: PatientData, collection:chromadb.api.models.Collection, n_results: int):
    metadata_filter = []
    if patient.age is not None:
        metadata_filter.append({"min_age": {"$lte": patient.age}})
        metadata_filter.append({"max_age": {"$gte": patient.age}})
    if patient.sex is not None:
        metadata_filter.append({"sex": {"$in": [patient.sex, "ALL"]}})

    where = None
    if len(metadata_filter) == 1:
        where = metadata_filter[0]
    elif len(metadata_filter) > 1:
        where = {"$and": metadata_filter}

    context_data = get_context_data(
        patient.clinical_info, 
        collection, 
        n_results, 
        where=where
        )
    return context_data


class TrialData(BaseModel):
    id: str
    title: str
    sponsor: Optional[str] = None
    status: Optional[str] = None
    locations: list[str] = []       
    n_us_locations: int = 0          
    other_countries: list[str] = []   
    phases: list[str] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    study_type: Optional[str] = None
    design_info: dict = {}     
    enrollment: Optional[int] = None
    arm_groups: list[dict] = []
    interventions: list[dict] = []
    primary_outcomes: list[str] = []

@tool(parse_docstring=True)
def get_clinical_trial(trial_id: str) -> Optional[TrialData]:
    """Get the full details of one clinical trial from ClinicalTrials.gov.

    Use this when the user gives an NCT number or asks for more about a trial shown
    earlier in the conversation (e.g. "tell me more about the second one"); take the id
    from the earlier results in that case.

    Args:
        trial_id: ClinicalTrials.gov id: "NCT" followed by 8 digits (e.g. "NCT05534438").

    Returns:
        Sponsor, status, phase, up to 10 US sites (with the total US site count and other
        countries with sites), dates, design, enrollment, arm groups, interventions
        and primary outcomes. None if no trial with that id has a site in the United States.
    """

    r = requests.get(
        "https://clinicaltrials.gov/api/v2/studies",
        params={
            "query.locn": "United States",
            "filter.ids": trial_id,
            "fields": "NCTId,BriefTitle,StatusModule,DesignModule,ArmsInterventionsModule,"
                      "OutcomesModule,SponsorCollaboratorsModule,LocationCity,LocationState,LocationCountry",
        },
    ).json()

    studies = r.get("studies", [])
    if not studies:
        return None
    trial = parse_trial(studies[0])
    return trial


MAX_LOCATIONS = 10


def parse_locations(locs: list[dict]) -> tuple[list[str], int, list[str]]:
    """Split trial sites into US sites ("City, State", capped at MAX_LOCATIONS),
    the total number of US sites, and the other countries with sites."""
    us_sites = set()
    other_countries = set()
    for loc in locs:
        country = loc.get("country")
        city = loc.get("city")
        if country == "United States":
            if city:
                state = loc.get("state")
                us_sites.add(f"{city}, {state}" if state else city)
        elif country:
            other_countries.add(country)
    us_sites = sorted(us_sites)
    return us_sites[:MAX_LOCATIONS], len(us_sites), sorted(other_countries)


def parse_trial(trial: dict) -> TrialData:
    p = trial["protocolSection"]
    ident = p["identificationModule"]
    status = p.get("statusModule", {})
    design = p.get("designModule", {})
    arms = p.get("armsInterventionsModule", {})
    outcomes = p.get("outcomesModule", {})
    sponsor = p.get("sponsorCollaboratorsModule", {})
    locs = p.get("contactsLocationsModule", {}).get("locations", [])
    us_locations, n_us_locations, other_countries = parse_locations(locs)

    trial_data = TrialData(
        id=ident["nctId"],
        title=ident["briefTitle"],
        sponsor=sponsor.get("leadSponsor", {}).get("name"),
        status=status.get("overallStatus"),
        locations=us_locations,
        n_us_locations=n_us_locations,
        other_countries=other_countries,
        phases=design.get("phases", []),
        start_date=status.get("startDateStruct", {}).get("date"),
        end_date=status.get("completionDateStruct", {}).get("date"),
        study_type=design.get("studyType"),
        design_info=design.get("designInfo", {}),
        enrollment=design.get("enrollmentInfo", {}).get("count"),
        arm_groups=arms.get("armGroups", []),
        interventions=arms.get("interventions", []),
        primary_outcomes=[o["measure"] for o in outcomes.get("primaryOutcomes", [])],
    )
    return trial_data


class ArticleData(BaseModel):
    id: str
    title: str = Field(description="Full article title")
    author: str = Field(description="Short version of authors list (ex. First author et al.)")
    journal: Optional[str] = Field(None, description="Full journal name")
    year: Optional[str] = Field(None, description="Article publication year")
    doi: Optional[str] = Field(None, description="Article doi url")
    abstract: str = Field(description="Article abstract")

@tool(parse_docstring=True)
def get_pubmed_articles(
    query: str,
    n_results: int = 3,
    min_date: Optional[str] = None,
    max_date: Optional[str] = None,
) -> list[ArticleData]:
    """Search PubMed for research articles on a topic, ranked by relevance.

    Use this when the user asks for research, studies, literature or evidence on a
    topic. Only journal articles, reviews and preprints that have an abstract are returned.

    Args:
        query: Research topic as concise PubMed search keywords (e.g. "osimertinib resistance
            EGFR NSCLC"), not a full sentence. Leave out dates and article counts.
        n_results: Number of articles to retrieve. Use the number the user asks for, otherwise 3.
        min_date: Earliest publication date, as "YYYY/MM/DD", "YYYY/MM" or "YYYY". Only set it
            if the user asks for a time range (e.g. "since 2020" -> "2020").
        max_date: Latest publication date, as "YYYY/MM/DD", "YYYY/MM" or "YYYY". Only set it
            if the user asks for a time range.

    Returns:
        Articles with PubMed id, title, short author list, journal, year, DOI and abstract.
        An empty list if nothing matches.
    """

    pubmed_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    # Only journal articles, reviews and preprints that have an abstract (no books or abstract-less records)
    term = f"({query}) AND (journal article[pt] OR review[pt] OR preprint[pt]) AND hasabstract"
    search_params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": n_results,
        "sort": "relevance",
    }
    if min_date or max_date:
        search_params["datetype"] = "pdat"
        search_params["mindate"] = min_date or "1900"
        search_params["maxdate"] = max_date or "3000"

    search = requests.get(pubmed_url + "esearch.fcgi", params=search_params).json()

    ids = search["esearchresult"]["idlist"]
    if not ids:
        return []

    fetch = requests.get(
        pubmed_url + "efetch.fcgi",
        params={"db": "pubmed", "id": ",".join(ids), "rettype": "abstract", "retmode": "xml"},
    )

    articles = parse_articles(fetch.text)
    return articles


def parse_articles(fetch_text: str):
    root = ET.fromstring(fetch_text)

    articles = []
    for art in root.iter("PubmedArticle"):
        pmid = art.findtext(".//MedlineCitation/PMID")
        title = "".join(art.find(".//ArticleTitle").itertext())

        first = art.find(".//AuthorList/Author")
        authors = art.findall(".//AuthorList/Author")
        n_authors = len(authors)
        if first is None:
            author = "Anonymous"
        else:
            name = first.findtext("LastName") or first.findtext("CollectiveName")
            if n_authors == 1:
                author = name
            elif n_authors == 2:
                second = authors[1]
                author = f"{name} & {second.findtext('LastName') or second.findtext('CollectiveName')}"
            else:
                author = f"{name} et al."

        journal = art.findtext(".//Journal/Title")
        year = art.findtext(".//Journal/JournalIssue/PubDate/Year")
        if year is None:
            medline_date = art.findtext(".//Journal/JournalIssue/PubDate/MedlineDate")
            year = medline_date[:4] if medline_date else None

        doi   = art.findtext('.//ArticleId[@IdType="doi"]')

        abstract = "\n".join(
            f'{a.get("Label", "")}: {"".join(a.itertext())}'
            for a in art.findall(".//Abstract/AbstractText")
        )
        article = ArticleData(
            id=pmid,
            title=title,
            author=author,
            journal=journal,
            year=year,
            doi=doi,
            abstract=abstract,
        )
        articles.append(article)
    return articles