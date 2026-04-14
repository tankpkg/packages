# Recipe Search

Sources: TheMealDB API documentation, web recipe search patterns, Gousto catalog structure

Covers: TheMealDB API endpoints (search, filter, lookup, random), query routing
by user intent, response parsing, fallback strategies when API lacks results.

## TheMealDB API Reference

Base URL: `https://www.themealdb.com/api/json/v1/1/`

Free tier (API key `1`) supports all read operations with no authentication.
Rate limit is generous for single-user agent use.

### Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `search.php?s={name}` | GET | Search meals by name |
| `search.php?f={letter}` | GET | List meals starting with letter |
| `lookup.php?i={id}` | GET | Get full meal details by ID |
| `random.php` | GET | Single random meal |
| `randomselection.php` | GET | 10 random meals (paid key only) |
| `filter.php?i={ingredient}` | GET | Filter by main ingredient |
| `filter.php?c={category}` | GET | Filter by category |
| `filter.php?a={area}` | GET | Filter by cuisine/area |
| `categories.php` | GET | List all categories with descriptions |
| `list.php?c=list` | GET | List all category names |
| `list.php?a=list` | GET | List all area/cuisine names |
| `list.php?i=list` | GET | List all ingredient names |

### Search by Name

```
GET https://www.themealdb.com/api/json/v1/1/search.php?s=Arrabiata
```

Returns full meal objects with all fields. Supports partial matches —
searching "chicken" returns all meals containing "chicken" in the name.

Response structure:
```json
{
  "meals": [
    {
      "idMeal": "52771",
      "strMeal": "Spicy Arrabiata Penne",
      "strCategory": "Vegetarian",
      "strArea": "Italian",
      "strInstructions": "...",
      "strMealThumb": "https://...",
      "strTags": "Pasta,Curry",
      "strYoutube": "https://...",
      "strIngredient1": "penne rigate",
      "strMeasure1": "1 pound",
      "strIngredient2": "olive oil",
      "strMeasure2": "1/4 cup",
      ...
    }
  ]
}
```

If no results: `{"meals": null}`.

### Filter Endpoints

Filter returns lightweight objects (id, name, thumbnail only). Use `lookup.php`
to get full details for selected meals.

```
GET filter.php?i=chicken_breast    # by ingredient (use underscores)
GET filter.php?c=Seafood           # by category
GET filter.php?a=Canadian          # by cuisine
```

Filter response (abbreviated):
```json
{
  "meals": [
    {
      "strMeal": "Honey Teriyaki Salmon",
      "strMealThumb": "https://...",
      "idMeal": "52773"
    }
  ]
}
```

After filtering, fetch full recipe with `lookup.php?i={idMeal}`.

### Available Cuisines (Areas)

American, British, Canadian, Chinese, Croatian, Dutch, Egyptian, Filipino,
French, Greek, Indian, Irish, Italian, Jamaican, Japanese, Kenyan, Malaysian,
Mexican, Moroccan, Norwegian, Polish, Portuguese, Russian, Spanish, Thai,
Tunisian, Turkish, Ukrainian, Vietnamese.

### Available Categories

Beef, Breakfast, Chicken, Dessert, Goat, Lamb, Miscellaneous, Pasta, Pork,
Seafood, Side, Starter, Vegan, Vegetarian.

### Ingredient Parsing from Response

Meals have 20 ingredient/measure pairs (`strIngredient1`–`strIngredient20`,
`strMeasure1`–`strMeasure20`). Many are empty strings or null. Parse them:

```
For i in 1..20:
  ingredient = meal[f"strIngredient{i}"]
  measure = meal[f"strMeasure{i}"]
  if ingredient and ingredient.strip():
    add (measure.strip(), ingredient.strip()) to ingredients list
```

## Query Routing

Match user intent to the right endpoint combination.

| User Says | Strategy | Endpoints |
|-----------|----------|-----------|
| "Find a chicken recipe" | Search by name | `search.php?s=chicken` |
| "What can I cook with salmon?" | Filter by ingredient | `filter.php?i=salmon` → `lookup.php` |
| "Give me Italian food" | Filter by cuisine | `filter.php?a=Italian` → `lookup.php` |
| "I want a dessert" | Filter by category | `filter.php?c=Dessert` → `lookup.php` |
| "Surprise me" / "random dinner" | Random | `random.php` |
| "What cuisines are available?" | List areas | `list.php?a=list` |
| "Show me pasta recipes" | Filter by category | `filter.php?c=Pasta` → `lookup.php` |
| "Vegetarian dinner ideas" | Filter by category | `filter.php?c=Vegetarian` → `lookup.php` |

### Multi-Criteria Searches

TheMealDB does not support compound filters (e.g., "Italian + chicken"). Strategy:

1. Filter by the most restrictive criterion first (usually ingredient)
2. Fetch full details for results
3. Filter client-side by the second criterion (check `strArea`, `strCategory`)

Example: "Italian chicken recipes"
1. `filter.php?i=chicken` → list of chicken meals
2. `lookup.php?i={id}` for each result
3. Keep only where `strArea == "Italian"`

### When TheMealDB Falls Short

The API has ~300 meals. For queries that return null or too few results:

1. **Web search fallback**: Search the web for `"{query} recipe site:allrecipes.com OR site:food.com OR site:bbcgoodfood.com"`
2. **Scrape recipe page**: Fetch the URL and extract recipe from structured data (JSON-LD `@type: Recipe`) or from page content
3. **Present with attribution**: Always link back to the source URL

### JSON-LD Recipe Extraction

Most major recipe sites embed structured data. Look for:

```html
<script type="application/ld+json">
{
  "@type": "Recipe",
  "name": "...",
  "recipeIngredient": ["1 cup flour", "2 eggs"],
  "recipeInstructions": [{"text": "Preheat oven..."}],
  "prepTime": "PT15M",
  "cookTime": "PT30M",
  "recipeYield": "4 servings",
  "nutrition": { "calories": "350" }
}
</script>
```

Parse with standard JSON. The `recipeIngredient` array and `recipeInstructions`
array map directly to the unified recipe format (see `references/personal-cookbook.md`).

## Presenting Search Results

### Comparison Table Format

When showing multiple results, present as a scannable table:

```markdown
| # | Recipe | Cuisine | Category | Time |
|---|--------|---------|----------|------|
| 1 | Honey Teriyaki Salmon | Japanese | Seafood | 30 min |
| 2 | Chicken Fajita Mac and Cheese | Mexican | Chicken | 35 min |
| 3 | Fish Stew | Italian | Seafood | 45 min |

Which one would you like? I can show the full recipe with ingredients.
```

### Full Recipe Format

When showing a single recipe:

```markdown
## Spicy Arrabiata Penne
**Cuisine:** Italian | **Category:** Vegetarian | **Servings:** 4

### Ingredients
- 1 pound penne rigate
- 1/4 cup olive oil
- 3 cloves garlic, minced
...

### Instructions
1. Bring a large pot of salted water to a boil...
2. Meanwhile, heat olive oil in a large skillet...
...

[Video](https://youtube.com/...) | [Photo](https://themealdb.com/...)
```

### Random Discovery

For "surprise me" or "I don't know what to cook":

1. Call `random.php` once
2. Present the meal with full details
3. Offer: "Want another suggestion? Or I can search for something specific."

If user wants options: call `random.php` 3 times and present as comparison table.

## Error Handling

| Scenario | Response |
|----------|----------|
| `{"meals": null}` | "No recipes found for that. Try a broader search or different ingredient." |
| Network error | "Can't reach TheMealDB right now. Let me search the web instead." |
| Empty ingredient list | Skip — meal data is incomplete, note to user |
| No YouTube link | Skip video link — not all meals have one |

## Gousto as Supplementary Source

Gousto offers 9,000+ recipes with richer metadata (nutritional info, prep time,
difficulty, ratings, step-by-step instructions with photos). Access requires
web scraping their recipe pages at `gousto.co.uk/cookbook/`.

Use Gousto when:
- User asks for nutritional information (calories, macros)
- User wants difficulty ratings
- TheMealDB returns no results for a specific query
- User wants detailed step-by-step photos

Scrape with web fetch tool → parse HTML → extract recipe data. Look for
JSON-LD structured data first, fall back to HTML parsing.

## Common Substitutions

When a recipe calls for an unavailable ingredient, suggest substitutions
to keep the user cooking rather than abandoning the recipe.

| Missing | Substitute | Notes |
|---------|-----------|-------|
| Buttermilk | Milk + 1 tbsp lemon juice per cup | Let sit 5 min |
| Heavy cream | Coconut cream (dairy-free) | Works in most sauces |
| Egg (baking) | 1/4 cup applesauce per egg | Adds slight sweetness |
| Fresh herbs | 1/3 amount dried herbs | Dried is more concentrated |
| Wine (cooking) | Equal amount broth + splash vinegar | Lacks depth but works |
| Sour cream | Greek yogurt | Nearly identical in cooking |
| Breadcrumbs | Crushed crackers or oats | Adjust seasoning |
| Lemon juice | Lime juice or white vinegar | 1:1 ratio |

Offer substitutions when the user mentions missing ingredients or asks
"what can I use instead of [X]?".
