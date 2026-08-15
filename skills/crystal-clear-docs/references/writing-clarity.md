# Behavioral Writing and Cognitive Prose

Sources: Todd Rogers and Jessica Lasky-Fink (Writing for Busy Readers), Steven Pinker (The Sense of Style), Google Technical Writing Courses, and Steve Krug (Don't Make Me Think).

Covers: Shape prose around the reader's desired action and limited attention. State the topic and point early, write concrete and coherent sentences, reduce action friction, edit without rigid word quotas, and test whether readers understand and act.

## Begin With the Reader Outcome

Define what the reader should know, decide, feel, or do after reading.

Write the outcome as an observable result:

> After reading, an on-call engineer can identify the failing dependency and choose the safe recovery command.

Avoid outcomes that describe only the document:

> This page provides an overview of incident recovery.

Use the outcome to decide what belongs. Keep information that changes the reader's understanding, choice, or action. Remove information that serves only the writer's wish to appear complete.

Ask these questions before drafting:

- Who will read this in the moment that matters?
- What prompted them to open it?
- What do they already know?
- What uncertainty blocks them?
- What action or judgment should become easier?
- What could they misunderstand with serious consequences?

Treat the reader's situation as part of the writing problem. A calm learner, an executive choosing an option, and an engineer responding to an outage need different prose even when the facts are identical.

## Respect the Attention Budget

For operational, workplace, and action-oriented documents, assume attention may be scarce, interrupted, and goal-directed. Deliberate study and specification review permit deeper reading but still benefit from visible structure.

Do not demand attention before delivering value. Put the information that helps the reader orient or act where they can encounter it early.

Spend attention deliberately:

| Reader cost | Justify it with |
| --- | --- |
| A new term | Greater precision or a reusable concept |
| A long explanation | A decision that depends on the reasoning |
| An exception | A likely or costly failure it prevents |
| A cross-reference | Useful depth that would distract from the current task |
| A qualification | Accuracy that materially changes interpretation |

Formatting supports prose; it does not rescue weak prose. Use short sections, descriptive labels, and selective emphasis to expose meaning, not to decorate the page.

Make the first visible text earn continued attention. Tell readers what subject they have reached, why it matters to them, and what the central point is.

## Put the Topic and Point Early

Name the topic before discussing its attributes. State the point before presenting the trail of reasoning when readers need the conclusion to interpret the evidence.

Weak opening:

> After several weeks of analysis across teams, during which we reviewed latency, cost, and operational burden, a number of findings emerged about the current queue design.

Stronger opening:

> The current queue design cannot meet the recovery target. It loses too much time retrying permanent failures. The analysis below explains the evidence and the replacement options.

Use an early point to create a frame, not to erase nuance. Add the most important condition in the same opening when it changes the recommendation.

For a request, lead with the requested action:

> Approve the database maintenance window by Thursday so the migration can run before the release freeze.

For an explanation, lead with the governing idea:

> Token rotation limits the damage from a stolen refresh token by invalidating its predecessor after use.

For a warning, lead with the consequence:

> Do not retry this command after a timeout; the first request may still be deleting records.

Delay the point only when discovery is the intended experience or when readers must inspect evidence without being anchored by a conclusion. Treat that choice as deliberate, not habitual.

## Make Value Truthful and Visible

Describe the value the document actually provides. Do not inflate convenience into certainty, imply safety without evidence, or promise simplicity while hiding necessary work.

Replace promotional claims with useful specifics:

| Vague claim | Truthful value |
| --- | --- |
| "Seamlessly integrates" | "Uses the existing OAuth connection; no second login is required" |
| "Instant results" | "Returns cached results in under a second in the common path" |
| "Easy to configure" | "Requires one environment variable and no code changes" |
| "Production ready" | "Supports retries, idempotency, and regional failover tested in staging" |

State tradeoffs beside benefits. Readers trust guidance that identifies where it stops being useful.

Prefer evidence over intensifiers. Replace "very reliable" with the observed failure rate, tested condition, or recovery behavior that supports the claim.

## Use Concrete Language

Make actors, actions, objects, and conditions visible.

Abstract:

> Appropriate optimization of resource utilization should be undertaken.

Concrete:

> Reduce each worker from 2 GB to 1 GB after its peak memory stays below 700 MB for seven days.

Prefer verbs that show what changes: `delete`, `compare`, `encrypt`, `retry`, `approve`, and `measure`. Question noun-heavy phrases such as "implementation of," "facilitation of," and "performance of."

Name the actor when responsibility matters:

> The deployment workflow creates the revision. The service owner approves traffic migration.

Use passive voice when the actor is unknown, irrelevant, or intentionally backgrounded:

> The signing key was exposed in a public log.

Choose examples with realistic names, values, constraints, and consequences. A concrete example should illuminate the rule rather than introduce accidental complexity.

Define unfamiliar terms in the context where the reader needs them. Do not interrupt experts with definitions of ordinary domain language, but do not make newcomers leave the page to decode a critical instruction.

## Counter the Curse of Knowledge

Assume expertise has hidden steps from you.

Look for knowledge that became invisible through repetition:

- A tool the reader may not have installed
- A permission the writer already possesses
- A state transition omitted between two commands
- A term used differently across teams
- A reason an apparently simpler option is unsafe
- A cue experts notice but novices do not

Do not solve the curse of knowledge by explaining everything. Identify the minimum background required for this reader outcome, then supply or link that background at the point of need.

Use a fresh reader to reveal hidden assumptions. Ask them to mark every point where they guess, reread, search elsewhere, or wonder whether a step succeeded.

When no representative reader is available, simulate their path:

1. Start from the stated prerequisites, not your own environment.
2. Follow each reference and command in order.
3. Record every unstated choice.
4. Check whether the visible result confirms progress.
5. Rewrite assumptions as prerequisites, instructions, or verification cues.

## Shape Sentence Geometry

Judge sentences by how their parts fit, not by a universal word limit.

Let a sentence carry one governing relationship that readers can hold in working memory. Add detail when it remains attached to a clear subject and verb. Split the sentence when qualifications compete, the subject disappears, or the reader must retain one clause while decoding another.

Overloaded:

> Because the migration, which was designed before regional replicas were available and therefore assumes a single writer, can replay events while traffic remains live, operators who begin the cutover before replication catches up may create duplicate records that are not removed automatically.

Reshaped:

> The migration assumes a single writer because it predates regional replicas. It can replay events while traffic remains live. If operators start the cutover before replication catches up, the replay may create duplicate records. Cleanup is not automatic.

Vary sentence length to match thought. Use a short sentence for a decision, warning, or transition. Use a longer sentence when its internal structure makes a relationship easier to understand than several disconnected statements would.

Keep modifiers near what they modify. Put conditions before an instruction when readers must know the condition before acting. Put secondary qualifications after the main clause when they should not delay comprehension.

## Manage Given and New Information

Begin a sentence with information readers already recognize, then move toward what is new or important.

Disconnected:

> A regional lease protects each write. The recovery controller may revoke it. Split-brain writes are prevented by the lease token.

Coherent:

> Each write carries a regional lease token. The recovery controller can revoke that token during failover. This revocation prevents split-brain writes.

Use familiar information as a handhold. Repeat a key noun when a pronoun could point to several things. Avoid unnecessary synonym changes that make one concept look like several concepts.

Place emphasis near the end of a sentence or paragraph when possible. Readers naturally treat the ending as the destination of the thought.

## Build Coherence Across Paragraphs

Give each paragraph a discernible job: make a claim, explain a mechanism, present evidence, qualify a rule, or derive a consequence.

Open with enough context to identify that job. Keep supporting sentences attached to it. Start a new paragraph when the discourse function changes, not when a numeric sentence target has been reached.

Maintain a visible line of reasoning:

1. State the claim or question.
2. Supply the reason, mechanism, or evidence.
3. Address the condition that changes it.
4. Connect the result to the reader's decision or action.

Use repeated key terms, parallel syntax, and explicit references to keep the subject stable. Do not rely on visual proximity alone to imply a logical relationship.

## Use Connectives to Expose Logic

Add connectives when the relationship between ideas is not already obvious.

| Relationship | Useful signals |
| --- | --- |
| Cause | because, since, as a result |
| Contrast | but, however, whereas |
| Condition | if, unless, only when |
| Evidence | for example, specifically, in the trace |
| Consequence | therefore, so, which means |
| Sequence | first, after, once, while |
| Qualification | usually, except, in this case |

Choose the connective that states the actual logic. Do not use "however" merely to vary prose or "therefore" when the conclusion does not follow.

Remove connective clutter when order and syntax already make the relationship plain. Clarity comes from visible logic, not from filling every transition slot.

## Reduce Action Friction

Writing for action requires more than explaining accurately. Make the desired behavior easy to identify, begin, complete, and verify.

Specify:

- The action and responsible person
- The object or location affected
- The deadline or triggering condition
- The required inputs
- The expected result
- The recovery path when the result differs

High friction:

> Teams should consider updating ownership information where appropriate.

Lower friction:

> Service owners: update the `Owner` field in the catalog before Friday. The catalog displays a green check when the change is saved.

Put links at the action point. Name links by destination or task rather than "click here." Preserve context so readers know what will happen before selecting a link or running a command.

Ask for the smallest meaningful next action. Separate required actions from optional improvements.

## Write Instructions That Support Judgment

Use imperative verbs for procedures: "Open," "Select," "Run," and "Verify."

Explain why when the reason changes how readers execute the step, choose among paths, or recover from failure. Avoid narrating obvious interface mechanics.

Pair consequential actions with boundaries:

> Run the backfill once in each region. Do not rerun a completed region; the script does not deduplicate billing events.

Show success cues after steps whose outcome may be ambiguous:

> Wait until the revision reports `Ready: True`, then send traffic.

Keep warnings before the hazardous action. State the consequence and the safer alternative.

## Calibrate Voice and Tone

Sound like a competent colleague who respects the reader's time.

Use direct address when it clarifies responsibility. Use "we" only for a real shared actor, not as a vague institutional voice.

Be confident about established facts and explicit about uncertainty:

> The cache invalidates within 60 seconds under normal operation. We have not measured invalidation time during a regional failover.

Avoid blame. Describe the state, cause, and remedy without labeling the reader careless or the task easy.

Match urgency to consequence. Reserve forceful language for genuine risk so warnings remain credible.

## Format for Cognitive Access

Use formatting to reveal the prose's structure.

- Use descriptive headings to expose questions, claims, and tasks.
- Use lists for genuinely parallel items or steps.
- Use tables when readers compare values across shared dimensions.
- Use bold sparingly to surface a decisive phrase during scanning.
- Use code style for literal names, values, commands, and symbols.
- Keep related explanation beside the object it explains.

Do not fragment a connected argument into bullets solely to make it look shorter. Do not bold complete paragraphs. Do not create visual variety that competes with the reading path.

Treat line length, spacing, and paragraph shape as contextual design decisions. Test the actual rendering on the devices and surfaces readers use.

## Edit in Behavioral Passes

Separate editing goals so one pass does not hide another.

### Outcome Pass

Check whether the draft enables the intended knowledge, decision, or action. Remove interesting material that does not serve that outcome.

### Point Pass

Move the topic, recommendation, request, or consequence earlier. Confirm that qualifications remain visible and truthful.

### Coherence Pass

Trace the subjects and logic from sentence to sentence. Repair unexplained jumps, ambiguous pronouns, unstable terminology, and missing connectives.

### Sentence Pass

Find buried verbs, distant modifiers, overloaded clauses, empty abstractions, and false emphasis. Reshape the sentence rather than enforcing a word quota.

### Friction Pass

Follow every requested action. Add missing inputs, ownership, links, success cues, and recovery instructions.

### Compression Pass

Cut repetition, throat-clearing, redundant metadata, and detail readers can infer safely. Preserve necessary reasoning and conditions.

Read the result aloud. Listen for breathless structures, accidental ambiguity, monotonous rhythm, and phrases that no colleague would naturally say.

## Test With Readers

Test comprehension and behavior, not preference alone.

Give representative readers a realistic task without explaining the draft. Observe what they do.

Ask them to:

- State the document's point in their own words
- Identify what applies to their situation
- Predict what an instruction will do
- Complete the target task
- Explain how they know they succeeded
- Find a specific fact later without rereading everything

Record hesitations, wrong turns, repeated reading, external searches, and confidently wrong interpretations. These behaviors reveal more than a general rating.

Avoid leading questions such as "Was the warning clear?" Ask "What risks do you see before running this command?"

Revise the prose where several readers fail. Revise navigation or layout when they understand the words but cannot find them. Revise the product when the documentation accurately exposes unnecessary complexity.

## Clarity Review Checklist

- [ ] Name the intended reader and observable outcome.
- [ ] Put the topic and central point where readers encounter them early.
- [ ] Describe value with evidence and material conditions.
- [ ] Use concrete actors, verbs, objects, and consequences.
- [ ] Supply hidden prerequisites without explaining irrelevant basics.
- [ ] Shape sentences around clear relationships rather than numeric limits.
- [ ] Move from given information to new information.
- [ ] Keep terminology stable and references unambiguous.
- [ ] Use connectives where readers need the logic made explicit.
- [ ] Make requested actions specific, located, and verifiable.
- [ ] Use formatting to reveal meaning rather than decorate it.
- [ ] Test whether representative readers understand and act.

## Relationship to Document Structure

Use this reference to decide what each sentence and paragraph must accomplish. Use `document-structure.md` after purpose and prose responsibilities are clear to arrange content for scanning, close reading, lookup, and task completion.
