---
name: "@tank/product-buying-researcher"
description: |
  Research products for purchase, compare options across retailers, and
  present findings on a locally-hosted comparison website. Covers the full
  buying research workflow: discovery questions (budget, use case, location,
  preferences), multi-source web research with critical evaluation of
  SEO/affiliate content, product comparison and ranking, and visual
  presentation via a local HTML server with direct buy links to retailers.

  Trigger phrases: "I want to buy", "find me a product", "what should I buy",
  "recommend a product", "best [product]", "help me choose",
  "product comparison", "research [product] for me", "looking to buy",
  "shopping for", "which [product] should I get", "compare [products]",
  "find the best [product]", "product research", "buying guide"
---

# Product Buying Researcher

## Core Philosophy

1. **Your product knowledge is STALE — do not trust it.** Products get
   discontinued, prices change weekly, new models launch constantly. NEVER
   recommend from memory. EVERY claim must come from live search or API data.
2. **Every search query MUST include a date.** Always append the current year
   (or month+year for fast-moving categories). Without a date, search engines
   return stale SEO content referencing discontinued products.
3. **Article prices are NOT live prices.** The ONLY acceptable price sources
   are: (a) the `search_products.py` / `check_prices.py` scripts, or (b)
   a live scrape of the actual retailer product page. Article prices, search
   snippets, and Reddit/YouTube prices are stale the day they're published.
4. **User needs drive rankings** — rank by fit for THIS user, not by general
   consensus.
5. **Sources have tiers** — editorial review sites > community discussion >
   affiliate SEO content.
6. **Show, don't just tell** — present results on a local comparison website.
7. **Use scripts when available** — the automation scripts below provide
   structured, live data from Google Shopping, Amazon, and retailer pages.
   Always prefer script output over manual web search when possible.

## API Setup (Optional but Recommended)

Scripts work without API keys (using free Amazon search via amzpy), but
setting up SerpAPI unlocks Google Shopping with structured multi-retailer
data, live prices, ratings, and images across all stores.

| Env Variable | Service | Free Tier | What It Unlocks |
|-------------|---------|-----------|-----------------|
| `SERPAPI_API_KEY` | [SerpAPI](https://serpapi.com) | 100 searches/mo | Google Shopping: prices, ratings, images across all retailers |

Install script dependencies:
```
pip install -r {this_skill_directory}/scripts/requirements.txt
```

## Quick-Start Workflow

### Step 1: Discover User Needs

Ask 2-3 targeted questions. Never more than 6 total across the conversation.
If the user already gave details, skip redundant questions.

Universal questions (always relevant):
- What will you primarily use this for?
- What's your budget range?
- Any must-have features or deal-breakers?

Situational questions (ask when relevant):
- Where are you located? (for shipping/availability/pricing)
- What are you currently using and what's wrong with it?
- What ecosystem are you in? (Apple/Android, smart home platform, etc.)

→ See `references/research-methodology.md` § Discovery Questions

### Step 2: Research Products

**Use scripts first, web search second.** Scripts return structured JSON with
live prices and buy links — far more reliable than parsing web search results.

#### 2a. Automated product search (preferred)

```bash
python3 {this_skill_directory}/scripts/search_products.py "wireless earbuds" \
  --max-results 10 --min-price 30 --max-price 200 --pretty
```

This searches Google Shopping (if `SERPAPI_API_KEY` is set) or Amazon (free
fallback). Returns JSON with name, price, rating, store, buy link, and image
for each product.

Use `--source serpapi` or `--source amazon` to force a specific source.
Use `--country us` to set locale (default: us).

#### 2b. Manual research (supplement scripts)

1. **Broad survey** — "best [category] [year]" on editorial review sites
   (Wirecutter, RTINGS, Consumer Reports, Tom's Guide). Identify 5-8 contenders.
2. **Spec collection** — manufacturer pages for each contender
3. **Expert reviews** — individual reviews for top 3-4 candidates
4. **Community validation** — Reddit, forums for ownership experiences

#### 2c. Price verification (CRITICAL)

```bash
python3 {this_skill_directory}/scripts/check_prices.py "Sony WH-1000XM5" \
  --max-results 8 --pretty
```

Or check specific retailer URLs:
```bash
python3 {this_skill_directory}/scripts/check_prices.py \
  --urls "https://amazon.com/dp/B0BX2L8PBT" "https://bestbuy.com/..." --pretty
```

Discard ALL prices seen in articles and search snippets. Only script output
or direct retailer page scrapes are acceptable price sources.

→ See `references/research-methodology.md` § Where to Search, § Search Strategies

### Step 3: Evaluate Sources Critically

- **Affiliate "best of" blogs**: extract spec tables, ignore rankings
- **"X vs Y" articles**: use for side-by-side specs, not conclusions
- **Reddit**: real experiences but biased toward complaints
- **YouTube**: check for sponsorship disclosures in descriptions

→ See `references/research-methodology.md` § Evaluating Affiliate Content

### Step 4: Rank and Recommend

Rank 3-5 products by user fit. Include pros, cons, and buy links for each.

If the user is comparing across product types (e.g., "earbuds vs over-ear
headphones"), organize products into categories. The template supports
three data formats — flat products, auto-grouped by category field, or
explicit categories with descriptions. See `references/data-format.md` §2
for the three formats and when to use each.

| Factor | Weight |
|--------|--------|
| Matches primary use case | Highest |
| Within budget | Hard requirement |
| Meets must-have features | Hard requirement |
| Expert consensus | High |
| Community satisfaction | Medium |
| Value for money | Medium |

### Step 5: Present on Local Website

1. Create directory: `mkdir -p /tmp/product-research`
2. Write product data JSON to `/tmp/product-research/data.json`
   → See `references/data-format.md` for schema and field guide
3. Start the server:
   ```
   python3 {this_skill_directory}/scripts/serve.py /tmp/product-research/data.json
   ```
   If you do not have shell/bash execution available, tell the user to run
   the command themselves: "Run this in your terminal: `python3 ...`"
4. Browser opens automatically with the comparison page
5. Tell user they can click buy links to visit retailers directly

### Step 6: Refresh Prices

Before showing the user final results, refresh all prices in data.json:

```bash
python3 {this_skill_directory}/scripts/enrich_data.py /tmp/product-research/data.json --pretty
```

This re-searches each product and updates prices, buy links, and images
with live data. Use `--dry-run` to preview changes without writing.

### Step 7: Iterate

After presenting results, ask if the user wants to adjust:
- Different price range or priorities
- More products or deeper research on a specific one
- Different retailers or regions

If they request changes, update `data.json`, run `enrich_data.py`, and
restart the server.

## Decision Trees

### How Many Questions to Ask

| User Input | Action |
|-----------|--------|
| Category only: "I need headphones" | Ask use case + budget |
| Category + use case: "headphones for running" | Ask budget + deal-breakers |
| Full context: "noise-cancelling headphones under $200 for commuting" | Start research immediately |
| Gift: "present for my dad" | Ask recipient interests + budget |

### Research Source Selection by Category

| Category | Go-To Sources | Watch For |
|----------|--------------|-----------|
| Electronics | RTINGS, Wirecutter, YouTube | Release dates, battery life claims |
| Home & Kitchen | Wirecutter, r/BuyItForLife | Warranty terms, durability |
| Software | G2, Capterra, free trials | Pricing changes, vendor lock-in |
| Fitness & Health | Certified testing, medical sources | Unverified health claims |
| Fashion | User reviews, YouTube try-ons | Sizing variance, return policies |

### Confidence Communication

| Confidence | Condition | What to Tell User |
|-----------|-----------|-------------------|
| High | 3+ expert sources agree | Recommend confidently |
| Medium | Mixed reviews or limited data | Recommend but note uncertainty |
| Low | Niche product, few reviews | State it's based on specs only, suggest waiting |

## Scripts

| Script | Purpose | API Key Needed? |
|--------|---------|-----------------|
| `scripts/search_products.py` | Search Google Shopping or Amazon for products. Returns structured JSON with prices, ratings, buy links, images. | SerpAPI key for Google Shopping; Amazon search is free |
| `scripts/check_prices.py` | Multi-retailer price comparison for a specific product. Can also scrape specific retailer URLs. | SerpAPI key for multi-retailer; URL scraping is free |
| `scripts/enrich_data.py` | Refresh prices and images in existing `data.json` with live data. | Same as search_products.py |
| `scripts/serve.py` | Launch local comparison website from `data.json`. | None |

All scripts output JSON to stdout and accept `--pretty` for formatted output.
Run any script with `--help` for full usage.

## Reference Files

| File | Contents |
|------|----------|
| `references/research-methodology.md` | Question frameworks, source tier system (Tier 1-3), critical evaluation of affiliate/SEO content with red flags table, search query patterns, location-aware retailer selection, ranking criteria, category-specific tips |
| `references/data-format.md` | Product data JSON schema, field requirements and guidelines, serve script usage, example data, troubleshooting |
