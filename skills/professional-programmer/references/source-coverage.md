# Source Coverage

Sources: Birat Rai's "97 Journey Every Programmer should Accomplish" Medium roadmap; Henney (ed.), 97 Things Every Programmer Should Know GitBook/GitHub text under CC BY-NC-SA 3.0; Tank contributing standard

Covers: how this skill establishes source coverage before synthesizing professional programming guidance.

## Coverage Policy

Use the Medium roadmap as the user's requested entry point and the canonical GitBook/GitHub source as the complete coverage source for all 97 items.

Do not copy prose from the Medium page, Medium step posts, GitBook pages, GitHub files, or the printed book. Convert the material into original, agent-actionable engineering practices.

Treat lesson titles as taxonomy labels, not as sufficient guidance. When a Medium step article is absent from the fetched page or inaccessible, use the corresponding canonical GitHub/GitBook item for coverage.

## What Was Read

The main Medium article was fetched and read. It contains a short journey manifesto, a reference to the book, and a numbered list of 97 programming path items.

The canonical GitHub `SUMMARY.md` was fetched and read. It lists all 97 items and maps each item to `thing_NN/README.md`.

The canonical GitBook/GitHub introduction was fetched and read. It states that the GitBook version is derived from the 97 Things project and is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 3.0.

## Coverage Counts

| Metric | Count | Meaning |
| ------ | ----- | ------- |
| Roadmap items | 97 | Total item count from the Medium page and canonical summary |
| Direct Medium links on fetched page | 74 | Items 1-74 have explicit step links in the fetched Medium page |
| Direct Medium links fetched successfully | 74 | Every direct Medium link on the fetched page was fetched through the text proxy into temp storage during implementation |
| Title-only items on fetched page | 23 | Items 75-97 appear without direct links in the fetched Medium page |
| Discovered Medium links outside main page | 0 | No additional Medium URLs are stored in the package ledger |
| Missing Medium links | 23 | Title-only rows are marked `missing` for Medium coverage and use canonical coverage |
| Canonical GitHub/GitBook item pages | 97 | Every item has a canonical `thing_NN/README.md` path |
| Blocked items | 0 | No item lacks canonical coverage |

## Ledger Interpretation

`assets/source-ledger.csv` is the source of truth for coverage. It records the item number, title, author attribution, Medium main page, Medium step URL where listed, discovered Medium step URL if any, Medium read status, canonical source URL, coverage status, and notes.

Rows 1-74 are marked `covered-from-medium-and-canonical`, with `medium_read_status` set to `read`. This records that the directly linked Medium step article was accessible during implementation while the skill synthesis still relies on original writing and canonical source coverage.

Rows 75-97 are marked `covered-from-canonical`, with `medium_read_status` set to `missing`. This records that the fetched Medium roadmap exposed the item title and author attribution but no direct step URL.

The final skill content does not quote or closely paraphrase Medium step posts. Medium access satisfies the user's source-reading requirement; canonical coverage provides complete item coverage and stable attribution.

## Copyright Handling

Attribution belongs in the skill description and reference `Sources:` lines.

Detailed package attribution is tracked in `assets/ATTRIBUTION.md`, including the CC BY-NC-SA 3.0 notice for the canonical 97 Things material and the package's original synthesis boundary.

Do not quote long passages. Avoid sentence-level paraphrase. Prefer new decision tables, checklists, and examples written for agent behavior.

When a concept overlaps an existing Tank skill, route to that skill rather than restating its full knowledge base.

## Practical Use

When updating this skill, update the ledger first. If a new Medium step URL is discovered, add it to the ledger and mark the status, but keep canonical coverage unless the Medium content has an explicit reusable license.

If any row becomes `blocked-needs-review`, do not publish new synthesized guidance for that item until coverage is resolved.

## Coverage Groups

| Range | Focus |
| ----- | ----- |
| 1-17 | prudence, standards, simplicity, refactoring, sharing, domain language, review, comments |
| 18-34 | learning, deployment, exceptions, practice, DSLs, test data, errors, culture, DRY, state |
| 35-52 | API design, humility, bug trackers, code removal, installability, IPC, build, tools, commits, data, estimation |
| 53-74 | linking, interim solutions, interfaces, visibility, message passing, polymorphism, testers, binaries, build ownership, types, professionalism, version control, reading code, performance |
| 75-97 | reduction, SRP, automation, analysis tools, tests, state, collaboration, Unix tools, algorithms, logging, supportability, small functions, customer ambiguity |

## Maintenance Rules

1. Keep the ledger at exactly 97 rows unless the canonical source changes.
2. Keep author attribution aligned with the canonical source when it differs from the Medium page.
3. Mark source limitations explicitly.
4. Prefer original examples over source-derived examples.
5. Keep this file factual; put professional guidance in the thematic references.

## Full Coverage Index

This table intentionally lists every roadmap item so reviewers can verify that no item disappeared during clustering. The thematic reference files synthesize these items into working agent guidance; this index only tracks coverage.

| # | Item | Thematic Reference |
| - | ---- | ------------------ |
| 1 | Act with Prudence | `professional-principles.md` |
| 2 | Apply Functional Programming Principles | `simplicity-and-design.md` |
| 3 | Ask What Would the User Do | `collaboration-and-process.md` |
| 4 | Automate Your Coding Standard | `tools-and-automation.md` |
| 5 | Beauty Is in Simplicity | `simplicity-and-design.md` |
| 6 | Before You Refactor | `refactoring-and-removal.md` |
| 7 | Beware the Share | `correctness-and-state.md` |
| 8 | The Boy Scout Rule | `refactoring-and-removal.md` |
| 9 | Check Your Code First | `professional-principles.md` |
| 10 | Choose Your Tools with Care | `tools-and-automation.md` |
| 11 | Code in the Language of the Domain | `simplicity-and-design.md` |
| 12 | Code Is Design | `simplicity-and-design.md` |
| 13 | Code Layout Matters | `simplicity-and-design.md` |
| 14 | Code Reviews | `collaboration-and-process.md` |
| 15 | Coding with Reason | `professional-principles.md` |
| 16 | A Comment on Comments | `simplicity-and-design.md` |
| 17 | Comment Only What the Code Cannot Say | `simplicity-and-design.md` |
| 18 | Continuous Learning | `professional-principles.md` |
| 19 | Convenience Is not an -ility | `conflict-resolution.md` |
| 20 | Deploy Early and Often | `tools-and-automation.md` |
| 21 | Distinguish Business Exceptions from Technical | `correctness-and-state.md` |
| 22 | Do Lots of Deliberate Practice | `professional-principles.md` |
| 23 | Domain-Specific Languages | `simplicity-and-design.md` |
| 24 | Don't Be Afraid to Break Things | `refactoring-and-removal.md` |
| 25 | Don't Be Cute with Your Test Data | `testing-and-verification.md` |
| 26 | Don't Ignore that Error | `correctness-and-state.md` |
| 27 | Understand Language Culture | `professional-principles.md` |
| 28 | Don't Nail Your Program Upright | `correctness-and-state.md` |
| 29 | Don't Rely on Magic | `simplicity-and-design.md` |
| 30 | Don't Repeat Yourself | `conflict-resolution.md` |
| 31 | Don't Touch that Code | `refactoring-and-removal.md` |
| 32 | Encapsulate Behavior | `simplicity-and-design.md` |
| 33 | Floating-point Numbers Aren't Real | `correctness-and-state.md` |
| 34 | Fulfill Ambitions with Open Source | `collaboration-and-process.md` |
| 35 | Golden Rule of API Design | `simplicity-and-design.md` |
| 36 | The Guru Myth | `collaboration-and-process.md` |
| 37 | Hard Work Does not Pay Off | `professional-principles.md` |
| 38 | How to Use a Bug Tracker | `tools-and-automation.md` |
| 39 | Improve Code by Removing It | `refactoring-and-removal.md` |
| 40 | Install Me | `tools-and-automation.md` |
| 41 | IPC Affects Response Time | `performance-and-systems.md` |
| 42 | Keep the Build Clean | `tools-and-automation.md` |
| 43 | Command-line Tools | `tools-and-automation.md` |
| 44 | Know More Than Two Languages | `professional-principles.md` |
| 45 | Know Your IDE | `tools-and-automation.md` |
| 46 | Know Your Limits | `professional-principles.md` |
| 47 | Know Your Next Commit | `tools-and-automation.md` |
| 48 | Data Belongs to a Database | `performance-and-systems.md` |
| 49 | Learn Foreign Languages | `professional-principles.md` |
| 50 | Learn to Estimate | `performance-and-systems.md` |
| 51 | Learn to Say Hello World | `tools-and-automation.md` |
| 52 | Let Your Project Speak | `collaboration-and-process.md` |
| 53 | Linker Is not Magic | `tools-and-automation.md` |
| 54 | Longevity of Interim Solutions | `professional-principles.md` |
| 55 | Interfaces Easy Correctly | `simplicity-and-design.md` |
| 56 | Make the Invisible Visible | `correctness-and-state.md` |
| 57 | Message Passing Scalability | `correctness-and-state.md` |
| 58 | Message to the Future | `professional-principles.md` |
| 59 | Missing Polymorphism | `simplicity-and-design.md` |
| 60 | Testers Are Your Friends | `collaboration-and-process.md` |
| 61 | One Binary | `tools-and-automation.md` |
| 62 | Only the Code Tells the Truth | `professional-principles.md` |
| 63 | Own and Refactor the Build | `tools-and-automation.md` |
| 64 | Pair Program and Flow | `collaboration-and-process.md` |
| 65 | Domain-Specific Types | `simplicity-and-design.md` |
| 66 | Prevent Errors | `correctness-and-state.md` |
| 67 | Professional Programmer | `professional-principles.md` |
| 68 | Everything Under Version Control | `tools-and-automation.md` |
| 69 | Step Away from Keyboard | `professional-principles.md` |
| 70 | Read Code | `professional-principles.md` |
| 71 | Read the Humanities | `collaboration-and-process.md` |
| 72 | Reinvent the Wheel Often | `professional-principles.md` |
| 73 | Resist Singleton | `correctness-and-state.md` |
| 74 | Dirty Performance Code Bombs | `performance-and-systems.md` |
| 75 | Simplicity from Reduction | `simplicity-and-design.md` |
| 76 | Single Responsibility Principle | `simplicity-and-design.md` |
| 77 | Start from Yes | `collaboration-and-process.md` |
| 78 | Automate Repeated Work | `tools-and-automation.md` |
| 79 | Code Analysis Tools | `tools-and-automation.md` |
| 80 | Required Behavior Tests | `testing-and-verification.md` |
| 81 | Precise Concrete Tests | `testing-and-verification.md` |
| 82 | Test While You Sleep | `testing-and-verification.md` |
| 83 | Testing Is Engineering Rigor | `testing-and-verification.md` |
| 84 | Thinking in States | `correctness-and-state.md` |
| 85 | Two Heads Better Than One | `collaboration-and-process.md` |
| 86 | Two Wrongs Difficult to Fix | `correctness-and-state.md` |
| 87 | Coding for Friends | `collaboration-and-process.md` |
| 88 | Unix Tools Are Friends | `tools-and-automation.md` |
| 89 | Right Algorithm and Data Structure | `performance-and-systems.md` |
| 90 | Verbose Logging Disturbs Sleep | `performance-and-systems.md` |
| 91 | WET Dilutes Bottlenecks | `performance-and-systems.md` |
| 92 | Programmers and Testers Collaborate | `collaboration-and-process.md` |
| 93 | Support Code Forever | `professional-principles.md` |
| 94 | Small Functions Using Examples | `simplicity-and-design.md` |
| 95 | Tests for People | `testing-and-verification.md` |
| 96 | Care About the Code | `professional-principles.md` |
| 97 | Customers Do not Mean What They Say | `collaboration-and-process.md` |

## Source Review Checklist

Use this checklist when updating the package:

1. Re-fetch the Medium roadmap and confirm direct link count.
2. Re-fetch canonical `SUMMARY.md` and confirm the 97 paths still exist.
3. Compare item titles against the ledger.
4. Confirm every title-only Medium item has canonical coverage.
5. Confirm every reference file still maps back to this index.
6. Confirm new examples are original and not source-derived prose.
7. Confirm attribution remains concise and accurate.
8. Confirm no source limitation is hidden in a footnote.
9. Confirm validation fails if the ledger loses a row.
10. Confirm `source-coverage.md` changes whenever source policy changes.

## Ledger Field Contract

| Field | Required Meaning | Validation |
| ----- | ---------------- | ---------- |
| item_number | Stable 1-97 roadmap index | Present and unique |
| title | Roadmap or canonical title | Non-empty |
| author | Original attribution | Non-empty |
| main_page_url | User-provided roadmap | Medium roadmap URL |
| medium_step_url | Direct URL listed on fetched roadmap | Optional |
| discovered_medium_step_url | URL found outside roadmap | Optional |
| medium_read_status | Access status | Enum only |
| canonical_source_url | Complete CC source path | Raw GitHub URL |
| coverage_status | Coverage basis | Enum only |
| notes | Source limitation | Concise |

## Status Semantics

| Status | Use When | Consequence |
| ------ | -------- | ----------- |
| read | Medium step fetched successfully | May inform understanding |
| missing | No Medium URL available | Use canonical coverage |
| inaccessible | URL fetch failed | Use canonical coverage |
| paywalled | Login/payment required | Use canonical coverage |
| duplicate | URL repeats another item | Use canonical coverage |
| not-applicable | Medium intentionally excluded | Explain in notes |

## Source Risks

| Risk | Symptom | Mitigation |
| ---- | ------- | ---------- |
| Partial reading | Rows lack statuses | Block publication |
| Source drift | Branch URLs change | Pin if automated |
| Copyright leakage | Prose resembles source | Rewrite as procedures |
| Over-compression | Slogans replace guidance | Use thematic references |
| Over-expansion | Duplicates specialists | Cross-route |

## Ingestion Procedure

1. Fetch the main Medium roadmap and record direct link count.
2. Fetch canonical summary and confirm 97 paths.
3. Fetch each direct Medium step article when accessible.
4. Do not package fetched Medium article bodies.
5. Use canonical paths for stable item coverage.
6. Update ledger before guidance.
7. Regenerate coverage counts after ledger changes.
8. Keep limitations visible.
9. Do not infer URLs for title-only rows.
10. Prefer original examples.
11. Review licensing before changing attribution.
12. Separate provenance from recommendation.
13. Fail validation when row count differs from 97.
14. Fail validation when status enum is invalid.
15. Fail validation when canonical URL is absent.
16. Pin source URLs if CI fetches them.
17. Block publish on unresolved rows.
18. Use this file as map, not content dump.
19. Keep claims traceable to ledger rows.
20. Avoid distinctive source phrasing.

## Source Responsibility Boundaries

| Need | Route | Do Not Duplicate |
| ---- | ----- | ---------------- |
| Deep code smell recipe | @tank/clean-code | Full refactoring catalog |
| BDD/E2E proof | @tank/bdd-e2e-testing | Framework setup |
| Security boundary | @tank/security-review | OWASP/CWE audit |
| Database performance | @tank/relational-db-mastery | Index tuning |
| Mechanical transform | @tank/ast-linter-codemod or js-tools | AST/LSP details |

## Coverage Case Patterns

| Case | Professional Move |
| ---- | ----------------- |
| Direct Medium link | Record URL and read status, keep canonical URL too. |
| Title-only Medium row | Mark Medium missing and use canonical coverage. |
| Fetch failure | Mark inaccessible instead of inventing coverage. |
| Canonical drift | Update all rows consistently if source paths move. |
| License concern | Rewrite as original guidance and avoid source examples. |
| Ledger count change | Block validation until exactly 97 rows are restored. |
| Discovered URL | Add without replacing canonical source. |
| Source summary mismatch | Update counts and status semantics together. |
| Blocked row | Stop publication and ask for review. |
| Runtime fetching proposal | Pin source URLs before automation. |
