# ATS Architecture & AI Screening

Sources: ResuTrack (2026), Jobscan (2024), impress.ai (2025), GoPerfect (2026), HiPeople (2025)

Covers: How modern ATS systems parse, score, and filter resumes — and where AI adds semantic intelligence.

## ATS Parse Stage

### What Happens

When you upload a resume, the ATS executes:

1. **Text extraction** — Convert PDF/docx to raw text
2. **Section identification** — Find Work Experience, Skills, Education
3. **Field mapping** — Extract: name, email, dates, titles, companies, skills
4. **Data normalization** — Convert to standardized format for database

### What Breaks Parsing

| Element | Problem |
|---------|---------|
| Tables | Columns create ambiguous read order |
| Multi-column | Left-to-right breaks section identification |
| Headers/footers | Often skipped or misattributed |
| Graphics | Text in images not extracted |
| Complex formatting | Nested structures lose hierarchy |
| Non-standard sections | "Where I've Worked" not recognized |

### What Works

- Single-column with clear section headers
- Standard section names (Work Experience, Skills, Education)
- Simple bullet points
- Standard fonts (Arial, Calibri, Times New Roman)

## ATS Score Stage

### Keyword Matching

Traditional ATS uses **exact string matching**:

```
Job requirement: "Python"
Resume contains: "Python" → MATCH (+points)
Resume contains: "Python scripting" → MATCH (+points)
Resume contains: "code in Python" → MATCH (+points)
Resume contains: "worked with py" → NO MATCH (partial)
```

### Scoring Algorithms

| Factor | Weight (typical) |
|--------|------------------|
| Exact keyword match | 40-50% |
| Skills section presence | 20-25% |
| Experience relevance | 15-20% |
| Education match | 10-15% |
| Format compliance | 5-10% |

### Relevance Scoring

Modern ATS ranks candidates by:

- **Keyword density** — How many required terms present
- **Keyword proximity** — Are related terms near each other?
- **Title match** — Does current/recent title align?
- **Experience length** — Years match requirements
- **Education threshold** — Degree level met

## AI Screening Stage

### What AI Adds

AI-powered screening (used by 78% of large tech firms per LinkedIn 2025) adds:

| Capability | What It Does |
|------------|--------------|
| Semantic matching | Understands "led team" = "managed team" |
| Context awareness | Weighs relevance, not just presence |
| Transferable skills | Identifies adjacent experience |
| Gap detection | Finds missing but obvious requirements |
| Explainable scores | Shows reasoning for each score |

### AI vs Traditional ATS

| Aspect | Traditional ATS | AI Screening |
|--------|-----------------|--------------|
| Keyword matching | Exact string | Semantic + exact |
| Understanding | Literal | Contextual |
| Synonyms | No match | Matches |
| Career progression | Ignores | Analyzes |
| Scoring explanation | None | Detailed |

### How AI Evaluation Works

Three-stage process:

**1. Parse** — Same as traditional ATS

**2. Evaluate** — Compare against role criteria:
   - Extract skills from resume
   - Map to role requirements
   - Score each dimension (technical, leadership, domain)
   - Weight by role priority

**3. Rank** — Compare against candidate pool:
   - Normalize scores across applicants
   - Identify top percentile
   - Flag borderline cases for human review

## ATS Platforms to Know

### Enterprise (Most Common)

| Platform | Market Share | Used By |
|----------|--------------|---------|
| Workday | ~30% | Enterprise, FAANG |
| SAP SuccessFactors | ~20% | Enterprise |
| iCIMS | ~15% | Mid-market |
| Greenhouse | ~10% | Tech startups |
| Oracle Taleo | ~10% | Enterprise |
| Lever | ~5% | Tech, growth |
| SmartRecruiters | ~5% | Mid-market |

### What This Means

Different ATS = different parsing behavior:

- **Workday** — Strict on format, strong keyword matching
- **Greenhouse** — Better at parsing varied formats, semantic scoring
- **iCIMS** — Good with structured data, less flexible
- **Lever** — Modern parsing, AI-integrated

**Implication**: Test your resume against multiple ATS using Jobscan/resumly.

## 2026 Evolution

### What's New

1. **Explainable AI** — Recruiters demand to see why candidates scored that way
2. **Bias mitigation** — Systems removing demographic signals
3. **Skills-first** — Moving away from degree/experience gatekeeping
4. **Multi-modal** — Integrating assessments, video interviews, not just resume
5. **Real-time feedback** — Candidates see match score before applying

### What This Means for You

- **Skills matter more** — Certifications, demonstrated skills > credentials
- **Keywords still critical** — Even with semantic matching, exact terms boost scores
- **Quantified impact** — AI can evaluate significance, not just presence
- **Consistency across platforms** — LinkedIn, resume, applications should align

## Testing Your Resume

### Tools

| Tool | What It Does |
|------|--------------|
| Jobscan | Simulates ATS scoring, keyword analysis |
| Resumly | AI-powered resume scoring |
| Resume Worded | ATS compatibility + optimization tips |
| ResumeATS.net | Focused keyword checking |

### Target Scores

| Score | Interpretation |
|-------|----------------|
| 90+ | Strong, likely passes ATS |
| 70-89 | Good, may miss some roles |
| 50-69 | Needs optimization |
| <50 | Significant issues |

### Quick Check

1. Upload resume to Jobscan
2. Paste job description
3. Review match score
4. Check which keywords missing
5. Add missing keywords naturally
6. Re-score until 90+