# Typography System Design

Sources: Lupton (Thinking with Type), Spiekermann (Stop Stealing Sheep), Bringhurst (Elements of Typographic Style), Wheeler (Designing Brand Identity)

---

## Type Category Personality

Every typeface carries cultural and psychological weight accumulated through decades of use. Selecting a category is the first typographic decision — it sets the emotional register before a single word is read.

### Serif

Serifs signal heritage, authority, and credibility. The small strokes at letter terminals create a visual rhythm that guides the eye along a line, making serifs well-suited to long-form reading. Usability research consistently shows serif typefaces score higher on perceived trustworthiness in editorial and financial contexts.

| Sub-category | Characteristics | Personality | Brand Fit |
|---|---|---|---|
| **Old Style** (Garamond, Caslon, EB Garamond) | Low contrast, angled stress, bracketed serifs | Warmth, history, humanist craft | Publishing, heritage, artisan |
| **Transitional** (Baskerville, Times New Roman, Libre Baskerville) | Medium contrast, upright stress, refined serifs | Balanced authority, academic | Law, finance, education |
| **Modern / Didone** (Bodoni, Didot, Cormorant) | Extreme contrast, vertical stress, hairline serifs | High fashion, drama, luxury | Luxury goods, editorial, beauty |
| **Slab Serif** (Rockwell, Clarendon, Arvo) | Low contrast, heavy rectangular serifs | Bold confidence, industrial | Retail, tech hardware, outdoor |

### Sans-Serif

Sans-serifs communicate modernity, clarity, and accessibility. The absence of serifs reads as democratic and forward-looking — which is why technology companies and startups default to this category. Sub-category choice determines whether the result feels warm or cold, precise or approachable.

| Sub-category | Characteristics | Personality | Brand Fit |
|---|---|---|---|
| **Grotesque** (Helvetica, Arial, Akzidenz) | Irregular curves, some quirks, neutral | Universal, corporate, neutral | Enterprise, government, legacy brands |
| **Neo-Grotesque** (Inter, DM Sans, Plus Jakarta Sans) | Screen-optimized, high legibility, minimal quirks | Contemporary, clean, functional | SaaS, apps, digital-first products |
| **Geometric** (Futura, Montserrat, Poppins) | Circles and straight lines, mathematical | Precise, modern, idealistic | Tech startups, design studios, architecture |
| **Humanist** (Gill Sans, Frutiger, Nunito) | Calligraphic influence, open apertures | Friendly, approachable, warm | Healthcare, education, nonprofits |

### Script and Handwritten

Script typefaces simulate handwriting or calligraphy. They carry strong associations with the personal, celebratory, and artisanal. Legibility degrades rapidly at small sizes and in all-caps settings — restrict script to display use only.

| Sub-category | Personality | Brand Fit |
|---|---|---|
| **Formal Script** (high contrast, connected strokes) | Elegance, ceremony, luxury | Wedding, fine dining, premium beauty |
| **Casual Script** (brush, informal) | Warmth, creativity, handmade | Artisan food, personal brands, creative studios |
| **Handwritten** (irregular, personal) | Authenticity, approachability | Lifestyle brands, children's products |

### Display and Decorative

Display typefaces are designed for large sizes and short text. They express strong personality but sacrifice legibility at body sizes. Use exclusively for headlines, logotypes, and campaign text.

### Monospace

Monospace typefaces signal technical precision, code, and developer culture. Each character occupies identical horizontal space — a functional constraint that became a personality marker for technology brands.

---

## Font Selection by Brand Personality

Map the brand's primary personality trait to a type category before evaluating individual fonts. This prevents the common mistake of selecting a font for aesthetic reasons that contradicts the brand's emotional positioning.

| Brand Personality | Primary Category | Sub-category Direction | Avoid |
|---|---|---|---|
| **Professional / Authoritative** | Serif | Transitional or Modern | Script, decorative display |
| **Modern / Innovative** | Sans-serif | Geometric or Neo-Grotesque | Old Style serif, slab |
| **Luxury / Premium** | Serif or Display | Modern/Didone, high contrast | Rounded sans, casual script |
| **Friendly / Approachable** | Sans-serif | Humanist, rounded | High-contrast serif, condensed |
| **Heritage / Traditional** | Serif | Old Style or Transitional | Geometric sans, display |
| **Creative / Expressive** | Display or Geometric sans | Distinctive, high personality | Generic grotesque |
| **Technical / Developer** | Sans-serif or Monospace | Neo-Grotesque, monospace accent | Script, decorative |
| **Playful / Youthful** | Rounded sans or Display | Humanist, variable weight | Formal serif, condensed grotesque |
| **Minimal / Editorial** | Sans-serif or Serif | Neo-Grotesque or Didone | Slab, casual script |
| **Trustworthy / Institutional** | Serif | Transitional | Decorative, script |

---

## Google Fonts by Brand Personality

These pairings are production-tested combinations. The heading font carries brand personality; the body font prioritizes legibility. All fonts listed are available free via Google Fonts.

### Tech / Startup / Modern

| Role | Font | Weight | Why |
|---|---|---|---|
| Display | Space Grotesk | 700 | Geometric with distinctive quirks; tech-forward without being cold |
| Heading | Inter | 600–700 | Screen-optimized, neutral authority, ubiquitous in SaaS |
| Body | DM Sans | 400 | Clean, highly legible, pairs cleanly with Inter |
| Caption | DM Sans | 400 | Consistent family, reduces font load |

Alternative: Syne (display, 700) + Inter (body, 400) — more expressive, suits design-forward startups.

### Luxury / Premium

| Role | Font | Weight | Why |
|---|---|---|---|
| Display | Cormorant Garamond | 300–400 | Extreme contrast, editorial elegance, high fashion associations |
| Heading | Playfair Display | 700 | Classic luxury personality, strong at large sizes |
| Body | Montserrat | 300–400 | Clean geometric contrast to the serif display; light weight reads premium |
| Caption | Montserrat | 400 | Consistent family |

Alternative: Cinzel (display, 400) + Nunito (body, 300) — more elevated, classical.

### Heritage / Traditional

| Role | Font | Weight | Why |
|---|---|---|---|
| Display | Playfair Display | 700 | Classic authority, strong editorial presence |
| Heading | Merriweather | 700 | Readable, trustworthy, designed for screen legibility |
| Body | Source Serif 4 | 400 | Optimized for long-form reading, warm and reliable |
| Caption | Source Serif 4 | 400 | Consistent family |

Alternative: Libre Baskerville (heading, 700) + Lato (body, 400) — balanced heritage with modern body.

### Friendly / Approachable

| Role | Font | Weight | Why |
|---|---|---|---|
| Display | Nunito | 700–800 | Rounded terminals, warm, immediately approachable |
| Heading | Poppins | 600 | Geometric but softened; friendly without being childish |
| Body | Open Sans | 400 | Universal legibility, warm neutrality |
| Caption | Open Sans | 400 | Consistent family |

Alternative: Raleway (heading, 600) + Lato (body, 400) — slightly more stylish, suits lifestyle brands.

### Creative / Expressive

| Role | Font | Weight | Why |
|---|---|---|---|
| Display | Syne | 700–800 | Distinctive, artistic, strong personality at large sizes |
| Heading | Josefin Sans | 600 | Elegant geometric, art deco influence |
| Body | Work Sans | 400 | Clean, versatile, does not compete with expressive display |
| Caption | Work Sans | 400 | Consistent family |

Alternative: Abril Fatface (display, 400) + Lato (body, 400) — bold editorial contrast, suits publishing and media.

### Editorial / Publishing

| Role | Font | Weight | Why |
|---|---|---|---|
| Display | Abril Fatface | 400 | Bold editorial impact, newspaper heritage |
| Heading | Libre Franklin | 700 | Newspaper grotesque lineage, strong hierarchy |
| Body | Merriweather | 400 | Designed for long-form screen reading |
| Caption | Libre Franklin | 400 | Consistent family, clear contrast with body |

Alternative: Oswald (heading, 600) + Source Serif 4 (body, 400) — strong contrast, suits news and commentary.

---

## Font Pairing Rules

Pairing typefaces is a constraint problem: the two fonts must be different enough to serve distinct roles, yet similar enough to feel like they belong to the same system. Violating these rules produces either visual monotony (too similar) or visual chaos (too different).

**Rule 1: Maximum two font families.**
Use weights, sizes, and spacing to create hierarchy within those families. A third typeface almost always signals a lack of system thinking. The exception is a monospace accent for code or data — treat it as a functional element, not a brand font.

**Rule 2: Pair opposites.**
The most reliable pairing is a serif heading with a sans-serif body, or a sans-serif heading with a serif body. Contrast in category creates clear role differentiation. Pairing two serifs or two sans-serifs requires careful weight and personality contrast to avoid confusion.

**Rule 3: Match personality, not just aesthetics.**
Both fonts must reinforce the same brand archetype. A geometric sans-serif heading paired with a warm humanist body creates a personality contradiction. Evaluate each font against the brand's emotional register independently before pairing.

**Rule 4: Establish unambiguous hierarchy.**
Every typographic level — display, heading, subheading, body, caption — must be visually distinct. If two levels look similar, one is redundant. Differentiate through size, weight, and optionally style (italic), not through additional typefaces.

**Rule 5: Limit weights to two or three per family.**
Loading five weights of a font family adds page weight and visual noise. Regular (400) and Bold (700) cover most use cases. Add a Medium (500) or Semibold (600) only when the hierarchy genuinely requires it.

---

## Typography Hierarchy System

A brand typography system defines six levels. Each level has a specific purpose; using a level outside its purpose breaks the system's logic.

| Level | Purpose | Size Range (web) | Weight | Line Height |
|---|---|---|---|---|
| **Display** | Hero sections, campaign headlines, landing page openers | 56–96px | 700–900 | 1.0–1.1 |
| **H1** | Primary page title, one per page | 36–52px | 700 | 1.1–1.2 |
| **H2** | Major section headings | 28–36px | 600–700 | 1.2–1.3 |
| **H3** | Subsection headings, card titles | 20–26px | 500–600 | 1.3–1.4 |
| **Body** | All reading text, paragraphs | 16–18px | 400 | 1.5–1.7 |
| **Caption / Label** | Supporting information, metadata, UI labels | 12–14px | 400–500 | 1.4–1.5 |

**Print equivalents:** Body text at 10–12pt, headings scaled proportionally. Line height in print is expressed as leading — body text typically 120–145% of point size.

**Minimum body size:** 16px on screen. Below 16px, reading comfort degrades for users over 40. Never use 14px or smaller for paragraph text.

**Letter spacing:** Tighten display and heading text slightly (−0.01em to −0.03em) to compensate for optical spacing at large sizes. Never tighten body text. Uppercase labels benefit from slight tracking (+0.05em to +0.1em).

---

## Type Scale Ratios

A type scale applies a single multiplier consistently across all hierarchy levels, producing proportional relationships that feel mathematically coherent. Choose one ratio and apply it throughout the system.

| Ratio | Name | Scale (from 16px base) | Character | When to Use |
|---|---|---|---|---|
| **1.25** | Major Third | 16 / 20 / 25 / 31 / 39 / 49px | Subtle, compact | Dense UIs, dashboards, data-heavy products |
| **1.333** | Perfect Fourth | 16 / 21 / 28 / 37 / 50 / 67px | Balanced, versatile | Most web applications, marketing sites |
| **1.5** | Perfect Fifth | 16 / 24 / 36 / 54 / 81px | Clear, editorial | Content-heavy sites, blogs, documentation |
| **1.618** | Golden Ratio | 16 / 26 / 42 / 68 / 110px | Dramatic, expressive | Landing pages, brand campaigns, portfolios |

**Practical guidance:**
- Use 1.25 when vertical space is constrained or content density is high.
- Use 1.333 as the default for most brand systems — it produces readable hierarchy without excessive size jumps.
- Use 1.5 when long-form reading is the primary use case.
- Use 1.618 only when the brand calls for dramatic visual impact; the large size jumps make it impractical for complex page layouts.

**Applying the scale:** Start with the body size (16px or 18px), then multiply up for headings and divide down for captions. Round to the nearest whole pixel for implementation.

---

## Font Loading for Web

Incorrect font loading causes layout shift, flash of unstyled text, and performance degradation. Follow this pattern for all Google Fonts implementations.

**Standard Google Fonts CSS link:**

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Playfair+Display:wght@700&display=swap">
```

The `preconnect` hints reduce DNS lookup and connection time. The `crossorigin` attribute on the gstatic link is required for CORS-enabled font files.

**`font-display: swap`** is included automatically in the Google Fonts CSS URL when `display=swap` is appended. This instructs the browser to render text in a fallback font immediately, then swap to the loaded font — preventing invisible text during load.

**Load only the weights you use.** Each additional weight adds approximately 20–40KB. A system using Regular (400) and Bold (700) should request only those two weights.

**Variable fonts** (where available) load a single file covering a range of weights. Inter and Playfair Display both offer variable font versions. Use the variable font URL format when the design uses more than two weights:

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap">
```

**System font fallback stack** for body text when the web font is unavailable:

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

---

## Common Typography Mistakes

These errors consistently make brand typography feel amateur or unresolved. Each has a specific cause and correction.

**Using more than two typefaces.** Adding a third font family almost never improves a system. It signals that the designer could not solve hierarchy problems within the existing system. Solve hierarchy with weight, size, and spacing first.

**Choosing a font for its name or trend status.** Fonts become overused quickly. Evaluate a font by its letterforms and personality fit, not by which brands currently use it. A font that was distinctive in 2022 may read as generic by 2026.

**Mismatching personality.** Pairing a playful rounded sans-serif with a high-contrast Didone serif creates a personality contradiction that users feel even if they cannot articulate it. Both fonts must serve the same emotional register.

**Body text below 16px.** Anything smaller than 16px on screen forces users to lean in. This is particularly damaging for brands targeting users over 35.

**Insufficient line height on body text.** Line height below 1.5 on body text causes lines to feel cramped and slows reading speed. The minimum for comfortable reading is 1.5; 1.6–1.65 is optimal for most typefaces.

**All-caps body text.** All-caps reduces reading speed by approximately 10–15% because it eliminates the word-shape recognition that readers rely on. Reserve all-caps for short labels, navigation items, and captions only.

**Ignoring optical size.** A typeface set at 72px needs tighter letter spacing than the same typeface at 16px. Most digital type does not auto-adjust for optical size. Manually tighten tracking on display text (−0.02em to −0.04em) and loosen it slightly on very small text.

**Justified text on screen.** Justified alignment creates uneven word spacing (rivers) on variable-width screens. Use left-aligned text for all body copy on web. Justified text is appropriate only in print with proper hyphenation.

**Decorative fonts in body text.** Display and script typefaces are designed for large sizes. At 16px, their distinctive features become noise that impedes reading. Body text must be set in a typeface designed for reading — typically a humanist sans-serif or a text-optimized serif.

**Neglecting fallback fonts.** A brand typography system that only specifies the web font will render in Times New Roman or Arial when the font fails to load. Always define a complete fallback stack that approximates the intended personality.
