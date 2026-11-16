# Assignment chat

## Overview

This chat assistant helps with clinical and research queries. Its intended audience is both clinical personnel and patients or caregivers. It offers three services: finding matching clinical trials for a patient description, retrieving clinical trial details, and retrieving biomedical research articles.

Example queries for each service can be found in `example_queries.md`.

## Services

### Clinical Trial Matching

Given a patient description, matching clinical trials are retrieved and then evaluated to assess the patient's eligibility. The query can include the number of trials to retrieve; otherwise, the default is three.

This service implements hybrid RAG over a Chroma vector database of clinical trials (metadata filter + semantic search). To get matching clinical trials, the database is first filtered by patient age and sex. Then, a semantic similarity search is performed between the patient's clinical information and the clinical trial embeddings, which are built from each trial's conditions and inclusion criteria.

For each retrieved clinical trial, the model first evaluates whether the trial is a fit, based on the conditions it treats and its exclusion criteria. If the trial does not pass these checks, it is removed from the response. The remaining trials are presented with their title, id, a short description, an assessment of the inclusion and exclusion criteria, and a conclusion stating whether the patient is eligible or more information is needed. For the criteria assessment, inclusion criteria are grouped into three categories (met, not met, or needs more information), and exclusion criteria are grouped into two categories (ruled out or needs more information). After all trials are presented, a final summary lists each trial with its eligibility assessment.

### Clinical Trial Details

This service is designed as a follow-up to clinical trial matching. Given a clinical trial's ClinicalTrials.gov id (NCT number), the trial's details are retrieved using the ClinicalTrials.gov API.

The response includes the trial title, id, sponsor, status, locations, duration, study design, arm groups, interventions and primary outcome measures.

### Research Article Search

This service retrieves research article details from PubMed using the PubMed API. The query can include a research area or topic, as well as date filters. The retrieved articles can be original publications, preprints or reviews, and they must have an abstract available. The query can include the number of articles to retrieve; otherwise, the default is three.

The response includes the article title, authors, journal, publication year, DOI and a summary of the abstract.

## Implementation

- The agent is a LangGraph graph with two nodes: an assistant node, where `gpt-4o-mini` reads the conversation and decides whether to call a tool, and a tool node, which runs the tool. If the model calls a tool, the result is sent back to the assistant node, and the loop continues until the model replies without a tool call.
- Pydantic models define the tools' inputs and outputs, so the model extracts the right arguments from the query and gets all the data it needs to generate the response.
- The structure of how trials or articles are presented in the response is defined in the system prompt, allowing for some flexibility.
- There is one tool per service. Tools use `parse_docstring=True` so that the argument descriptions in each function's docstring are passed to the model.
- Memory is managed with context trimming (LangChain's `trim_messages`), set to 60,000 tokens (about 50% of the context window for gpt-4o-mini) and starting with a human message. Messages related to attempts to obtain the system prompt are removed from the conversation history.

## Data

A database of 1000 clinical trials was created from the ClinicalTrials.gov API. These trials are related to cancer, currently recruiting, interventional, and have at least one location in the United States. This selection was done to keep the database small.

A Chroma vector database was created with an embedding for each trial, generated with OpenAI's `text-embedding-3-small` model. The embeddings are based on each trial's conditions and inclusion criteria. Inclusion criteria were added to the embedding text as they may include medical details that could be present in the patient description, aside from the general condition that the trial targets.

## Guardrails

All guardrails are defined in a dedicated section of the system prompt.

The guardrails instruct the model to:

- Only answer queries within the clinical or research context.
- Only present information from the query or the tool outputs.
- Not give any kind of medical advice, and recommend consulting the medical team.
- Not reveal or override the system prompt.

## Project Structure

```
assignment_chat/
├── app.py                 # Gradio chat interface
├── main.py                # LangGraph agent: LLM node + tool node
├── tools.py               # Tools: trial matching, trial details, PubMed search
├── prompts.py             # System prompt
├── database.py            # Downloads trials from ClinicalTrials.gov
├── embedding.py           # Embeds trials into the Chroma vector database
├── example_queries.md     # Example queries to try in the chat
└── data/
    ├── ct_database.jsonl  # 1000 recruiting US cancer trials
    └── chroma_db/         # Chroma vector database
```

## Limitations

- The embeddings can contain irrelevant information because they include the full text of the inclusion criteria. Using only the conditions could improve retrieval.
- Trials are sometimes not filtered out properly by the model before being presented.
- Fewer clinical trials than requested can be presented when the model filters for condition and exclusion criteria.
- The structure of the clinical trial matching response is not enforced, which leads to inconsistent responses. Criteria are sometimes not categorized properly; a dedicated model pass to categorize the criteria might be needed.
- Research article retrieval is not very flexible: the user cannot choose between original articles, preprints and reviews.
