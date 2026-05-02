# Collaboration and Process

Sources: Henney (ed.), 97 Things Every Programmer Should Know; Gregory on programmer/tester collaboration; Rising on future maintainers; Tank github-issues, bdd-e2e-testing, and clean-code skills

Covers: code review, working with testers, customer requirement clarity, blameless incident analysis, documentation discipline, and honest estimation.

## Operating Standard

Software is a team sport played through technical artifacts. Code is the most durable communication medium on a team — more durable than meetings, Slack threads, or design docs — because it is the only artifact the system actually executes. Everything else is commentary.

Two failure modes dominate professional collaboration. First, defaulting to taste over evidence: "this is bad" or "use best practices" as review feedback creates defensiveness without a path forward. Second, treating other roles as obstacles: testers as a phase that slows shipping, customers as confused, on-call as someone else's problem. Both modes optimize for the appearance of moving fast at the cost of actually shipping reliable systems.

A coding agent's job in this domain is to default to clarity, evidence, and respect — even (especially) when the technical position is correct. A correct point made dismissively gets implemented worse than a correct point made constructively, and the difference is paid by the next maintainer.

## Quick Routing

| Situation | Principle to apply |
| --------- | ------------------ |
| Reviewer left "this is bad" with no alternative | Principle 1: Reviews need evidence and alternatives |
| Tester gets the work after dev complete | Principle 2: Testers are partners, not phases |
| Customer asks for a button, sketch, or specific UI | Principle 3: Customers describe solutions, not outcomes |
| Production incident — looking for the engineer who broke it | Principle 4: Diagnose systems, not people |
| New contributor has to ask Slack to set up the dev env | Principle 5: Documentation belongs at decision boundaries |
| Asked "when can you ship this?" | Principle 6: Estimates are ranges with assumptions |

## Principle 1: Reviews need evidence and alternatives

State: a review comment that names a risk, points at the evidence, and offers a concrete alternative is a contribution. A comment that says "this is bad" is a tax on the author with no path forward.

### What goes wrong without it

Two patterns ruin code review. First, the vague critic: comments like "needs work," "use best practices," or "this is ugly" — true or not, they don't help the author act. The author either guesses what the reviewer meant (often wrong) or pushes back, and the review becomes a back-and-forth where neither side has the data to converge. Second, the rubber-stamp: reviewers who approve without engaging because the comments-without-alternatives style has trained them that engagement is expensive. Real bugs ship because the review process became a ritual.

### Anti-pattern

```
# In a PR review:

reviewer: This is bad.

reviewer: I don't like this approach.

reviewer: Use best practices here.

reviewer: This won't scale.
```

The author cannot act on any of these. "Bad" how? "Don't like" why? "Best practices" which? "Won't scale" — at what load, in which dimension? The author either guesses (and might guess wrong) or pushes back asking for specifics, which often makes the reviewer defensive.

### Better approach

```
# In a PR review:

reviewer: This loop calls the database once per item. With ~1000 items per
          request (see metrics dashboard, p99 batch size), this will issue
          1000+ queries per call, dominating request latency.

          Suggested alternative: prefetch with .select_related("customer", "address")
          on line 23, which collapses to one query. There's a similar pattern
          in src/orders/list.py:45 you could mirror.

          [BLOCKING — this would surface as a P95 latency regression in production.]

---

reviewer: The error message "something went wrong" doesn't help on-call
          diagnose this. Suggested: "payment gateway timeout: order_id={id},
          gateway_response_code={code}, retrying in {n}s" — this matches the
          structured-log format we use elsewhere (see src/payments/errors.py).

          [NON-BLOCKING — useful improvement, not blocking merge.]

---

reviewer: I'd prefer dependency injection here over the singleton, but that's
          taste; the existing code uses singletons consistently. Approving
          as-is; if we ever want to migrate, that's a separate refactor PR.

          [NIT — taste comment, not blocking.]
```

Each comment names the risk, cites evidence, proposes a concrete alternative, and labels its severity. The author can act, push back with their own evidence, or agree — and the review converges on a decision instead of grinding.

### Why this wins

- Reviews become technical conversations with evidence on both sides, not status games.
- The author learns what to look for next time. Reviewers learn to articulate concerns precisely.
- Severity labels (`BLOCKING`, `NON-BLOCKING`, `NIT`) tell the author what must be addressed and what's a preference.
- Real bugs get caught because reviewers are engaged; rubber-stamping disappears.

### Why the alternative loses

- Vague comments either get ignored (real risk slips through) or get over-implemented (author rewrites large parts based on a misread of the comment).
- Reviewers who get pushback without evidence stop leaving comments. The next bug ships unreviewed.
- The author can't tell what's blocking and what's a preference, so they treat everything as blocking, which slows every PR.

### When this principle yields

For genuinely subjective preferences (variable name choices in a small file, formatting that the formatter doesn't enforce), a quick taste comment is fine — but label it as such (`NIT`) so the author knows it's not blocking. The test is whether you'd block merge on this. If yes, give evidence. If no, label clearly.

### Verification

Browse a few recent PRs in the repo. Each comment names a specific risk or alternative; severity is clear; threads converge on a decision in 1-2 round-trips, not 10.

## Principle 2: Testers are partners, not a phase after coding

State: testers help define what "correct" means. Bring them in before code is written, not after. Late-stage testing finds bugs but cannot prevent the architecture that produced them.

### What goes wrong without it

Engineering finishes "the feature" and hands it to QA. QA finds 30 bugs, of which 10 are surface-level (easy fixes) and 20 are architectural (the feature was designed to handle one tenant; QA found that it breaks with multi-tenant data; fixing that requires re-doing the data model). The surface-level bugs ship; the architectural bugs become known issues that recur for a year. Engineering's lesson: "QA blocks releases." QA's lesson: "engineering doesn't think about edge cases." Both are wrong; the process is.

### Anti-pattern

```
Sprint timeline:
  Week 1: Engineering writes code.
  Week 2: Engineering writes more code.
  Week 3: QA tests the feature for the first time.
  Week 4 (panic): QA found problems that require redesign; ship date is tomorrow.
                  Surface bugs fixed, architectural bugs deferred.
```

QA had no influence on the design. By the time they could influence anything, the code was written and changing it was expensive. The bugs they found late were predictable from the requirements — but nobody asked them upfront.

### Better approach

```
Sprint timeline:
  Day 1: Engineering, QA, and PM run a 30-minute Example Mapping session.
         Output: a list of concrete examples covering happy paths, edge cases,
         failure modes, and known awkward cases.
         
         Example output for "user uploads a profile photo":
           - Happy: 2MB JPEG uploads, displays correctly.
           - Boundary: 5MB JPEG (max allowed) uploads.
           - Boundary: 5.0001MB JPEG rejected with clear message.
           - Edge: corrupted JPEG rejected without crashing the server.
           - Edge: PNG with embedded metadata stripped before storage.
           - Edge: animated GIF — what's the policy? Reject? First frame? (PM decision)
           - Failure: storage backend down — graceful retry, no data loss.
           - Multi-tenant: user A uploads; user B in different tenant cannot see it.
           - Compliance: photo deletion request removes from CDN cache too.

  Days 2-7: Engineering writes code AND tests for the agreed examples.
            QA reviews tests as they're written, suggests missing cases.
            Architectural concerns surface in days 2-3, not day 14.

  Days 8-9: QA does exploratory testing, looking for cases nobody listed.
            (This is where their real expertise pays off.)

  Day 10: Ship.
```

Engineering and QA both shaped the design from day 1. The architectural concerns surfaced before they were expensive. QA's exploratory testing in week 2 finds genuinely unexpected issues, not predictable ones.

### Why this wins

- Architectural problems caught on day 2 cost a refactor; on day 14 they cost a re-design.
- Engineering writes more meaningful tests because they're co-authored with someone whose job is finding edge cases.
- QA's late-stage exploratory testing is more valuable because it's looking for the unknown unknowns, not catching the known unknowns engineering forgot.
- The team ships more reliable features in less total elapsed time.

### Why the alternative loses

- "QA tests at the end" is a recipe for either shipping bugs (because there's no time to fix what QA found) or missing dates (because there is time but the fixes are expensive).
- The relationship becomes adversarial. Engineering sees QA as a blocker; QA sees engineering as the source of avoidable bugs.
- Knowledge of edge cases lives only in QA's head, so when QA changes roles, the knowledge is lost.

### When this principle yields

For genuinely small changes with no testable behavior change (a typo fix, a dependency bump with no API surface change), QA involvement is overkill. The test is whether the change has user-visible behavior. If yes, get QA involved at the example-mapping stage.

### Verification

Each non-trivial feature has documented examples (in a feature file, a doc, or a ticket) that were agreed upon before code was written. QA's exploratory time finds new issues, not known-but-unfixed ones.

## Principle 3: Customers describe solutions, not outcomes

State: when a customer asks for "a button to do X," they have already done one design pass on their own and named the result. Treat their request as one possible solution, not the requirement.

### What goes wrong without it

A customer asks for an "export to Excel" button on the orders page. Engineering builds it. Customer files another ticket: "the export takes 5 minutes for our data and times out." Engineering rewrites it for streaming. Customer files another: "I need to schedule it daily at 6am." And another: "I need it emailed to my finance team." Six tickets in, the team realizes the customer never wanted a button — they wanted a daily emailed financial report, and the button was their first guess at how to ask for it.

### Anti-pattern

```
Customer: "Can you add an Export to Excel button on the orders page?"

Engineer: "Sure!"
[Implements button. Ships. Marks ticket closed.]

Customer (3 days later): "It times out for our data."
Engineer: [Adds streaming. Ships.]

Customer (1 week later): "I need it daily."
Engineer: [Adds scheduling. Ships.]

Customer (1 week later): "Can it email to my team?"
Engineer: [Adds email integration. Ships.]

Total: 4 features built, 3 reworks, 1 month elapsed, customer still not fully happy.
```

Each request was treated as a self-contained ask. The team built four features when they should have built one (a scheduled report).

### Better approach

```
Customer: "Can you add an Export to Excel button on the orders page?"

Engineer: "Happy to look into that. Before I start, can I ask:
            - What will you do with the exported data?
            - How often will you export?
            - Who else will see the result?
            - Is there an existing process this would replace?"

Customer: "Our finance team needs a daily report of yesterday's orders by
           category, broken down by region, for their morning standup at 8am.
           Right now I export manually and email it to them, takes me 30 minutes."

Engineer: "OK, the actual outcome you want is 'finance team has yesterday's
           categorized orders waiting in their inbox by 8am every day.' Is that right?"

Customer: "Yes, exactly."

Engineer: "Two options:
            (a) The button you asked for. You keep doing the daily export manually,
                but it's faster than today. Cost: 1 day of work.
            (b) A scheduled report that emails finance directly at 7am with the
                exact format they want. Cost: 3 days of work, but eliminates your
                manual step entirely.
            Which would you prefer?"

Customer: "(b), definitely."
```

The team built the right thing the first time. The customer got a better outcome. The total work was 3 days instead of one month of incremental rework.

### Why this wins

- The customer's actual problem gets solved, not their guessed solution.
- The team builds the right thing once instead of building four wrong things and reworking.
- The customer feels heard, which builds trust for future conversations.
- The team's velocity on customer asks visibly improves because the work is more aligned.

### Why the alternative loses

- Building exactly what was asked for, when the ask is a solution rather than an outcome, leads to incremental rework forever.
- The customer experiences "engineering doesn't get it" even though engineering built exactly what was requested.
- The team's morale drops because every ticket spawns three more.

### When this principle yields

When the customer's ask is genuinely the outcome (e.g., "the page renders the wrong amount; the math is wrong"), there's no underlying need to surface — the bug is the bug. The test is whether the request has a measurable user-visible outcome behind it. If yes, ask for the outcome. If no, the request is the outcome.

### Verification

Tickets that describe outcomes ("finance team has yesterday's report by 8am") get implemented in one pass; tickets that describe solutions ("add a button") tend to spawn follow-ups. The team's bug-vs-feature ratio improves when this principle is applied consistently.

## Principle 4: Diagnose systems, not people

State: when a bug ships or an incident happens, the question is not "who broke it?" but "how did the system allow it?" Blame produces defensiveness; system thinking produces process improvements.

### What goes wrong without it

The team's incident postmortems become trials. Engineers stop volunteering for risky work because they don't want to be "the one who caused the outage." Knowledge of what nearly went wrong (and was caught at the last minute) doesn't get shared because admitting near-misses feels like admitting fault. The team's effective risk tolerance drops, and slow caution replaces real safety.

### Anti-pattern

```
Incident postmortem meeting:

Lead: "OK, so the production database went down for 45 minutes. Who
       deployed last?"

Engineer A: "I did, but my change was a small CSS fix..."

Lead: "We need to be more careful. Engineer A, please review your process
       and don't do this again."

Postmortem document:
  Root cause: Engineer A deployed without sufficient testing.
  Action item: Engineer A to review deployment process.
  
Two weeks later: a different engineer deploys a different change, the same
underlying issue causes another outage, and the team is surprised.
```

The "root cause" was a person. People don't change reliably; systems do. The next outage is inevitable because nothing structural changed.

### Better approach

```
Incident postmortem meeting (blameless format):

Facilitator: "Let's reconstruct the timeline first, then look for system
              improvements. No one is on trial here. We want to understand
              what the system permitted, not who pushed which button."

Timeline:
  14:23 - Engineer A deploys a CSS-only change.
  14:24 - Database CPU spikes to 100%.
  14:24 - Alerting fires.
  14:30 - On-call engaged, starts investigating.
  14:42 - Determines the deploy ran a database migration as a side effect.
  14:45 - Rollback deployed.
  15:08 - Database recovers fully.

System causes:
  1. The deployment script ran `prisma migrate deploy` even when the deploy
     was CSS-only. The migration runner did not check whether there were
     pending migrations.
  2. Pending migrations from a different developer's branch were merged the
     previous day, but the database was not migrated until this deploy
     happened to trigger it.
  3. The migration acquired a long-running lock on a hot table, which
     starved production traffic.
  4. Alerting fired but did not include "database migration in progress" as
     a probable cause, slowing diagnosis.

Action items (system improvements):
  1. Migration runner: skip when no pending migrations exist.
  2. CI: require migrations to be deployed within 24h of merge, not deferred.
  3. Migrations: use lock_timeout and split into compatible pre/post phases.
  4. Alerting: surface "active migration on PROD" as a top-line signal.
  5. Runbook: document the "database CPU pinned + recent deploy" pattern.

Engineer A: not mentioned in action items, because nothing about Engineer A
            caused the outage. Anyone else, deploying anything, would have
            triggered the same incident.
```

The postmortem identified five system improvements that prevent the next incident, regardless of who deploys.

### Why this wins

- The next outage from this class of cause is prevented.
- Engineers feel safe sharing what went wrong, including near-misses, which produces better learning.
- Risk tolerance is calibrated by real understanding, not by fear.
- The team's incident rate trends down because each incident teaches the system, not just an individual.

### Why the alternative loses

- Blame produces fear. Fear produces secrecy. Secrecy produces repeated incidents.
- "Be more careful" is not an action item. It's a wish.
- Senior engineers leave teams where every mistake becomes personal. Junior engineers stop taking on risky work.

### When this principle yields

When a person genuinely is doing harm (repeated negligence, deliberate sabotage, ignoring agreed processes), the conversation is HR/management, not a postmortem. The test is whether the same incident could happen with anyone else in the same role. If yes, blameless system review. If the incident requires this specific person's choices, that's a different conversation and not a postmortem.

### Verification

Postmortems produce action items about systems, processes, and tooling. Engineer names appear as participants and observers, not as causes. The next quarter's incident rate is lower than the last because the system is improving.

## Principle 5: Documentation belongs at decision boundaries

State: documentation should explain what cannot be inferred from code: setup, architecture, external contracts, tradeoffs, and runbooks. It should not duplicate what the code already says.

### What goes wrong without it

Two failure modes. First, no documentation: new contributors spend their first week asking Slack questions to set up their dev environment, deploy a change, or understand why a module is structured the way it is. Second, the wrong documentation: the team writes detailed docs of every function ("returns the user's name") that go stale immediately, while leaving the actually important things (how to set up auth tokens, why we chose Postgres over MongoDB, what the on-call runbook is for outages) undocumented because "everyone knows."

### Anti-pattern

```
docs/
  ├── api-reference/
  │   ├── UserService.md          (auto-generated, restates the type signatures)
  │   ├── OrderService.md         (auto-generated, stale, refers to renamed methods)
  │   └── ... (50 more like this)
  └── readme.md                   (one-liner: "This is our app")

Setup process: ask in Slack.
Deployment process: ask in Slack.
On-call runbook: ask the senior engineer.
Architecture: lives in the head of one person.
Why we chose X over Y: lost forever.
```

The auto-generated docs add no value (the code is right there). The decision-boundary docs that *would* add value don't exist.

### Better approach

```
docs/
  ├── README.md                       # Project overview + links to other docs.
  ├── getting-started.md              # Clone -> running in 15 minutes.
  ├── architecture.md                 # The 4 services, why they exist, how they talk.
  ├── deployment.md                   # How to ship a change end-to-end.
  ├── on-call/
  │   ├── runbook.md                  # Common incident patterns + fixes.
  │   ├── escalation.md               # Who to wake up when.
  │   └── postmortem-template.md      # Blameless format.
  ├── decisions/
  │   ├── 0001-postgres-over-mongodb.md       # ADR
  │   ├── 0002-monolith-over-microservices.md # ADR
  │   └── 0003-react-over-vue.md              # ADR
  └── contracts/
      ├── payment-gateway.md          # External API quirks, undocumented behavior.
      └── auth-provider.md            # SSO setup, token lifetimes, gotchas.

# What's NOT here: auto-generated API reference (the code is the API reference,
# augmented by inline JSDoc/docstrings where they add value).
```

The docs cover what the code cannot: external context, decisions, runbooks, setup. A new contributor can set up, deploy, and on-call without phoning anyone. The decisions made years ago are still findable. The team's knowledge survives team rotation.

### Why this wins

- New contributors are productive in days, not weeks.
- On-call doesn't depend on the senior engineer being awake.
- Architectural decisions are revisitable because the original reasoning is preserved.
- The docs that exist are read because they actually contain non-obvious information.

### Why the alternative loses

- Auto-generated API docs go stale faster than they're updated, so they actively mislead.
- "Everyone knows" excludes new contributors and breaks when knowledge holders leave.
- Setup-via-Slack scales poorly: every new contributor costs senior engineer time.
- Decisions without ADRs get re-litigated every two years because nobody remembers why they were made.

### When this principle yields

For genuinely small projects with one or two contributors and no plans to grow, a short README is enough. The test is whether anyone other than the original team will read the code or operate the system. If yes, decision-boundary docs are essential.

### Verification

A new contributor can clone the repo and ship a small change end-to-end (setup, dev, test, deploy) by following the docs alone, without asking anyone. The decision logs explain what's weird about the architecture before someone proposes "improving" it.

## Principle 6: Estimates are ranges with assumptions

State: a single-number estimate is a guess that becomes a commitment by accident. Honest estimates are ranges with named assumptions and named risks, plus a check-in cadence.

### What goes wrong without it

The PM asks for a date; the engineer says "two days"; the PM tells the customer; the customer plans around it; reality requires two weeks; the customer is angry and the engineer feels punished for being honest about the issues. Next time, the engineer pads aggressively, which means estimates lose all signal — and the team's planning becomes purely a guessing game.

### Anti-pattern

```
PM: "When can you have this ready?"

Engineer: "Two days."

PM: [Tells customer "Tuesday."]

Engineer: [Hits unexpected database migration complexity, then an auth integration
           bug, then QA finds an edge case.]

Engineer: [Following Tuesday]: "I need more time."

PM: "You said two days a week ago."

Customer: "We've been waiting since Tuesday."

[Trust damaged.]
```

The original "two days" was the optimistic case for the part the engineer had thought about. The risks were invisible. The estimate became a commitment without anyone deciding to commit.

### Better approach

```
PM: "When can you have this ready?"

Engineer: "Honest answer: I don't know yet. Best case 2 days, worst case
           2 weeks, most likely 5-7 days.
           
           Assumptions driving the optimistic case:
           - The auth integration works as the docs describe.
           - The migration is forward-only with no backfill.
           - QA can review within 24h of dev complete.
           
           Risks pulling toward the pessimistic case:
           - The auth docs are from 2019 and may be stale.
           - The migration touches the orders table; if backfill is needed,
             that's 3 days of additional work.
           - Security review is queue-deep this week.
           
           I'll know by end-of-day tomorrow whether we're closer to optimistic
           or pessimistic. Want me to check in then?"

PM: "Yes please. What's the customer's actual deadline?"

Engineer: "Good question. If they need it by Friday no matter what, I should
           cut scope: drop the partial-refund support, ship just full refunds.
           That fits in the optimistic case."

PM: "Let me check with the customer and get back to you."
```

The estimate is honest. The PM has the data to decide whether to commit, what to commit to, and what to escalate. The check-in cadence is built in. Risk that materializes is not a surprise.

### Why this wins

- The PM can make a real commitment ("Friday for full-refund-only" instead of "Tuesday for everything"), which the customer can plan around.
- The engineer is not on the hook for a number they didn't pick.
- When risks materialize, they were named in advance, so adjusting expectations is a continuation of the original conversation, not a betrayal.
- Over time, estimation calibration improves because the team is collecting data on which assumptions held and which risks materialized.

### Why the alternative loses

- Single-number estimates default to commitments.
- Engineers learn to either pad (estimates become meaningless) or be optimistic (estimates are wrong).
- Customers learn that engineering dates are unreliable, which damages every future commitment.

### When this principle yields

For genuinely tiny tasks where the variance is small (a one-line dependency bump, a typo fix), a single number is fine. The test is whether the work could plausibly take more than 2x the estimate. If yes, give a range with assumptions.

### Verification

Estimates include ranges, assumptions, and risks. After the work is done, retrospectively note which assumptions held and which risks materialized — that's the calibration data that improves future estimates.

## Routing

Use `@tank/github-issues` for issue triage, labels, milestones, and bulk issue operations.

Use `@tank/bdd-e2e-testing` for the example-mapping and three-amigos workflow that brings testers and product into the design phase.

Use `@tank/clean-code` when collaboration friction is rooted in code that is hard to read, review, or change.

Use `references/professional-principles.md` when the collaboration question is "what does professional behavior look like here?"

Use `references/conflict-resolution.md` when collaboration involves a real principle conflict (deadline vs tests, customer ask vs technical correctness).
