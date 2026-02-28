# Issue Triage

Sources: GitHub issue management patterns, SWE-bench (Princeton), Sweep.dev triage heuristics, BDD in Action (Smart/Molak)

Triage is the first and most critical step in the BDD-fixer lifecycle. If you get triage wrong, you waste tokens and compute time trying to fix problems that are not fixable, not bugs, or not understood. You are a senior engineer. Do not approach an issue with the assumption that the user is right or that the code is wrong. Approach it with skepticism.

## Section 1: Classification Matrix

Before touching any code, classify the issue. Use the following matrix to decide your immediate next step.

| Category | Signal patterns | Action |
|----------|-----------------|--------|
| Bug report | Explicit repro steps, error messages, "expected vs actual" sections, tracebacks, clear regression signals. | Proceed to verification and fix. |
| Feature request | Phrases like "it would be nice", "can you add", "support for X", enhancement labels, lack of error signals. | Write acceptance test, then implement. |
| Question | Phrases like "how do I", "is it possible", "what is the best way", lack of repro steps or expected behavior. | Answer the question, link to docs, and close. |
| Invalid | Reports that contradict documentation, issues that cannot be reproduced after 3 attempts, user error in setup. | Close with a detailed explanation of why it is not a bug. |
| Duplicate | Same root cause, identical error messages, or identical repro steps as an existing open/closed issue. | Link to the original issue and close as duplicate. |
| Incomplete | Missing repro steps, no version info, vague descriptions like "it does not work" or "I get an error". | Ask for clarification using the standard template. |

## Section 2: Reading an Issue (Extraction Protocol)

A human issue is a messy narrative. Your job is to extract structured data from that narrative. Use this protocol to parse every issue before moving to the Gherkin phase.

### Title Analysis
Do not trust the title. Users often describe their attempted solution ("Cannot find module X") instead of the actual problem ("Installation fails on Windows").
- Is the title a symptom or a guessed cause?
- Does the title match the body? If not, the body is the source of truth.

### Body Parsing: The Signal Search
Scan the body for the following technical artifacts:
- Code blocks: Look for configuration snippets, CLI invocations, or API usage.
- Error messages: Find the specific exception name or error code.
- Stack traces: Identify the deepest frame that belongs to the current repository.
- Versions: Look for runtime versions, OS details, and package versions.

### Expected vs Actual Behavior
This is the core of the BDD contract. If these are not explicitly stated, you must infer them or ask.
- Expected: What is the "happy path" or the correct contract?
- Actual: What is the specific deviation? Is it a crash, a wrong value, or a hang?

### Repro Steps Verification
Check if the repro steps are "Turnkey".
- Are they specific enough to automate?
- Do they include the necessary data/input?
- Do they assume a specific environment you do not have?

### Mental Extraction Template
Before proceeding, you should be able to fill out this mental model:
- Primary Goal: [What is the user trying to do?]
- Technical Blocker: [What specific error/behavior stops them?]
- Scope: [Is it one function, one CLI command, or the whole app?]
- Repro Complexity: [Can I replicate this with a single test case?]

## Section 3: The gh CLI for Issue Reading

Use the GitHub CLI to gather all context. Do not rely on just the initial issue body; comments often contain the "missing link" for reproduction.

### Viewing the Issue Metadata
Get the full picture including labels and assignees to ensure no one else is already working on it.
```bash
gh issue view 123 --json title,body,labels,comments,assignees,state
```

### Searching for Context
Check if this is a recurring problem or a known regression.
```bash
gh issue list --label "bug" --state open --json number,title
```

### Extracting Comment Data
Users often provide the actual repro steps in the third or fourth comment after being prompted by others.
```bash
gh issue view 123 --json comments --jq '.comments[].body'
```

### Analyzing the JSON Output
When parsing the JSON, prioritize the `body` and `comments`. Use `jq` filters to isolate code blocks if the issue is long.

## Section 4: When NOT to Fix

Knowing when to walk away is what separates seniors from juniors. If an issue meets any of the following criteria, stop the fix process and label/comment instead.

| Signal | Action | Reason |
|--------|--------|--------|
| No clear expected behavior | Ask for clarification | You cannot write a test for an undefined state. |
| Affects deprecated API | Close or Redirect | We do not fix bugs in code that is slated for removal. |
| Requires breaking changes | Escalate to Maintainer | Architectural shifts require human consensus, not auto-fixes. |
| Wishlist / No criteria | Label "needs-discussion" | Vague enhancements lead to scope creep and bloat. |
| User confusion | Answer and Close | Documentation issues are not code bugs. |
| Security vulnerability | Private Disclosure | Never fix security bugs in public PRs without a coordinated disclosure. |
| Out of scope | Close as "Won't Fix" | The tool should not do things it was never intended to do. |

### Decision Heuristics
- If the fix takes more than 50 lines of code change but the issue is "minor", it might be an architectural problem.
- If you find yourself needing to change 3+ unrelated files, the issue is likely a "Feature Request" disguised as a "Bug".

## Section 5: Asking for Clarification

If an issue is incomplete, do not guess. Guessing leads to "works on my machine" PRs that get rejected. Use the following template to respond to the user.

### Clarification Template
```markdown
Thanks for reporting this! To help fix this, I need a few more details:

1. **What did you expect to happen?**
2. **What actually happened?** (Please provide the exact error message or a description of the behavior)
3. **Steps to reproduce:** (A minimal, self-contained code snippet or CLI command sequence)
4. **Environment:** (OS, runtime version, package version)
```

### When to Ask vs. Close
- Ask: If the user provided some signal but missed the "how" (e.g., they gave an error but no repro).
- Close: If the issue is a single sentence with no context and the user has a history of "drive-by" low-quality reports.
- Proceed: Only if you can recreate the failure locally using the information provided.

## Section 6: Priority Signals

Not all bugs are equal. Use these signals to determine which issues to prioritize if multiple are assigned to you.

### P0: Critical
- Data loss or corruption.
- Security vulnerabilities (CRITICAL: handle via private channels).
- Complete service outage or "cannot start" regressions.
- Affects 100% of users on a major platform.

### P1: High
- Core feature is broken with no easy workaround.
- Significant performance degradation (e.g., 10x slower).
- Regressions in the most used API endpoints or CLI commands.

### P2: Medium
- Edge case bugs affecting specific configurations.
- Minor features not working as documented.
- UI/UX papercuts that do not block functionality.
- Has a known, simple workaround.

### P3: Low
- Cosmetic issues (typos, alignment).
- Refactoring suggestions with no functional impact.
- Nice-to-have enhancements for niche use cases.

### Crowdsourced Urgency
Watch the "reactions" and "me too" comments. If an issue has 5+ thumbs up or 3+ duplicate reports within 24 hours, escalate the priority regardless of the technical severity. High-volume "papercuts" are often more damaging to reputation than a silent P1.
