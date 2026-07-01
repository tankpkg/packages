# Product Research Methodology

Sources: Consumer research best practices, search evaluation heuristics,
affiliate content analysis, product review journalism standards.

How to research products effectively: where to search, how to evaluate
sources critically, what questions to ask the user, and how to synthesize
findings into confident recommendations.

---

## 0. Your Knowledge Is Out of Date — Act Accordingly

You are an LLM. Your training data has a cutoff date. Everything you
"know" about specific products — prices, availability, model lineups,
retailer stock, feature sets — is potentially WRONG by the time you
are reading this.

**Hard rules:**

- NEVER recommend a specific product based on memory alone. Always verify
  through live web search that it still exists, is still sold, and is
  still relevant.
- NEVER state a price from memory. Prices change weekly. A product you
  "know" costs $299 might now cost $199 — or $399 — or be discontinued.
- NEVER assume a product is the "current model." Manufacturers release
  successors constantly. The model you remember may be 2 generations old.
- If web search returns no results for a product you "remember," it may
  have been discontinued or renamed. Do NOT present it to the user.
- When comparing products, every data point must come from a web source
  retrieved during THIS session. Cite the source.

**Why this matters:**

A user trusting your recommendation may spend hundreds of dollars. Stale
data leads to recommending discontinued products, wrong prices, missing
superior alternatives that launched after your training cutoff, or sending
the user to retailers that no longer stock the item. The cost of one live
search is negligible. The cost of a wrong recommendation is real money.

**Every search query MUST include a date.** Append the current year (or
month+year for fast-moving categories) to every query. This ensures search
engines return current content, not stale SEO pages from years ago.

| Wrong | Right |
|-------|-------|
| `best wireless earbuds` | `best wireless earbuds 2026` |
| `Sony WH-1000XM5 review` | `Sony WH-1000XM5 review 2026` |
| `best budget laptop` | `best budget laptop February 2026` |
| `robot vacuum comparison` | `robot vacuum comparison 2026` |

For fast-moving categories (phones, laptops, GPUs), include month+year.
For slower categories (furniture, cookware), year is sufficient.

---

## 1. Discovery Questions

Ask these BEFORE researching. Adapt to the product category — not every
question applies to every product. Ask 3-5 questions, never more than 6.
Do not dump all questions at once; ask the most critical 2-3 first, then
follow up based on answers.

### Universal Questions (ask for every product)

| Priority | Question | Why It Matters |
|----------|----------|----------------|
| 1 | What will you primarily use this for? | Determines which features matter |
| 2 | What's your budget range? | Filters the field immediately |
| 3 | Are there any must-have features or deal-breakers? | Hard constraints before research |

### Situational Questions (ask when relevant)

| Trigger | Question | Example |
|---------|----------|---------|
| Physical product | Where are you located? (for shipping/availability) | Electronics, furniture, appliances |
| Replacing something | What are you currently using and what's wrong with it? | Upgrades, replacements |
| Technical product | What's your experience level? | Cameras, audio gear, tools |
| Ecosystem product | What other devices/platforms do you use? | Headphones (Apple/Android), smart home |
| Gift | Who is this for? Age, interests, experience? | Any gift purchase |
| Recurring purchase | How often do you buy this? Bulk? | Consumables, supplies |

### Question Principles

- Never ask what you can infer. If user says "gaming laptop under $1000"
  you already have category, use case, and budget
- Ask one message at a time, 2-3 questions max per message
- Offer sensible defaults: "Budget? (Most popular range is $X-$Y)"
- If user says "I don't know" — proceed with mainstream recommendations
  and note your assumptions

---

## 2. Where to Search

### Source Tier System

Organize research by source reliability. Start with Tier 1 and expand
only if needed.

#### Tier 1 — High Trust (start here)

| Source Type | Examples | Strengths | Watch For |
|------------|---------|-----------|-----------|
| Editorial review sites | Wirecutter, RTINGS, Consumer Reports, Tom's Guide | Rigorous testing methodology, disclosed affiliate relationships, long-term testing | Limited product selection, may not cover niche products |
| Manufacturer specs | Official product pages | Accurate specifications | Marketing bias, missing real-world performance |
| Professional/niche reviewers | Category-specific YouTube channels, specialty publications | Deep domain expertise, hands-on testing | May have sponsorship deals — check disclosures |

#### Tier 2 — Moderate Trust (supplement Tier 1)

| Source Type | Examples | Strengths | Watch For |
|------------|---------|-----------|-----------|
| Reddit discussions | r/BuyItForLife, r/headphones, r/buildapc, product-specific subs | Real user experiences, long-term ownership reports, community consensus | Sample bias toward complaints, outdated posts, astroturfing |
| YouTube reviews | Popular tech/product reviewers with >100K subs | Visual demonstrations, real-world usage | Sponsored content — always check descriptions, some reviewers only cover items they receive free |
| Retailer reviews (high volume) | Amazon (100+ reviews), Best Buy | Volume of opinions, verified purchases | Fake reviews, incentivized reviews, rating inflation |

#### Tier 3 — Low Trust (use with extreme caution)

| Source Type | Examples | What to Extract | Critical Problems |
|------------|---------|----------------|-------------------|
| "Best X" / "Top 10" blogs | Generic SEO affiliate sites | Feature comparison tables, spec lists | Rankings driven by affiliate commission, not quality. See "Evaluating Affiliate Content" below |
| "X vs Y" articles | SEO comparison pages | Side-by-side spec comparisons | Written for search rankings, not genuine comparison. Often haven't tested either product |
| Social media ads/posts | Instagram, TikTok, influencer posts | Product awareness only | Paid promotions, undisclosed sponsorships |
| Single retailer with few reviews | Small shops, niche retailers | Price data only | Unreliable review quality |

---

## 3. Evaluating Affiliate Content (Critical)

Most "best product" and "X vs Y" articles are SEO affiliate content.
They rank on Google because they're optimized for search, not because
they provide the best advice. This does NOT mean they're useless — but
you must extract value carefully.

### What to TRUST from affiliate blogs

- **Specification comparison tables** — factual data is usually accurate
- **Feature checklists** — which models have which features
- **Product existence** — discovering products you didn't know about

**NOT trustworthy from affiliate blogs: PRICES.** Article prices are stale
the day they're published. A 2024 article saying "$45" may reflect a launch
promotion, a different SKU, or a price that changed 6 months ago. NEVER
use article prices in your output. See § Price Verification below.

### What to DISTRUST from affiliate blogs

- **Rankings and "best overall" picks** — often the highest-commission product
- **Subjective quality claims** — "amazing sound quality" without measurements
- **"Winner" declarations in vs articles** — the winner is usually whoever pays more
- **Conspicuous absence** — great products with low affiliate commissions get excluded

### Red Flags in Product Content

| Red Flag | What It Means |
|----------|--------------|
| Every product has a "check price on Amazon" button | Pure affiliate play |
| No mention of ANY downsides | Not a real review |
| "Updated [this month]" but content is generic | Date manipulation for SEO freshness |
| Top pick is always the most expensive option | Commission-driven ranking |
| Article covers products from only one brand | Possible brand sponsorship |
| No photos of actual product testing | Writer never touched the product |
| Identical structure across many product categories | Content mill, not experts |

### The Correct Approach to Affiliate Content

1. **Extract facts**: specs, features, price ranges, product names
2. **Ignore rankings**: their #1 pick is not necessarily the best
3. **Cross-reference**: any claim in an affiliate blog must be confirmed
   by a Tier 1 or Tier 2 source
4. **Use for discovery**: these articles often surface products you'd miss,
   which you then research through better sources

---

## 4. Search Strategies

### Search Query Patterns

Use these search patterns with web search tools. **EVERY query MUST
include the current year** (or month+year for fast-moving categories).
Without a date, you will get stale SEO content about discontinued products.

| Goal | Search Pattern | Example |
|------|---------------|---------|
| Expert reviews | `best [product] [year] site:wirecutter.com OR site:rtings.com` | `best wireless earbuds 2026 site:wirecutter.com` |
| Reddit consensus | `best [product] [year] site:reddit.com` | `best vacuum cleaner 2026 site:reddit.com` |
| Specific comparison | `[product A] vs [product B] [year]` | `Sony XM6 vs Bose QC Ultra 2026` |
| Deal/price history | `[product] price history camelcamelcamel` | `Sony WH-1000XM5 price history` |
| Reliability data | `[product] problems OR issues [year] reddit` | `Dyson V15 problems 2026 reddit` |
| Professional tests | `[product] tested OR measurements [year] site:rtings.com` | `Samsung TV tested 2026 site:rtings.com` |

### Research Sequence

Follow this order for efficient, thorough research:

1. **Broad survey** — search "best [category] [current year]" on 2-3 Tier 1
   sources. ALWAYS include the year. Goal: identify the 5-8 top contenders
2. **Spec collection** — visit manufacturer pages for each contender.
   Goal: accurate feature/spec comparison
3. **Expert deep-dives** — search for individual reviews of top 3-4 contenders.
   Goal: real-world performance data
4. **Community validation** — check Reddit and forums for ownership experiences.
   Goal: long-term reliability, common complaints
5. **Price verification (CRITICAL)** — Discard ALL prices you noted from
   articles, search snippets, Reddit posts, or YouTube videos during steps
   1-4. Those prices are stale. Now scrape the actual retailer product page
   (Amazon listing, Best Buy listing, etc.) for each finalist product on
   at least 2 retailers. These retailer-page prices are the ONLY prices
   you may put in your final output.

   **Sanity-check every price.** If a product's price seems surprisingly
   low (e.g., a 16GB RAM single-board computer at $45 when competitors are
   $100+), something is wrong. Re-verify on the retailer page. Common
   causes of wrong prices: article cited a different SKU/variant, a
   promotional price that expired, a different region's pricing, or a
   bare-board price without RAM/storage.

   **If a retailer page price differs from an article price by >20%,
   the retailer page wins. Always.**
6. **Final synthesis** — combine all data into recommendation. Every price
   in your output must have come from a retailer page scraped in step 5,
   not from articles or memory

### Location-Aware Research

If the user provides their location, adapt the research:

| Region | Retailer Focus | Price Considerations |
|--------|---------------|---------------------|
| US | Amazon, Best Buy, Walmart, B&H, Costco | Tax varies by state, Prime benefits |
| UK | Amazon UK, Currys, John Lewis, Argos | Include VAT, check import duties |
| EU | Amazon (country-specific), local chains | VAT included, cross-border shipping |
| Canada | Amazon CA, Best Buy Canada, Canada Computers | CAD pricing, cross-border duties |
| Australia | Amazon AU, JB Hi-Fi, Officeworks | AUD pricing, shipping constraints |
| Other | Search "[product] buy in [country]" | Note currency, import fees, warranty coverage |

---

## 5. Synthesis and Ranking

### Ranking Criteria

Rank products by how well they match the user's stated needs, NOT by
overall "best product" consensus. A $50 product that perfectly fits the
user's needs outranks a $500 product that's overkill.

| Factor | Weight |
|--------|--------|
| Matches user's primary use case | Highest |
| Within stated budget | Hard requirement |
| Meets must-have features | Hard requirement |
| Expert review consensus | High |
| Community satisfaction | Medium |
| Value for money | Medium |
| Brand reliability / warranty | Low-Medium |

### Writing the Recommendation

- Lead with the recommendation, not the methodology
- Explain WHY product #1 beats #2 for THIS user's needs
- Acknowledge trade-offs honestly: "Product B has better X, but for your
  use case, Product A's Y matters more"
- Include a budget alternative if the top pick is expensive
- Note if the user should wait (upcoming model refresh, expected sales)

### Confidence Levels

Be honest about research confidence:

| Confidence | When | What to Say |
|-----------|------|-------------|
| High | 3+ Tier 1 sources agree, ample reviews available | "Strong recommendation based on extensive testing data" |
| Medium | Mixed reviews, limited testing data, newer product | "Good option based on available data — consider waiting for more reviews" |
| Low | Niche product, few reviews, conflicting information | "Limited data available — recommendation based on specs and early reports" |

---

## 6. Category-Specific Research Tips

### Electronics (headphones, TVs, phones, laptops)

- RTINGS.com has objective measurements for audio, TVs, monitors
- Check release date — products older than 2 years may have successors coming
- Battery life claims are usually optimistic — look for real-world tests

### Home & Kitchen (appliances, cookware, furniture)

- Wirecutter excels here with long-term testing
- r/BuyItForLife for durability-focused recommendations
- Check warranty terms — major differentiator in appliances

### Software & Digital Products

- G2, Capterra for business software reviews
- Free trials matter more than reviews — recommend trying before buying
- Check pricing changes — SaaS products change pricing frequently

### Health & Fitness (supplements, equipment, wearables)

- Be extra cautious about health claims
- Prefer products with third-party testing certifications
- Check if "clinical studies" are actually independent
