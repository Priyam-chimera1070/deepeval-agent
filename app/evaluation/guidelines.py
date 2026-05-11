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
Evaluate whether the agent output strictly complies with the updated DxSynthesizer™ prompt (May 2026 revision) for generating evidence-dense, citation-clean, unified executive congress intelligence briefs.

Be STRICT, granular, and evidence-driven. Penalize hallucination, citation breakage, role-ordering errors, and bullet usage heavily. Do NOT penalize a section for being short when the reference is genuinely sparse and the prescribed fallback string is used.

## CORE EVALUATION STANDARD

The response must be:

* Strictly grounded in `model_context` only — no external knowledge
* Structurally complete: exactly 8 sections in the role-correct order
* A UNIFIED narrative inside every section — content MUST NOT be split into "Medical Affairs:" / "Development:" sub-blocks
* Role-aware ONLY at the section-ordering level (role does not change what goes inside a section)
* Maximally dense — every extractable fact from every chunk reflected
* Fully cited using clickable markdown links `([N](#ref-N))` everywhere
* Numerically verbatim (no rounding, no paraphrasing of values)
* Free of bullet points (prose, numbered lists, or markdown tables only)
* Non-hallucinatory (zero inference beyond the reference)

## EVALUATION ORDER (apply in this order for stable scoring)

1. Fallback compliance (global + per-section)
2. Structural compliance (8 sections, `### N. NAME` headings, `---` separators)
3. Role-based section ORDERING
4. Unified-narrative enforcement (no MA/Dev sub-section split)
5. Citation discipline (format, integrity, anchors)
6. References section validity
7. Factual accuracy & numerical fidelity
8. Depth extraction (8 dimensions) and content density
9. Section-specific structural checks
10. Style, readability, no-bullet rule

---

## 1. SOURCE GROUNDING & INPUT FIDELITY

The response must:

* Use ONLY `model_context` as the source of truth
* Reflect available metadata (conference, year, business unit, area of interest, role)
* Utilize ALL retrieved chunks (no silent discarding of "tangential" documents)
* Answer the user query directly
* Never inject outside medical knowledge or assumptions

Penalize if:

* Unsupported facts appear
* Generic boilerplate replaces evidence
* Major findings from the reference are omitted

---

## 2. GLOBAL FALLBACK RULE

If `model_context` has zero documents OR the query is not answerable from the reference, the output MUST be EXACTLY:

"I cannot answer based on current source material."

No structure, no preamble, no commentary, no headings.

HARD FAIL if:

* The agent generates structured sections when this fallback was required → cap 0.30
* The fallback string is paraphrased ("I'm unable to answer…", "no data is available…")

## 2A. PER-SECTION FALLBACK RULE

If a single section has no supporting evidence, the section heading MUST still appear, followed by EXACTLY:

"No sufficient evidence in current source material."

Penalize if:

* A required section heading is omitted because of missing evidence
* The absence is filled with fabricated, padded, or inferred content
* The fallback string is paraphrased

---

## 3. ROLE-BASED SECTION ORDERING (CRITICAL)

Role controls ONLY the order of entire sections — NEVER the content inside them.

If Role = Medical Affairs, the exact section order is:

1. CONFERENCE AT A GLANCE
2. EXECUTIVE SUMMARY
3. CLINICAL DATA HIGHLIGHTS
4. ASSAY INNOVATIONS & VAF
5. COMPETITIVE LANDSCAPE & EMERGING PLATFORMS / NEW TECHNOLOGIES
6. KEY THOUGHT LEADERS & PRESENTERS
7. KEY TAKEAWAYS
8. REFERENCES

If Role = Development, the exact section order is:

1. CONFERENCE AT A GLANCE
2. EXECUTIVE SUMMARY
3. COMPETITIVE LANDSCAPE & EMERGING PLATFORMS / NEW TECHNOLOGIES
4. ASSAY INNOVATIONS & VAF
5. CLINICAL DATA HIGHLIGHTS
6. KEY THOUGHT LEADERS & PRESENTERS
7. KEY TAKEAWAYS
8. REFERENCES

Penalize if:

* Sections appear in the wrong order for the detected role
* Any section is duplicated
* Content inside a section is reordered by track (only the section-level position changes with role)
* The legacy 9-section structure is used (e.g., a standalone "GUIDELINE UPDATES & CLINICAL RECOMMENDATIONS" section — that content must be folded into Executive Summary / Clinical Data Highlights / Competitive Landscape as appropriate)

---

## 4. UNIFIED NARRATIVE ENFORCEMENT (CRITICAL)

Every section MUST be a single unified narrative that combines Medical Affairs and Development insights.

The response MUST NOT contain:

* Sub-headings labeled "Medical Affairs:", "Development:", "[Lead Track – …]", "[Secondary Track – …]", "**Medical:**", "**Dev:**", etc.
* Two parallel narratives covering the same content split by track
* Any mechanism that separates content by role inside a section

Sub-headings ARE allowed when they name a study, drug, assay, platform, or theme (per Section 3 and Section 4 prompts) — but NOT when they label a track.

Penalize if:

* Any track-label sub-heading appears inside a section
* Content is duplicated across track sub-blocks instead of synthesized

---

## 5. CITATION FORMAT (CRITICAL — HIGH WEIGHT)

The ONLY accepted in-text citation format is the clickable markdown link:

`([1](#ref-1))`, `([2](#ref-2))`, …

Required:

* Every factual sentence and every table row carries ≥1 citation in this exact format
* The same source reuses the SAME number throughout the document
* Numbers are assigned in the order sources first appear in the body, starting at 1, with no gaps
* Multiple sources on one sentence are listed as `([1](#ref-1)), ([2](#ref-2))` — never `([1, 2](#ref-1))` or `([1](#ref-1)([2](#ref-2))`

Forbidden — penalize when ANY of these appear:

* Plain-number citations: bare `[1]`, `(1)`, trailing `3` at end of sentence
* Placeholder text from the template: literal `[n](#ref-n)` or `([n](#ref-n))`
* The LEGACY DxSynthesizer 📌-emoji format: `*(📌 Presenter, Institution | Session | Conference Year)*` — this format is OBSOLETE and MUST NOT appear anywhere
* Citations that include filenames, page numbers, presenter names, or session titles inside the in-text link (those belong in the References list only)
* Bracket-and-pound-only forms like `[#]`, `[#1]`, `(#ref-1)` without the leading `[1]`
* Markdown footnote syntax `[^1]`

Anchor-tag scope:

* `<a id="ref-N"></a>` may appear ONLY inside the References section
* Penalize any anchor tag in the body, headings, tables, or earlier sections

---

## 6. CITATION INTEGRITY (CRITICAL — HIGH WEIGHT)

* Every in-text citation number MUST correspond to an entry that actually exists in the References list
* The set of citation numbers in the body MUST equal the set of numbers in References — no extras, no gaps
* If References has N entries, no body citation may use a number > N
* Numbers must be assigned in order of first appearance, starting at 1
* Same source → same number on every reuse (no duplicate entries for the same file/page)
* "No sufficient evidence in current source material." and skipped Glance rows do NOT require citation

Penalize if:

* Any orphan citation (number used in body but missing from References) appears
* Any unused entry exists in References (cited nowhere)
* Numbering has gaps (e.g., body uses 1, 2, 4 but no 3)
* The same file/page appears under two different numbers
* Numbers are assigned non-sequentially relative to first appearance

---

## 7. STRUCTURAL COMPLIANCE (HEADINGS & SEPARATORS)

Required:

* Heading format EXACTLY `### N. SECTION TITLE` (markdown H3 + Arabic numeral + period + space + ALL-CAPS title)
* Numbering 1–8 matches the role-correct section order
* A horizontal rule `---` on its own line between every two adjacent sections
* No additional sections, no missing sections, no renamed sections

Penalize if:

* Heading uses bold (`**1. CONFERENCE...**`), H2 (`## 1.`), H4, or omits the number
* Section title is reworded ("Conference Snapshot" instead of "CONFERENCE AT A GLANCE")
* `---` separator missing in ≥1 transition
* Extra sections invented or required section dropped

---

## 8. NO-BULLET RULE

Allowed content formats inside the output:

* Prose paragraphs
* Numbered lists (1., 2., 3., …) — required in Section 7 Key Takeaways
* Markdown tables

Forbidden:

* Unordered bullet lists (`-`, `*`, `•`) in body content
* Hybrid bullets like `* **Finding:**` block lists

(The presence of `*` inside markdown table cells for emphasis is acceptable; the violation is line-leading bullets.)

Penalize gradient:

* 1–2 stray bullets → minor penalty (no cap)
* 3+ bulleted lines or any section rendered primarily as bullets → cap 0.70
* Entire response in bullet form → cap 0.55

---

## 9. SECTION 1 — CONFERENCE AT A GLANCE

Required:

* Header line: `**[Conference] [Year] — [Business Unit] — [Area of Interest]**`
* Role line: `Role: [Detected from query]`
* A two-column markdown table (Field / Value)
* INCLUDE a row ONLY when the reference contains data for that field. OMIT the entire row when data is absent. NEVER write "not reported", "N/A", "—", "Not available", or any placeholder for missing fields
* Every included row's Value ends with one or more citations in `([N](#ref-N))` format
* Candidate fields (include only when present in reference): Dates & Location, Total Attendees, Exhibiting Companies, Corporate Workshops, Lilly Presence & Sponsorship, Key Themes of the Congress
* After the table: a 3–5 sentence orienting paragraph (scientific tone, dominant disease areas, strategic context) with ≥1 citation

Penalize if:

* "not reported" or any other placeholder appears in any Value cell → cap 0.75
* Rows are forced in despite absent data
* Table is omitted when ≥2 fields have data
* Orienting paragraph is missing or uncited
* Lilly Presence row invents booth numbers, sponsorship tiers, or activities not in the reference (treat as hallucination → see §17)

---

## 10. SECTION 2 — EXECUTIVE SUMMARY

Required:

* 3 to 4 detailed paragraphs (Paragraph 4 conditional on reference depth)
* Each paragraph 4–5 sentences when evidence allows (3 strong sentences acceptable; 1–2 is too thin)
* Single unified narrative — do NOT split into "Medical:" / "Development:" sub-blocks
* Paragraph 1: most significant clinical and scientific findings
* Paragraph 2: guideline updates, biomarker expansions, implications for practice and assay strategy
* Paragraph 3: competitive landscape, emerging platforms, Lilly strategic positioning
* Paragraph 4 (if data supports): real-world evidence, unmet needs, forward-looking signals
* Every sentence carries ≥1 citation in `([N](#ref-N))` format

Penalize if:

* Fewer than 3 paragraphs without fallback justification → cap 0.75
* Track-labeled sub-blocks appear → cap 0.60 (counts as §4 violation)
* Most sentences lack citations
* Paragraphs are padded/repetitive without new dimensions

---

## 11. SECTION 3 (MA) / SECTION 5 (Dev) — CLINICAL DATA HIGHLIGHTS

Required:

* For each study, dataset, assay, or platform finding, a dedicated sub-heading (study name, drug name, assay name, or theme) followed by a full prose paragraph
* Cover where supported: study design/phase/population size, primary + secondary endpoint results with EXACT numerical values, subgroup/biomarker-stratified outcomes, real-world evidence, patient-reported outcomes/QoL, safety/tolerability, analytical performance (sensitivity, specificity, concordance with exact values), VAF thresholds and LOD, platform/sample-type comparisons, operational metrics (TAT, QNS, cost), inter-lab reproducibility, comparison to prior SoC/historical benchmarks, regulatory submission status, presenter clinical-significance statements
* Minimum 3 paragraphs when the reference supports it
* Every paragraph cited

Penalize if:

* Numerical evidence rounded, paraphrased, or distorted → see §17
* Generic statements replace specific data
* Track-labeled sub-blocks appear

---

## 12. SECTION 3 (Dev) / SECTION 5 (MA) — COMPETITIVE LANDSCAPE & EMERGING PLATFORMS / NEW TECHNOLOGIES

Required:

* For each competitor drug, platform, or technology, a dedicated sub-heading followed by a full prose paragraph
* Cover where supported: named competitor drugs/mechanisms/programs, named competitor diagnostic platforms with performance specs, head-to-head or indirect comparisons, new CE-IVD / FDA-cleared market entrants, emerging technologies (AI interpretation, novel sample types, ultra-sensitive sequencing), patient-access / testing-standard / care-pathway effects, CDx landscape shifts, head-to-head assay comparisons with exact metrics, presenter commentary, unmet needs relative to Lilly programs
* Every paragraph cited

Penalize if:

* Competitor names invented or claimed specs fabricated → §17
* Generic "the competitive landscape is evolving" filler replaces specifics
* Track-labeled sub-blocks appear

---

## 13. SECTION 4 — ASSAY INNOVATIONS & VAF (DYNAMIC STRUCTURE)

Required:

* Single unified narrative — do NOT split into Lead Track / Secondary Track sub-blocks (this is the major change from the legacy prompt; track separation in this section is now FORBIDDEN)
* Structure adapts to content:
  - If the reference contains structured technical performance data for ≥2 platforms (sensitivity, specificity, VAF, LOD, concordance, etc.), include a comparison table with ONLY the columns for which data exists. Do NOT force-include empty columns
  - If the reference is primarily descriptive/qualitative, use detailed prose paragraphs instead of a table
  - If both apply, include both a table AND supporting prose
* Every table must include a "Source" column with `([N](#ref-N))` citations
* Supporting prose covers: clinical utility and impact, patient population relevance, analytical/operational characteristics not in the table, linked outcomes or validation data, presenter or guideline statements
* ≥1 prose paragraph per platform or innovation theme
* Every paragraph cited

Penalize if:

* Table is force-included with empty columns or "not reported" cells
* Table is omitted when ≥2 platforms have structured comparable data
* Track-labeled sub-blocks ("Lead Track / Secondary Track / Medical / Development") appear → cap 0.60
* Source column missing from any table

---

## 14. SECTION 6 — KEY THOUGHT LEADERS & PRESENTERS

Required:

* Markdown table with columns: `#`, `Name & Credentials`, `Institution`, `Topic Presented`, `Track`, `Session Title`, `Year`
* `Track` cell uses one of: `MA`, `Dev`, `Both`
* EVERY named speaker in the reference appears as a row
* No fabricated names — penalize HARD (§17) if any speaker not in reference appears
* After the table, a 3–4 sentence paragraph identifying the most influential voices (cited)

Penalize if:

* Any named speaker omitted
* Any row uses an invented name/institution → §17 hallucination cap
* Table columns deviate from prescribed schema
* Closing paragraph missing or uncited

---

## 15. SECTION 7 — KEY TAKEAWAYS

Required:

* 8 to 10 numbered statements (7 strong takeaways acceptable when evidence is thin; <7 only with fallback justification)
* Single unified list — NOT split by track
* Each statement = full sentence of 2–3 clauses naming: specific finding + strategic implication + recommended action / watch item, separated by em-dashes (`—`) per prompt template
* Action verbs preferred (Anchor, Build, Match, Pursue, Deploy, Engineer, Align, Launch, Validate, Position, Prioritize, Monitor, Adopt)
* Every takeaway cited with `([N](#ref-N))`
* No vague platitudes, no generic templated phrasing, no duplicate takeaways

Penalize if:

* Fewer than 7 takeaways when evidence supports more → cap 0.75
* Track separation appears (Lead/Secondary, MA/Dev) → cap 0.60
* Missing the finding → implication → action structure across most takeaways
* Takeaways uncited
* Bullets (`-`, `*`) used instead of numbered list → §8

---

## 16. SECTION 8 — REFERENCES (CRITICAL)

Required:

* Rendered as a NUMBERED LIST — NOT a markdown table
* Each entry EXACTLY in the form: `N. <a id="ref-N"></a> FileName, Descriptor`
* `FileName` is the EXACT `metadata.file_name` from the source chunk (e.g., `2025_aacr_full-summary_api_obudx_v1.pdf`, `2026-03-25_acmg-executive-briefs-all_api_dxcoe_v1.pptx`)
* `FileName` file extension preserved exactly as in metadata (`.pdf` stays `.pdf`, `.pptx` stays `.pptx`)
* `Descriptor` is one of ONLY these forms:
  - `Slide X` (single slide)
  - `Slide X-Y` (hyphenated range — REQUIRED for consecutive slides)
  - `p. X` or `p. X-Y` (for non-slide PDFs)
  - `Conference Overview` (when chunk has no page/slide info, e.g., document-level summary chunks)
* For non-consecutive pages, commas allowed only between true gaps (e.g., `Slide 12, 18-20`)
* Numbering matches in-text citation numbers (1, 2, 3, …)
* Every reference is cited at least once in the body; every body citation has a matching reference (see §6)

Forbidden in References — penalize:

* Rendered as a markdown table (legacy format) → cap 0.50
* Per-chunk artifact filenames (e.g., `…-chunk11.txt`, `…-chunk15.txt`) → cap 0.55
* Altered/invented file extensions (e.g., changing `.pdf` to `.txt`) → cap 0.55
* Invented prose descriptors like "File extract from AACR congress data", "Summary of file", "Document overview", etc. (only `Slide …`, `p. …`, or `Conference Overview` are allowed) → cap 0.65
* Consecutive pages listed with commas instead of a hyphenated range (e.g., `Slide 35,36,37,38` or `Slide 35, 36, 37, 38` instead of `Slide 35-38`) → cap 0.85
* Including presenter / institution / session / conference / year in the reference entry → cap 0.75
* Missing `<a id="ref-N"></a>` anchor on any entry → cap 0.70
* Anchor tag format wrong (e.g., `<a name="ref-1">`, `[#ref-1]`, missing closing `</a>`) → cap 0.70

Note on `[CONFIDENCE: HIGH/MEDIUM/LOW]` tag: the new prompt does NOT require it. Do not penalize its absence. If present, it must be on its own line after the References list.

---

## 17. FACTUAL ACCURACY & ANTI-HALLUCINATION (CRITICAL)

Check:

* Exact values, units, percentages preserved verbatim — NO rounding, NO paraphrasing
* No invented metrics, presenters, institutions, studies, sessions, or trial names
* No overstatement of evidence
* Direct quotes reproduced verbatim in quotation marks AND cited immediately
* Missing data handled with prescribed fallback strings (§2, §2A) — never with fabricated content

Hallucination phrase blacklist — penalize when any of these appear UNLESS the reference itself uses the same language:

* "likely"
* "presumably"
* "it can be inferred"
* "this suggests"
* "appears to"
* "may indicate"
* "is expected to"
* "is anticipated to"

HARD-FAIL items:

* Hallucinated presenter, institution, or trial name → cap 0.40
* Fabricated metric, percentage, sample size, p-value, HR, OR, VAF, LOD → cap 0.40
* Quote attributed to someone who never said it in the reference → cap 0.35
* Speculative future-tense claims not present in the reference → cap 0.55
* Phrase blacklist triggered ≥3 times → cap 0.70
* Numerical value rounded/paraphrased rather than preserved verbatim → cap 0.60

---

## 18. DEPTH EXTRACTION COMPLIANCE (HIGH WEIGHT)

Before scoring depth, mentally inventory every chunk against the 8 dimensions:

| Dimension | Check |
|---|---|
| WHAT | Core finding/result/recommendation surfaced |
| WHO | Named speakers, institutions, study authors, populations preserved |
| NUMBERS | EVERY quantitative value extracted (%, n, p, HR, OR, VAF, sensitivity, specificity, TAT, cost, concordance) |
| CONTEXT | Disease setting, line of therapy, biomarker context, regulatory backdrop |
| COMPARISON | Head-to-head, versus, competitor, historical benchmark |
| IMPLICATION | Clinical practice / assay development / CDx strategy meaning |
| GAP | Stated limitation, unmet need, open question |
| SIGNAL | Forward-looking statement, pipeline mention, emerging trend |

Rule of thumb: a chunk with 5 extractable facts must contribute ~5 facts to the output, not 1.

Penalize heavily if:

* Multiple facts compressed into a single sentence
* Numeric values omitted despite being in the reference
* Comparison / implication insights missing when reference provides them
* Same point repeated/rephrased instead of new dimensions extracted

Density rules:

* When evidence is sufficient, each section contains ≥2–3 full paragraphs
* Each paragraph addresses a distinct theme or sub-finding
* No padding, no repetition, no rephrasing the same point twice
* If evidence supports both a table AND prose, include both

Do NOT penalize short output when the reference is genuinely sparse and the per-section fallback string (§2A) is used.

---

## 19. STYLE & EXECUTIVE READABILITY

Check:

* Executive tone — precise, concise, scannable
* Professionally formatted markdown
* Abbreviations defined on first use
* Length: typically 2,000–4,500 words for a complete brief; >5,500 words usually indicates filler
* High signal-to-noise ratio

Penalize if:

* Rambling or filler-heavy
* Duplicate content across sections
* Excessive length without added information

---

## 20. SCORING GUIDANCE WITH HARD CAPS

Score HIGH (0.85–1.00):

* All 8 sections present in correct `### N. NAME` format and role-correct order
* Unified narratives in every section (no track sub-blocks)
* Excellent source grounding with zero hallucinations
* `([N](#ref-N))` citations everywhere, fully integrity-checked
* References as numbered list with proper anchors, real filenames, collapsed page ranges
* Full depth extraction (all 8 dimensions where present)
* Executive-ready output, no bullets, no placeholders

Score MEDIUM (0.70–0.84):

* Mostly compliant with minor formatting/depth issues
* ≤2 minor citation format issues
* 1–2 sections slightly thin
* Stray bullets or one paraphrased numeric value

Score LOW (0.40–0.69):

* Structural problems (wrong heading format, missing separator)
* Citation coverage gaps (>15% of factual claims uncited)
* Weak extraction in multiple sections
* Hallucination phrase blacklist triggers
* Bullet-heavy formatting

Score FAIL (<0.40):

* Major hallucinations (presenter/metric/trial)
* Missing required section(s)
* Wrong role-based ordering
* Track-labeled sub-blocks inside sections
* Plain-number citations or `[n](#ref-n)` placeholders left in output
* Legacy 9-section structure or legacy 📌 citation format used
* Structured answer when the global fallback was required

HARD CAPS (take the MINIMUM of all caps that trigger):

* Structured answer produced when "I cannot answer based on current source material." was required → max 0.30
* Quote fabricated and attributed to a real or invented speaker → max 0.35
* Any hallucinated presenter, institution, trial, or fabricated metric → max 0.40
* Missing ≥1 required section heading → max 0.45
* References rendered as a table (legacy format) instead of numbered list → max 0.50
* Plain-number citations (`[1]`, `(1)`, trailing `3`) OR template placeholders `[n](#ref-n)` left in output → max 0.50
* Missing References section entirely → max 0.50
* Per-chunk `chunkXX.txt` filenames OR altered file extensions in References → max 0.55
* Wrong role-based section ordering → max 0.55
* Legacy 📌-emoji citation format used anywhere → max 0.55
* Speculative future-tense claims not present in reference → max 0.55
* Track-labeled sub-blocks ("Medical Affairs:", "Development:", "Lead Track", "Secondary Track") inside any section → max 0.60
* Numerical value rounded or paraphrased instead of preserved verbatim → max 0.60
* Orphan citation (body number > N or not in References) OR unused References entry → max 0.60
* Invented prose descriptors in References (anything other than `Slide …`, `p. …`, `Conference Overview`) → max 0.65
* Phrase blacklist triggered ≥3 times → max 0.70
* `<a id="ref-N"></a>` anchor tag appearing outside the References section → max 0.70
* 3+ bulleted lines anywhere in output → max 0.70
* Missing `<a id="ref-N"></a>` anchor on any References entry → max 0.70
* Section 2 has fewer than 3 paragraphs without fallback justification → max 0.75
* Section 7 has fewer than 7 takeaways when evidence supports more → max 0.75
* "not reported" / placeholder text in any Conference at a Glance Value cell → max 0.75
* Including presenter / institution / session / year in a References entry → max 0.75
* Heading format deviates from `### N. NAME` for ≥1 section → max 0.80
* Consecutive pages listed with commas instead of hyphenated range (`Slide 35,36,37,38` vs `Slide 35-38`) → max 0.85

---

## 21. REQUIRED JUDGE OUTPUT EMPHASIS

When generating judge feedback, prioritize identifying:

* Missing sections, wrong role ordering, or legacy 9-section structure
* Track-labeled sub-blocks (the #1 regression from the previous prompt)
* Citation format violations (plain numbers, legacy 📌, placeholder `[n]`)
* Citation integrity failures (orphans, gaps, duplicates for same source)
* References format failures (table format, chunk filenames, wrong descriptors, uncollapsed page ranges)
* Hallucinated presenters, metrics, quotes, trials
* Bullet usage and any prohibited list formats
* Depth dimensions under-extracted (which of WHAT/WHO/NUMBERS/CONTEXT/COMPARISON/IMPLICATION/GAP/SIGNAL was missed)
* Numerical rounding or paraphrasing
* "not reported" appearing in Conference at a Glance instead of row omission

Return clear strengths, specific issues (with section numbers and concrete examples), and actionable section-level suggestions.

---

## FINAL RULE

This is NOT a summarization task.
This is a HIGH-FIDELITY EXTRACTION + UNIFIED-NARRATIVE EXECUTIVE INTELLIGENCE task with strict citation, structural, and factual compliance.
Evaluate strictly on: fallback handling, structural compliance, role ordering, unified narrative, citation discipline, References validity, factual accuracy, depth extraction, and no-bullet formatting.
""",
}


def get_guidelines(agent_name: str) -> str:
    """
    Returns guidelines string for a known agent, or empty string if not registered.
    Matching is case-insensitive.
    """
    return AGENT_GUIDELINES.get(agent_name.lower().strip(), "")
