# Plan Workflow

Sources: Marshall/Todd/Rhodes (Ultimate Guide to Google Ads 6e, 2020) Ch 4–6, 12; McDonald (Google Ads Workbook 2023) §1, §3, §4.

Covers: how to interrogate the SMB owner, translate answers into a campaign.json structure, and decide brand/non-brand/competitor splits. Read before invoking `scripts/plan.py`.

## Step 0 — Verify prerequisites before talking budget

Before any campaign creation, confirm the SMB owner has each of these. If any are missing, fix them FIRST. Spending on ads with missing prerequisites guarantees waste.

| Prerequisite | Why it matters | How to check |
|---|---|---|
| Conversion tracking installed and verified | Without it, you're "flying blind" (Marshall Ch 7). Every bidding optimization downstream is impossible. | Ask the user: "What conversion are you currently tracking, and does its count match your CRM/Stripe/etc?" |
| A coherent landing page | McDonald Gotcha #1. Generic homepage = paying Google to send guppies to bad fish food. | Visit the URL with the brief in hand. 20-second test: can a stranger tell what's offered and what to do next? |
| Account is in Expert Mode, not Smart Mode | Smart Mode blocks Editor CSV import entirely. | Tools → Switch to Expert Mode |
| `Ad Suggestions` is off | McDonald Gotcha #3. Auto-suggested ads optimize for clicks, not conversions. | Settings → Account Settings → Ad Suggestions → "Don't automatically apply" |
| `Automated Assets` is off | Same problem at the asset layer. | Ads & Assets → Assets → Account-level automated assets → Advanced Settings → all OFF |
| Account has 2-step verification | Google Ads accounts are stolen for ad-budget abuse. | Google account security → 2-step verification |

These six checks become a `precheck.md` artifact the skill emits before any campaign generation.

## Step 1 — Interrogate the business (the brief)

Marshall Ch 4–5 + McDonald §1 prescribe the same shape: customer-first, USP-first, intent-first. The brief asks 11 questions. Skip none.

| # | Question | Used for |
|---|---|---|
| 1 | What does your business do, in one sentence? | Campaign naming, RSA headline 1 |
| 2 | Who is your ideal customer? (demographics, situation, problem) | Audience signals, geo defaults |
| 3 | What's your USP? (six elements from Marshall Ch 5 — buyer, what, angle, what-not, time, guarantee) | Headlines 2–5, descriptions |
| 4 | What's the single action you want a visitor to take? | Conversion definition, landing-page check |
| 5 | What is one converted customer worth to you (lifetime, or per sale)? | Bid ceiling, CPA target |
| 6 | What geographic area do you serve? | Geo targeting (numeric IDs from `assets/geo-targets-seed.csv`) |
| 7 | What's your monthly ad budget? | Daily budget = monthly ÷ 30.4 |
| 8 | Are you running on Google Ads now? If yes, what's working and what isn't? | Bid-strategy ramp logic; reuse vs replace |
| 9 | Do you have competitors who bid on your name? | Brand-defense campaign decision |
| 10 | Top 5 competitor names + websites | Competitor campaign decision; ad-copy reconnaissance |
| 11 | Is your customer base on desktop or mobile primarily? (gut answer is fine) | Device bid adjustments at v1 |

Default rule for #5: if the user can't or won't answer, ask "What's the most you'd pay for one new customer and still be happy?" That's the CPA ceiling, even if the user calls it a guess.

## Step 2 — Apply the campaign-separation decision matrix

Marshall Ch 12 + McDonald §4 agree on this matrix. Use it BEFORE generating campaign.json.

| Reason | Separate campaigns? | Why |
|---|---|---|
| Different ad type (Search/Display/Shopping/YT) | Yes | v1 only emits Search, so trivially one. |
| Different geo with different CPA, currency, or spelling | Yes | Independent budget control + local copy |
| Different intent level (brand vs non-brand vs competitor) | Yes | CPAs and budgets diverge by 5–10× |
| Different product lines with different margins | Yes | Independent budget knobs |
| Different ad groups inside one theme | No | Use ad groups, not campaigns |
| User has only one product, one geo, no competition | No | Start with one campaign. Split later. |

**SMB v1 default:** one brand campaign + one non-brand campaign for the primary product. Add competitor campaign only if the user named competitors in Q10 who already run ads.

### Brand campaign rules

- Owns ~5% of total budget (Marshall Ch 12).
- Keywords: variations of the business name + branded product names.
- Match types: exact for the canonical name (`[acme plumbing]`), phrase for the variations (`"acme plumbing"`).
- Ads should explicitly say "Official site" and your USP.
- Even if you own organic #1, run brand defense. Competitors bidding on your name push you below the fold on mobile.

### Non-brand campaign rules

- Keywords: transactional service/product terms + helper words (`quote`, `near me`, geo).
- Match types: phrase + exact only. No broad at v1 (McDonald Gotcha #2).
- One core keyword theme → one ad group. Aim for 5–10 ad groups, ≤20 keywords per group (Hagakure soft limit).

### Competitor campaign rules

- Run only if your competitor has a weak USP relative to yours, or if they aren't running brand defense.
- Keywords: their brand name in exact or phrase.
- Ads MUST NOT use their trademark in the ad copy (use yours).
- Ads MUST go to a comparison page, not your homepage.
- Expect CVR between your brand and non-brand campaigns.

## Step 3 — Apply HOT/WARM/COLD tagging to every keyword

From McDonald §3. Every keyword going into campaign.json carries an intent tag:

| Tag | Meaning | Default match type | Default bid factor |
|---|---|---|---|
| HOT | Transactional + helper word (`emergency plumber san francisco`) | Exact `[...]` | 1.0 × base |
| WARM | Transactional only (`plumber`) | Phrase `"..."` | 0.7 × base |
| COLD | Educational or ambiguous (`how to fix sink`) | Skip in v1, OR isolate in low-bid ad group | 0.3 × base |

The plan-step UI must show the user every keyword with its tag and let them flip tags.

## Step 4 — Build the keyword worksheet (10 substeps)

From McDonald §3 and Marshall Ch 9. The worksheet is internal data, never shown to the user as a wall — it gets converted into ad groups.

1. List 5–10 core products/services as seed terms.
2. Add helper words for transactional intent: `quote`, `price`, `near me`, `best`, `top-rated`, `licensed`, `affordable` (not `cheap`), `same day`, `emergency`.
3. Add geo terms from Q6 — city + state + neighborhood.
4. Pull 5–10 phrasings from competitor sites (Q10) and ads.
5. Tag each candidate HOT/WARM/COLD.
6. Group by theme — each theme is one ad group.
7. Wrap each in `[...]` or `"..."` per Step 3 default; user may override.
8. For each ad group, list 5–10 likely negative keywords (`free`, `cheap`, `diy`, `course`, `job`, `salary`, `wiki`, plus theme-specific negatives).
9. Add account-level negatives that apply to all ad groups (e.g. `jobs`, `internship`, `class`).
10. Identify any single-keyword whales — keywords expected to be >50% of ad-group spend. Put them in their own ad group.

## Step 5 — Set the budget and bid strategy

From Marshall Ch 6 + Ch 8, McDonald §5.

### Budget rules
- Daily budget = monthly ad budget (Q7) ÷ 30.4.
- Daily budget must be ≥ 5–10× expected max CPC.
- If estimated CPC > daily/5, scope the campaign smaller (fewer keywords or tighter geo).
- Per-campaign budgets only. Never shared budgets at v1.

### Bid strategy ramp
| Account state | Strategy |
|---|---|
| Brand new, no conversion data | Manual CPC |
| 1–49 conversions/month per campaign | Manual CPC, still |
| 50–99 conv/mo per campaign | Enhanced CPC (eCPC) |
| 100+ conv/mo per campaign with lead-gen | Target CPA, set to Q5 ÷ expected lead-to-customer ratio |
| 100+ conv/mo with ecom, mixed price points | Target ROAS |

### Starting CPC
- Start at $1–2 per click unless Keyword Planner suggests otherwise.
- For each keyword, optionally read Keyword Planner's "Estimated Top of Page Bid" as the upper guide.
- Skill never auto-fetches Keyword Planner — emit a placeholder and prompt the user to fill in.

## Step 6 — Write the RSAs (Responsive Search Ads)

From Marshall Ch 10 + McDonald §5.

Each ad group gets ONE RSA at v1 (skill can output multiple later for split testing).

Headlines (3–15, ≤30 chars each):
- Headline 1: USP / primary keyword phrase verbatim
- Headline 2: Benefit (not feature) — Marshall Ch 10 dimension #3
- Headline 3: Call-to-action with strong verb (`Get a Free Quote`, `Book Today`)
- Headlines 4–10: variations testing price / scarcity / social proof / empathy / specificity
- Pin headlines sparingly — only brand name to position 1 if needed. Pinning >50% of headlines starves the ML.

Descriptions (2–4, ≤90 chars each):
- Description 1: expand the USP — promise + proof
- Description 2: call-to-action + offer + path-of-least-resistance
- Description 3 (optional): scarcity / urgency / guarantee
- Description 4 (optional): logical proof point (numbers beat generalities)

### Attract/Repel for ambiguous keywords (McDonald §5)
When the keyword could attract wrong-fit buyers (e.g., `pet boarding` for a cat-only business), include explicit repel language: "Cats only — no dogs." This is non-optional; ambiguous keywords without repel language burn budget.

### Path 1 / Path 2 (≤15 chars, alphanumeric + hyphen)
Mirror the keyword theme in the display URL: `example.com/emergency-plumber/san-francisco`. Doesn't have to match the actual final URL.

### Final URL
Must be the dedicated landing page for the ad group's theme, not the homepage. (Marshall Ch 11 + McDonald Gotcha #1.)

### Editorial gotchas (validator rules)
- No ALL CAPS
- No emojis or ASCII art
- No phone numbers in ad text (use call extension)
- No `Click here`
- No `Sale! Sale! Sale!` repetition
- No double spaces

## Step 7 — Plan the extensions (assets)

Marshall Ch 10 + McDonald §1. Six extension types matter for v1:

| # | Extension | When to emit | Skill emits at v1? |
|---|---|---|---|
| 1 | Sitelinks | Always — 4–6 links to related pages | Yes |
| 2 | Callouts | Always — 4 non-clickable highlights | Yes |
| 3 | Structured Snippets | Almost always — `Services:`, `Types:`, `Brands:` | Yes |
| 4 | Call extension | If user takes calls + Q11 mobile=yes | Yes when applicable |
| 5 | Location | Local business with physical address | Yes when applicable |
| 6 | Price | E-commerce with clear price tiers | Skip v1 unless explicit |

## Step 8 — Emit campaign.json

`scripts/plan.py` takes the brief + worksheet + decisions above and emits a `campaign.json` matching the data model in `references/02-csv-schema.md`. It does NOT emit CSVs directly — `scripts/csv_emit.py` does that from campaign.json. This separation lets the user edit campaign.json and re-emit CSVs without re-running the brief.

## Decision tree summary

```
USER REQUESTS A CAMPAIGN
   |
   v
Prerequisites all green?  ----no---> Output precheck.md, STOP
   |yes
   v
Run 11-question brief
   |
   v
Apply campaign-separation matrix  ---> 1, 2, or 3 campaigns
   |
   v
For each campaign:
   - HOT/WARM/COLD-tag every keyword
   - Group by theme → ad groups
   - Wrap with [ ] or " " per tag
   - Generate 5–10 negatives per group + account-level negatives
   - Compute daily budget from Q7
   - Pick bid strategy from conversion-volume table
   - For each ad group: write 1 RSA (3–15 H, 2–4 D) + path1/path2 + final_url
   - Attach sitelinks, callouts, structured snippets
   |
   v
Emit campaign.json + precheck.md
   |
   v
HAND OFF to scripts/csv_emit.py + scripts/validate.py
```

## Quotables for the agent's own self-talk

- "Job of an ad is to get the click. Job of the landing page is to make the sale." — Marshall Ch 4
- "Specificity, not trust, is what you need in Google Ads." — McDonald §3
- "The winner is not the business that gets the cheapest leads. The winner is the business that can afford to pay the most per lead." — Dan Kennedy, via Marshall Ch 7

## Source attribution

- Marshall, Todd, Rhodes. *Ultimate Guide to Google Ads, 6e* (Entrepreneur Press, 2020), Ch 4–6, 12.
- McDonald, Jason. *Google Ads (AdWords) Workbook 2023* (JM Internet Group, 2023), §1, §3, §4.
