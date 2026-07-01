# Video Recipe Extraction

Sources: YouTube Data API patterns, web scraping best practices, structured recipe schema (schema.org)

Covers: detecting video URL platform, extracting recipe data from video pages
(description, transcript, comments, structured data), building structured recipe
output, confidence scoring for extraction quality.

## URL Detection

Identify the platform from the URL to route extraction strategy.

| Platform | URL Patterns |
|----------|-------------|
| YouTube | `youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/` |
| TikTok | `tiktok.com/@user/video/`, `vm.tiktok.com/` |
| Instagram | `instagram.com/reel/`, `instagram.com/p/` |
| Facebook | `facebook.com/watch/`, `fb.watch/` |
| Generic | Any other URL — attempt JSON-LD extraction |

## YouTube Extraction

YouTube is the richest source because it often has: video description with
ingredients, auto-generated transcript, comments with corrections, and
sometimes JSON-LD recipe markup from the creator.

### Strategy (ordered by reliability)

1. **Fetch the page** — Use web fetch/scrape tool to get the YouTube page HTML
2. **Check for JSON-LD** — Some food creators embed `@type: Recipe` structured data
3. **Parse description** — Video descriptions often list ingredients and steps
4. **Extract transcript** — Auto-captions contain spoken instructions
5. **Combine sources** — Cross-reference description ingredients with transcript steps

### Description Parsing

Common patterns in cooking video descriptions:

```
INGREDIENTS:
- 2 cups flour
- 1 tsp salt
- 3 eggs

INSTRUCTIONS:
1. Preheat oven to 350°F
2. Mix dry ingredients
3. Add eggs and stir
```

Parsing rules:
- Look for headers: "ingredients", "recipe", "what you need", "you'll need"
- Ingredient lines: start with `-`, `•`, `*`, or a quantity (number or fraction)
- Instruction lines: start with numbers, or follow an "instructions"/"method"/"steps" header
- Stop parsing at: "FOLLOW ME", "SUBSCRIBE", links section, sponsor text

### Transcript Extraction

YouTube auto-generates captions for most videos. Access via:

1. Fetch page HTML
2. Look for `timedtext` or `captions` data in the page source
3. Alternative: use web search for `"{video_title} recipe transcript"`

Transcript processing:
- Remove timestamps
- Identify cooking actions: "add", "mix", "stir", "bake", "chop", "sauté"
- Group sequential cooking actions into numbered steps
- Extract mentioned quantities and ingredients

### Channel-Specific Patterns

Some popular cooking channels have consistent formats:

| Channel Style | Description Format | Extraction Approach |
|--------------|-------------------|---------------------|
| Professional (Bon Appétit, NYT) | Full recipe in description | Parse description directly |
| Casual creator | Partial ingredients, refers to blog | Follow blog link, extract from there |
| Short-form (Shorts) | Minimal description | Rely on transcript + comments |
| Blog-linked | "Full recipe at [link]" | Follow the link, use JSON-LD extraction |

## TikTok Extraction

TikTok cooking videos are typically short (15-180 seconds) with minimal text.

### Strategy

1. **Fetch page** — Scrape the TikTok page (may need stealth scraping for anti-bot)
2. **Parse caption** — The video caption sometimes contains ingredients
3. **Check comments** — Creators often post recipes in pinned comments
4. **Audio transcript** — TikTok auto-captions when available
5. **Web search** — Search for `"{creator name} {recipe name} recipe"` to find blog post

### Challenges

- Anti-bot protections require stealth scraping or browser automation
- Captions are often brief: "Viral pasta recipe" with no details
- Recipe may only be shown visually in the video (text overlay)
- Consider: ask user for any additional context they remember

## Instagram Extraction

Instagram Reels and posts often link to external recipe blogs.

### Strategy

1. **Fetch page** — May require authenticated scraping
2. **Parse caption** — Recipes sometimes in post caption
3. **Check for link** — "Link in bio" or direct URL to recipe blog
4. **Follow link** — Extract structured recipe from the linked page

### Caption Format

Instagram recipes often use emoji bullets:

```
[emoji] 2 tbsp butter
[emoji] 1 onion, diced
[emoji] 2 chicken breasts
[emoji] Salt and pepper to taste
```

Parse emoji-prefixed lines as ingredient lines (creators use food emoji as bullets).

## Structured Output Format

Extracted recipes follow a unified schema regardless of source.

```json
{
  "title": "One-Pot Lemon Garlic Pasta",
  "source": {
    "platform": "youtube",
    "url": "https://youtube.com/watch?v=...",
    "creator": "Cooking With Me"
  },
  "servings": 4,
  "prepTime": "10 minutes",
  "cookTime": "20 minutes",
  "totalTime": "30 minutes",
  "difficulty": "easy",
  "cuisine": "Italian",
  "dietary": ["vegetarian"],
  "ingredients": [
    {"quantity": "1", "unit": "pound", "item": "spaghetti"},
    {"quantity": "4", "unit": "cloves", "item": "garlic, minced"},
    {"quantity": "2", "unit": "tbsp", "item": "olive oil"},
    {"quantity": "1", "unit": "", "item": "lemon, juiced and zested"}
  ],
  "instructions": [
    "Bring a large pot of salted water to a boil.",
    "Cook spaghetti according to package directions.",
    "Meanwhile, sauté garlic in olive oil until golden.",
    "Toss drained pasta with garlic oil, lemon juice, and zest."
  ],
  "notes": "Creator suggests adding red pepper flakes for heat.",
  "confidence": 0.85,
  "extractionMethod": "description + transcript"
}
```

## Confidence Scoring

Not all extractions are equally reliable. Rate confidence to set user expectations.

| Score | Meaning | Criteria |
|-------|---------|----------|
| 0.9–1.0 | High | JSON-LD structured data found, or full recipe in description |
| 0.7–0.89 | Good | Ingredients from description + steps from transcript |
| 0.5–0.69 | Moderate | Partial info — ingredients OR steps, not both |
| 0.3–0.49 | Low | Mostly inferred from transcript, may have gaps |
| < 0.3 | Unreliable | Only video title available, heavy guessing |

### Factors That Raise Confidence

- JSON-LD `@type: Recipe` present → +0.3
- Explicit "INGREDIENTS" section in description → +0.2
- Numbered steps in description → +0.2
- Transcript available → +0.1
- Quantities with units found → +0.1

### Factors That Lower Confidence

- No description text → -0.3
- TikTok with only emoji caption → -0.2
- No transcript available → -0.1
- Ingredients without quantities → -0.1

## Presenting Extracted Recipes

When showing an extracted recipe to the user:

```markdown
## Extracted Recipe: One-Pot Lemon Garlic Pasta
**Source:** [Cooking With Me on YouTube](https://youtube.com/...)
**Confidence:** 4/5 (85% — from description + transcript)

### Ingredients (4 servings)
- 1 lb spaghetti
- 4 cloves garlic, minced
- 2 tbsp olive oil
- 1 lemon, juiced and zested

### Instructions
1. Bring a large pot of salted water to a boil.
2. Cook spaghetti according to package directions.
...

> NOTE: This recipe was extracted automatically. Some measurements
> may be approximate. Watch the original video for visual guidance.

Save to your cookbook? Add to shopping list?
```

Show the confidence warning when score is below 0.7. Offer next actions
(save to cookbook, generate shopping list) to keep the workflow flowing.

## Facebook and Generic URL Extraction

### Facebook Watch / Reels

Facebook cooking videos follow similar patterns to Instagram:

1. Fetch the page (may require browser automation for anti-bot)
2. Parse post text for recipe content
3. Check comments for recipes shared by the creator
4. Follow any external links to recipe blogs

### Generic Recipe URLs

For non-video URLs (recipe blogs, cooking sites):

1. Fetch the page HTML
2. Search for JSON-LD `@type: Recipe` — most recipe sites include this
3. If no JSON-LD, look for `itemtype="http://schema.org/Recipe"` microdata
4. If no structured data, parse the page content heuristically:
   - Find headers containing "ingredient" or "instruction"/"direction"/"method"
   - Extract lists following those headers
5. Build structured recipe from extracted data

### Multi-Language Considerations

Cooking content comes in many languages. When extracting from non-English sources:

- Ingredient quantities use universal number formats (1, 2, 1/2)
- Unit abbreviations vary by language (tsp/cac/TL/кч)
- Present the recipe in the user's language, translating where needed
- Keep original ingredient names if translation is uncertain — the user can
  recognize "mozzarella" or "tofu" in any language

## Fallback When Extraction Fails

If scraping fails or yields too little data:

1. Search the web: `"{video title}" recipe ingredients`
2. Check if the creator has a blog — search `"{creator name}" blog recipe`
3. Ask the user: "I couldn't extract a full recipe from that video. Could you share any details you remember (main ingredient, cuisine type)?"
4. Offer to search for a similar recipe: "Want me to find a similar [cuisine] recipe instead?"
