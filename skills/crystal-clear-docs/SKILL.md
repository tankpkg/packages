---
name: "@tank/crystal-clear-docs"
description: |
  Design technical documentation that readers can find, understand, use, and
  transfer to new situations. Covers outcome-driven document design, reader and
  mental-model analysis, prior knowledge and misconceptions, cognitive load,
  worked examples, multimedia learning, behavioral writing, navigation, and
  evidence-informed validation. Synthesizes Mayer, Lovett et al., How People Learn
  II, Wiggins and McTighe, Neelen and Kirschner, Dunlosky and Rawson, Rogers and
  Lasky-Fink, and Pinker.

  Trigger phrases: "crystal clear docs", "clear documentation",
  "explain this clearly", "teach this concept", "help readers understand",
  "improve this guide", "technical writing", "write a tutorial",
  "write a how-to guide", "documentation psychology", "fix confusing docs",
  "reader mental model", "add a diagram", "documentation usability",
  "make this easier to learn", "write a runbook", "safety-critical docs",
  "architecture page", "retry boundaries"
---

# Crystal Clear Docs

Create documentation that produces the intended reader outcome, not merely a
polished page.

## Core Philosophy

1. **Define the change before the content.** State what readers must find,
   decide, explain, or do and what evidence would demonstrate success.
2. **Design for the reader's current model.** New information is interpreted
   through prior knowledge, misconceptions, goals, language, and context.
3. **Expose structure, not just facts.** Make entities, relationships, causes,
   constraints, decisions, and applicability conditions visible.
4. **Match support to expertise.** Give novices explicit guidance and
   experienced readers direct access to dense reference and boundary cases.
   Fade support only in adaptive, facilitated, or multi-attempt experiences.
5. **Validate performance, not polish.** "Looks clear" is weak evidence. Ask
   representative readers to find, explain, predict, execute, or adapt.

Learning research supplies mechanisms and design hypotheses, not universal
page rules. Much of the evidence comes from instruction and controlled studies;
validate each application with the actual audience, task, medium, and delay.

## Task Router

| Request | Start with |
| --- | --- |
| Diagnose or design a document system | `references/outcome-driven-design.md` |
| Teach a concept or correct a misconception | `references/reader-mental-models.md`, then `references/layered-writing.md` |
| Write a runbook or safety-critical procedure | `references/document-structure.md`, then `references/reader-mental-models.md` |
| Design an architecture or process diagram | `references/svg-diagrams.md` |
| Rewrite confusing prose | `references/writing-clarity.md` |
| Repair navigation or layout | `references/document-structure.md` |

## Workflow

### 1. Diagnose the Need

Identify the observed performance gap before accepting "write documentation"
as the solution.

- Fix tools, permissions, incentives, or workflow when information is not the
  blocker.
- Use reference or point-of-work support when readers only need retrieval.
- Use instruction when readers must retain, reason, judge, or transfer.

See `references/outcome-driven-design.md`.

### 2. Define Outcome and Evidence

Write an observable outcome:

> Given [situation and resources], the reader can [task or judgment] to
> [quality criteria], including [important variation].

Define the proof before outlining the page. Match evidence to the goal: lookup,
execution, explanation, diagnosis, adaptation, or transfer.

### 3. Model the Reader

Record only dimensions that change a design decision:

- Domain and task knowledge
- Knowledge organization and likely misconceptions
- Goals, value, confidence, and agency
- Language, tools, environment, access, risk, and culture
- What novices need exposed and experts can safely skip

See `references/reader-mental-models.md`.

### 4. Choose the Documentation Job

| Reader need | Primary form | Optimize for |
| --- | --- | --- |
| Find an exact fact | Reference | Search, stable labels, completeness |
| Complete a known task | How-to | Actions, decisions, checks, recovery |
| Learn an end-to-end capability | Tutorial | Guided task, feedback, fading |
| Explain behavior | Concept page | Causal model, examples, prediction |
| Choose among options | Decision guide | Criteria, contrasts, boundaries |
| Recover from failure | Troubleshooting guide | Evidence, causes, tests, remedies |
| Respond under pressure | Runbook | Safe sequence, stop conditions, escalation |

Split incompatible jobs instead of forcing one page to serve all of them.

### 5. Build Understanding

When understanding or transfer matters:

1. Activate or supply prerequisites.
2. State the governing question or useful idea.
3. Explain the causal or structural model.
4. Show a worked example with decisions and reasons.
5. Contrast an example, nonexample, near miss, or boundary case.
6. Prompt prediction or self-explanation where it exposes the model.
7. Fade guidance and vary the case when independent use matters.
8. Provide answer criteria, automated checks, or human feedback where the
   delivery medium supports them.

A static page cannot observe competence or personalize feedback. It can offer
worked, partial, and independent variants, but the reader or an external system
must choose the appropriate stage and evaluate the result.

See `references/layered-writing.md`.

### 6. Select Representations by Cognitive Job

| Relationship | Useful representation |
| --- | --- |
| Cause, qualification, argument | Prose |
| Ordered action | Numbered procedure |
| Exact executable form | Code |
| Aligned comparison or lookup | Table |
| Flow, state, hierarchy, space, interaction | Diagram |
| Change over time or quantity | Appropriate chart |

Add words and visuals when they complement each other. Signal structure, keep
corresponding elements close, segment meaningful complexity, pretrain notation
when needed, and provide accessible alternatives.

See `references/svg-diagrams.md`.

### 7. Write and Arrange for Use

- Put the topic, point, action, or consequence where readers encounter it early.
- Use concrete actors, verbs, objects, conditions, and outcomes.
- Shape sentences around clear relationships, not word-count quotas.
- Move from familiar information to new information.
- Use headings, lists, tables, callouts, links, and emphasis only when they
  expose meaning or reduce action friction.
- Preserve coherent prose when causality or qualification matters.
- Test the rendered document on the media readers actually use.

See `references/writing-clarity.md` and `references/document-structure.md`.

## Common Problems

### "Readers can copy the example but cannot adapt it"

Expose the governing principle and decision cues. Add a near miss, a changed
case, and an explanation prompt. Fade copied steps before testing transfer.

### "Beginners are lost but experts find it tedious"

Keep one source of truth but provide different entry paths: concise reference
for experienced readers and skippable prerequisites, reasoning, and worked
examples for novices. Never hide safety conditions in the novice path.

### "The page is easy to scan but nobody understands it"

Restore coherent relationships. Lists and headings help navigation; they do not
replace causal explanation, examples, contrasts, and integration with prior
knowledge.

### "The explanation feels clear, but we cannot tell if it worked"

Test the target performance. Ask readers to paraphrase the model, predict a
result, complete the task, diagnose a fresh failure, or choose under changed
constraints. Observe errors and revise where understanding breaks.

## Quality Gate

- [ ] Confirm documentation can address the actual problem.
- [ ] State an observable reader outcome and matching evidence.
- [ ] Identify required prior knowledge and likely misconceptions.
- [ ] Choose structure and representation from the reader's task.
- [ ] Preserve conditions, boundaries, and safety-critical nuance.
- [ ] Distinguish lookup, execution, and durable understanding.
- [ ] Distinguish immediate comprehension, supported execution, durable
  learning, and transfer; one successful attempt does not prove all four.
- [ ] Make success and recovery observable.
- [ ] Support access across relevant devices and assistive technologies.
- [ ] Validate with representative readers and realistic tasks.

## Example

See the [Async Export Documentation Set](assets/examples/async-export-docs/README.md)
for a layered, multi-file example with concept, task, reference,
troubleshooting, runbook, diagram, and validation-plan outputs.

## Reference Index

| File | Contents |
| --- | --- |
| `references/outcome-driven-design.md` | Performance diagnosis, backward design, transfer, evidence, document types, alignment, evaluation |
| `references/reader-mental-models.md` | Prior knowledge, mental models, misconceptions, expertise, motivation, culture, metacognition |
| `references/layered-writing.md` | Explanation sequencing, worked examples, contrasts, scaffolding, retrieval, feedback, transfer |
| `references/svg-diagrams.md` | Multimedia learning, diagram selection, signaling, integration, accessibility, Mermaid, SVG |
| `references/writing-clarity.md` | Attention, concrete prose, sentence geometry, coherence, action friction, behavioral editing |
| `references/document-structure.md` | Document types, reading modes, semantic chunks, navigation, code, responsive and accessible layout |
