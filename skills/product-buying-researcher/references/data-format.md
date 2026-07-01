# Product Data Format and Presentation

Sources: Web application data patterns, product comparison site
conventions, JSON schema design.

Specification for the product data JSON file that powers the comparison
website. Covers the schema, field descriptions, presentation workflow,
and the serve script.

---

## 1. Data File Location

Write the product data as a JSON file to a working directory. Convention:

```
/tmp/product-research/data.json
```

The serve script reads this file and combines it with the HTML template.

---

## 2. JSON Schema

The template supports three input formats. Use whichever fits the
research best — the template auto-detects the format.

### Format A: Flat products (simplest)

Use when researching a single product category.

```json
{
  "metadata": { ... },
  "recommendation": "string",
  "products": [
    { "rank": 1, "name": "Product A", ... },
    { "rank": 2, "name": "Product B", ... }
  ]
}
```

### Format B: Products with category field (auto-grouped)

Use when the user asked about multiple types (e.g., "earbuds and
over-ear headphones"). Add a `category` field to each product and the
template groups them automatically.

```json
{
  "metadata": { ... },
  "recommendation": "string",
  "products": [
    { "rank": 1, "name": "Sony WF-1000XM5", "category": "Wireless Earbuds", ... },
    { "rank": 2, "name": "AirPods Pro 2", "category": "Wireless Earbuds", ... },
    { "rank": 1, "name": "Sony WH-1000XM5", "category": "Over-Ear Headphones", ... }
  ]
}
```

### Format C: Explicit categories (most control)

Use when you want named categories with descriptions, or custom ordering.

```json
{
  "metadata": { ... },
  "recommendation": "string",
  "categories": [
    {
      "name": "Budget Picks",
      "description": "Best options under $50",
      "products": [
        { "rank": 1, "name": "Product A", ... }
      ]
    },
    {
      "name": "Premium",
      "description": "Top-tier regardless of price",
      "products": [
        { "rank": 1, "name": "Product X", ... }
      ]
    }
  ]
}
```

When using Format C, the `products` top-level key is ignored if
`categories` is present and non-empty.

---

## 3. Full Product Object

Every product (in any format) uses this shape:

```json
{
  "rank": "number — position (1 = best match for user)",
  "name": "string — full product name with model number",
  "image": "string | null — URL to product image",
  "price": "string — representative price, e.g. $249",
  "priceRange": "string | null — price range across retailers, e.g. $228-$348",
  "rating": "number | null — average rating out of 5, e.g. 4.7",
  "ratingSource": "string | null — where the rating comes from, e.g. Amazon (15K reviews)",
  "highlights": "string — 1-2 sentence summary of what makes this product notable",
  "bestFor": "string | null — who this product is ideal for",
  "pros": ["string array — 3-5 key advantages"],
  "cons": ["string array — 2-4 honest drawbacks"],
  "category": "string | null — only used in Format B for auto-grouping",
  "buyLinks": [
    {
      "store": "string — retailer name",
      "url": "string — direct link to product page",
      "price": "string | null — price at this retailer"
    }
  ]
}
```

---

## 4. Category Object (Format C)

```json
{
  "name": "string — category display name (e.g. 'Budget Picks', 'Premium')",
  "description": "string | null — short subtitle shown next to the heading",
  "products": ["array of product objects as defined above"]
}
```

| Field | Required | Notes |
|-------|----------|-------|
| name | Yes | Displayed as a section heading. Keep short and descriptive |
| description | No | One-line subtitle. Shown in muted text next to the heading |
| products | Yes | Non-empty array. Each product uses the schema from §3 |

---

## 5. Field Guidelines

### metadata

| Field | Required | Notes |
|-------|----------|-------|
| query | Yes | Use the user's words or a cleaned-up version. This becomes the page title |
| date | Yes | ISO date of when research was conducted |
| location | No | Only if user provided it. Affects retailer selection |
| budget | No | Include if user stated a budget. Helps contextualize the recommendation |
| priorities | No | List features the user emphasized. Shown as tags on the page |
| notes | No | Any extra context: "replacing a broken unit", "for my daughter" |

### products

Include 3-5 products per category. Fewer than 3 feels incomplete. More
than 7 per category creates decision fatigue.

| Field | Required | Notes |
|-------|----------|-------|
| rank | Yes | Sequential within each category, 1 = best match. Rank by user fit, not "objectively best" |
| name | Yes | Full name including brand and model: "Sony WH-1000XM5" not "Sony headphones" |
| image | No | Use manufacturer or retailer product image URL. Template handles missing images gracefully |
| price | Yes | The most common or representative price |
| priceRange | No | Show if prices vary significantly across retailers |
| rating | No | Aggregate rating if available. Prefer sources with high review counts |
| ratingSource | No | Always cite where the rating comes from |
| highlights | Yes | What makes this product stand out. Focus on user-relevant strengths |
| bestFor | No | One-line descriptor of ideal buyer. Helps user self-identify |
| pros | Yes | 3-5 items. Be specific: "30-hour battery" not "good battery" |
| cons | Yes | 2-4 items. Be honest. Every product has real drawbacks |
| category | No | Only for Format B (auto-grouping). Ignored when using Format C |
| buyLinks | Yes | 2-4 retailers with direct links and prices. More links = more helpful |

### buyLinks

- Always include at least 2 retailers when possible
- Use direct product page URLs, not search result pages
- Include price at each retailer — users compare across stores
- If user provided location, prioritize retailers available in their region
- Order by price (lowest first) or by retailer reliability

---

## 6. Format Detection (How the Template Works)

The template's `normalize()` function auto-detects the format:

1. If `categories` array exists and is non-empty → use it directly (Format C)
2. Else if any product has a `category` field → group by category (Format B)
3. Else → show all products in a single flat list (Format A)

All three formats are backward-compatible. Existing data files without
categories continue to work unchanged.

When multiple categories exist, the template shows:
- A pill-style category navigation bar
- Section headings for each category
- An "All" pill to show everything
- Animated transitions when switching categories

---

## 7. Serving the Website

### File Preparation

1. Create the working directory:
   ```
   mkdir -p /tmp/product-research
   ```

2. Write the data file:
   ```
   Write product data JSON to /tmp/product-research/data.json
   ```

3. Start the server using the skill's serve script:
   ```
   python3 {skill_directory}/scripts/serve.py /tmp/product-research/data.json
   ```

The script automatically:
- Finds an available port (starting at 8432)
- Combines the HTML template with the product data
- Opens the browser
- Prints the URL to the console

### After Serving

Tell the user:
- The URL where results are available (printed by the script)
- That they can click any "buy" link to go directly to the retailer
- That they can press Ctrl+C in the terminal to stop the server
- Offer to refine the research if they want changes

---

## 8. Example Data

### Flat format (Format A)

```json
{
  "metadata": {
    "query": "Best Wireless Earbuds for Running",
    "date": "2025-06-15",
    "budget": "$50-150",
    "priorities": ["sweat resistance", "secure fit", "battery life"]
  },
  "recommendation": "The Jabra Elite 8 Active offers the best combination of secure fit, durability, and sound quality for runners in your budget.",
  "products": [
    {
      "rank": 1,
      "name": "Jabra Elite 8 Active",
      "price": "$129",
      "rating": 4.5,
      "ratingSource": "Amazon (3,200 reviews)",
      "highlights": "IP68 rated with a wing-tip design that stays put during intense workouts.",
      "bestFor": "Serious runners who need earbuds that won't fall out",
      "pros": [
        "IP68 dust and water resistance",
        "Secure wing-tip fit",
        "8-hour battery (32 with case)",
        "Strong ANC for outdoor noise"
      ],
      "cons": [
        "Bass can be overpowering on default EQ",
        "Touch controls take practice",
        "Case is bulky"
      ],
      "buyLinks": [
        {"store": "Amazon", "url": "https://amazon.com/dp/example", "price": "$129"},
        {"store": "Best Buy", "url": "https://bestbuy.com/example", "price": "$129"}
      ]
    }
  ]
}
```

### Categorized format (Format C)

```json
{
  "metadata": {
    "query": "Best Headphones 2025",
    "date": "2025-06-15",
    "budget": "$50-350",
    "priorities": ["sound quality", "comfort", "noise cancellation"]
  },
  "recommendation": "For earbuds, the Sony WF-1000XM5 leads in sound quality. For over-ear, the Sony WH-1000XM5 is unbeatable for comfort on long listening sessions.",
  "categories": [
    {
      "name": "Wireless Earbuds",
      "description": "Compact, portable, great for commuting and workouts",
      "products": [
        {
          "rank": 1,
          "name": "Sony WF-1000XM5",
          "price": "$228",
          "priceRange": "$218-$280",
          "rating": 4.6,
          "ratingSource": "RTINGS (lab tested)",
          "highlights": "Best-in-class sound quality with effective ANC in a compact form factor.",
          "bestFor": "Audiophiles who want top sound in earbud form",
          "pros": ["Exceptional sound quality", "Effective ANC", "Compact case", "LDAC support"],
          "cons": ["No multipoint connection", "Average call quality", "IPX4 only"],
          "buyLinks": [
            {"store": "Amazon", "url": "https://amazon.com/dp/example1", "price": "$228"},
            {"store": "Best Buy", "url": "https://bestbuy.com/example1", "price": "$248"}
          ]
        }
      ]
    },
    {
      "name": "Over-Ear Headphones",
      "description": "Maximum comfort and sound for home and office use",
      "products": [
        {
          "rank": 1,
          "name": "Sony WH-1000XM5",
          "price": "$298",
          "priceRange": "$278-$348",
          "rating": 4.7,
          "ratingSource": "Amazon (25K reviews)",
          "highlights": "Industry-leading ANC with all-day comfort and 30-hour battery.",
          "bestFor": "Office workers and frequent travelers",
          "pros": ["30-hour battery", "Best-in-class ANC", "Extremely comfortable", "Speak-to-chat"],
          "cons": ["No aptX support", "Doesn't fold flat", "Bass-heavy default EQ"],
          "buyLinks": [
            {"store": "Amazon", "url": "https://amazon.com/dp/example2", "price": "$298"},
            {"store": "B&H Photo", "url": "https://bhphoto.com/example2", "price": "$278"}
          ]
        }
      ]
    }
  ]
}
```

---

## 9. Common Issues

| Problem | Fix |
|---------|-----|
| Images not loading | Image URLs must be full HTTPS URLs. Check they're not behind auth |
| Missing product data | Ensure required fields (name, rank, price, pros, cons, buyLinks) are present |
| Server won't start | Check if another process is using the port. Script tries 50 ports |
| Page shows "No products found" | Verify data.json is valid JSON and has a non-empty products array (or categories array) |
| Buy links go to wrong page | Use direct product page URLs, not retailer homepage or search pages |
| Category pills not showing | Need 2+ categories, or at least one product with a non-empty `category` field |
| Products not grouped | Ensure the `category` field is set on each product (Format B) or use explicit `categories` array (Format C) |
