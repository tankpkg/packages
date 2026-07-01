# Personal Cookbook

Sources: Recipe management app patterns, JSON data persistence, tagging and search design

Covers: recipe storage schema, local JSON persistence, tagging system, search
and filter operations, ratings and notes, import/export, and cookbook management
commands.

## Storage Location

Store the personal cookbook as a JSON file at a predictable location:

```
~/.cooking-mastery/cookbook.json
```

Create the directory and file on first use. The file contains a single JSON
object with metadata and a recipes array.

## Cookbook Schema

```json
{
  "version": "1.0",
  "lastModified": "2026-04-14T12:00:00Z",
  "recipes": [
    {
      "id": "r_1713100800_abc123",
      "title": "Spicy Arrabiata Penne",
      "slug": "spicy-arrabiata-penne",
      "source": {
        "type": "themealdb",
        "url": "https://www.themealdb.com/meal/52771",
        "originalId": "52771"
      },
      "cuisine": "Italian",
      "category": "Pasta",
      "dietary": ["vegetarian"],
      "difficulty": "easy",
      "prepTime": "10 minutes",
      "cookTime": "25 minutes",
      "servings": 4,
      "ingredients": [
        {"quantity": "1", "unit": "lb", "item": "penne rigate"},
        {"quantity": "1/4", "unit": "cup", "item": "olive oil"},
        {"quantity": "3", "unit": "cloves", "item": "garlic, minced"},
        {"quantity": "1", "unit": "can", "item": "crushed tomatoes (28 oz)"},
        {"quantity": "1", "unit": "tsp", "item": "red pepper flakes"}
      ],
      "instructions": [
        "Cook penne in salted boiling water until al dente.",
        "Heat olive oil in a large skillet over medium heat.",
        "Add garlic and red pepper flakes, cook 1 minute.",
        "Pour in crushed tomatoes, simmer 15 minutes.",
        "Toss drained pasta with sauce. Serve immediately."
      ],
      "tags": ["quick", "weeknight", "pasta", "spicy"],
      "rating": 4,
      "notes": "Added extra garlic — was even better.",
      "timesCooked": 3,
      "lastCooked": "2026-04-10",
      "dateAdded": "2026-03-15T10:30:00Z",
      "imageUrl": "https://www.themealdb.com/images/media/meals/..."
    }
  ]
}
```

## Recipe ID Generation

Generate unique IDs combining timestamp and random suffix:

```
r_{unix_timestamp}_{random_6_chars}
```

Example: `r_1713100800_f3k9x2`

The slug is a URL-friendly version of the title: lowercase, spaces to hyphens,
strip special characters.

## Core Operations

### Save a Recipe

When user says "save this recipe" or "add to cookbook":

1. Format the recipe into the schema above
2. Read existing cookbook file (or create if not exists)
3. Check for duplicates by title (case-insensitive) or source URL
4. If duplicate found, ask: "This recipe is already saved. Update it?"
5. Append to recipes array
6. Write back to file
7. Confirm: "Saved 'Spicy Arrabiata Penne' to your cookbook (tagged: quick, weeknight)"

### Search Recipes

When user says "find [X] in my cookbook" or "what pasta recipes do I have":

Search across these fields (case-insensitive partial match):
- `title`
- `cuisine`
- `category`
- `tags` (array contains)
- `ingredients[].item` (any ingredient matches)
- `notes`

Return results sorted by relevance (title match > tag match > ingredient match).

### List Recipes

When user says "show my cookbook" or "what recipes do I have":

Present as a scannable table:

```markdown
## Your Cookbook (24 recipes)

| # | Recipe | Cuisine | Tags | Rating | Last Cooked |
|---|--------|---------|------|--------|-------------|
| 1 | Spicy Arrabiata Penne | Italian | quick, pasta | 4/5 | Apr 10 |
| 2 | Chicken Tikka Masala | Indian | comfort, spicy | 5/5 | Apr 8 |
| 3 | Fish Tacos | Mexican | quick, seafood | 3/5 | Mar 28 |
...

Filter by: cuisine, tag, rating, or ingredient. What would you like to see?
```

### Update a Recipe

When user wants to modify a saved recipe:

1. Find recipe by title or ID
2. Apply changes (update fields, add tags, change rating)
3. Update `lastModified` timestamp
4. Write back to file
5. Confirm changes

### Delete a Recipe

1. Find recipe by title or ID
2. Confirm: "Remove 'Spicy Arrabiata Penne' from your cookbook?"
3. Remove from array
4. Write back to file

### Rate a Recipe

When user says "rate [recipe] 4 stars" or after cooking:

1. Find recipe by title
2. Set `rating` field (1-5)
3. Increment `timesCooked`
4. Set `lastCooked` to today
5. Confirm: "Rated 'Arrabiata Penne' 4/5 (cooked 3 times)"

### Add Notes

When user says "add a note to [recipe]":

1. Find recipe by title
2. Append to `notes` field (or replace)
3. Confirm: "Note added to 'Arrabiata Penne'"

## Tagging System

### Suggested Tags

Assign tags automatically based on recipe attributes, then let user customize.

| Auto-Tag Condition | Tag |
|-------------------|-----|
| Total time ≤ 30 min | `quick` |
| Total time ≤ 15 min | `express` |
| No meat ingredients | `vegetarian` |
| No animal products | `vegan` |
| No gluten ingredients | `gluten-free` |
| Category == Dessert | `dessert` |
| Cooking method = oven | `baked` |
| Cooking method = grill | `grilled` |
| One-pot/pan recipe | `one-pot` |

### User-Defined Tags

Users can add any custom tags:
- `meal-prep` — Good for batch cooking
- `date-night` — Impressive dishes
- `kids-love` — Family favorites
- `budget` — Economical recipes
- `holiday` — Special occasion dishes

## Smart Features

### "What Should I Cook?"

When user asks without specifics:

1. Check what they haven't cooked recently (sort by `lastCooked` ascending)
2. Favor higher-rated recipes (4-5 stars)
3. Consider the day (weekday → suggest `quick` tagged; weekend → any)
4. Present 3 suggestions:

```markdown
Based on your cookbook, how about:

1. **Chicken Tikka Masala** (5/5) — Last cooked 2 weeks ago
2. **Honey Garlic Salmon** (4/5) — You haven't made this in a month
3. **Mushroom Risotto** (4/5) — Perfect for a weeknight

Pick one, or tell me what you're in the mood for.
```

### Recipe Statistics

When user asks "show my cooking stats" or "what do I cook most":

```markdown
## Your Cooking Stats

**Total recipes:** 24
**Most cooked:** Chicken Stir Fry (8 times)
**Highest rated:** Chicken Tikka Masala (5/5)
**Favorite cuisine:** Italian (7 recipes)

**Cuisine breakdown:**
- Italian: 7 recipes
- Asian: 5 recipes
- Mexican: 4 recipes
- Indian: 3 recipes
- Other: 5 recipes

**Cooking frequency:** ~3 times per week
```

## Import and Export

### Import from URL

When user shares a recipe URL (not video):

1. Fetch the page
2. Look for JSON-LD `@type: Recipe` structured data
3. Parse into cookbook schema
4. Present for confirmation before saving

### Export Cookbook

When user says "export my cookbook":

Output options:
- **JSON** — Full cookbook.json file
- **Markdown** — Readable recipe book format
- **Individual recipes** — One markdown file per recipe

### Markdown Export Format

```markdown
# My Cookbook

## Spicy Arrabiata Penne
*Italian | Vegetarian | 4/5 | 35 min*

### Ingredients (4 servings)
- 1 lb penne rigate
- 1/4 cup olive oil
...

### Instructions
1. Cook penne in salted boiling water...
...

**Notes:** Added extra garlic — was even better.
**Tags:** quick, weeknight, pasta, spicy

---

## Chicken Tikka Masala
...
```

## Error Handling

| Scenario | Response |
|----------|----------|
| Cookbook file doesn't exist | Create it with empty recipes array |
| Cookbook file is corrupted JSON | Backup the corrupted file, create fresh |
| Duplicate recipe detected | Ask user: update existing or save as new? |
| Recipe not found in search | "No recipes matching '[query]' in your cookbook. Search online instead?" |
| No recipes saved yet | "Your cookbook is empty! Search for a recipe to save your first one." |
