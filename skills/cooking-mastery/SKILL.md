---
name: "@tank/cooking-mastery"
description: |
  Your AI agent becomes a personal chef — find any recipe by name, cuisine,
  category, or ingredient via TheMealDB API (free, no auth). Extract structured
  recipes from YouTube, TikTok, and Instagram video URLs with confidence scoring.
  Plan weekly meals based on dietary preferences, pantry contents, and family
  size. Generate organized shopping lists grouped by aisle with export to Bring!,
  Apple Reminders, or plain text. Save and manage a personal cookbook with tags,
  ratings, and persistent local storage.

  Synthesizes TheMealDB API documentation, web recipe extraction patterns
  (JSON-LD schema.org Recipe), USDA Dietary Guidelines, grocery organization
  practices, and recipe management app patterns.

  Trigger phrases: "find me a recipe", "what can I cook with",
  "recipe for", "extract recipe from video", "meal plan",
  "weekly meal plan", "shopping list", "add to cookbook",
  "save this recipe", "random dinner idea", "Italian recipes",
  "what should I cook", "recipe from URL", "grocery list",
  "what's for dinner", "vegetarian recipes", "gluten free recipe",
  "cooking with leftovers", "what can I make"
---

# Cooking Mastery

Find recipes, extract them from videos, plan meals, build shopping lists,
and manage a personal cookbook.

## Core Philosophy

1. **TheMealDB first, web fallback** — Free API covers the common case
   (~300 meals, 29 cuisines, 14 categories). When it returns nothing,
   fall back to web search + JSON-LD extraction from recipe sites.
2. **Video is just another source** — YouTube, TikTok, Instagram URLs
   produce the same structured recipe object as API results. Parse
   description, transcript, and structured data; score confidence.
3. **Recipes flow into actions** — A found recipe is not the end. Offer
   next steps: save to cookbook, generate shopping list, add to meal plan.
4. **Shopping lists are organized** — Group ingredients by grocery aisle,
   merge duplicates across recipes, flag pantry staples the user likely has.
5. **The cookbook remembers** — Saved recipes persist in
   `~/.cooking-mastery/cookbook.json` with tags, ratings, notes, and
   cooking history. Suggest recipes the user hasn't cooked recently.

## Quick-Start: Common Tasks

### "Find me a recipe for [X]"

1. Search TheMealDB: `search.php?s={query}`
2. If results, present as comparison table (name, cuisine, time)
3. If no results, search the web for `"{query} recipe"` and extract JSON-LD
4. Show full recipe on selection. Offer: save, shopping list, or plan.
   -> See `references/recipe-search.md` for all API endpoints and query routing

### "What can I cook with [ingredients]?"

1. Filter TheMealDB by main ingredient: `filter.php?i={ingredient}`
2. Fetch full recipes for results
3. Score by overlap with user's available ingredients
4. Present top 3 with missing ingredients highlighted
   -> See `references/recipe-search.md` (pantry matching)
   -> See `references/meal-planning.md` (pantry-based suggestions)

### "Extract recipe from this video"

1. Detect platform from URL (YouTube, TikTok, Instagram)
2. Fetch page, look for JSON-LD first, then parse description/transcript
3. Build structured recipe with confidence score
4. Present with confidence warning if below 70%
   -> See `references/video-recipe-extraction.md`

### "Plan meals for the week"

1. Gather: people count, dietary restrictions, preferences, time constraints
2. Build 7-day plan with protein rotation, cuisine variety, effort balance
3. Source each recipe from TheMealDB or web
4. Present as weekly table. Offer shopping list generation.
   -> See `references/meal-planning.md`

### "Make a shopping list for [recipes]"

1. Parse ingredients from all selected recipes
2. Normalize units, merge duplicates
3. Group by grocery aisle category
4. Flag pantry staples separately
5. Export: plain text (default), Bring!, Apple Reminders, or markdown table
   -> See `references/shopping-lists.md`

### "Save this recipe" / "Show my cookbook"

1. Save: format recipe to schema, check duplicates, persist to JSON
2. Search: match across title, tags, cuisine, ingredients
3. Suggest: favor high-rated, not-recently-cooked recipes
   -> See `references/personal-cookbook.md`

## Decision Trees

### Query Type Routing

| User Intent | Action | Primary Reference |
|-------------|--------|-------------------|
| Search by name/cuisine/category | TheMealDB API | `recipe-search.md` |
| Search by ingredient | TheMealDB filter + pantry match | `recipe-search.md` |
| Random suggestion | TheMealDB random endpoint | `recipe-search.md` |
| Extract from video URL | Scrape + parse | `video-recipe-extraction.md` |
| Extract from recipe URL | Fetch + JSON-LD | `video-recipe-extraction.md` |
| Weekly meal plan | Planning workflow | `meal-planning.md` |
| Shopping list | Ingredient aggregation | `shopping-lists.md` |
| Save/search/rate recipe | Cookbook CRUD | `personal-cookbook.md` |
| "What should I cook?" | Cookbook suggestion engine | `personal-cookbook.md` |

### Dietary Restriction Handling

| Restriction | TheMealDB Support | Fallback |
|-------------|-------------------|----------|
| Vegetarian | Category filter | Direct |
| Vegan | Category filter | Direct |
| Gluten-free | No filter | Check ingredients list |
| Dairy-free | No filter | Check ingredients list |
| Nut-free | No filter | Check ingredients list |
| Halal / Kosher | No filter | Check ingredients list |
| Keto / Low-carb | No filter | Check ingredients + macros |

See `references/meal-planning.md` for ingredient exclusion lists per restriction.

### Data Flow Between Features

```
Search/Video → Recipe Object → Save to Cookbook
                             → Generate Shopping List
                             → Add to Meal Plan → Generate Shopping List
```

Every feature produces or consumes the same recipe object format, enabling
seamless chaining between search, save, plan, and shop.

## Permissions

| Permission | Scope | Reason |
|-----------|-------|--------|
| Network | `themealdb.com` | Recipe search API |
| Network | `*.youtube.com`, `*.tiktok.com`, `*.instagram.com` | Video recipe extraction |
| Network | `api.getbring.com` | Shopping list export (optional) |
| Filesystem | Read + Write `~/.cooking-mastery/` | Personal cookbook persistence |

## Reference Index

| File | Contents |
|------|----------|
| `references/recipe-search.md` | TheMealDB API endpoints, query routing, response parsing, web fallback, JSON-LD extraction |
| `references/video-recipe-extraction.md` | URL detection, platform-specific scraping, structured output, confidence scoring |
| `references/meal-planning.md` | Planning workflow, dietary restrictions, pantry suggestions, portion scaling, weekly plan format |
| `references/shopping-lists.md` | Ingredient parsing, unit normalization, aisle grouping, multi-recipe aggregation, export formats |
| `references/personal-cookbook.md` | Cookbook schema, CRUD operations, tagging, search, ratings, import/export |
