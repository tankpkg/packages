# Reader Mental Models

Sources: Lovett et al. (How Learning Works), National Academies (How People Learn II), Dunlosky and Rawson (The Cambridge Handbook of Cognition and Education), Neelen and Kirschner (Evidence-Informed Learning Design), Pinker (The Sense of Style)
Covers: Model readers across relevant dimensions, activate and repair prior knowledge, support coherent knowledge organization, address misconceptions and expertise reversal, and account for motivation, culture, context, and metacognition.

## Model the Reader as a System

Reject the idea of a single average reader.

Model variation that changes how the document will be interpreted or used.

Do not reduce readers to job titles, generations, personality types, or preferred "learning styles."

Treat reader characteristics as interacting conditions, not fixed labels.

| Dimension | Diagnostic question | Possible design consequence |
| --- | --- | --- |
| Domain knowledge | What concepts, facts, and patterns can readers already use? | Adjust explanation, examples, and assumed vocabulary |
| Task experience | Have readers performed this task in real conditions? | Adjust scaffolding, exception coverage, and verification |
| Knowledge organization | Are facts connected into a usable model? | Add structure, causal relations, comparisons, or maps |
| Beliefs and misconceptions | Which existing explanations compete with the intended one? | Elicit, contrast, refute, and replace |
| Language and discourse | Which terms, genres, and conventions are familiar? | Define local language and expose tacit conventions |
| Goals and value | Why would readers invest effort here? | Lead with relevant stakes and useful outcomes |
| Expectancy and agency | Do readers believe success is possible and controllable? | Add achievable entry points, feedback, and choices |
| Social position and identity | Does the document signal belonging, authority, or exclusion? | Revise examples, voice, assumptions, and access |
| Physical and technical context | Where, when, and on what device will reading occur? | Adjust navigation, density, format, and offline support |
| Metacognitive skill | Can readers judge whether they understand and select a strategy? | Add checks, criteria, and recovery prompts |

Build personas only when they encode evidence about these consequential dimensions.

Discard decorative persona details that do not alter a design decision.

### Gather Reader Evidence

Prefer behavior over speculation.

Use multiple signals:

- Observe readers attempting representative tasks.
- Ask readers to explain what they think is happening before correcting them.
- Collect terms readers search for rather than only terms experts prefer.
- Inspect recurring errors for underlying rules or beliefs.
- Compare novice and expert navigation paths.
- Identify where readers seek reassurance, stop, or escalate.
- Note environmental constraints such as interruptions, device size, latency, or privacy.
- Ask what a successful result looks like in the reader's own context.

Do not infer understanding from fluent conversation alone.

Ask for prediction, explanation, classification, or application that reveals the underlying model.

Treat user preference as one input, not as proof of learning effectiveness.

Readers can accurately report friction and goals while misjudging which presentation produces durable understanding.

## Diagnose Prior Knowledge

Treat prior knowledge as the foundation on which readers interpret every sentence.

Classify its state before deciding how much context to add.

| Prior-knowledge state | Reader behavior | Documentation response |
| --- | --- | --- |
| Accurate and activated | Applies relevant concepts at the right moment | Build directly and avoid redundant scaffolding |
| Accurate but inert | Knows the fact but does not recognize when it applies | Add cues, scenarios, and applicability conditions |
| Insufficient | Lacks prerequisites needed to interpret the explanation | Provide pretraining or link a prerequisite path |
| Inappropriate | Activates a familiar but irrelevant analogy or procedure | Contrast contexts and mark the boundary |
| Inaccurate | Uses a flawed rule or causal account | Elicit, challenge, and replace the model |
| Fragmented | Recalls pieces without relationships | Supply an organizing structure and integration prompts |

Do not treat all gaps as missing facts.

A reader may possess the facts yet organize them in a way that blocks application.

### Activate Relevant Knowledge

Use activation when readers already have a useful foundation but may not retrieve it spontaneously.

Choose a cue that matches the future use:

- Ask a short prediction before the explanation.
- Name a familiar situation that shares the target structure.
- Present a diagnostic question that exposes the relevant distinction.
- Briefly recap prerequisites in the language used on this page.
- Link the new concept to an existing workflow or artifact.
- Show where the new item fits in a familiar system.

Keep activation focused.

Do not invite a broad brainstorm that activates irrelevant associations.

Do not assume a hyperlink activates knowledge; state the minimum prerequisite relation at the point of use.

### Supply Missing Prerequisites

Pretrain the names, roles, and relationships of essential components before explaining a complex process.

Use prerequisite links when readers can pause and learn separately.

Use inline reminders when switching pages would break the task.

Make prerequisite status visible:

| Prerequisite type | Best support |
| --- | --- |
| Term needed to parse the next sentence | Define inline |
| Small relationship needed throughout | Add a compact model or recap |
| Independent foundational skill | Link a distinct prerequisite guide |
| Tool setup required before action | Put in prerequisites and verify explicitly |
| Optional depth for advanced reasoning | Place in a linked explanation |

Avoid recursive prerequisite chains with no clear starting point.

Offer a stable entry route for readers who lack the assumed base.

## Design the Intended Knowledge Organization

Do not present information as a pile of facts and expect readers to infer expert structure.

Experts tend to organize knowledge around deep principles, causal relations, and conditions of use.

Novices tend to rely more on surface features, literal labels, and the order in which information appeared.

Expose the structure that supports the target reasoning.

| Target reasoning | Useful organization |
| --- | --- |
| Explain why something happens | Cause-and-effect chain or mechanism |
| Execute a process | Sequence with states, decisions, and feedback loops |
| Compare alternatives | Matrix using decision-relevant dimensions |
| Classify a case | Hierarchy with defining and distinguishing features |
| Understand a system | Components, relations, flows, and boundaries |
| Diagnose failure | Symptom-to-cause network with disconfirming evidence |
| Apply a principle | Principle linked to varied cases and limits |
| Plan work | Goal, dependencies, constraints, and checkpoints |

Choose one primary organization for the main explanation.

Add secondary views only when readers must transform between them.

Keep labels and relations consistent across prose, diagrams, examples, and navigation.

Do not use a diagram merely to repeat nearby prose.

Use it when spatial arrangement makes relationships easier to inspect.

### Support Mental Model Construction

Treat comprehension as active model building.

Help readers select relevant elements, organize them, and integrate them with prior knowledge.

Signal what matters without turning every sentence into emphasis.

Make causal links explicit when experts might silently infer them.

Use examples to instantiate a model, not to substitute for one.

Pair a principle with more than one meaningfully varied case when transfer matters.

Use a contrast case to reveal which features are structural and which are incidental.

Ask readers to explain why a step or decision follows when that inference is central.

Do not overload the model with every exception during first construction.

Establish the normal structure, then attach exceptions at the point they modify it.

### Detect Fragmented Models

Look for these signals:

- Readers can repeat definitions but cannot predict consequences.
- Readers execute steps but cannot recover when the interface changes.
- Readers recognize examples but cannot classify a new case.
- Readers mention many components but omit relations among them.
- Readers use the correct rule only when the page uses identical wording.
- Readers cannot explain why a prohibited action is unsafe.

Respond by repairing organization, not by adding more disconnected facts.

## Address Misconceptions as Competing Models

Treat a durable misconception as an explanatory model that may be coherent and useful in some familiar situations.

Do not assume that stating the correct fact will erase it.

Avoid foregrounding a misconception without making the correction and replacement model more prominent.

Use a replacement sequence:

1. Elicit or name the reader's likely prediction.
2. Show a case where that prediction fails or becomes incomplete.
3. Explain the mechanism behind the discrepancy.
4. Present the replacement model clearly.
5. Apply the replacement to a new case.
6. Mark situations where the old shortcut still appears plausible.

Keep the correction respectful.

Attack the model, not the reader's intelligence or identity.

### Classify the Error Before Correcting It

| Error type | Example pattern | Repair strategy |
| --- | --- | --- |
| Missing distinction | Treats two related terms as interchangeable | Compare them on a consequential case |
| Overgeneralization | Applies a valid rule outside its boundary | State conditions and show a boundary case |
| Faulty causality | Attributes an outcome to the wrong mechanism | Trace causal evidence and competing predictions |
| Surface analogy | Maps visible similarities while missing structural differences | Compare relation-by-relation and mark the break |
| Procedural habit | Repeats an obsolete sequence despite changed conditions | Interrupt with recognition cues and replacement practice |
| Identity-linked belief | Treats correction as a threat to group or self | Reduce threat, establish shared goals, and preserve agency |

Use examples of actual errors when privacy and safety permit.

Explain why the wrong answer feels reasonable.

That explanation helps readers notice the same trap later.

Do not promise instant correction for deeply rehearsed beliefs.

Provide repeated opportunities to choose the replacement model in relevant contexts.

## Adapt for Expertise Without Creating Two Truths

Treat expertise as domain-specific and uneven.

A reader may be expert in the business domain and novice in the tool, or the reverse.

Do not infer broad expertise from seniority or title.

Account for expertise reversal: guidance that supports novices can become redundant, slow, or distracting for knowledgeable readers.

| Design element | Novice value | Expert risk | Adaptive response |
| --- | --- | --- | --- |
| Worked example | Reduces unguided search | Repeats an automated procedure | Make it skippable and link from the concise path |
| Definitions | Establishes shared vocabulary | Interrupts fluent reading | Define inline once and provide reference access |
| Step-by-step instructions | Supports coordination | Obscures exceptions and intent | Offer a compact checklist plus expanded steps |
| Explanatory diagram | Builds a system model | Restates a familiar model | Lead with the decision or delta for experts |
| Frequent prompts | Directs attention | Creates friction and loss of agency | Fade or collapse prompts by experience level |
| Basic examples | Ground abstraction | Fail to challenge judgment | Add advanced boundary and failure cases |

Layer by reader need rather than duplicating entire manuals.

Provide a fast path that preserves safety-critical conditions.

Provide an expanded path that explains rationale, prerequisites, and examples.

Keep canonical facts and policy in one maintained location.

Do not hide essential warnings in beginner-only material.

For safety-critical documents, validate both paths separately:

- Ask a representative novice to execute the expanded path without coaching.
- Ask an experienced operator to use the fast path under realistic pressure.
- Confirm both paths preserve the same hazards, stop conditions, authority, and verification criteria.
- Treat any safety condition missed by either audience as a structural failure.

### Avoid the Curse of Knowledge

Apply Pinker's warning that writers struggle to imagine what readers do not know.

Audit expert drafts for invisible assumptions:

- Undefined actors, objects, states, or acronyms.
- Causal steps compressed into "therefore," "simply," or "obviously."
- Procedures that begin after an unmentioned setup step.
- Categories whose distinguishing features remain tacit.
- Examples that require insider history to make sense.
- References such as "this," "it," or "the process" with ambiguous antecedents.
- Nominalized actions that conceal who does what.

Ask a representative reader to paraphrase, not merely approve, the draft.

Ask experts to state what they noticed that a novice might not notice.

Use those cues as explicit teaching targets.

## Design for Motivation and Agency

Treat motivation as a dynamic interaction among value, expectancy, goals, identity, and environment.

Do not label readers as motivated or unmotivated without examining the task and context.

| Motivation condition | Reader interpretation | Documentation response |
| --- | --- | --- |
| Low value | "This does not help a goal I care about." | Connect the content to a credible consequence or task |
| Low expectancy | "Even with effort, I cannot succeed." | Clarify prerequisites, reduce initial complexity, and show progress |
| Low agency | "The outcome is controlled by others." | Expose choices, escalation paths, and controllable actions |
| Goal conflict | "Other work matters more right now." | Support scanning, defer optional depth, and respect time constraints |
| Threat or non-belonging | "This system was not made for people like me." | Remove deficit framing and signal legitimate participation |
| Distrust | "The source or policy is not credible." | State authority, evidence, rationale, limits, and update history |

Lead with relevance, not hype.

Explain why the task matters to the reader's work or decision.

Make success criteria visible so effort feels directed.

Provide meaningful choices where multiple valid routes exist.

Do not manufacture engagement with decorative stories, jokes, or images unrelated to the model.

Interesting but extraneous details can compete with essential processing.

## Account for Culture and Context

Treat learning and interpretation as culturally situated.

Do not frame cultural difference as a deficit inside the reader.

Examine both the reader and the document's own assumptions.

| Context factor | Audit question |
| --- | --- |
| Language | Does fluency in the document language differ from domain competence? |
| Authority | Are readers expected to question, comply, negotiate, or seek approval? |
| Collaboration | Is the task individual in the document but collective in practice? |
| Risk | What social, legal, financial, or physical cost accompanies a mistake? |
| Access | Can readers reach the document, tools, links, and examples in their environment? |
| Time | Are readers studying, scanning during work, or responding under pressure? |
| Local practice | Do examples assume one region, organization, or technical stack? |
| Identity | Do examples and labels imply who belongs or who is competent? |

Separate universal claims from local conventions.

Label organization-specific policy as policy, not as an inherent property of the domain.

Explain unfamiliar discourse practices such as how to read a log, interpret a standard, or challenge a decision.

Use asset framing: connect new material to knowledge readers developed in work, community, language, or adjacent domains.

Test translations and localized examples for conceptual equivalence, not word substitution alone.

Preserve reader dignity in error messages, warnings, and prerequisite guidance.

## Support Metacognition

Do not assume that readers accurately know whether they understand.

Fluent prose and familiar examples can create confidence without transferable knowledge.

Support a self-regulation cycle:

| Phase | Reader question | Documentation support |
| --- | --- | --- |
| Plan | What am I trying to accomplish, and what do I need? | Outcomes, prerequisites, route choices |
| Monitor | Am I following and producing the expected result? | Predictions, checkpoints, observable states |
| Evaluate | Does my result meet the criteria? | Verification, examples, rubrics, tests |
| Adjust | What should I do if it does not? | Diagnosis, recovery, alternate explanations, escalation |

Use checks that reveal the quality of the mental model.

Prefer "What would happen if this input changed, and why?" over "Does this make sense?"

Ask readers to compare their output with explicit criteria.

Provide feedback that identifies the gap and the next useful action.

Distinguish confidence from evidence.

Encourage readers to predict before checking the answer when prediction is safe and relevant.

Make stopping rules explicit so readers know when to seek help rather than persist with a faulty model.

Avoid turning every page into a quiz.

Add metacognitive support where miscalibration would cause meaningful error or block transfer.

## Validate the Reader Model

Treat the reader model as a revisable hypothesis.

Test it with representative people and authentic tasks.

Look for mismatches between assumed and observed behavior.

| Observation | Likely model error | Revision direction |
| --- | --- | --- |
| Readers skip background and fail later | Prerequisites are invisible or poorly placed | Surface a concise dependency at the decision point |
| Readers reread but cannot explain | Structure is fragmented | Add relations, mechanism, or a coherent overview |
| Readers follow steps but choose the wrong branch | Recognition cues are underspecified | Add contrasts and conditions of applicability |
| Experts abandon the page | Scaffolding dominates the fast path | Layer detail and foreground expert decisions |
| Novices copy without adapting | Example surface features dominate | Extract the principle and vary the next case |
| Readers reject a correction | Misconception carries value, identity, or trust | Address threat, evidence, and replacement model |
| Readers report clarity but fail a new case | Fluency was mistaken for understanding | Add prediction, application, and delayed checks |

Segment findings by consequential dimensions rather than by demographics alone.

Do not generalize from one vocal reader when evidence shows meaningful variation.

Preserve alternate paths when different reader states genuinely require different support.

## Reader Model Review

Use this review before publication:

- Identify the reader dimensions that alter design decisions.
- Verify prior knowledge rather than assuming it from title or tenure.
- Distinguish accurate, inert, insufficient, inappropriate, inaccurate, and fragmented knowledge.
- Activate only knowledge relevant to the target model.
- Expose deep structure, causal relations, and conditions of use.
- Pair principles with varied cases when transfer matters.
- Treat misconceptions as competing models that require replacement.
- Layer novice support and expert access without duplicating truth.
- Audit the draft for the curse of knowledge.
- Connect effort to value, expectancy, agency, and meaningful goals.
- Inspect cultural, linguistic, social, and environmental assumptions.
- Add metacognitive checks where confidence can diverge from performance.
- Validate the model through paraphrase, prediction, application, and observed use.
- Revise the reader model when behavior contradicts it.

Design for readers as active sense-makers whose knowledge, goals, identities, and contexts shape what the document becomes in use.
