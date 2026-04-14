# Meal Planning

Sources: USDA Dietary Guidelines (2020-2025), meal prep community patterns, nutritional balance frameworks

Covers: weekly meal plan generation, dietary restriction handling, pantry-based
suggestions, nutritional variety, portion scaling, and plan output formats.

## Planning Workflow

### Step 1: Gather Preferences

Before generating a plan, collect:

| Question | Why |
|----------|-----|
| How many people? | Portion scaling |
| Any dietary restrictions? | Filter incompatible recipes |
| What's already in your fridge/pantry? | Prioritize using what's available |
| Cooking skill level? | Match recipe difficulty |
| How many meals per day? | Scope the plan (dinner only vs full day) |
| Any cuisine preferences? | Guide variety without monotony |
| Time constraints? | Quick weekday meals, elaborate weekend cooking |
| Budget considerations? | Favor economical ingredients |

If user provides partial info, apply sensible defaults:
- 2 adults, no restrictions, dinner only, mixed cuisines, moderate skill

### Step 2: Build the Plan

Planning rules for a balanced, enjoyable week:

1. **Protein rotation** — Never repeat the same protein two days in a row
2. **Cuisine variety** — Rotate through 3-4 cuisines across the week
3. **Cooking method variety** — Mix baking, sautéing, grilling, slow-cooking
4. **Effort distribution** — Heavier cooking on weekends, quick meals midweek
5. **Leftover strategy** — Sunday roast → Monday's sandwiches or fried rice
6. **Seasonal awareness** — Suggest lighter meals in summer, hearty in winter

### Step 3: Source Recipes

For each planned meal:
1. Search TheMealDB first (see `references/recipe-search.md`)
2. If no result, search the web for a matching recipe
3. Include full ingredient lists for shopping list generation

### Step 4: Present and Iterate

Show the plan, then ask for swaps. Users frequently want to change 1-2 meals.

## Dietary Restrictions

### Common Restrictions and Filtering

| Restriction | TheMealDB Filter | Additional Rules |
|-------------|-----------------|------------------|
| Vegetarian | `filter.php?c=Vegetarian` | Exclude meat, poultry, fish |
| Vegan | `filter.php?c=Vegan` | Exclude all animal products |
| Gluten-free | No filter — check ingredients | Exclude wheat, barley, rye, oats (unless certified GF) |
| Dairy-free | No filter — check ingredients | Exclude milk, cheese, butter, cream, yogurt |
| Nut-free | No filter — check ingredients | Exclude all tree nuts and peanuts |
| Low-carb / Keto | No filter — check ingredients | Limit carbs to <50g per meal, favor proteins and fats |
| Halal | No filter — check ingredients | Exclude pork, alcohol in cooking |
| Kosher | No filter — check ingredients | Exclude pork, shellfish; no meat + dairy together |
| Pescatarian | `filter.php?c=Seafood` + Vegetarian | Fish and seafood OK, no meat/poultry |

### Ingredient Checking

When TheMealDB doesn't have a category filter for a restriction, check
each recipe's ingredients against exclusion lists:

```
Gluten sources: flour, bread, breadcrumbs, pasta (unless GF),
  soy sauce (use tamari), beer, barley, rye, couscous, bulgur

Dairy sources: milk, cream, butter, cheese, yogurt, whey,
  casein, ghee (sometimes OK), sour cream, ice cream

Nut sources: almonds, cashews, walnuts, pecans, pistachios,
  pine nuts, peanuts, hazelnuts, macadamias, coconut (usually OK)
```

## Pantry-Based Suggestions

When user says "what can I cook with what I have":

### Collection Phase

Ask: "What proteins, vegetables, and pantry staples do you have?"

Organize into categories:
- **Proteins**: chicken, beef, tofu, eggs, fish, etc.
- **Vegetables**: onions, garlic, peppers, tomatoes, etc.
- **Pantry staples**: rice, pasta, canned tomatoes, spices, oils
- **Dairy**: cheese, milk, cream, butter

### Matching Strategy

1. Filter TheMealDB by primary ingredient: `filter.php?i={main_protein}`
2. Fetch full recipes for results
3. Score each recipe by ingredient overlap with user's pantry
4. Rank by: (ingredients user has) / (total ingredients needed)
5. Present top 3 with missing ingredients highlighted

### Presentation

```markdown
## What You Can Cook

### 1. Chicken Stir Fry (95% match)
You have 9/10 ingredients. **Missing:** sesame oil

### 2. Chicken Fajitas (80% match)
You have 8/10 ingredients. **Missing:** tortillas, sour cream

### 3. Chicken Curry (70% match)
You have 7/10 ingredients. **Missing:** coconut milk, curry paste, lime
```

## Weekly Plan Format

### Standard Output

```markdown
# Meal Plan: Week of January 20

| Day | Dinner | Cuisine | Time | Protein |
|-----|--------|---------|------|---------|
| Monday | Chicken Stir Fry | Asian | 25 min | Chicken |
| Tuesday | Spaghetti Bolognese | Italian | 40 min | Beef |
| Wednesday | Fish Tacos | Mexican | 30 min | Fish |
| Thursday | Vegetable Curry | Indian | 35 min | Chickpeas |
| Friday | Pizza Night | Italian | 45 min | Varied |
| Saturday | Grilled Salmon | Mediterranean | 30 min | Salmon |
| Sunday | Roast Chicken | British | 90 min | Chicken |

## Shopping List
[Auto-generated from all recipes — see references/shopping-lists.md]

---
Want to swap any meals? I can also generate the full shopping list.
```

### Full Day Plan (when requested)

```markdown
# Full Day Meal Plan: Monday

**Breakfast:** Greek Yogurt Parfait (10 min)
- Greek yogurt, granola, berries, honey

**Lunch:** Chicken Caesar Wrap (15 min)
- Leftover chicken, romaine, parmesan, tortilla

**Dinner:** Teriyaki Salmon Bowl (30 min)
- Salmon, rice, edamame, avocado, teriyaki sauce

**Snacks:** Apple slices with peanut butter | Trail mix
```

## Portion Scaling

Scale recipes by family size:

| Original Servings | Target | Multiplier |
|-------------------|--------|------------|
| 4 | 2 (couple) | 0.5x |
| 4 | 4 (family) | 1x |
| 4 | 6 (large family) | 1.5x |
| 4 | 1 (solo) | 0.25x |

Apply multiplier to all ingredient quantities. Round to practical amounts:
- Don't say "0.25 onion" → say "1 small onion" or "half an onion"
- Don't say "0.5 egg" → say "1 egg" (round up for baking)
- Don't say "0.125 tsp" → say "a pinch"

### Rounding Rules

| Unit | Round to |
|------|----------|
| tsp / tbsp | Nearest 1/4 |
| cups | Nearest 1/4 |
| oz / g | Nearest whole number |
| items (eggs, onions) | Round up |
| "pinch" / "to taste" | Keep as-is |

## Leftover Integration

Plan for intentional leftovers to reduce cooking days:

| Cook on | Leftover becomes |
|---------|-----------------|
| Sunday roast chicken | Monday chicken salad or wraps |
| Big batch chili | Wednesday chili dogs or nachos |
| Extra rice | Friday fried rice |
| Roasted vegetables | Next day's frittata or grain bowl |

When generating a plan, mark leftover reuse with "(L)" to indicate no extra
cooking needed, reducing the perceived effort for the week.

## Seasonal Considerations

Suggest seasonally appropriate meals:

| Season | Favored Styles | Avoid |
|--------|---------------|-------|
| Spring | Light salads, grilled fish, fresh herbs | Heavy stews |
| Summer | Grilled meats, cold soups, salads, BBQ | Long oven roasts |
| Autumn | Roasts, soups, squash dishes, comfort food | Light cold dishes |
| Winter | Stews, casseroles, warm soups, baked dishes | Raw-heavy meals |

Determine season from the current date and the user's hemisphere.

## Budget-Conscious Planning

When budget is a concern, apply these strategies:

### Economical Ingredient Swaps

| Expensive | Budget Alternative | Savings |
|-----------|-------------------|---------|
| Salmon | Canned tuna or tilapia | 60-70% |
| Beef tenderloin | Chuck roast (slow-cook) | 50% |
| Fresh herbs | Dried herbs | 80% |
| Pine nuts | Sunflower seeds | 70% |
| Parmesan | Pecorino or nutritional yeast | 40% |
| Saffron | Turmeric + paprika | 95% |

### Planning for Savings

1. **Build around sales** — Ask what's on sale this week, plan meals around those proteins
2. **Batch-cook staples** — Rice, beans, roasted vegetables last multiple meals
3. **Use whole chickens** — Roast once, use in 3-4 meals through the week
4. **Meatless days** — 2-3 vegetarian dinners per week significantly cuts cost
5. **Seasonal produce** — In-season vegetables are 30-50% cheaper

### Budget Meal Plan Template

Aim for $50-75/week for 2 adults (dinner only):

| Day | Meal Type | Budget Target |
|-----|-----------|---------------|
| Monday | Pasta or grain bowl | $5-7 |
| Tuesday | Chicken + vegetables | $8-10 |
| Wednesday | Vegetarian | $4-6 |
| Thursday | Leftovers remix | $0 (already bought) |
| Friday | Budget fish or eggs | $6-8 |
| Saturday | Slow cooker or batch | $8-10 |
| Sunday | Roast + sides | $10-12 |

## Cooking Skill Adaptation

Match recipe complexity to the user's stated skill level.

| Skill Level | Recipe Characteristics | Avoid |
|-------------|----------------------|-------|
| Beginner | Under 10 ingredients, under 5 steps, common techniques (boil, sauté, bake) | Tempering chocolate, making roux, deboning fish |
| Intermediate | Up to 15 ingredients, multi-step, some technique required | Soufflés, complex sauces, deep frying |
| Advanced | Any complexity, specialized techniques welcome | Nothing — suggest everything |

For beginners, add brief technique explanations:
- "Sauté (cook in a pan with a little oil over medium-high heat)"
- "Simmer (keep the liquid just below boiling — small bubbles)"
- "Fold (gently mix by scooping from the bottom upward)"
