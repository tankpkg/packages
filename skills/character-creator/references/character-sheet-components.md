# Character Sheet Components

Sources: Harder (Creative Character Design for Games), Hu (Mastering Character Design), Silver (The Silver Way), CGWire (2026), SCAD animation standards

This file defines what goes into each component of a professional character sheet — the visual deliverable. It covers the content, structure, and quality standards for every sheet type. It does not cover how to generate images with AI (ai-generation-pipeline.md), how to write prompts (prompt-engineering.md), or the written character bible (character-bible-output.md).

---

## 1. What Is a Character Sheet

A character sheet is the production blueprint that ensures every artist, animator, rigger, or writer working with a character draws them consistently. It is not concept art. It is not a portfolio piece. It is a technical document that answers the question: "What does this character look like from every angle, in every emotional state, at every scale?"

Professional studios treat the character sheet as a contract. Once approved, it governs all downstream production. Inconsistencies in the sheet propagate into every frame, every render, every panel. The sheet must be unambiguous.

A complete character sheet package contains: turnaround, expression sheet, proportion guide, pose sheet, detail callouts, props sheet, color palette documentation, and annotations. The mandatory subset varies by production type (see Section 10).

---

## 2. Turnaround Sheet

The turnaround is the most critical component. It shows the character from multiple angles on a single sheet, aligned on horizontal construction guidelines so proportions are verifiable at a glance.

### View Requirements

**Minimum (3 views):** Front, Side (profile), Back.

**Professional standard (5 views):** Front, 3/4 Front, Side, 3/4 Back, Back.

The 3/4 views are not optional in professional production. They reveal how the character reads in the most common camera angles used in games and animation. A character that looks strong from the front can appear flat or confusing at 3/4 without deliberate design.

### Construction Guidelines

Draw horizontal guidelines across all views before placing any features. These lines must pass through:

- Top of head (crown)
- Brow line
- Eye line
- Base of nose
- Mouth line
- Chin
- Shoulder line
- Chest / bust line
- Waist
- Hip line
- Knee line
- Ankle line
- Ground plane

Every view on the sheet shares these guidelines. If the eye line on the front view sits at a different height than the eye line on the side view, the turnaround is wrong. This is the most common professional error.

### What Each View Reveals

| View | Primary Purpose |
|------|----------------|
| Front | Symmetry, facial feature placement, shoulder width, overall silhouette |
| 3/4 Front | Depth of facial features, nose projection, cheekbone structure, hair volume |
| Side (Profile) | Depth of head, posture, spine curve, nose and chin projection, foot arch |
| 3/4 Back | Hair construction, back of costume, shoulder blade position |
| Back | Costume back detail, hair fall, heel and sole design |

### Common Mistakes

- **Inconsistent head size across views.** The head must be the same height in every view. Measure with the head-as-unit system (Section 4) and verify numerically.
- **Floating features.** Eyes, ears, and nose that shift up or down between views because construction guidelines were not used.
- **Missing back view.** Animators and riggers need the back. Omitting it forces guesswork.
- **Foreshortening in the side view.** The side view is an orthographic projection, not a perspective drawing. Do not tilt the head or body.
- **Costume detail only on the front.** Every costume element must be resolved on all views, including seams, closures, and back panels.

---

## 3. Expression Sheet

The expression sheet documents the character's emotional range. It is the primary reference for animators and illustrators who must convey emotion without losing character consistency.

### Core Set (6 Expressions)

Every character sheet requires these six expressions at minimum:

1. Neutral — resting face, no emotion, the baseline
2. Happy — genuine smile, eyes engaged
3. Sad — downturned mouth, heavy brow, wet or lowered eyes
4. Angry — furrowed brow, compressed lips or bared teeth
5. Surprised — raised brows, wide eyes, open mouth
6. Fearful — raised inner brows, wide eyes, tense jaw

### Extended Set (12 Expressions)

Professional animation and game production adds six more:

7. Disgusted — raised upper lip, wrinkled nose, narrowed eyes
8. Confused — asymmetric brow, slight head tilt implied by expression
9. Determined — set jaw, focused eyes, slight brow compression
10. Smug — half-smile, one raised brow, relaxed confidence
11. Embarrassed — averted gaze, flushed cheeks (color note), compressed smile
12. Laughing — eyes closed or crinkled, open mouth, visible teeth

### Eye and Mouth Breakdowns

For each expression, include a separate close-up row showing:

- **Eyes only:** brow position, eyelid shape, pupil size, any wrinkle lines
- **Mouth only:** lip shape, teeth visibility, corner position, chin tension

These breakdowns allow animators to blend expressions by combining eye and mouth states independently. A character can have happy eyes with a sad mouth (bittersweet). Without the breakdowns, this nuance is lost.

### View Requirements

Each expression must appear in at minimum:

- Front view (primary)
- 3/4 front view (secondary)

The 3/4 view reveals how the expression reads in the most common camera angle. An expression that works in flat front view can collapse or read incorrectly at 3/4.

### Expression Range and Character Personality

The expression sheet encodes personality. A villain's "happy" expression should read differently from a hero's. Document the character-specific rules:

- Which expressions are exaggerated vs. restrained for this character
- Whether the character smiles with teeth or without
- Whether anger reads as cold and controlled or explosive
- Asymmetric tendencies (one brow higher, one corner of mouth lower)

---

## 4. Proportion Guide

The proportion guide establishes the character's measurements using the head as the unit of measurement. This system is universal across studios and production types because it scales with the character — a 7-head character is 7-head whether drawn at thumbnail size or full page.

### Head-as-Unit System

Measure the character's total height in multiples of the head height. Mark each head unit with a horizontal tick on the proportion guide. Annotate the total count.

### Style-to-Head-Count Reference

| Style | Head Count | Examples |
|-------|-----------|---------|
| Realistic | 7 to 8 heads | Live-action game characters, grounded drama |
| Heroic / Idealized | 8 to 9 heads | Superhero comics, action game protagonists |
| Stylized | 5 to 6 heads | Animated series, stylized games |
| Chibi / Super-deformed | 2 to 3 heads | Mobile games, mascots, comedic characters |

These are ranges, not rules. A 6.5-head character is valid. What matters is that the count is documented and consistent across all sheets.

### Key Measurement Annotations

Mark and label these measurements on the proportion guide:

- **Shoulder width:** expressed as a multiple of head width (e.g., "2.5 heads wide")
- **Waist position:** which head unit the waist falls at
- **Hip width:** expressed as a multiple of head width
- **Arm length:** from shoulder to wrist, expressed in head units
- **Hand size:** palm height relative to face height (typically 3/4 of face)
- **Leg length:** from hip to floor, expressed in head units
- **Foot length:** relative to head height

### Proportions as Character Encoding

Proportions communicate character type before the viewer reads a single costume detail:

- Long legs and short torso: speed, elegance, youth
- Wide shoulders and narrow waist: physical power, heroism
- Long arms relative to body: reach, menace, simian quality
- Large hands: labor, strength, clumsiness (comedic)
- Short legs and wide torso: stability, stubbornness, comedic weight
- Elongated neck: aristocracy, fragility, otherworldliness

Document the intentional proportion choices and their rationale in the annotations section (Section 9).

---

## 5. Pose Sheet

The pose sheet shows the character in motion and at rest. It supplements the turnaround's static orthographic views with poses that reveal personality, movement style, and production-specific requirements.

### T-Pose / A-Pose (Rigging Reference)

Required for all game characters. Mandatory for any character that will be rigged and animated in a 3D pipeline.

- **T-Pose:** Arms extended horizontally, palms facing down, legs together. Used for skeletal rigging.
- **A-Pose:** Arms at approximately 45 degrees, palms facing inward. Preferred for shoulder deformation in modern rigs.

The T-pose or A-pose must show the character in their default costume with no expression (neutral face). It is a technical document, not a character moment.

### Idle Pose

The idle pose is the character's personality-revealing neutral stance — how they stand when nothing is happening. This is the pose that appears most frequently in games and animation.

The idle pose must answer: Does this character stand with weight on one hip? Do they cross their arms? Do they slouch or stand at attention? Where do their hands rest?

Document the idle pose from front and 3/4 front views minimum.

### Action Poses (2 to 4 Poses)

Select poses that are specific to this character's role and movement vocabulary:

- A combat character needs an attack pose and a defensive pose
- A magic user needs a casting pose
- A comedic character needs an exaggerated reaction pose
- A stealth character needs a crouched or sneaking pose

Action poses are drawn in perspective and with energy. They are not orthographic. Their purpose is to communicate movement quality, not to serve as measurement references.

### Silhouette Views

For each pose (including the turnaround front view), include a black-filled silhouette version. Fill the entire character outline with solid black — no interior detail.

The silhouette test is the industry standard for readability. A character whose silhouette is ambiguous or interchangeable with other characters fails the test. The silhouette must be immediately recognizable as this specific character.

Annotate which design elements create the distinctive silhouette (hair shape, weapon, costume outline, body proportion).

---

## 6. Detail Callouts

Detail callouts are enlarged, isolated drawings of specific character features that are too small to read clearly on the turnaround. They are not decorative — they resolve ambiguity that would otherwise cause inconsistency across artists.

### Face Details

- **Eye construction:** Iris shape, pupil shape, eyelid thickness, lash style, inner corner detail, any asymmetry
- **Ear shape:** Outer helix, inner structure, lobe style, any jewelry or modification
- **Nose profile:** Bridge width, tip shape, nostril shape from front and 3/4 view
- **Mouth at rest:** Lip thickness ratio (upper to lower), corner shape, philtrum

### Hand Details

- **Finger proportions:** Length ratios between fingers, knuckle prominence
- **Nail style:** Shape (square, rounded, pointed), length, any color or decoration
- **Palm structure:** Thenar eminence size, overall hand shape (wide, narrow, tapered)

### Costume Details

- **Closures:** Buckle design, button style, zipper pull, lacing pattern
- **Patterns:** Repeat unit of any textile pattern, scale relative to body
- **Fabric texture notes:** Written annotation describing material behavior (stiff leather, flowing silk, heavy wool)
- **Seam placement:** Where panels join, topstitching style
- **Wear and damage:** Specific tears, patches, stains — their location and appearance

### Hair Details

- **Section breakdown:** How the hair divides into masses (front section, side sections, back mass)
- **Movement behavior:** Written note on how hair moves — does it move as one mass, in sections, or strand by strand?
- **Hairline shape:** Widow's peak, straight, receding, or irregular
- **Any accessories:** Pins, ties, bands — their exact position and construction

### Footwear Details

- **Sole profile:** Thickness, heel height, toe shape
- **Upper construction:** Panels, lacing, buckles
- **Sole pattern:** Tread design if visible

---

## 7. Props Sheet

The props sheet documents every object the character carries, wears, or uses. Props must be designed with the same rigor as the character — they are part of the visual identity.

### View Requirements

Each prop must appear from a minimum of three angles:

- Front or primary face
- Side profile
- Top or back (whichever reveals the most information)

Complex props (weapons with moving parts, bags with multiple compartments) require additional views to resolve all surfaces.

### Scale Reference

Every prop must appear at least once next to the character's hand at the correct scale. This is non-negotiable. A sword that looks correct in isolation can be wildly wrong in proportion to the character. Show the hand gripping or holding the prop.

### Functional Breakdowns

For props with moving parts, show the range of motion:

- A folding weapon shown open and closed
- A bag shown with flap open and closed
- A mechanical device shown in its operational states

Label the moving parts and indicate the direction of movement with arrows.

### Material and Texture Annotations

Write material notes directly on the prop drawing:

- Metal type (brushed steel, aged bronze, polished gold)
- Leather quality (smooth, tooled, cracked)
- Fabric (canvas, velvet, burlap)
- Wood grain direction
- Any surface treatment (paint, rust, patina, engraving)

These notes guide texture artists and colorists who will not be present when the prop is designed.

---

## 8. Color Palette Documentation

Color documentation is a technical specification, not a mood board. Every color used on the character must be documented with enough precision that any artist can reproduce it exactly.

### Per-Color Documentation Format

For each distinct color in the character's design, document three variants:

| Variant | Purpose |
|---------|---------|
| Base | The color as it appears in flat, neutral lighting |
| Shadow | The color as it appears in shadow (typically 20-30% darker, slightly shifted in hue) |
| Highlight | The color as it appears in direct light (typically 15-20% lighter, slightly desaturated) |

For each variant, provide:

- A filled color swatch (minimum 40x40px in the document)
- HEX code (e.g., `#C4472A`)
- RGB values (e.g., `R:196 G:71 B:42`)

### Usage Notes

Annotate each color with its application:

- Which body regions or costume elements use this color
- Whether the shadow variant is used for ambient occlusion, cast shadows, or both
- Any special cases (this color appears desaturated in flashback sequences)

### Color Grouping

Organize the palette by region, not by hue:

1. Skin tones (base, shadow, highlight, blush, lip)
2. Hair colors (base, shadow, highlight, any secondary tones)
3. Primary costume colors
4. Secondary costume colors
5. Accent colors (buttons, trim, insignia)
6. Eye colors
7. Props and accessories

### The 60-30-10 Verification

After documenting all colors, verify the palette follows the 60-30-10 distribution:

- 60%: Dominant color (typically the primary costume or skin tone mass)
- 30%: Secondary color (supporting costume elements)
- 10%: Accent color (the color that makes the character memorable)

If the distribution is significantly off, note it and explain the intentional deviation.

---

## 9. Annotations and Design Notes

Annotations are written rules that govern how the character is drawn. They capture decisions that cannot be shown visually — behavioral rules, consistency requirements, and design intent.

### What to Annotate

**Hair rules.** Document the specific behavior of the character's hair:
- "The forelock always falls to the LEFT of center, never right."
- "The ponytail always has three visible strands at the tie point."
- "In action poses, the hair separates into two masses, never one."

**Costume rules.** Document non-obvious costume behavior:
- "The collar is always turned up. It is never flat."
- "The left sleeve is always rolled to the elbow. The right is always full length."
- "The coat hem always shows at least 3cm of lining when the character moves."

**Movement personality notes.** Document how the character moves:
- "This character leads with the chest, not the head."
- "Hands are always slightly open, never fully fisted except in combat."
- "Weight shifts to the right hip when standing idle."

**Asymmetry rules.** Document any intentional asymmetry:
- "The right eye is always drawn slightly larger than the left."
- "The scar on the left cheek is always visible in 3/4 view."

### What to Show Visually vs. Annotate

Show visually: anything that has a specific shape, proportion, or color. Annotate: behavioral rules, sequence rules, and intent that cannot be captured in a single drawing.

Do not annotate what is already clear from the drawings. Redundant annotations add noise and reduce the authority of the annotations that matter.

---

## 10. Industry Format Differences

The core package (turnaround, expressions, proportion guide, poses, detail callouts, props, color palette, annotations) is mandatory across all production types. The following table covers additions and variations.

| Component | Games | Animation | Comics |
|-----------|-------|-----------|--------|
| Turnaround (5 views) | Mandatory | Mandatory | Recommended |
| Expression sheet (6 core) | Mandatory | Mandatory | Mandatory |
| Expression sheet (12 extended) | Recommended | Mandatory | Recommended |
| T-pose / A-pose | Mandatory | Recommended | Not required |
| Silhouette views | Mandatory | Mandatory | Mandatory |
| Texture map reference | Mandatory | Not required | Not required |
| Polygon budget annotation | Mandatory | Not required | Not required |
| Hitbox reference | Recommended | Not required | Not required |
| Lip sync chart (8+ phoneme shapes) | Not required | Mandatory | Not required |
| Blink sequence (open / half / closed) | Not required | Mandatory | Not required |
| Hair physics zones | Not required | Mandatory | Not required |
| Height comparison chart | Recommended | Mandatory | Mandatory |
| Costume variants (full turnaround each) | Recommended | Recommended | Mandatory |

**Games — texture map reference:** A UV-unwrapped flat view showing how textures map to the model. Annotate which texture sheet covers which body region and the target polygon count with LOD tiers.

**Animation — lip sync chart:** A grid showing the character's mouth shapes for each phoneme group (A/I, E, O, U, F/V, L/TH, M/B/P, rest). Minimum 8 shapes. Hair physics zones annotate which hair masses simulate independently and their relative stiffness.

**Comics — costume variants:** A full 3-view turnaround for each significant costume change (civilian, battle, disguise). Height comparison shows the character beside at least two other cast members at the same scale.

---

## 11. Complete Deliverable Checklist

**Turnaround:** Front / Side / Back (minimum) — 3/4 Front / 3/4 Back (professional standard) — horizontal construction guidelines aligned across all views.

**Expression Sheet:** 6 core expressions — eye breakdown row — mouth breakdown row — front and 3/4 front per expression — extended 12 (production-dependent).

**Proportion Guide:** Head-as-unit tick marks — total head count annotated — shoulder width, waist position, arm length, hand size, leg length all labeled.

**Pose Sheet:** T-pose or A-pose — idle pose (front and 3/4 front) — 2 to 4 action poses — silhouette views for front turnaround and key action poses.

**Detail Callouts:** Eye construction — ear shape — nose profile — mouth at rest — hand proportions and nail style — costume closures and hardware — fabric texture notes — hair section breakdown — footwear detail.

**Props Sheet:** Each prop from 3+ angles — scale reference with character hand — functional breakdown for moving parts — material and texture annotations.

**Color Palette:** Base / shadow / highlight swatch per color — HEX and RGB per swatch — usage notes — colors organized by region — 60-30-10 distribution verified.

**Annotations:** Hair behavior rules — costume behavior rules — movement personality notes — asymmetry rules.
