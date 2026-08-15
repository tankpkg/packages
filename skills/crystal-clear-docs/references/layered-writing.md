# Evidence-Informed Explanation Design

Sources: Richard E. Mayer (Multimedia Learning), Dunlosky and Rawson (The Cambridge Handbook of Cognition and Education), Lovett et al. (How Learning Works), National Academies (How People Learn II), Mirjam Neelen and Paul A. Kirschner (Evidence-Informed Learning Design), Grant Wiggins and Jay McTighe (Understanding by Design), Barbara Minto (The Pyramid Principle, where useful).

Covers: Design explanations for lookup, execution, and durable understanding; sequence prerequisite knowledge and causal models; use worked examples, contrasts, scaffolding, retrieval, feedback, and transfer checks to support outcomes that can be evaluated.

Evidence boundary: Treat these principles as evidence-informed adaptations. Most source studies concern instruction, training, or controlled learning tasks. A static document cannot diagnose mastery, schedule practice, or deliver personalized feedback unless another person or system supplies those functions.

## Start with the Reader's Intended Performance

Define what the reader must do after reading before deciding how to organize the page.

Replace broad goals such as "understand caching" with observable performances:

- Identify when a cache can return stale data.
- Configure a cache safely for one endpoint.
- Predict what happens after invalidation fails.
- Diagnose a low hit rate from logs and request patterns.
- Choose between local and distributed caching for a new service.

Use backward design:

1. Specify the desired performance.
2. Decide what evidence would demonstrate that performance.
3. Identify the knowledge and reasoning required.
4. Design explanation, practice, and feedback around that evidence.
5. Remove content that does not support the performance.

Do not equate content coverage with learning; the presence of a definition, example, or diagram does not show that a reader can use it.

## Distinguish Three Documentation Jobs

Choose the dominant job of each page or section.
Do not force every reader through the same instructional sequence.

| Job | Reader question | Primary design | Evidence of success |
| --- | --- | --- | --- |
| Lookup | "What is the exact value or syntax?" | Searchable, concise, stable reference | Reader finds the correct fact quickly |
| Execution | "How do I complete this task?" | Goal-oriented procedure with checks | Reader completes the task correctly |
| Understanding | "Why does this behave this way?" | Prerequisites, causal model, examples, practice | Reader explains, predicts, and transfers |

### Design Lookup Content

Optimize lookup content for retrieval from the document, not memorization.

- Use specific headings that match likely search terms.
- Put exact syntax, defaults, constraints, and return values near each other.
- Use tables when readers compare fields across a stable schema.
- Keep examples adjacent to the referenced option.
- Link to explanatory material instead of embedding a lesson in every entry.
- Preserve canonical terminology so search remains reliable.

Test lookup content by asking a representative reader to find a fact under time pressure, then measure whether the answer is found and interpreted correctly.

### Design Execution Content

Organize procedures around a concrete outcome.

- State the end state and prerequisites before the first action.
- Use action-oriented steps in the order the system requires.
- Show expected output at consequential checkpoints.
- Explain decisions where different inputs require different actions.
- Put recovery guidance beside failure-prone steps.
- End with a verification that tests the real outcome.

Do not interrupt an execution path with long conceptual digressions.
Link or defer deeper explanations unless the concept is required to choose the next action safely.

### Design Understanding Content

Build a model the reader can reason with.

- Activate relevant prior knowledge.
- Supply missing prerequisites.
- Explain entities, relations, mechanisms, and constraints.
- Demonstrate reasoning through worked examples.
- Contrast cases that differ on a decisive feature.
- Prompt the reader to explain and predict.
- Test application in a changed context.

Treat understanding as a family of usable capabilities, such as explaining, interpreting, applying, predicting, diagnosing, adapting, or taking a relevant perspective. Select evidence from the intended outcome; repeating vocabulary alone is insufficient.

## Diagnose Prior Knowledge Before Adding Detail

Prior knowledge shapes what readers notice, how they organize new information, and what they infer.
It can help, remain inert, or actively mislead.

Audit the intended audience:

| Prior-knowledge state | Evidence | Design response |
| --- | --- | --- |
| Missing | Reader cannot interpret foundational terms | Teach or link the prerequisite first |
| Inactive | Reader knows the idea but does not apply it | Prompt recall and connect it explicitly |
| Fragmented | Reader knows isolated facts without relations | Organize facts into a causal or structural model |
| Inaccurate | Reader predicts the wrong outcome consistently | Expose the misconception with a discriminating case |
| Sufficient | Reader can explain prerequisite relationships | Compress review and move to application |

Avoid the expert blind spot: experts compress familiar steps into chunks and may omit decisions novices still need to make.

Run a prerequisite audit:

1. Write the target performance.
2. List every decision required to perform it.
3. For each decision, list the facts, concepts, and cues it depends on.
4. Mark likely novice gaps and misconceptions.
5. Teach only the prerequisites that the target performance requires.

## Sequence for Meaning, Not Merely Simplicity

Sequence content so each part enables the next act of reasoning.

Use these relationships deliberately:

| Relationship | Sequence | Example |
| --- | --- | --- |
| Prerequisite | Foundation before dependent concept | Identity before authorization rules |
| Causal | Cause, mechanism, consequence | Retry load before retry storms |
| Procedural | Required action order | Create key, configure client, verify signature |
| Structural | Whole, parts, relations | Request lifecycle before middleware internals |
| Comparative | Shared frame before differences | Common queue semantics before provider tradeoffs |
| Increasing variability | Stable case before changed conditions | Single process before distributed coordination |

Do not assume "simple to complex" identifies the correct order.
A simple fact can be useless until the reader sees the problem it explains.

## Build a Causal Model

Name the parts of the system and explain how they interact over time.

A useful causal explanation answers:

1. What entities participate?
2. What state does each entity hold?
3. What event initiates change?
4. What mechanism transforms the state?
5. What constraint limits the mechanism?
6. What observable consequence follows?
7. Under what conditions does the explanation stop applying?

Prefer mechanism statements over labels.

Weak:

> The service experiences cache stampede.

Stronger:

> When a popular key expires, concurrent requests all miss before any request repopulates the value. Each request then starts the same expensive database query, multiplying load during the expiry window.

The stronger explanation supports prediction.
A reader can infer that request coalescing or staggered expiry changes the outcome.

## Use Progressive Disclosure by Purpose

Preserve progressive disclosure when it helps readers enter at the right depth.
Do not treat it as a universal top-to-bottom gradient.

Provide separate paths when readers have different goals:

```text
Concept page: model, mechanism, examples, transfer
Task guide: prerequisites, actions, checks, recovery
Reference: exact syntax, constraints, defaults
```

Within an understanding page, disclose complexity in model-preserving layers:

1. State the phenomenon and useful governing idea.
2. Introduce the minimum entities and relationships.
3. Demonstrate the mechanism in a representative case.
4. Add boundary conditions and exceptions.
5. Ask the reader to apply the model to a varied case.

Keep each shorter layer accurate; do not omit an exception when the omission would produce unsafe action or a false prediction.

Use expandable sections for optional evidence, derivations, or environment-specific details.
Do not hide prerequisites, decision criteria, or verification steps.

## Design Worked Examples Around Reasoning

Use worked examples when a task contains interacting steps or unfamiliar decisions.
Show not only what to do, but how to decide.

A complete worked example includes:

- The goal and initial state.
- The cues that matter.
- The rule or principle selected.
- Each action or inference.
- The reason for consequential steps.
- The resulting state.
- A check against the goal.

### Worked Example: Diagnose a Retry Storm

**Scenario:** A client retries failed requests three times with no delay. A dependency slows down but remains available.

**Reasoning:**

1. Observe that failures are transient and concurrent across many clients.
2. Identify immediate retries as additional demand during the same degraded period.
3. Predict that each original request can create three more requests.
4. Infer that increased demand further reduces dependency capacity.
5. Choose exponential backoff with jitter to spread retries over time.
6. Verify by comparing request amplification and dependency latency before and after the change.

**Governing principle:** A retry policy must reduce synchronized load, not merely repeat an operation.

**Boundary:** Do not retry non-idempotent operations without a deduplication strategy.

This example exposes decisions and constraints rather than presenting configuration as magic.

## Pair Examples with Nonexamples and Contrasts

One positive example often leaves the category boundary unclear.
Use contrasts to reveal which feature controls the outcome.

| Pattern | Purpose | Prompt |
| --- | --- | --- |
| Example | Demonstrate a valid application | "Why does this satisfy the rule?" |
| Nonexample | Expose a violation | "Which condition fails?" |
| Near miss | Isolate one decisive difference | "What single change would make it valid?" |
| Counterexample | Limit an overgeneralized claim | "Where does the rule stop applying?" |
| Varied example | Show surface changes with deep structure preserved | "What remains the same?" |

Keep irrelevant differences low when teaching a new distinction.
Increase surface variation later to support transfer.

Example for idempotency:

- Example: `PUT /users/42` sets the complete user representation; repeating it leaves the same state.
- Nonexample: `POST /charges` creates a new charge on every successful repetition.
- Near miss: `POST /charges` with a stable idempotency key can return the prior result instead of creating another charge.
- Contrast question: Which property matters, the HTTP verb or the effect of repetition?

Use the answer to correct shallow rules such as "POST is never idempotent."

## Scaffold Performance, Then Fade Support

Supply temporary support that lets readers perform reasoning they cannot yet complete independently.

Use scaffolds such as:

- A decision checklist.
- A partially completed example.
- Labeled reasoning steps.
- A diagnostic question sequence.
- A template with prompts.
- Immediate feedback on a first attempt.

In an adaptive tutorial, course, or facilitated sequence, fade support as competence grows:

| Stage | Reader activity | Support |
| --- | --- | --- |
| Model | Study a fully worked example | All decisions and reasons shown |
| Complete | Fill selected missing steps | Critical cues remain visible |
| Practice | Solve a similar case | Short checklist available |
| Vary | Solve a changed case | Only the goal and constraints remain |
| Transfer | Solve an unfamiliar case | No procedural prompts |

Do not remove support according to a fixed page count or schedule.
Fade when performance shows that the support is no longer needed.

In a static document, provide clearly labeled worked, completion, and independent variants. Let readers choose a path and include answer criteria; do not claim that the page itself detected competence or adapted guidance.

Avoid permanent scaffolds that prevent independent judgment.
A template is harmful when readers fill fields without understanding why they exist.

## Prompt Self-Explanation

Ask readers to explain relationships, choices, and errors in their own words.
Self-explanation helps integrate new information with prior knowledge and exposes gaps.

Use focused prompts:

- Why is this step necessary?
- Which evidence supports this diagnosis?
- What would change if this assumption were false?
- How does this result follow from the mechanism?
- Which part of the example maps to the governing principle?
- Why is the tempting alternative wrong here?

Place prompts after meaningful chunks, not after every sentence.
Require an explanation that can be checked against criteria.

Avoid vague prompts such as "Do you understand?" Recognition and confidence are weak evidence of understanding.

## Add Retrieval, Not Just Rereading

Prompt readers to recall or reconstruct important ideas without looking at the answer.
Retrieval strengthens access to knowledge and reveals what remains unavailable.

Use low-cost retrieval in documentation:

- Ask for a prediction before revealing the outcome.
- End a section with two or three recall questions.
- Ask readers to recreate a decision rule from a new scenario.
- Provide troubleshooting symptoms and require a likely cause.
- Insert a delayed checkpoint after related material.

Separate retrieval from lookup; do not require memorization of values that readers should safely retrieve from reference material.

Retrieve durable structures instead:

- Mechanisms.
- Decision criteria.
- Failure signatures.
- Safety constraints.
- Relationships among concepts.

Provide the answer after an honest attempt and explain why it is correct.

## Design for Transfer

Test whether the reader can apply the underlying principle when surface details change.

Move through increasing distance:

1. Repeat the same structure with different values.
2. Change irrelevant surface features.
3. Combine the principle with another constraint.
4. Present a context where the principle competes with another goal.
5. Ask the reader to identify when the principle does not apply.

Example transfer sequence for rate limiting:

- Configure a fixed limit for one public endpoint.
- Choose a key for limits shared across multiple instances.
- Protect a costly operation where requests have unequal cost.
- Balance abuse prevention against bursty legitimate traffic.
- Explain why client-side throttling alone does not enforce a server limit.

Do not label a near-copy as transfer.
Change the cues enough that the reader must recognize deep structure.

## Provide Feedback That Advances the Model

Make feedback timely enough to connect with the reader's decision when the medium supports feedback.
Explain the gap between the response and the target, then identify a next action.

| Feedback type | Useful content | Avoid |
| --- | --- | --- |
| Outcome | Whether the result met the criterion | Praise without evidence |
| Process | Which reasoning step succeeded or failed | Restating the answer only |
| Cue | Which signal the reader missed | Giving away every later step |
| Strategy | A better approach for the next attempt | General advice such as "be careful" |
| Self-regulation | How to check work independently | Dependence on an expert grader |

Use automated validation, answer explanations, peer review, or instructor feedback according to the delivery context. A static page can provide criteria and model answers but cannot identify a reader's actual error without an external response mechanism.

For an incorrect diagnosis, explain which observation contradicts it.
For a correct guess, still ask for the mechanism or evidence.

Do not overload feedback with every possible improvement.
Prioritize the misconception or decision that most affects future performance.

## Verify Learning and Document Quality

Align verification with the intended performance.

| Intended outcome | Weak check | Stronger check |
| --- | --- | --- |
| Recall a constraint | Reread the warning | State the constraint without looking |
| Execute a task | Confirm steps were read | Inspect the resulting system behavior |
| Explain a mechanism | Repeat the definition | Predict an outcome and justify it |
| Diagnose a failure | Recognize a shown answer | Diagnose a fresh case from evidence |
| Choose an approach | List options | Select under constraints and defend the tradeoff |
| Transfer a principle | Repeat the example | Apply it in a structurally similar new domain |

Use teach-back as evidence only when the explanation includes relationships and predictions.
Verbatim repetition does not demonstrate a usable model.

Collect evidence from real readers where practical:

- Search success for lookup pages.
- Task completion and error recovery for procedures.
- Prediction accuracy and justification for conceptual explanations.
- Performance on varied cases for transfer.
- Recurring support questions after publication.

Revise the explanation at the point where evidence shows a breakdown.
Do not add general detail when the failure is a missing cue, prerequisite, or feedback loop.

## Review for Coherence and Cognitive Demand

Keep the reader's effort directed toward the target model.

Remove or relocate content that introduces terms, stories, or edge cases without supporting the intended performance.
Chunk information around meaningful decisions rather than arbitrary length.
Use consistent names for the same entity.
Signal causal connectors such as "because," "therefore," and "only when."

Review each section with these questions:

1. What must the reader do after this section?
2. Which prerequisite does that performance require?
3. Which relationship or mechanism should the reader build?
4. Where does the explanation model expert reasoning?
5. Which contrast clarifies the boundary?
6. Where does support fade?
7. What must the reader retrieve or explain?
8. How does a varied case test transfer?
9. What feedback follows an error?
10. What observable evidence verifies success?

## Explanation Design Blueprint

Use this blueprint for a concept intended to support durable understanding:

```text
Target performance
  State what the reader will explain, predict, choose, or diagnose.

Prior knowledge
  Name required prerequisites and likely misconceptions.

Organizing question
  Frame the problem the model resolves.

Governing idea
  Give an accurate, useful answer at entry depth.

Causal or structural model
  Explain entities, relations, mechanisms, constraints, and boundaries.

Worked example
  Demonstrate decisions and reasons, then verify the result.

Contrast set
  Add an example, nonexample, near miss, or counterexample.

Guided attempt
  Provide a partial solution, prompts, and targeted feedback.

Independent attempt
  Fade support and vary the context.

Retrieval and self-explanation
  Ask the reader to reconstruct and justify the model.

Transfer check
  Require application under changed surface conditions.

Verification
  Compare observable performance with explicit criteria.
```

Use only the parts required by the intended performance.
Keep lookup and execution paths direct when durable learning is not the reader's goal.
