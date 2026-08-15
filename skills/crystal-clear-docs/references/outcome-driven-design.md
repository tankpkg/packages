# Outcome-Driven Documentation Design

Sources: Wiggins and McTighe (Understanding by Design), Lovett et al. (How Learning Works), National Academies (How People Learn II), Neelen and Kirschner (Evidence-Informed Learning Design), Dunlosky and Rawson (The Cambridge Handbook of Cognition and Education), Pinker (The Sense of Style)
Covers: Diagnose the need, define task and transfer outcomes, design backward from evidence, select an appropriate document type, align content with authentic use, and evaluate results.

Evidence boundary: Apply learning and instructional-design findings as mechanisms and design hypotheses. Much of the research comes from courses, training, or controlled studies rather than static technical pages. Validate transfer to the actual audience, task, medium, and time horizon.

## Start With the Performance Need

Treat documentation as an intervention, not as an automatic response to every problem.

Ask what people must do differently, where they must do it, and what currently prevents them.

Do not begin with a topic list, a requested format, or an inventory of available material.

Begin with the gap between current and desired performance.

Separate four commonly conflated needs:

| Observed need | Diagnostic question | Likely response |
| --- | --- | --- |
| Access | Do readers know enough but fail to find facts at the moment of use? | Improve retrieval, navigation, labels, search, or point-of-work support |
| Execution | Do readers know what to do but face missing tools, permissions, time, incentives, or coordination? | Repair the environment or workflow; do not prescribe more explanation |
| Learning | Must readers build knowledge or skill that persists beyond the document? | Design explanation, guided practice, feedback, and later application |
| Judgment | Must readers choose among cases where no fixed procedure is sufficient? | Teach principles, contrasts, criteria, and decision practice |

Diagnose before writing because a polished learning document cannot fix a missing permission, broken interface, contradictory policy, or absent incentive.

Use evidence from actual work when possible:

- Observe representative tasks and failure points.
- Inspect support requests, error patterns, search terms, and abandoned workflows.
- Ask performers what cues they use and where uncertainty begins.
- Compare successful and unsuccessful outputs against real criteria.
- Confirm whether the problem persists when information is available at the point of need.

Treat stakeholder requests as hypotheses.

Translate "we need a guide" into a testable performance statement before accepting the format.

### Distinguish Performance Support From Learning

Choose performance support when readers can consult the document during work and do not need fluent recall.

Choose learning support when delay, risk, workload, or context makes consultation impractical, or when readers must recognize situations independently.

Combine both when readers need a durable model plus precise operational details.

| Situation | Favor point-of-work support | Favor durable learning |
| --- | --- | --- |
| Rare, stable procedure | Checklist or runbook | Only if failure has severe consequences |
| Frequent recurring task | Concise reference may remain useful | Build fluency and exception handling |
| High-stakes response | Add an executable protocol | Rehearse recognition, judgment, and recovery |
| Rapidly changing facts | Keep facts external and maintainable | Teach stable principles and update detection |
| Novel troubleshooting | Provide diagnostic trees and telemetry references | Build causal models and case comparison |
| Policy compliance | Surface required actions at decision points | Explain rationale when interpretation is required |

Do not equate memorization with learning value.

Externalize details that are cheap and safe to look up.

Develop internal knowledge when it enables recognition, inference, speed, or transfer.

## Define the Intended Change

Define learning as a durable change in knowledge or capability, inferred cautiously from later behavior rather than from exposure to content.

Infer that change from later performance rather than from page views or self-reported familiarity alone.

Write the outcome from the reader's point of view:

> Given [realistic situation and available resources], the reader can [observable task or judgment] to [quality criteria], including [important variation or exception].

Make the conditions explicit.

Specify whether readers may search, use tools, consult teammates, or follow a checklist.

Avoid testing unaided recall if real performance permits reference use.

Specify the product or consequence that demonstrates success.

Avoid weak outcomes such as "understand the system," "know the policy," or "be aware of the feature" unless you define what that understanding enables.

Keep four outcomes distinct:

| Outcome | Appropriate evidence | Do not infer automatically |
| --- | --- | --- |
| Immediate comprehension | Accurate paraphrase, inference, or prediction now | Durable retention |
| Supported performance | Correct task completion with the document and normal tools | Unaided capability |
| Durable learning | Relevant knowledge or capability remains available after delay | Broad transfer |
| Transfer | Correct performance under a meaningfully changed case | Reliability in every context |

Treat one observation as evidence under its tested conditions, not proof of every outcome.

### Define Task, Knowledge, and Judgment

Decompose an outcome only far enough to expose what the document must support.

| Outcome component | Ask | Documentation implication |
| --- | --- | --- |
| Whole task | What meaningful result must the reader produce? | Anchor the document in the complete workflow |
| Constituent actions | Which steps must be coordinated? | Show sequence, dependencies, and handoffs |
| Concepts | What relationships must make sense? | Explain a model, not a glossary alone |
| Recognition cues | What tells the reader which action applies? | Include symptoms, thresholds, and contrasts |
| Quality criteria | What distinguishes acceptable from unsafe or incomplete? | Show standards, examples, and nonexamples |
| Exceptions | Where does the normal path fail? | Integrate branches near the relevant decision |
| Recovery | How can the reader detect and correct failure? | Add verification and rollback guidance |

Keep the whole task visible while teaching parts.

Avoid fragmenting a complex performance into disconnected pages that never show coordination.

## Specify Transfer Deliberately

Treat transfer as a design target, not an automatic by-product of clear explanation.

Define the distance between the documented example and the future use.

| Transfer dimension | Near transfer | Farther transfer |
| --- | --- | --- |
| Context | Same tool and environment | Different tool, team, or environment |
| Time | Immediate use | Delayed use |
| Function | Same task | Related but structurally different task |
| Representation | Same labels and interface | Different terminology or surface features |
| Support | Same prompts available | Fewer prompts or independent recognition |

Do not claim broad transfer from success on a copied example.

Expect transfer to weaken as surface cues, time, function, and support diverge.

Design for the actual transfer distance:

- State the underlying principle after grounding it in a concrete case.
- Compare cases that share structure but differ in surface details.
- Contrast similar-looking cases that require different actions.
- Name the cues that determine applicability.
- Explain where an analogy breaks.
- Ask readers to predict, decide, or diagnose before revealing the answer.
- Fade prompts only when independent performance is required.

Do not teach a supposedly generic skill without the domain knowledge that makes the skill usable.

Critical thinking, troubleshooting, and judgment depend on relevant knowledge structures.

## Design Backward From Evidence

Use three linked stages:

| Stage | Design question | Required artifact |
| --- | --- | --- |
| Desired result | What should readers be able to do or decide later? | Outcome statement with conditions and criteria |
| Acceptable evidence | What performance would justify confidence? | Authentic task, checks, and scoring criteria |
| Learning and support | What document experience makes that evidence likely? | Content, examples, practice, navigation, and support |

Do not write content and invent evaluation afterward.

Define acceptable evidence before deciding sections, visuals, or media.

Use the evidence target to remove attractive but irrelevant material.

Reject both coverage-driven and activity-driven design.

Coverage-driven design asks, "What information can we include?"

Activity-driven design asks, "What interactive or visual element can we add?"

Outcome-driven design asks, "What change must occur, and what experience is necessary for it?"

### Define Evidence of Understanding

Distinguish recall from usable understanding.

| Evidence | What it supports | What it does not establish alone |
| --- | --- | --- |
| Recognition | Reader can identify a presented fact or option | Independent recall or application |
| Recall | Reader can reproduce information | Appropriate use in context |
| Explanation | Reader can connect causes, mechanisms, or rationale | Reliable execution under variation |
| Application | Reader can use knowledge in a familiar case | Transfer to materially different cases |
| Diagnosis | Reader can infer causes from evidence | Ability to implement a remedy |
| Adaptation | Reader can modify an approach under new constraints | Consistency across future situations |
| Self-correction | Reader can detect and repair an error | Prevention of all initial errors |

Match evidence to the intended outcome.

Use multiple forms of evidence when the task combines knowledge, execution, and judgment.

Do not use satisfaction, completion, engagement, or perceived learning as substitutes for performance evidence.

Treat those measures as implementation signals, not proof of learning.

## Build Authentic Tasks

Define authenticity by correspondence to consequential work, not by visual realism alone.

Consider five dimensions:

| Dimension | Design question |
| --- | --- |
| Task | Does the reader perform the same kind of thinking and action used in practice? |
| Physical or technical context | Are the relevant tools, constraints, noise, and interfaces represented? |
| Social context | Are collaboration, approval, communication, and handoffs represented? |
| Output | Does the task produce the artifact or consequence expected in practice? |
| Criteria | Is performance judged by standards that matter in the real setting? |

Simplify an authentic task without stripping away the decisions that make it authentic.

Remove incidental complexity first.

Retain consequential cues, tradeoffs, and failure modes.

For learning experiences that support multiple attempts, use worked examples for unfamiliar tasks, then offer partially completed and independent cases when independent action matters.

Use scenarios when context changes the correct response.

Use nonexamples when common outputs look plausible but violate an important criterion.

Do not make practice artificially difficult merely to appear rigorous.

Preserve the difficulty inherent in the target judgment while removing difficulty caused by unclear wording or irrelevant detail.

## Select the Document Type From the Outcome

Choose the smallest document system that supports the real task.

| Reader need | Primary document type | Essential design feature |
| --- | --- | --- |
| Complete a known procedure now | How-to guide | Ordered actions, prerequisites, verification, recovery |
| Look up an exact fact | Reference | Stable labels, exhaustive definitions, searchability |
| Build a causal or conceptual model | Explanation | Relationships, mechanisms, diagrams, examples |
| Choose among alternatives | Decision guide | Criteria, tradeoffs, branches, boundary cases |
| Respond consistently under pressure | Checklist or runbook | Short executable steps, stop conditions, escalation |
| Learn a new end-to-end capability | Tutorial or guided walkthrough | Coherent task, scaffolding, feedback, transfer prompt |
| Diagnose a failure | Troubleshooting guide | Symptoms, evidence collection, causal branches, recovery |
| Adopt a changed policy or behavior | Change guide | Rationale, changed actions, migration path, consequences |

Split document types when their reading modes conflict.

Do not bury lookup material inside a narrative tutorial.

Do not force conceptual explanation into terse procedural steps when readers need a model to handle exceptions.

Link layers through task language so readers can move from action to explanation without losing context.

## Align Every Element

Build an alignment matrix before drafting or during revision.

| Outcome | Evidence | Content or support | Authentic variation | Evaluation signal |
| --- | --- | --- | --- | --- |
| State one observable capability | Name the proving performance | Include only enabling knowledge and guidance | Add a relevant change in context | Record a behavior tied to the outcome |

Check alignment in both directions.

For every content block, identify the outcome it enables.

For every outcome, identify sufficient content, support, and evidence.

Remove orphan content that serves no outcome.

Repair orphan outcomes that have no path to mastery.

Avoid decorative interactivity, diagrams, or examples that attract attention without helping readers select, organize, integrate, or apply information.

Treat media as a means, never as the strategy itself.

## Write for Use, Not Display

Present the subject as something the reader can inspect, reason about, and act on.

Follow Pinker's practical implication of classic style: direct attention to the thing being explained rather than to the author's process of explaining it.

Make actors, actions, objects, and causal relations explicit.

Do not hide uncertainty behind nominalizations or institutional abstractions.

State assumptions and boundaries where they change the decision.

Prefer a concrete case before a compressed abstraction when the abstraction depends on expert knowledge.

Name the principle after the case so readers can recognize it elsewhere.

## Evaluate the Document as an Intervention

Evaluate at several levels without conflating them.

| Level | Question | Useful evidence |
| --- | --- | --- |
| Reach | Did the intended readers encounter the document? | Search discovery, entry paths, audience coverage |
| Usability | Could readers find and interpret what they needed? | Task observation, findability failures, comprehension checks |
| Learning | Did readers build durable knowledge or skill? | Delayed explanation, application, or retrieval |
| Transfer | Could readers perform under realistic variation? | Novel cases, workplace outputs, reduced assistance |
| Performance | Did the target result improve? | Error rate, cycle time, quality, escalation, rework |
| System effect | Did the intervention create new costs or risks? | Maintenance burden, misuse, inequitable access, downstream failures |

Use baseline evidence when available.

Compare performance against explicit criteria rather than against impressions of polish.

Inspect failures for design information:

- If readers cannot find the right page, repair information architecture.
- If readers find it but misread it, repair wording, representation, or assumed knowledge.
- If readers explain it but cannot act, add authentic application and decision cues.
- If readers act in the example but fail elsewhere, strengthen transfer design.
- If readers can act but do not, investigate incentives, access, workflow, or trust.
- If successful readers stop using the document, determine whether they learned or merely abandoned it.

Do not interpret lower page views as failure when the intended performance requires fewer visits.

Do not interpret high page views as success when repeated visits signal poor retrieval or unresolved confusion.

### Use Evidence-Informed Iteration

Combine three sources of evidence:

| Evidence source | Contribution | Limitation |
| --- | --- | --- |
| Research | Supplies mechanisms, tested principles, and boundary conditions | May not match the exact audience or environment |
| Local data | Reveals real behavior, constraints, and outcomes | Can be noisy, incomplete, or confounded |
| Practitioner judgment | Integrates context and feasibility | Can preserve habit, bias, or fashionable myths |

Require the three sources to challenge one another.

Do not copy a technique solely because it worked elsewhere.

Ask what mechanism it relies on and whether the relevant conditions hold here.

Document uncertainty when evidence is indirect.

Run a small, consequential test before scaling a costly design.

Revise the outcome, evidence, or intervention when results expose a faulty assumption.

## Outcome Design Review

Use this review before publication:

- Confirm that the problem is actually addressable through documentation.
- State the desired performance in observable terms.
- Define the conditions and resources available during real use.
- Specify required transfer distance instead of assuming transfer.
- Choose evidence that matches the intended capability.
- Represent an authentic task, output, context, and quality standard.
- Select the document type from the reader's need.
- Align every section and medium with an outcome.
- Separate implementation signals from learning and performance evidence.
- Plan evaluation across usability, learning, transfer, and system effects.
- Record boundary conditions and unresolved assumptions.
- Remove content that exists only because it was available.

Treat publication as the start of evidence collection, not the end of design.
