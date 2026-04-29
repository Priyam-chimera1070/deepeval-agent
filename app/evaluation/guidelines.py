AGENT_GUIDELINES = {
    "rag agent": """
1. Structure & Completeness — output must contain all 7 sections in order, Key Insights first, minimum 4 maximum 8 cards per section
2. Role Specificity — strict Medical Affairs vs Development separation must be maintained throughout
3. Content Accuracy & Grounding — no fabrication allowed, every claim must be grounded in source data, sources cited per card
4. CCG Alignment — Medical Affairs must use full 3-column format in Section 4, Development must use condensed format in Section 6
5. Confidence & Transparency — Section 7 must include HIGH/MEDIUM/LOW confidence rating with clear rationale for each rating
6. Filter Confirmation — all 5 filters must be explicitly confirmed before generating output
""",
    "dxsynthesizer": """
Evaluate whether the agent output fully complies with the updated DxSynthesizer™ prompt for generating structured executive congress intelligence briefs from retrieved medical congress documents.

## CORE EVALUATION STANDARD

The response must be:

* Strictly grounded in provided reference data only
* Complete in the required 9-section format
* Correctly role-ordered
* Fully cited using the prescribed citation formats
* Executive-grade in usefulness
* Free from hallucination, filler, and unsupported claims

Judge both content quality and instruction compliance.

## EVALUATION ORDER (apply in this order for stable scoring)

1. Structural compliance (9 sections present + correct heading format)
2. Role detection and lead/secondary track ordering
3. Citation discipline (formats and coverage)
4. Factual accuracy and source grounding
5. Section-specific content depth
6. Style and executive readability

---

## 1. SOURCE GROUNDING & INPUT FIDELITY

Check that the response:

* Uses only the provided reference/context as the source of truth
* Answers the user query directly
* Uses chat history only for continuity, never as a source of facts
* Reflects available metadata such as conference, year, business unit, and area of interest
* Does not inject external medical knowledge or assumptions

Fail if:

* Unsupported facts appear
* Generic content unrelated to context appears
* Important context evidence is ignored

---

## 2. QUERY ANSWERABILITY RULE

If the query is not answerable from reference data, the correct output is exactly:

"I cannot answer based on current source material."

with no extra notes, no preamble, and no commentary.

Fail if:

* The model fabricates an answer when evidence is absent
* Adds explanations when the explicit fallback should have been used

## 2A. PER-SECTION FALLBACK RULE

If a single section has no supporting evidence, the section heading MUST still appear, followed by exactly:

*"No sufficient evidence in current source material."*

Fail if:

* A required section heading is omitted because of missing evidence
* The absence is filled with fabricated, padded, or inferred content
* The exact fallback string is paraphrased (e.g., "no data available")

---

## 3. ROLE DETECTION & TRACK PRIORITIZATION

The system must detect role from query context and prioritize sections accordingly.

If role = Medical Affairs:

* Medical Affairs content first in every dual-track section
* Development content second

If role = Development:

* Development content first
* Medical Affairs content second

Both tracks must still be included unless impossible due to absent evidence.

Fail if:

* Wrong role inferred
* Wrong track ordering in any dual-track section
* Only one track shown without justification
* Role ignored across sections

---

## 4. TRACK CLASSIFICATION QUALITY

Findings must be correctly separated into:

Medical Affairs Track:

* Clinical outcomes
* Guidelines
* Patient impact
* Safety / efficacy
* Practice change
* Access / care delivery

Development Track:

* Assay platforms
* Biomarkers
* AI / algorithms
* Technical performance
* Diagnostics pipelines
* Competitive technology
* Analytical specifications

Anchoring examples (use as classification reference):

* "hs-Troponin LoD = 1.2 ng/L"  → Development
* "0/1-hour rule-out reduced ED LoS by 2.4 hours"  → Medical Affairs
* "ctDNA assay 84% concordance with tissue IHC"  → Development
* "EAU guideline added PSMA PET to staging"  → Medical Affairs

Fail if:

* Clinical findings placed under technical sections
* Technical metrics placed under patient-facing sections
* Major themes omitted

---

## 5. REQUIRED 9-SECTION STRUCTURE (MANDATORY)

The response MUST include these headings in EXACT format `### N. HEADING` and EXACT order:

1. ### 1. CONFERENCE AT A GLANCE
2. ### 2. EXECUTIVE SUMMARY
3. ### 3. GUIDELINE UPDATES & CLINICAL RECOMMENDATIONS
4. ### 4. KEY THOUGHT LEADERS & PRESENTERS
5. ### 5. CLINICAL DATA HIGHLIGHTS
6. ### 6. COMPETITIVE LANDSCAPE & EMERGING PLATFORMS / NEW TECHNOLOGIES
7. ### 7. ASSAY INNOVATIONS / VAF
8. ### 8. KEY TAKEAWAYS
9. ### 9. REFERENCES

Check:

* All 9 headings present
* Correct numerical order
* Heading format matches `### N. NAME` (markdown H3 with number)
* No structural substitutions (e.g., `**1. CONFERENCE...**` is non-compliant)

Fail if:

* Any section heading is missing
* Order is wrong
* Heading format deviates from `### N. NAME`
* Sections are merged, renamed, or split

---

## 6. SECTION 1 — CONFERENCE AT A GLANCE

Required elements:

* Header line: **[Conference] [Year] — [Business Unit] — [Area of Interest]**
* Role line: Role: [Detected from query]
* Bullets:
  - Dates & Location *(📌 source)*
  - Total Attendees *(📌 source)*
  - Exhibiting Companies *(📌 source)*
  - Corporate Workshops *(📌 source)*
  - Lilly Presence & Sponsorship *(📌 source)*
  - Key Themes of the Congress *(📌 source)*

Numbers must come from reference when available. Use "not reported" only when genuinely absent.

Lilly Presence & Sponsorship — HARD FAIL if the agent invents booth numbers, sponsorship tiers, satellite-symposium counts, or activities not explicitly in the reference. "not reported" is the correct answer when absent.

Fail if:

* Header is incomplete or missing role line
* Required bullets are missing
* Invented numbers appear
* Lilly information is fabricated

---

## 7. SECTION 2 — EXECUTIVE SUMMARY

Check that:

* Two short paragraphs exist (one per track)
* Lead track paragraph appears first
* Each paragraph is 2–4 sentences when evidence allows (3 is typical; 2 strong sentences acceptable)
* Each paragraph synthesizes findings (not bullet-copy)
* Directly answers user intent
* Each paragraph closes with a citation in the form: *📌 Presenter, Institution | Session | Conference Year*

Fail if:

* Only one paragraph
* Wrong track order
* Generic or padded summary
* Missing or malformed citations

---

## 8. SECTION 3 — GUIDELINE UPDATES & CLINICAL RECOMMENDATIONS

Both lead and secondary tracks must be present.

Lead Track should cover (where supported):

* Updated guidelines
* Clinical recommendations
* Testing standards
* Required biomarkers
* Practice change implications

Secondary Track should cover (where supported):

* Assay development implications
* CDx update cycles
* Analytical requirements

Each paragraph must end with a citation.

Fail if:

* Section is superficial
* One track missing without per-section fallback
* No citation support

---

## 9. SECTION 4 — KEY THOUGHT LEADERS & PRESENTERS

Required:

* Markdown table format
* Columns: Name, Institution, Topic, Track, Source
* Every named speaker present in the reference is included
* Track labels are MA / Dev / Both
* No invented names

Fail if:

* Named speakers omitted
* Hallucinated speakers added
* Required columns missing
* Track labels wrong

---

## 10. SECTION 5 — CLINICAL DATA HIGHLIGHTS

Lead Track (when supported):

* Clinical findings
* Real-world evidence
* Outcomes
* Patient impact

Secondary Track (when supported):

* Sensitivity, specificity
* Concordance
* VAF
* Platform comparisons
* Operational metrics

Natural prose with thematic sub-headings; every paragraph cited.

Fail if:

* Only generic statements
* Numerical evidence distorted
* Wrong track ordering

---

## 11. SECTION 6 — COMPETITIVE LANDSCAPE & EMERGING PLATFORMS / NEW TECHNOLOGIES

Lead Track:

* Clinical implications of competitor activity
* Effects on patient access, testing standards, care delivery

Secondary Track:

* Competitor platforms
* New entrants
* Emerging technologies
* Pipeline signals
* Head-to-head comparisons
* CDx shifts

Fail if:

* Competitor content missing when present in reference
* No strategic interpretation
* Unsupported claims

---

## 12. SECTION 7 — ASSAY INNOVATIONS / VAF (HIGH-WEIGHT TRACK SEPARATION CHECK)

Lead Track:

* Patient-facing benefits enabled by innovations only
* MUST NOT contain raw analytical specs

Secondary Track (analytical detail goes here):

* Sensitivity %
* Specificity %
* Concordance %
* VAF thresholds
* Detection limits
* Sample types
* Panel sizes
* Turnaround time
* QNS rates
* Tables when comparative data exists

HIGH-WEIGHT CHECK: Presence of raw analytical specs in Section 7 Lead Track is a significant violation.

Examples:

* "Enables non-invasive retesting at progression"  ✓ Lead Track
* "Reduces unnecessary biopsies by 32%"  ✓ Lead Track
* "ctDNA assay 84% concordance with tissue IHC"  ✗ belongs in Secondary
* "LoD 1.2 ng/L with CV <10%"  ✗ belongs in Secondary

Fail if:

* Technical metrics missing despite evidence
* Raw specs incorrectly placed in Lead Track
* No citations in tables/rows

---

## 13. SECTION 8 — KEY TAKEAWAYS

Required:

* 6–10 action-oriented bullets when evidence allows (8 is typical; 6 strong bullets acceptable)
* Lead track bullets first, secondary track bullets after
* Action verbs preferred (Anchor, Build, Match, Pursue, Deploy, Engineer, Align, Launch, etc.); descriptive bullets allowed if clearly action-implying
* Non-repetitive
* Every bullet cited *(📌 source)*

Fail if:

* Weak descriptive bullets that imply no action (e.g., "There is interest in X")
* Missing citations
* No track separation
* Fewer than 5 bullets when evidence supports more

---

## 14. SECTION 9 — REFERENCES

Required:

* Markdown table with columns: #, Presenter, Institution, Session / Publication, Conference, Year
* # column uses Arabic numerals (1, 2, 3, ...)
* Every cited source in the brief appears in this table
* Confidence statement immediately after the table — exactly one of:
  - `[CONFIDENCE: HIGH]` — All findings sourced directly from the reference.
  - `[CONFIDENCE: MEDIUM]` — Some findings inferred from adjacent content. Flagged inline.
  - `[CONFIDENCE: LOW]` — Insufficient data in the reference. Adjust filters or verify ingestion.

Fail if:

* No references section
* Fake or inconsistent sources
* Confidence tag missing or in wrong format
* Sources cited inline but absent from the table

---

## 15. CITATION DISCIPLINE (CRITICAL — HIGH WEIGHT)

Citation discipline alone can lower a score by up to 0.20 even if other criteria pass.

Required formats:

* Bullet points: end with `*(📌 Presenter, Institution | Session | Conference Year)*`
* Prose paragraphs: end with separate line `*📌 Presenter, Institution | Session | Conference Year*`
* Table rows: include a Source column with `Session, Year` or `Plenary, Year`
* When no presenter is named: fallback to `*📌 Workshop/Session Title | Conference Year*`
* The 📌 emoji is MANDATORY — text-only citations like "(source: X)" or "[1]" alone fail
* "not reported" and "No sufficient evidence in current source material." lines do NOT require citation

Fail if:

* Many factual claims are uncited
* Citation format deviates from prescribed patterns
* Citations do not correspond to entities in the reference
* Fake citations appear

---

## 16. FACTUAL ACCURACY & DATA PRESERVATION

Check that:

* Exact values, units, and percentages are preserved verbatim
* No invented metrics, presenters, or institutions
* No overstatement of evidence
* Missing data is handled honestly with the prescribed fallback strings

Fail if:

* Wrong numbers
* Hallucinated trials, speakers, or results
* Unsupported certainty

---

## 17. STYLE & EXECUTIVE READABILITY

Check that output is:

* Executive tone — precise and concise
* Professionally formatted markdown
* Easy to scan
* Good use of bullets, prose, and tables
* Minimal redundancy
* Clear terminology / abbreviations defined on first use
* Length: typically 1,500–3,500 words for a complete brief; outputs >5,000 words are usually filler-heavy

Fail if:

* Rambling text or filler-heavy writing
* Poor readability
* Duplicate content across sections
* Excessive length without added information

---

## 18. SCORING GUIDANCE WITH HARD CAPS

Score HIGH (0.85–1.00) when:

* All 9 sections present in correct heading format and order
* Excellent source grounding
* Correct role prioritization
* Strong synthesis
* High citation compliance
* Executive-ready output
* No hallucinations

Score MEDIUM (0.70–0.84) when:

* Mostly compliant with moderate omissions or shallow areas

Score LOW (0.40–0.69) when:

* Partial structure, weak depth, citation gaps, ordering issues

Score FAIL (<0.40) when:

* Major hallucinations
* Missing sections
* Wrong format
* Unsupported content
* Severe instruction non-compliance

HARD CAPS (apply regardless of other strengths):

* Missing ≥1 required section heading → max score 0.50
* Wrong role/track ordering in ≥3 sections → max score 0.55
* ≥30% of factual claims uncited → max score 0.60
* Any hallucinated presenter or fabricated metric → max score 0.45
* Missing References table OR missing CONFIDENCE tag → max score 0.65
* Section 7 Lead Track contains raw analytical specs → max score 0.80
* Heading format deviates from `### N. NAME` for ≥1 section → max score 0.85

---

## 19. REQUIRED JUDGE OUTPUT EMPHASIS

When generating judge feedback, prioritize:

* Missing required sections
* Wrong role detection / ordering
* Citation format failures and coverage gaps
* Omitted key evidence from reference
* Hallucinated claims (especially Lilly presence and presenters)
* Section 7 lead/secondary contamination
* Weak executive usefulness
* Specific actionable improvements

Return clear strengths, issues, and concrete suggestions.
""",
}


def get_guidelines(agent_name: str) -> str:
    """
    Returns guidelines string for a known agent, or empty string if not registered.
    Matching is case-insensitive.
    """
    return AGENT_GUIDELINES.get(agent_name.lower().strip(), "")
