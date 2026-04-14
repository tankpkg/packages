# Shopping Lists

Sources: Grocery industry aisle organization, ingredient parsing patterns, Bring! API integration

Covers: parsing ingredients from recipes, unit normalization, aisle/category
grouping, multi-recipe aggregation, duplicate merging, and export to Bring!,
Apple Reminders, or plain text formats.

## Ingredient Parsing

### From TheMealDB Format

TheMealDB returns ingredient/measure pairs as separate fields:

```
strIngredient1: "chicken breast"    strMeasure1: "2"
strIngredient2: "olive oil"         strMeasure2: "2 tbsp"
strIngredient3: "garlic"            strMeasure3: "3 cloves"
```

Parse into structured format:

```json
{"quantity": "2", "unit": "", "item": "chicken breast"}
{"quantity": "2", "unit": "tbsp", "item": "olive oil"}
{"quantity": "3", "unit": "cloves", "item": "garlic"}
```

### From Free-Text Ingredients

When parsing recipe text from web sources or video extraction:

Common formats:
```
2 cups all-purpose flour
1/2 teaspoon salt
3 large eggs
1 (14 oz) can diced tomatoes
Salt and pepper to taste
Cooking spray
```

Parsing rules:
1. **Leading number** → quantity (support fractions: 1/2, 1/4, 3/4)
2. **Unit word after number** → unit (see unit table below)
3. **Remaining text** → item name
4. **Parenthetical** → size/clarification, keep with item
5. **"to taste"** → no quantity, mark as pantry staple
6. **No number** → quantity is implicit 1 or "as needed"

### Unit Recognition

| Written As | Normalized |
|-----------|-----------|
| cup, cups, c | cup |
| tablespoon, tablespoons, tbsp, Tbsp, T | tbsp |
| teaspoon, teaspoons, tsp, t | tsp |
| ounce, ounces, oz | oz |
| pound, pounds, lb, lbs | lb |
| gram, grams, g | g |
| kilogram, kilograms, kg | kg |
| milliliter, milliliters, ml, mL | ml |
| liter, liters, l, L | L |
| clove, cloves | clove |
| piece, pieces, pc | piece |
| can, cans | can |
| bunch, bunches | bunch |
| head, heads | head |
| pinch | pinch |
| dash | dash |
| slice, slices | slice |
| handful | handful |

## Aisle Categorization

Group ingredients by grocery store section for efficient shopping.

### Category Map

| Category | Items |
|----------|-------|
| Produce | Fruits, vegetables, fresh herbs, lettuce, avocado, lemon, lime, ginger, garlic, onion, potatoes, tomatoes, peppers, mushrooms, carrots, celery, broccoli, spinach |
| Meat & Poultry | Chicken, beef, pork, lamb, turkey, ground meat, sausage, bacon |
| Seafood | Salmon, shrimp, cod, tuna, tilapia, mussels, crab |
| Dairy & Eggs | Milk, cream, butter, cheese, yogurt, sour cream, eggs, cream cheese |
| Bakery & Bread | Bread, tortillas, pita, buns, rolls, croissants |
| Pasta & Grains | Pasta, rice, quinoa, couscous, noodles, oats, bulgur, barley |
| Canned & Jarred | Canned tomatoes, beans, coconut milk, broth, stock, tomato paste, olives, capers |
| Oils & Vinegars | Olive oil, vegetable oil, sesame oil, coconut oil, balsamic vinegar, wine vinegar, soy sauce |
| Spices & Seasonings | Salt, pepper, cumin, paprika, oregano, basil, thyme, cinnamon, chili flakes, curry powder, turmeric, garlic powder, bay leaves |
| Baking | Flour, sugar, baking powder, baking soda, vanilla extract, chocolate chips, cocoa powder, cornstarch, yeast |
| Frozen | Frozen vegetables, frozen fruit, frozen pizza dough, ice cream |
| Snacks & Nuts | Almonds, walnuts, cashews, peanuts, pine nuts, breadcrumbs, crackers |
| Condiments | Ketchup, mustard, mayonnaise, hot sauce, Worcestershire, fish sauce, hoisin, honey, maple syrup |
| Beverages | Wine (for cooking), beer (for cooking), stock/broth (if liquid) |

### Categorization Strategy

1. Check item against known category keywords
2. For ambiguous items, use the most common grocery placement
3. Items like "garlic" could be produce or spices — put in produce (whole) or spices (powder)
4. When uncertain, default to "Other"

## Multi-Recipe Aggregation

When building a shopping list from multiple recipes (e.g., a weekly meal plan),
combine duplicate ingredients.

### Merging Rules

1. **Same item, same unit** → add quantities
   - Recipe A: 2 cups flour + Recipe B: 1 cup flour → 3 cups flour

2. **Same item, different units** → convert to common unit, then add
   - 1 tbsp olive oil + 1/4 cup olive oil → 5 tbsp olive oil

3. **Same item, no quantity** → keep single entry with "as needed"
   - "Salt to taste" + "Salt to taste" → "Salt (to taste)"

4. **Similar items, different forms** → keep separate
   - "fresh basil" and "dried basil" are different items
   - "chicken breast" and "chicken thighs" are different items

### Common Conversions

| From | To | Factor |
|------|-----|--------|
| 1 tbsp | 3 tsp | 3x |
| 1 cup | 16 tbsp | 16x |
| 1 cup | 8 fl oz | 8x |
| 1 lb | 16 oz | 16x |
| 1 kg | 2.2 lb | 2.2x |
| 1 L | 4.2 cups | 4.2x |

## Export Formats

### Plain Text (default)

```
SHOPPING LIST (3 recipes, 12 items)

PRODUCE
□ 2 onions
□ 4 cloves garlic
□ 1 head broccoli
□ 3 tomatoes

MEAT & POULTRY
□ 2 chicken breasts
□ 1 lb ground beef

DAIRY & EGGS
□ 1 cup shredded cheese
□ 6 eggs

PASTA & GRAINS
□ 1 lb spaghetti
□ 2 cups rice

CANNED & JARRED
□ 1 can (14 oz) diced tomatoes
□ 1 can coconut milk
```

### Markdown Table

```markdown
| Category | Item | Qty |
|----------|------|-----|
| Produce | Onions | 2 |
| Produce | Garlic | 4 cloves |
| Meat | Chicken breast | 2 |
| Dairy | Eggs | 6 |
```

### Bring! Integration

Bring! is a popular shared shopping list app. Integration via their unofficial API.

Base URL: `https://api.getbring.com/rest/v2/`

Workflow:
1. User provides Bring! list UUID (from app settings or URL)
2. For each ingredient, POST to add item:
   ```
   PUT /bringlists/{listUuid}
   Content-Type: application/x-www-form-urlencoded

   uuid={listUuid}&purchase={item_name}&specification={quantity_and_unit}
   ```
3. Items appear immediately in the user's Bring! app

Item naming for Bring!:
- Use the main ingredient name as `purchase` (e.g., "Chicken breast")
- Use quantity + unit as `specification` (e.g., "2 pieces")
- Bring! auto-categorizes most common grocery items

### Apple Reminders

Generate a list of reminders that can be added via Siri Shortcuts or the
Reminders app URL scheme:

```
x-apple-reminderkit://REMCDReminder/create?title=2 onions&list=Shopping
```

Or provide the list as text for the user to paste into Reminders:

```
2 onions
4 cloves garlic
1 head broccoli
2 chicken breasts
```

One item per line — Apple Reminders creates one reminder per line when pasting.

## Pantry Staple Detection

Some ingredients are common pantry staples that most people already have.
Flag these separately so users can skip items they already own.

### Common Pantry Staples

Salt, pepper, olive oil, vegetable oil, flour, sugar, butter, garlic powder,
onion powder, dried oregano, dried basil, soy sauce, vinegar, baking powder,
baking soda, vanilla extract, paprika, cumin, cinnamon.

### Presentation

```
SHOPPING LIST

NEED TO BUY (10 items)
□ 2 chicken breasts
□ 1 lb spaghetti
□ 3 tomatoes
...

PROBABLY HAVE (check your pantry)
□ Olive oil
□ Salt
□ Garlic powder
□ Dried oregano
```

## Smart Suggestions

When generating a shopping list, add helpful notes:

- **Bulk opportunities**: "You need onions for 3 recipes — buy a bag instead of individual"
- **Substitution notes**: "No coconut milk? Heavy cream works as a substitute"
- **Freshness tips**: "Buy the salmon for Thursday's dinner last — use within 2 days"
- **Budget tips**: "Frozen broccoli works just as well here and costs less"
