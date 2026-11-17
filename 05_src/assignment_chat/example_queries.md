# Example Queries

## 1. Clinical Trial Matching

Paste a patient note or description. The assistant extracts the patient's age, sex and clinical information, retrieves matching trials, and checks each trial's inclusion and exclusion criteria against the patient. To retrieve a specific number of trials, add it to the query (e.g. "Find 5 trials for...").

### Patient descriptions

Patient descriptions from the [TREC](https://www.trec-cds.org/) 2016 Clinical Decision Support Track and 2022 Clinical Trials Track.

**Patient 1**

```
85M dementia, colon cancer and recent colectomy with primary reanastomosis p/w melena. HCT 30 to 23 but hemodynamically stable. NGL negative. Exam notable for Tm 99 BP 128/50 HR 70 RR 16 with sat 100 on RA. WD man, NAD. Chest clear, JVP 8cm. RR s1s2. Soft abdomen, well healed surgical scar. No edema or cord. Labs notable for WBC 7K, HCT 24, K+ 4.0, Cr 0.7.
```

**Patient 2**

```
An 82 man with chronic obstructive pulmonary disease, status-post bioprosthetic atrial valve replacement for atrial stenosis, atrial fibrillation with cardioversion, right nephrectomy for renal cell carcinoma, colon cancer status-post colectomy, presents with 9 day history of productive cough, fever and dyspnea.
```

**Patient 3**

```
A 52 year-old woman with chronic obstructive pulmonary disease and breast cancer who presented to an outside hospital with shortness of breath and back pain for several weeks. Had been seen by primary care provider for the back pain and treated with pain medications. Subsequently developed rash that was thought to be zoster. In the last few days, oxygen requirement increased and she had cough, fevers and sore throat. Noted oxygen saturation of 79% with ambulation at home. At outside hospital she was diagnosed with "multi-focal pneumonia." In the process of obtaining a computerized tomography scan, contrast infiltrated her arm with skin blistering and swelling. She was treated with ceftriaxone and transferred to current hospital.
```

**Patient 4**

```
A 63-year-old man comes to the clinic for recent unintentional weight loss. The patient also has epigastric discomfort after meals. He has no known medical problems and takes no medications. His blood pressure is 130/75 and pulse rate is 88/min. He is not febrile. Upper endoscopy shows a lesion in the stomach that shows typical features of diffuse-type adenocarcinoma presenting with signet ring cells that do not form glands.
```

### Written by a patient or caregiver

The assistant can also be used by patients and their families, who describe their situation in plain language.

```
Hi, I'm a 54 year old woman and I was diagnosed with breast cancer last month. The doctor said it's hormone positive and HER2 negative. I had surgery 2 weeks ago. Are there any studies I could join?
```

```
my dad is 72 and has prostate cancer that spread to his bones. hes been on lupron and they said its not working anymore. what trials are there for him
```

## 2. Clinical Trial Details

Ask for a trial by its NCT number to get its sponsor, status, phase, locations, dates, design, arm groups, interventions and primary outcomes.

```
Give me the details of trial NCT07100080.
```

```
What is NCT05534438 about?
```

## 3. Research Articles

Ask for research on a topic. The assistant searches PubMed and summarizes each article's abstract. You can include a number of articles and a date range.

```
Find research articles on osimertinib resistance in EGFR-mutated lung cancer.
```

```
Find 5 articles on CAR-T therapy for multiple myeloma published since 2023.
```
