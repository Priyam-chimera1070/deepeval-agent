"""Generate sample_payload_dxsynth.json aligned to the May 2026 DxSynthesizer prompt revision.

Structural rules baked into every run:
- 8 sections (no "Guideline Updates" section)
- Role-based section ordering (MA vs Dev)
- Single unified narrative per section (no Medical/Development sub-blocks)
- Clickable citations `([N](#ref-N))`
- References = numbered list with `<a id="ref-N"></a> FileName, Slide X-Y`
- No "not reported" in Conference at a Glance (rows omitted)
- No bullets — prose / numbered lists / tables only
- No `[CONFIDENCE: ...]` tag (deprecated)
- `---` separator between every two sections
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(__file__).parent / "sample_payload_dxsynth.json"


class Scenario:
    def __init__(self, conf, year, bu, areas, role, query, slug, themes,
                 drug, comparator, assay, metric_a, metric_b, metric_c, docs):
        self.conf = conf
        self.year = year
        self.bu = bu
        self.areas = areas
        self.role = role
        self.query = query
        self.slug = slug
        self.themes = themes
        self.drug = drug
        self.comparator = comparator
        self.assay = assay
        self.metric_a = metric_a
        self.metric_b = metric_b
        self.metric_c = metric_c
        self.docs = docs  # list of 5 tuples (file_name, descriptor, presenter, institution, session, track)


def fn(conf, year, kind="full-summary"):
    return f"{year}_{conf.lower()}_{kind}_api_obudx_v1.pdf"


SCENARIOS = [
    Scenario(
        conf="AACR", year=2025, bu="Oncology",
        areas="HER2-Breast Cancer, Lung Cancer", role="Medical Affairs",
        query="Brief on HER2-low Breast Cancer advances at AACR 2025 for Medical Affairs.",
        slug="aacr-her2low-ma",
        themes="liquid biopsy, ctDNA quantification, MRD detection, PI3Kα-mutant strategies, multiomic risk stratification",
        drug="ETX-636", comparator="inavolisib",
        assay="NeXT Personal MRD",
        metric_a="median PFS 15.7 vs 9.7 months at TF >1% cut-off",
        metric_b="sensitivity 97% and specificity 97% on the OncodeAi-Breast spectral panel",
        metric_c="LOD 1–3 ppm with PPV 80.7% under intra-individual methylation filtering",
        docs=[
            (fn("AACR", 2025), "Slide 21-24", "Xing Fan", "GeneScience Pharmaceuticals", "Preclinical Efficacy in Breast Cancer", "Both"),
            (fn("AACR", 2025, "ctdna-mrd"), "Slide 35-38", "Catherine Alix-Panabieres", "Universite de Montpellier", "Liquid Biopsy and MRD for Early Detection", "MA"),
            (fn("AACR", 2025), "Slide 53-54", "Robert B. Cameron", "University of Chicago", "ctDNA Shedding in NSCLC", "MA"),
            (fn("AACR", 2025, "pi3k-inhibitors"), "Slide 59-62", "Robert Koncar", "Ensem Therapeutics", "ETX-636 Allosteric PI3K-alpha Inhibition", "Both"),
            (fn("AACR", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "AACR 2025 Conference Overview", "Both"),
        ]),
    Scenario(
        conf="ASCO", year=2025, bu="Oncology",
        areas="Colorectal Cancer, Pancreatic Cancer", role="Medical Affairs",
        query="Summarize ASCO 2025 GI Oncology updates for Medical Affairs.",
        slug="asco-gi-ma",
        themes="neoadjuvant immunotherapy, KRAS G12C/G12D inhibition, ctDNA-guided adjuvant escalation, MSI-H biology",
        drug="Adagrasib", comparator="Sotorasib",
        assay="Signatera tumor-informed ctDNA",
        metric_a="DFS HR 0.38 (95% CI 0.21–0.69) in ctDNA-positive resected stage III CRC",
        metric_b="sensitivity 94.2% at 4 weeks post-op and specificity 98.0%",
        metric_c="LOD 0.01% VAF with mean panel size 16 patient-specific variants",
        docs=[
            (fn("ASCO", 2025), "Slide 12-15", "Heinz-Josef Lenz", "USC Norris", "GI Oncology Plenary", "MA"),
            (fn("ASCO", 2025, "krasg12c"), "Slide 28-31", "Eileen O'Reilly", "Memorial Sloan Kettering", "KRAS-Directed Therapies", "Both"),
            (fn("ASCO", 2025, "ctdna-mrd"), "Slide 44-47", "Michael Overman", "MD Anderson", "ctDNA-Guided Adjuvant Trials", "MA"),
            (fn("ASCO", 2025), "Slide 62-64", "Various", "Multi-institutional", "GI Cancers Real-World Evidence", "MA"),
            (fn("ASCO", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "ASCO 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="ESMO", year=2025, bu="Oncology",
        areas="NSCLC, SCLC", role="Development",
        query="Develop a brief on ESMO 2025 Lung Cancer pipeline for Development.",
        slug="esmo-lung-dev",
        themes="ADC pipeline expansion, EGFR exon20 inhibitors, DLL3 bispecific T-cell engagers in SCLC, perioperative IO",
        drug="Datopotamab deruxtecan", comparator="docetaxel",
        assay="Guardant Reveal tumor-naive ctDNA",
        metric_a="ORR 38.2% (95% CI 30.4–46.5) in 2L+ EGFR-mutant NSCLC",
        metric_b="sensitivity 88.5% and specificity 99.1% across stage I-III NSCLC",
        metric_c="LOD 0.025% VAF on a fixed 500-gene panel with median TAT 7 days",
        docs=[
            (fn("ESMO", 2025), "Slide 18-21", "Solange Peters", "CHUV Lausanne", "Lung Cancer Plenary", "Dev"),
            (fn("ESMO", 2025, "adc-pipeline"), "Slide 33-37", "Pasi Janne", "Dana-Farber", "ADC Development in NSCLC", "Dev"),
            (fn("ESMO", 2025, "sclc"), "Slide 49-52", "Charles Rudin", "Memorial Sloan Kettering", "DLL3 Bispecifics in SCLC", "Dev"),
            (fn("ESMO", 2025), "Slide 64-66", "Various", "Multi-institutional", "Tumor-Naive ctDNA Symposium", "Dev"),
            (fn("ESMO", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "ESMO 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="ASH", year=2024, bu="Oncology",
        areas="Multiple Myeloma, DLBCL", role="Medical Affairs",
        query="ASH 2024 Hematology highlights for Medical Affairs.",
        slug="ash-heme-ma",
        themes="BCMA bispecifics, CAR-T sequencing, MRD-negativity as regulatory endpoint, T-cell engager safety",
        drug="Teclistamab", comparator="Talquetamab",
        assay="clonoSEQ NGS-MRD",
        metric_a="ORR 63.0% with median DOR 18.4 months in triple-class-refractory MM",
        metric_b="MRD sensitivity 1 cell in 10^6 nucleated cells (10^-6)",
        metric_c="grade >=3 CRS 0.6% and ICANS 3.0%",
        docs=[
            (fn("ASH", 2024), "Slide 14-17", "Saad Usmani", "Memorial Sloan Kettering", "Myeloma Plenary", "MA"),
            (fn("ASH", 2024, "bispecifics"), "Slide 29-32", "Krina Patel", "MD Anderson", "BCMA Bispecific Real-World Data", "MA"),
            (fn("ASH", 2024, "lymphoma"), "Slide 46-49", "Catherine Diefenbach", "NYU Langone", "DLBCL Late-Breaking Abstracts", "MA"),
            (fn("ASH", 2024), "Slide 58-60", "Various", "Multi-institutional", "MRD Endpoints Workshop", "Both"),
            (fn("ASH", 2024, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "ASH 2024 Overview", "Both"),
        ]),
    Scenario(
        conf="AHA", year=2025, bu="Cardiovascular",
        areas="Heart Failure, ASCVD", role="Medical Affairs",
        query="AHA 2025 cardiovascular outcomes brief for Medical Affairs.",
        slug="aha-cv-ma",
        themes="GLP-1 cardiovascular benefits, Lp(a) lowering, SGLT2 inhibition in HFpEF, AI-ECG screening",
        drug="Tirzepatide", comparator="semaglutide",
        assay="high-sensitivity Troponin I",
        metric_a="MACE HR 0.78 (95% CI 0.69–0.88) over 36 months",
        metric_b="LOD 1.2 ng/L at the 99th-percentile cut-off of 14 ng/L",
        metric_c="HFpEF hospitalization reduction 25.8% versus placebo",
        docs=[
            (fn("AHA", 2025), "Slide 9-12", "Christie Ballantyne", "Baylor College of Medicine", "Late-Breaking Clinical Trials I", "MA"),
            (fn("AHA", 2025, "hfpef"), "Slide 24-27", "Javed Butler", "Baylor Scott and White", "HFpEF Outcomes", "MA"),
            (fn("AHA", 2025, "biomarkers"), "Slide 39-42", "Marc Pfeffer", "Brigham and Women's", "Biomarker-Guided Therapy", "Both"),
            (fn("AHA", 2025), "Slide 55-56", "Various", "Multi-institutional", "Lp(a) Lowering Workshop", "MA"),
            (fn("AHA", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "AHA 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="ADA", year=2025, bu="Diabetes",
        areas="Type 2 Diabetes, Obesity", role="Medical Affairs",
        query="ADA 2025 Diabetes and Obesity brief for Medical Affairs.",
        slug="ada-t2d-ma",
        themes="incretin-based therapies, oral GLP-1, dual and triple agonists, MASH co-benefits, CGM-derived endpoints",
        drug="Retatrutide", comparator="tirzepatide",
        assay="continuous glucose monitoring time-in-range",
        metric_a="mean weight loss 24.2% at 48 weeks on the 12 mg dose",
        metric_b="HbA1c reduction 2.16% from baseline 8.3%",
        metric_c="time-in-range improvement of 18.6 percentage points",
        docs=[
            (fn("ADA", 2025), "Slide 11-14", "Julio Rosenstock", "Velocity Clinical Research", "Late-Breaking Trials", "MA"),
            (fn("ADA", 2025, "incretins"), "Slide 26-29", "Daniel Drucker", "Lunenfeld-Tanenbaum", "Incretin Pharmacology Update", "Both"),
            (fn("ADA", 2025, "obesity"), "Slide 41-44", "Carel le Roux", "University College Dublin", "Obesity Outcomes", "MA"),
            (fn("ADA", 2025), "Slide 57-58", "Various", "Multi-institutional", "CGM Endpoint Symposium", "Both"),
            (fn("ADA", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "ADA 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="AAN", year=2025, bu="Neuroscience",
        areas="Alzheimer's Disease, Multiple Sclerosis", role="Medical Affairs",
        query="AAN 2025 Neurology brief for Medical Affairs.",
        slug="aan-neuro-ma",
        themes="anti-amyloid antibodies, plasma p-tau217 screening, BTK inhibitors in MS, ARIA risk stratification",
        drug="Donanemab", comparator="lecanemab",
        assay="Plasma p-tau217 immunoassay",
        metric_a="iADRS slowing 35.1% versus placebo at 76 weeks (p<0.001)",
        metric_b="sensitivity 96.0% and specificity 81.5% for amyloid-PET positivity",
        metric_c="ARIA-E incidence 24.0% versus 12.6% with comparator",
        docs=[
            (fn("AAN", 2025), "Slide 13-16", "Reisa Sperling", "Brigham and Women's", "Plenary on Anti-Amyloid Therapy", "MA"),
            (fn("AAN", 2025, "biomarkers"), "Slide 27-30", "Randall Bateman", "Washington University", "Plasma Biomarker Adoption", "Both"),
            (fn("AAN", 2025, "ms"), "Slide 42-45", "Stephen Hauser", "UCSF", "BTK Inhibitors in MS", "MA"),
            (fn("AAN", 2025), "Slide 56-57", "Stephen Salloway", "Butler Hospital", "ARIA Risk Management", "MA"),
            (fn("AAN", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "AAN 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="AAD", year=2025, bu="Immunology",
        areas="Atopic Dermatitis, Psoriasis", role="Medical Affairs",
        query="AAD 2025 Dermatology immunology brief for Medical Affairs.",
        slug="aad-derm-ma",
        themes="IL-13 selective inhibition, OX40 pathway, oral TYK2 inhibitors, JAK safety re-evaluation",
        drug="Lebrikizumab", comparator="dupilumab",
        assay="EASI-75 response endpoint",
        metric_a="EASI-75 response 58.8% at week 16 (95% CI 53.0–64.6)",
        metric_b="IGA 0/1 response 41.2% versus 14.4% placebo",
        metric_c="conjunctivitis incidence 6.9% versus 1.8% placebo",
        docs=[
            (fn("AAD", 2025), "Slide 10-13", "Emma Guttman-Yassky", "Mount Sinai", "AD Plenary", "MA"),
            (fn("AAD", 2025, "il13"), "Slide 25-28", "Jonathan Silverberg", "GW University", "IL-13 Pathway Update", "MA"),
            (fn("AAD", 2025, "psoriasis"), "Slide 40-43", "Andrew Blauvelt", "Oregon Medical Research", "Psoriasis Late-Breakers", "MA"),
            (fn("AAD", 2025), "Slide 54-55", "Various", "Multi-institutional", "TYK2 Inhibitor Workshop", "Both"),
            (fn("AAD", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "AAD 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="ACR", year=2024, bu="Immunology",
        areas="Rheumatoid Arthritis, Lupus", role="Medical Affairs",
        query="ACR 2024 Rheumatology brief for Medical Affairs.",
        slug="acr-rheum-ma",
        themes="CAR-T in autoimmune disease, IL-23 in axSpA, anifrolumab real-world data, IFN signature stratification",
        drug="Anifrolumab", comparator="belimumab",
        assay="Type-I IFN gene signature",
        metric_a="BICLA response 47.8% versus 31.5% placebo at week 52",
        metric_b="LLDAS attainment 30.0% versus 19.0% at 12 months",
        metric_c="serious infection rate 4.0 versus 4.5 per 100 patient-years",
        docs=[
            (fn("ACR", 2024), "Slide 8-11", "Richard Furie", "Northwell Health", "Lupus Plenary", "MA"),
            (fn("ACR", 2024, "cart"), "Slide 23-26", "Georg Schett", "Erlangen", "CAR-T in Autoimmunity", "Both"),
            (fn("ACR", 2024, "axspa"), "Slide 38-41", "Iain McInnes", "University of Glasgow", "axSpA Pathway Update", "MA"),
            (fn("ACR", 2024), "Slide 52-53", "Various", "Multi-institutional", "IFN Signature Workshop", "Both"),
            (fn("ACR", 2024, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "ACR 2024 Overview", "Both"),
        ]),
    Scenario(
        conf="ATS", year=2025, bu="Respiratory",
        areas="Asthma, COPD", role="Medical Affairs",
        query="ATS 2025 Respiratory brief for Medical Affairs.",
        slug="ats-resp-ma",
        themes="TSLP biology in severe asthma, biologics in COPD, eosinophil-driven phenotyping, FeNO biomarker uptake",
        drug="Tezepelumab", comparator="benralizumab",
        assay="FeNO point-of-care assay",
        metric_a="annualised exacerbation rate ratio 0.44 (95% CI 0.37–0.53)",
        metric_b="FeNO cut-off >=25 ppb enriched 2.2-fold greater FEV1 response",
        metric_c="ACQ-6 reduction -1.55 versus -1.22 placebo",
        docs=[
            (fn("ATS", 2025), "Slide 9-12", "Sally Wenzel", "University of Pittsburgh", "Severe Asthma Symposium", "MA"),
            (fn("ATS", 2025, "copd"), "Slide 24-27", "Klaus Rabe", "LungenClinic Grosshansdorf", "Biologics in COPD", "MA"),
            (fn("ATS", 2025, "biomarkers"), "Slide 38-41", "Mona Bafadhel", "King's College London", "Eosinophil-Driven Phenotyping", "Both"),
            (fn("ATS", 2025), "Slide 52-53", "Various", "Multi-institutional", "FeNO Implementation Workshop", "Both"),
            (fn("ATS", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "ATS 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="AACR", year=2024, bu="Oncology",
        areas="Prostate Cancer, Bladder Cancer", role="Development",
        query="AACR 2024 GU Oncology pipeline brief for Development.",
        slug="aacr-gu-dev",
        themes="PSMA radioligands, AR degraders, FGFR pipeline in urothelial cancer, AR-V7 ctDNA monitoring",
        drug="ARV-766", comparator="enzalutamide",
        assay="AR-V7 ctDNA digital PCR",
        metric_a="PSA50 response 45.0% in heavily pre-treated mCRPC",
        metric_b="sensitivity 95.0% and specificity 98.5% for AR-V7 detection",
        metric_c="LOD 0.05% VAF with TAT 5 business days",
        docs=[
            (fn("AACR", 2024), "Slide 14-17", "Johann de Bono", "Royal Marsden", "GU Plenary", "Dev"),
            (fn("AACR", 2024, "psma"), "Slide 29-32", "Karim Fizazi", "Gustave Roussy", "PSMA Radioligand Pipeline", "Dev"),
            (fn("AACR", 2024, "urothelial"), "Slide 44-47", "Andrea Necchi", "Vita-Salute San Raffaele", "FGFR Bladder Cancer", "Dev"),
            (fn("AACR", 2024), "Slide 59-60", "Various", "Multi-institutional", "ctDNA in GU Cancers", "Dev"),
            (fn("AACR", 2024, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "AACR 2024 Overview", "Both"),
        ]),
    Scenario(
        conf="ASCO", year=2024, bu="Oncology",
        areas="Melanoma, Renal Cell Carcinoma", role="Medical Affairs",
        query="ASCO 2024 GU/Melanoma immunotherapy brief for Medical Affairs.",
        slug="asco-melrcc-ma",
        themes="TIL therapy, LAG-3 combinations, perioperative IO in RCC, PD-L1 22C3 standardization",
        drug="Lifileucel", comparator="nivolumab plus relatlimab",
        assay="PD-L1 IHC 22C3 companion diagnostic",
        metric_a="ORR 31.4% with median DOR not yet reached at 18.6 months",
        metric_b="PD-L1 CPS >=10 enriched response 1.9-fold",
        metric_c="grade >=3 treatment-related adverse events 33.1%",
        docs=[
            (fn("ASCO", 2024), "Slide 12-15", "Jeffrey Weber", "NYU Langone", "Melanoma Plenary", "MA"),
            (fn("ASCO", 2024, "rcc"), "Slide 27-30", "Toni Choueiri", "Dana-Farber", "Perioperative IO in RCC", "MA"),
            (fn("ASCO", 2024, "til"), "Slide 41-44", "Georgina Long", "Melanoma Institute Australia", "TIL Therapy Real-World Evidence", "MA"),
            (fn("ASCO", 2024), "Slide 55-56", "Various", "Multi-institutional", "PD-L1 Standardization Workshop", "Both"),
            (fn("ASCO", 2024, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "ASCO 2024 Overview", "Both"),
        ]),
    Scenario(
        conf="ESMO", year=2024, bu="Oncology",
        areas="Gastric Cancer, Esophageal Cancer", role="Medical Affairs",
        query="ESMO 2024 Upper GI brief for Medical Affairs.",
        slug="esmo-uppergi-ma",
        themes="Claudin 18.2 targeting, FGFR2b ADCs, IO in HER2+ gastric cancer, MSI-H subgroup outcomes",
        drug="Zolbetuximab", comparator="trastuzumab deruxtecan",
        assay="Claudin 18.2 IHC 43-14A",
        metric_a="OS HR 0.75 (95% CI 0.60–0.94) in CLDN18.2-positive gastric cancer",
        metric_b="IHC >=75% membranous staining cut-off enriched response 2.0-fold",
        metric_c="median PFS 8.8 versus 6.4 months",
        docs=[
            (fn("ESMO", 2024), "Slide 11-14", "Florian Lordick", "University of Leipzig", "Gastric Cancer Plenary", "MA"),
            (fn("ESMO", 2024, "cldn182"), "Slide 26-29", "Yelena Janjigian", "Memorial Sloan Kettering", "Claudin 18.2 Targeting", "MA"),
            (fn("ESMO", 2024, "esophageal"), "Slide 40-43", "Kohei Shitara", "National Cancer Center East", "Esophageal Cancer Late-Breakers", "MA"),
            (fn("ESMO", 2024), "Slide 54-55", "Various", "Multi-institutional", "IHC Standardization Workshop", "Both"),
            (fn("ESMO", 2024, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "ESMO 2024 Overview", "Both"),
        ]),
    Scenario(
        conf="EHA", year=2025, bu="Oncology",
        areas="AML, MDS", role="Development",
        query="EHA 2025 Myeloid pipeline brief for Development.",
        slug="eha-myeloid-dev",
        themes="menin inhibitors in NPM1/KMT2A AML, MRD-driven trial design, IDH combinations, flow-cytometry MRD",
        drug="Revumenib", comparator="ziftomenib",
        assay="multiparameter flow-cytometry MRD",
        metric_a="CR/CRh rate 30.0% in heavily pre-treated KMT2A-rearranged AML",
        metric_b="MRD sensitivity 10^-4 on an 8-color panel",
        metric_c="median DOR 6.4 months with median TTR 1.9 months",
        docs=[
            (fn("EHA", 2025), "Slide 13-16", "Eytan Stein", "Memorial Sloan Kettering", "AML Plenary", "Dev"),
            (fn("EHA", 2025, "menin"), "Slide 27-30", "Ghayas Issa", "MD Anderson", "Menin Inhibitor Development", "Dev"),
            (fn("EHA", 2025, "mds"), "Slide 42-45", "Andrew Wei", "Peter MacCallum", "MDS Late-Breakers", "Dev"),
            (fn("EHA", 2025), "Slide 57-58", "Various", "Multi-institutional", "MRD Endpoint Workshop", "Dev"),
            (fn("EHA", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "EHA 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="CTAD", year=2025, bu="Neuroscience",
        areas="Alzheimer's Disease", role="Development",
        query="CTAD 2025 AD development pipeline brief for Development.",
        slug="ctad-ad-dev",
        themes="preclinical AD trials, blood biomarker screening pipelines, anti-tau antibodies, ADRD trial endpoints",
        drug="Remternetug", comparator="donanemab",
        assay="Plasma Abeta42/40 mass spectrometry",
        metric_a="amyloid plaque clearance to <24.1 centiloids in 75.8% of participants at 12 months",
        metric_b="sensitivity 93.0% and specificity 90.0% for amyloid PET status",
        metric_c="precision CV <8% across reference labs",
        docs=[
            (fn("CTAD", 2025), "Slide 10-13", "Randall Bateman", "Washington University", "AD Plenary", "Dev"),
            (fn("CTAD", 2025, "biomarkers"), "Slide 24-27", "Eric Reiman", "Banner Alzheimer's Institute", "Blood Biomarker Pipeline", "Dev"),
            (fn("CTAD", 2025, "tau"), "Slide 39-42", "Bart De Strooper", "UK DRI", "Anti-Tau Antibody Pipeline", "Dev"),
            (fn("CTAD", 2025), "Slide 53-54", "Various", "Multi-institutional", "Preclinical AD Trial Workshop", "Dev"),
            (fn("CTAD", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "CTAD 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="DDW", year=2025, bu="Immunology",
        areas="IBD, Eosinophilic Esophagitis", role="Medical Affairs",
        query="DDW 2025 GI immunology brief for Medical Affairs.",
        slug="ddw-gi-ma",
        themes="selective IL-23 inhibition, oral S1P modulators in UC, IL-13 in EoE, fecal biomarker integration",
        drug="Mirikizumab", comparator="risankizumab",
        assay="Fecal calprotectin lateral-flow",
        metric_a="clinical remission 49.9% at week 12 versus 25.1% placebo",
        metric_b="endoscopic improvement 61.0% versus 36.5% placebo",
        metric_c="calprotectin <150 ug/g correlated with mucosal healing in 78.4% of patients",
        docs=[
            (fn("DDW", 2025), "Slide 11-14", "William Sandborn", "UC San Diego", "IBD Plenary", "MA"),
            (fn("DDW", 2025, "il23"), "Slide 26-29", "Bruce Sands", "Mount Sinai", "IL-23 Pathway Update", "MA"),
            (fn("DDW", 2025, "eoe"), "Slide 41-44", "Evan Dellon", "UNC Chapel Hill", "EoE Late-Breakers", "MA"),
            (fn("DDW", 2025), "Slide 55-56", "Various", "Multi-institutional", "S1P Modulator Workshop", "Both"),
            (fn("DDW", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "DDW 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="ECTRIMS", year=2025, bu="Neuroscience",
        areas="Multiple Sclerosis", role="Medical Affairs",
        query="ECTRIMS 2025 MS therapeutics brief for Medical Affairs.",
        slug="ectrims-ms-ma",
        themes="BTK inhibitors in progressive MS, anti-CD20 sequencing, NfL as treatment-response biomarker, smouldering MS",
        drug="Tolebrutinib", comparator="ocrelizumab",
        assay="Serum Neurofilament Light",
        metric_a="6-month confirmed disability progression HR 0.69 (95% CI 0.55–0.88)",
        metric_b="serum NfL reduction 38.4% from baseline at 24 weeks",
        metric_c="ALT elevation >3x ULN in 4.0% of patients",
        docs=[
            (fn("ECTRIMS", 2025), "Slide 12-15", "Xavier Montalban", "Vall d'Hebron", "MS Plenary", "MA"),
            (fn("ECTRIMS", 2025, "btk"), "Slide 27-30", "Amit Bar-Or", "Penn Medicine", "BTK Inhibitor Update", "MA"),
            (fn("ECTRIMS", 2025, "nfl"), "Slide 42-45", "Gavin Giovannoni", "Queen Mary London", "NfL Biomarker Integration", "Both"),
            (fn("ECTRIMS", 2025), "Slide 56-57", "Various", "Multi-institutional", "Smouldering MS Workshop", "MA"),
            (fn("ECTRIMS", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "ECTRIMS 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="WCLC", year=2025, bu="Oncology",
        areas="NSCLC", role="Medical Affairs",
        query="WCLC 2025 Lung Cancer brief for Medical Affairs.",
        slug="wclc-nsclc-ma",
        themes="perioperative IO, EGFR/MET ADCs, KRAS G12D pipeline, ctDNA MRD-guided adjuvant decisions",
        drug="Patritumab deruxtecan", comparator="amivantamab",
        assay="ctDNA MRD assay tumor-naive",
        metric_a="ORR 30.1% in EGFR-mutant NSCLC after osimertinib failure",
        metric_b="MRD sensitivity 90.0% at 4 weeks post-resection",
        metric_c="median DOR 7.0 months at the recommended phase 2 dose",
        docs=[
            (fn("WCLC", 2025), "Slide 10-13", "Solange Peters", "CHUV Lausanne", "Lung Cancer Plenary", "MA"),
            (fn("WCLC", 2025, "egfr"), "Slide 25-28", "Tony Mok", "Chinese University of Hong Kong", "EGFR-Directed Therapies", "MA"),
            (fn("WCLC", 2025, "perio"), "Slide 40-43", "Suresh Ramalingam", "Emory Winship", "Perioperative IO", "MA"),
            (fn("WCLC", 2025), "Slide 54-55", "Various", "Multi-institutional", "ctDNA MRD Workshop", "Both"),
            (fn("WCLC", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "WCLC 2025 Overview", "Both"),
        ]),
    Scenario(
        conf="SABCS", year=2024, bu="Oncology",
        areas="HR+ Breast Cancer", role="Medical Affairs",
        query="SABCS 2024 HR+ Breast Cancer brief for Medical Affairs.",
        slug="sabcs-hrpos-ma",
        themes="oral SERDs, CDK4/6 inhibitors in early breast cancer, PI3Kalpha-mutant strategies, ESR1 mutation monitoring",
        drug="Elacestrant", comparator="fulvestrant",
        assay="ESR1 mutation ctDNA digital PCR",
        metric_a="PFS HR 0.55 (95% CI 0.39–0.77) in ESR1-mutant population",
        metric_b="LOD 0.5% VAF on an 11-variant panel",
        metric_c="median PFS 3.8 versus 1.9 months",
        docs=[
            (fn("SABCS", 2024), "Slide 9-12", "Aditya Bardia", "UCLA", "Breast Cancer Plenary", "MA"),
            (fn("SABCS", 2024, "serd"), "Slide 24-27", "Komal Jhaveri", "Memorial Sloan Kettering", "Oral SERD Pipeline", "MA"),
            (fn("SABCS", 2024, "cdk46"), "Slide 39-42", "Hope Rugo", "UCSF", "CDK4/6 in Early Breast Cancer", "MA"),
            (fn("SABCS", 2024), "Slide 53-54", "Various", "Multi-institutional", "ESR1 ctDNA Workshop", "Both"),
            (fn("SABCS", 2024, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "SABCS 2024 Overview", "Both"),
        ]),
    Scenario(
        conf="ENDO", year=2025, bu="Diabetes",
        areas="Obesity, MASH", role="Development",
        query="ENDO 2025 Obesity and MASH pipeline brief for Development.",
        slug="endo-obesity-dev",
        themes="amylin analogs, glucagon co-agonism, MASH biomarker development, MRI-based liver fat quantification",
        drug="CagriSema", comparator="semaglutide",
        assay="MRI-PDFF liver fat quantification",
        metric_a="mean weight loss 22.7% at 68 weeks (intent-to-treat)",
        metric_b="MRI-PDFF reduction >=30% in 71.0% of MASH patients",
        metric_c="ALT normalisation in 56.3% of treated patients",
        docs=[
            (fn("ENDO", 2025), "Slide 10-13", "Lee Kaplan", "Mass General", "Obesity Plenary", "Dev"),
            (fn("ENDO", 2025, "mash"), "Slide 24-27", "Arun Sanyal", "VCU", "MASH Biomarker Pipeline", "Dev"),
            (fn("ENDO", 2025, "amylin"), "Slide 39-42", "Caroline Apovian", "Brigham and Women's", "Amylin Analog Development", "Dev"),
            (fn("ENDO", 2025), "Slide 53-54", "Various", "Multi-institutional", "Glucagon Co-Agonism Workshop", "Dev"),
            (fn("ENDO", 2025, "executive-overview"), "Conference Overview", "Various", "Multi-institutional", "ENDO 2025 Overview", "Both"),
        ]),
]

assert len(SCENARIOS) == 20


# ---------------------------------------------------------------------------
# Section builders.
# ---------------------------------------------------------------------------
def c(n: int) -> str:
    return f"([{n}](#ref-{n}))"


def sec1_glance(s: Scenario) -> str:
    return (
        f"### 1. CONFERENCE AT A GLANCE\n\n"
        f"**{s.conf} {s.year} — {s.bu} — {s.areas}**\n"
        f"Role: {s.role}\n\n"
        f"| Field | Value |\n"
        f"|-------|-------|\n"
        f"| Exhibiting Companies | Eli Lilly, {s.docs[0][3]}, {s.docs[1][3]}, {s.docs[2][3]}, and other multi-institutional collaborators {c(5)} |\n"
        f"| Corporate Workshops | Dedicated workshops on {s.themes.split(',')[0].strip()} and {s.themes.split(',')[-1].strip()} with technical Q+A sessions {c(5)} |\n"
        f"| Key Themes of the Congress | {s.themes} {c(5)} |\n\n"
        f"The {s.conf} {s.year} congress focused heavily on {s.themes.split(',')[0].strip()} and {s.themes.split(',')[1].strip()}, with translational sessions dominating the late-breaking abstract slots {c(1)}. "
        f"Discussion across plenary sessions emphasised the maturing role of biomarker-guided patient selection in {s.areas.split(',')[0].strip()} and the operational requirements that emerging assays place on routine practice {c(2)}. "
        f"Strategic dialogue extended into the implications for assay co-development, regulatory submission timing, and patient-access pathways {c(3)}.\n\n"
        f"---\n"
    )


def sec_exec(s: Scenario) -> str:
    return (
        f"### 2. EXECUTIVE SUMMARY\n\n"
        f"The most clinically significant finding at {s.conf} {s.year} was the demonstration that {s.drug} produced {s.metric_a} in the {s.areas.split(',')[0].strip()} population studied by {s.docs[0][2]} and colleagues {c(1)}. "
        f"In parallel, {s.docs[1][2]} presented data showing that the {s.assay} platform delivered {s.metric_b} across the validation cohort, reinforcing the role of this biomarker in patient stratification {c(2)}. "
        f"The combination of these clinical and analytical signals was reflected in updated practice discussions, with {s.docs[2][2]} highlighting how early biomarker capture changes the adjuvant decision window in {s.areas.split(',')[-1].strip()} {c(3)}. "
        f"Across all plenary slots, the underlying message was that {s.areas.split(',')[0].strip()} care is shifting from empiric to molecularly directed sequencing {c(5)}.\n\n"
        f"Biomarker-driven recommendations expanded during the congress, with several sessions referencing the {s.assay} performance characteristics — {s.metric_b} — as the basis for incorporating the assay into routine practice {c(2)}. "
        f"Speakers underlined that {s.metric_c} provides the analytical headroom needed to support guideline-grade adoption, with implications for both companion-diagnostic strategy and laboratory workflows {c(4)}. "
        f"{s.docs[2][2]} explicitly linked persistent biomarker positivity to therapeutic intensification, signalling a meaningful change in patient-management algorithms {c(3)}. "
        f"These positions were echoed in the implementation workshop, which catalogued the analytical and pre-analytical requirements for site adoption {c(5)}.\n\n"
        f"On the competitive landscape, {s.drug} was contrasted directly with {s.comparator} in head-to-head and indirect-comparison datasets, with the new agent delivering {s.metric_a} {c(4)}. "
        f"{s.docs[1][2]} positioned this as a competitive inflection for {s.areas.split(',')[0].strip()} development, particularly for the cohort defined by the {s.assay} {c(2)}. "
        f"The platform discussion highlighted that Lilly's partnered-assay strategy now operates against a comparator field where {s.metric_c} is the new analytical benchmark {c(4)}. "
        f"Real-world evidence presented in the late-breaking session further reinforced that early intensification under biomarker control improves outcomes {c(3)}.\n\n"
        f"Looking forward, several presentations flagged ongoing unmet needs in {s.areas.split(',')[-1].strip()}, particularly around inter-laboratory reproducibility and the absence of standardised reporting templates {c(5)}. "
        f"{s.docs[3][2]} pointed to the need for prospective registry-based confirmation of the {s.metric_a} signal in routine practice {c(4)}. "
        f"Forward-looking pipeline mentions included next-generation degraders and dual-mechanism platforms expected to enter pivotal evaluation within the coming year {c(2)}. "
        f"The cumulative direction of {s.conf} {s.year} positions {s.areas.split(',')[0].strip()} as the proving ground for biomarker-directed, assay-coupled therapeutic strategy {c(1)}.\n\n"
        f"---\n"
    )


def _clinical_block(s: Scenario, heading_idx: int) -> str:
    return (
        f"### {heading_idx}. CLINICAL DATA HIGHLIGHTS\n\n"
        f"#### {s.drug} pivotal dataset in {s.areas.split(',')[0].strip()}\n\n"
        f"The pivotal dataset presented by {s.docs[0][2]} ({s.docs[0][3]}) reported {s.metric_a} in the {s.areas.split(',')[0].strip()} cohort, with the primary endpoint reached at the pre-specified interim analysis {c(1)}. "
        f"Subgroup analyses stratified by the {s.assay} biomarker status confirmed that the magnitude of benefit tracked closely with marker positivity, reinforcing the case for marker-directed prescribing {c(2)}. "
        f"Safety data were consistent with the known class profile, with no new signals identified during the reporting window {c(1)}. "
        f"The presenter framed the data as practice-informing for the molecularly defined subgroup but emphasised that confirmatory phase 3 readouts remain the gating step {c(1)}.\n\n"
        f"#### {s.assay} analytical validation\n\n"
        f"Analytical validation of the {s.assay} platform reported {s.metric_b}, with {s.metric_c} setting the operational floor for prospective application {c(2)}. "
        f"{s.docs[1][2]} reviewed concordance against tissue-based reference methods, with sample-type comparisons demonstrating that plasma-derived inputs were non-inferior to tissue across the validation cohort {c(2)}. "
        f"Turn-around-time and quantity-not-sufficient rates were benchmarked against the prior generation of assays in the same workflow, supporting routine-laboratory implementation {c(5)}.\n\n"
        f"#### Real-world evidence and adjuvant decision-making\n\n"
        f"Real-world data presented by {s.docs[2][2]} ({s.docs[2][3]}) corroborated the registrational signal, with the magnitude of effect preserved across the registry-defined population {c(3)}. "
        f"Persistent biomarker positivity at the post-treatment landmark was associated with a higher rate of subsequent relapse, supporting an intensification pathway anchored to the assay output {c(3)}. "
        f"{s.docs[3][2]} extended the analysis to inter-laboratory reproducibility, reporting that variation across reference sites remained within the pre-specified acceptance band {c(4)}.\n\n"
        f"---\n"
    )


def _competitive_block(s: Scenario, heading_idx: int) -> str:
    return (
        f"### {heading_idx}. COMPETITIVE LANDSCAPE & EMERGING PLATFORMS / NEW TECHNOLOGIES\n\n"
        f"#### {s.comparator} comparator dataset\n\n"
        f"{s.comparator} remains the principal external comparator for {s.drug} in {s.areas.split(',')[0].strip()}, and the indirect-comparison analysis presented by {s.docs[0][2]} positioned the new agent against the prior class benchmark {c(1)}. "
        f"Head-to-head data were not yet available, but matched-cohort analyses indicated that the {s.metric_a} differential was preserved after baseline-characteristic adjustment {c(4)}. "
        f"Presenters cautioned that real-world confirmation in routine settings remains the critical next step for definitive class positioning {c(2)}.\n\n"
        f"#### Emerging platforms and AI-enabled interpretation\n\n"
        f"Among emerging platforms, the {s.assay} system was highlighted as a benchmark for analytical performance at {s.metric_c}, with a parallel AI-assisted interpretation layer described by {s.docs[1][2]} {c(2)}. "
        f"New CE-IVD market entrants in the same category were positioned as direct competitors for Lilly's partnered companion diagnostic, with the head-to-head specifications presented in the analytical workshop {c(5)}. "
        f"The CDx landscape shift documented at the congress moves the analytical performance floor upward and tightens the validation requirements for second-generation entrants {c(4)}.\n\n"
        f"#### Unmet needs surfaced relative to current pipeline\n\n"
        f"{s.docs[3][2]} highlighted that unmet need persists for patients who progress on the current standard despite biomarker negativity, an indication for which Lilly's pipeline has visibility but no late-stage asset {c(4)}. "
        f"The congress consensus indicated that next-generation platforms able to combine ultra-sensitive detection with broad mutation tracking will define the competitive ceiling over the coming cycle {c(3)}.\n\n"
        f"---\n"
    )


def _assay_block(s: Scenario, heading_idx: int) -> str:
    sens_spec = s.metric_b
    if " and " in sens_spec:
        sens, spec = sens_spec.split(" and ", 1)
    else:
        sens, spec = sens_spec, "matched reference"
    return (
        f"### {heading_idx}. ASSAY INNOVATIONS & VAF\n\n"
        f"The {s.assay} platform was the central analytical asset discussed at {s.conf} {s.year}, delivering {s.metric_b} with {s.metric_c} as the validated operational envelope {c(2)}. "
        f"Patients with persistent biomarker positivity were identified as the population most likely to benefit from intensification under this assay, with {s.docs[2][2]} linking the analytical signal directly to the adjuvant decision pathway {c(3)}. "
        f"The platform also reduces sample-quantity-not-sufficient failures relative to the prior generation, with the analytical workshop reporting consistent performance across plasma and tissue inputs {c(5)}.\n\n"
        f"| Platform | Sensitivity | Specificity | VAF Threshold / LOD | Sample Type | Source |\n"
        f"|----------|-------------|-------------|---------------------|-------------|--------|\n"
        f"| {s.assay} | {sens} | {spec} | {s.metric_c} | Plasma | {c(2)} |\n"
        f"| Comparator next-generation assay | within validation envelope | within validation envelope | matched specification | Plasma | {c(4)} |\n\n"
        f"Beyond the table, {s.docs[3][2]} described the implementation workflow at reference sites, with inter-laboratory reproducibility CV maintained inside the pre-specified band and a defined re-test pathway for borderline calls {c(4)}. "
        f"Presenters and guideline-aligned reviewers concluded that the platform is now operationally ready for routine deployment in the {s.areas.split(',')[0].strip()} setting, with adoption pacing tied to laboratory accreditation cycles {c(5)}.\n\n"
        f"---\n"
    )


def sec_thought_leaders(s: Scenario, heading_idx: int) -> str:
    topics = [
        f"Pivotal data on {s.drug}",
        f"Validation of {s.assay}",
        "Real-world adjuvant decision-making",
        "Inter-laboratory reproducibility",
        "Conference-level overview",
    ]
    rows = "\n".join(
        f"| {i+1} | {d[2]} | {d[3]} | {topics[i]} | {d[5]} | {d[4]} | {s.year} |"
        for i, d in enumerate(s.docs)
    )
    return (
        f"### {heading_idx}. KEY THOUGHT LEADERS & PRESENTERS\n\n"
        f"| # | Name & Credentials | Institution | Topic Presented | Track | Session Title | Year |\n"
        f"|---|--------------------|-------------|------------------|-------|---------------|------|\n"
        f"{rows}\n\n"
        f"The most influential voices at {s.conf} {s.year} were {s.docs[0][2]} and {s.docs[1][2]}, whose linked clinical and analytical presentations defined the congress narrative {c(1)}. "
        f"{s.docs[2][2]} reinforced the practice-change implications through real-world data, while {s.docs[3][2]} anchored the implementation discussion {c(3)}. "
        f"Across institutions, the convergence of perspectives signalled an inflection in {s.areas.split(',')[0].strip()} {c(2)}.\n\n"
        f"---\n"
    )


def sec_takeaways(s: Scenario, heading_idx: int) -> str:
    return (
        f"### {heading_idx}. KEY TAKEAWAYS\n\n"
        f"1. {s.drug} delivered {s.metric_a} in the biomarker-defined {s.areas.split(',')[0].strip()} cohort — this repositions the agent as the leading molecularly directed option — adopt the data in upcoming medical-affairs field communications and prepare evidence packages for payer-access discussions {c(1)}.\n"
        f"2. {s.assay} validation at {s.metric_b} sets a new analytical benchmark for the category — laboratory networks should plan validation studies against this floor — engineer CDx partnership terms to lock the analytical specification before second-generation entrants close the gap {c(2)}.\n"
        f"3. Persistent biomarker positivity is now linked to adjuvant intensification per the real-world dataset — this shifts the adjuvant decision algorithm — align medical-affairs talking tracks and prepare clinician-education modules for the new pathway {c(3)}.\n"
        f"4. {s.metric_c} defines the operational envelope required for routine deployment — reference labs must benchmark internal performance to this specification — prioritise internal validation studies in the next two reporting cycles {c(4)}.\n"
        f"5. Indirect comparison against {s.comparator} indicates a preserved differential after adjustment — competitive positioning should anchor on the biomarker-defined subgroup — coordinate launch messaging with the global field-medical team to emphasise the marker-directed advantage {c(4)}.\n"
        f"6. CE-IVD market entrants in the same category are closing the analytical gap — validate the Lilly partnered assay against the new entrants — monitor regulatory submission cycles to identify timing windows for protective filings {c(5)}.\n"
        f"7. Inter-laboratory reproducibility CV remained within the pre-specified band across reference sites — this de-risks scaled deployment — launch site-level qualification studies in priority geographies during the next quarter {c(4)}.\n"
        f"8. Unmet need persists for biomarker-negative progressors after current standard of care — this is an open development opportunity — prioritise pipeline scouting and early-stage business-development engagement for assets active in this population {c(3)}.\n"
        f"9. Real-world evidence from the registry analysis corroborated the registrational signal — this strengthens the case for broader label discussion — build the regulatory narrative around the consolidated dataset for the next interaction window {c(3)}.\n"
        f"10. Forward-looking pipeline mentions flagged next-generation degraders and dual-mechanism platforms entering pivotal evaluation — monitor these readouts as competitive-intelligence priorities — position the Lilly portfolio response in the upcoming strategic-planning cycle {c(2)}.\n\n"
        f"---\n"
    )


def sec_references(s: Scenario) -> str:
    lines = ["### 8. REFERENCES\n"]
    for i, d in enumerate(s.docs, start=1):
        fname, descriptor = d[0], d[1]
        lines.append(f"{i}. <a id=\"ref-{i}\"></a> {fname}, {descriptor}")
    return "\n".join(lines) + "\n"


def build_output(s: Scenario) -> str:
    parts = [sec1_glance(s), sec_exec(s)]
    if s.role == "Medical Affairs":
        parts.append(_clinical_block(s, 3))
        parts.append(_assay_block(s, 4))
        parts.append(_competitive_block(s, 5))
    else:
        parts.append(_competitive_block(s, 3))
        parts.append(_assay_block(s, 4))
        parts.append(_clinical_block(s, 5))
    parts.append(sec_thought_leaders(s, 6))
    parts.append(sec_takeaways(s, 7))
    parts.append(sec_references(s))
    return "".join(parts)


def main() -> None:
    base_ts = datetime(2026, 5, 11, 15, 2, 0)
    runs = []
    for idx, s in enumerate(SCENARIOS, start=1):
        ts = (base_ts + timedelta(minutes=2 * (idx - 1))).strftime("%Y-%m-%dT%H:%M:%SZ")
        runs.append({
            "run_id": f"run-{idx:02d}-{s.slug}",
            "timestamp": ts,
            "user_query": s.query,
            "input": (f"Conference: {s.conf} | Year: {s.year} | Business Unit: {s.bu} | "
                      f"Area of Interest: {s.areas} | Role: {s.role}"),
            "output": build_output(s),
        })

    payload = {
        "agent_name": "DxSynthesizer",
        "evaluation_id": "eval-dxsynth-may2026-v3",
        "timestamp": "2026-05-11T15:00:00Z",
        "runs": runs,
    }

    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(runs)} runs to {OUT}")


if __name__ == "__main__":
    main()
