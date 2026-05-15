---
name: "@tank/tech-cv-writer"
description: |
  Write ATS-optimized CVs for tech/SWE roles using 2026 AI-screening standards.
  Covers ATS keyword matching, LaTeX resume templates, quantified achievement framing,
  LinkedIn profile optimization, and role-specific tailoring. Synthesizes ResuTrack,
  Jobscan, GeniusResume, and 2025-2026 hiring research.

  Trigger phrases: "write a resume", "cv for software engineer", "ATS optimized",
  "resume for tech role", "tech resume", "software engineer cv", "make my resume pass ats",
  "linkedin profile optimization", "latex resume", "resume 2026", "cv for developer",
  "tech job application", "resume keywords", "pass applicant tracking system"
---

# Tech CV Writer

Write CVs optimized for 2026's AI-screened hiring landscape.

## Why 2026 Is Different

- **78% of tech firms** use AI models to pre-filter resumes (LinkedIn Talent Report 2025)
- **75% of resumes** rejected by ATS before human sees them (Jobscan)
- ATS scans in **6-7 seconds**, looking for exact keyword matches
- AI screening uses **semantic understanding**, not just keywords

## Core Philosophy

1. **ATS first, humans second** — Format for parsing, then design for readers
2. **Keywords are literal** — "React.js" ≠ "ReactJS" to some parsers
3. **Quantify everything** — Numbers beat adjectives every time
4. **One role, one CV** — Tailor keywords per application
5. **LaTeX = clean parsing** — Agents compile it easily, ATS parses cleanly

## ATS Framework

| Stage | What Happens |
|-------|--------------|
| Parse | Extract contact, experience, skills (use standard sections) |
| Score | Match keywords from job description (exact phrasing) |
| Rank | Compare against candidates (keyword density matters) |
| Filter | Reject below threshold (90+ = human review) |

**AI screening adds:** Semantic matching, context awareness, transferable skills detection.

See `references/ats-architecture.md` for deep dive.

## Resume Structure

### Section Order (Reverse Chronological)

1. Header (Name, Title, Contact, Links)
2. Professional Summary (2-3 sentences)
3. Technical Skills (categorized)
4. Professional Experience
5. Projects (if applicable)
6. Education / Certifications

### Format Rules

| Rule | Why |
|------|-----|
| Single-column | Two-column breaks parsing |
| Standard headings | "Work Experience" not creative names |
| 10-12pt standard font | Reliable parsing |
| .docx OR .pdf (not scanned) | Avoid image-based PDFs |
| No tables/graphics | Breaks keyword extraction |

## Keyword Strategy

### Extraction Process

1. Copy job description
2. Identify hard skills, tools, frameworks
3. Map to your exact phrasing
4. Embed in skills + bullet points

### Keyword Priority

| Priority | Type | Example |
|----------|------|---------|
| P0 | Required tech | Python, React, AWS |
| P1 | Preferred | CI/CD, Agile, microservices |
| P2 | Nice-to-have | Leadership, mentoring |

See `references/keyword-strategy.md` for full keyword clusters by role.

## Bullet Formula

```
[Action Verb] [What] [How] [Result with metrics]
```

| Weak | Strong |
|------|--------|
| "Wrote Python scripts" | "Developed Python automation scripts reducing manual processing time by 40%" |
| "Worked on API" | "Designed RESTful APIs handling 10K+ requests/day with 99.9% uptime" |

See `references/bullet-formulas.md` for complete action verbs and before/after examples.

## LaTeX Templates

LaTeX produces clean, ATS-friendly output — agents compile it easily.

### Quick Template

```latex
\documentclass[11pt]{article}
\usepackage[left=0.75in,right=0.75in,top=0.5in,bottom=0.5in]{geometry}
\usepackage{enumitem}
\begin{document}
\textbf{Name} \hfill email@example.com
\\ Role \href{github.com/user}{GitHub} | \href{linkedin.com/in/user}{LinkedIn}

\section*{Technical Skills}
Languages: Python, JavaScript, Go

\section*{Experience}
\textbf{Software Engineer} \hfill Company \textit{2023--Present}
\begin{itemize}
  \item Built APIs serving 50K daily requests
  \item Reduced pipeline time by 45\% using GitHub Actions
\end{itemize}
\end{document}
```

**Advantages:** Clean text extraction, version control friendly, consistent output.

See `references/latex-templates.md` for full templates (entry-level, senior, full-stack, DevOps).

## LinkedIn Optimization

| Section | Content |
|---------|---------|
| Headline | Role + key value proposition |
| About | 3-line summary: expertise + achievement + what you seek |
| Skills | Match resume keywords + adjacent skills |
| Projects | Links to deployed projects |

See `references/linkedin-optimization.md` for full guide.

## Role-Specific Approaches

| Stage | Focus |
|-------|-------|
| Junior (0-2 yr) | Projects first, coursework, open source |
| Mid (3-5 yr) | Ownership, technical depth, growing leadership |
| Senior (5+ yr) | Team leadership, architecture, cross-team influence |
| Career Pivot | Transferable skills, ML projects prominent |

See `references/role-templates.md` for all templates.

## Common ATS Mistakes

| Mistake | Fix |
|---------|-----|
| Multi-column template | Single-column only |
| Synonyms | Use exact terms from job posting |
| No metrics | Quantify every achievement |
| Too many skills | List 10-15 most relevant |

## Quality Checklist

- [ ] ATS score 90+ on Jobscan/resumly
- [ ] Keywords from job description matched
- [ ] All bullets have metrics
- [ ] Single-column, no graphics
- [ ] Standard section headings
- [ ] PDF compiles without errors (if LaTeX)
- [ ] LinkedIn keywords match resume

## Reference Index

| File | Contents |
|------|----------|
| `references/ats-architecture.md` | ATS/AI parsing, scoring, ranking deep dive |
| `references/keyword-strategy.md` | Full keyword clusters by role |
| `references/bullet-formulas.md` | Action verbs, metric frameworks, examples |
| `references/latex-templates.md` | Entry-level, senior, full-stack, DevOps templates |
| `references/role-templates.md` | Junior, senior, career pivot approaches |
| `references/linkedin-optimization.md` | Profile sections, headline, content strategy |