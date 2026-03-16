# Character Bible and Output Formats

Sources: Harder (Creative Character Design for Games), Pixune Studios (2026), ScreenCraft, game design document patterns

This file covers the written deliverable formats for character creation: the character bible template, JSON schema, markdown spec, quick card, file organization, medium-specific adaptations, and quality checklist. It does not cover visual design theory (character-sheet-components.md), AI image generation (ai-generation.md), or the discovery interview (discovery-interview.md).

---

## 1. What Is a Character Bible

A character bible is the written companion to the visual character sheet. Where the sheet shows what a character looks like, the bible explains why — and establishes the rules that keep the character consistent across every creator, scene, and medium that touches them.

The bible serves two functions. First, it is a design document: it records the decisions made during character creation so those decisions can be defended, referenced, and handed off. Second, it is a consistency contract: it tells other writers, artists, animators, and game designers exactly what this character is and is not allowed to do.

A complete character deliverable always includes both the visual sheet and the written bible. Neither is sufficient alone.

---

## 2. The 10-Section Character Bible Template

### Section 1: Identity Snapshot

The one-page summary. Fill this in last — it distills everything below.

```
Name: [CHARACTER NAME]
Age: [AGE or AGE RANGE]
Species / Race: [HUMAN / ELF / ANDROID / etc.]
Gender: [GENDER IDENTITY]
Role: [PROTAGONIST / ANTAGONIST / MENTOR / ALLY / NPC / etc.]
Archetype: [HERO / SAGE / TRICKSTER / SHADOW / INNOCENT / CAREGIVER / EXPLORER / RULER / CREATOR / LOVER / JESTER / EVERYMAN]
One-Line Essence: [The single sentence that captures who this character is at their core — their defining quality and contradiction in one breath.]
```

### Section 2: Physical Description

```
Height: [HEIGHT in cm or ft/in]
Weight / Build: [WEIGHT and BUILD — lean, stocky, wiry, imposing, slight, etc.]
Distinguishing Features: [SCARS, MARKINGS, UNUSUAL EYES, PROSTHETICS, HAIR, etc. — the details that make them recognizable in silhouette]
Skin / Complexion: [DESCRIPTION]
Hair: [COLOR, TEXTURE, STYLE, and whether it changes under stress or circumstance]
Eyes: [COLOR and what they communicate — cold, warm, calculating, open, etc.]
Voice: [PITCH, TEXTURE, ACCENT, PACE — e.g., "low and measured, slight northern accent, never raises above conversational volume"]
Mannerisms: [3-5 specific physical habits — how they stand, what they do with their hands, eye contact patterns, nervous tells]
How They Carry Themselves: [The overall physical impression — do they take up space or minimize it? Do they move with purpose or drift?]
```

### Section 3: Backstory

Focus on the wound and the turning point — these two elements drive all behavior. Everything else is context.

```
Origin: [WHERE and WHAT they came from — place, family, social class, formative environment]
The Wound: [The defining injury — emotional, physical, or social — that shaped their psychology. This is not backstory decoration; it is the engine of their behavior.]
Turning Point: [The moment that set them on their current path. What happened, and what did they decide about the world as a result?]
Secrets: [What they hide from others / [WHAT THEY HIDE FROM THEMSELVES]]
Key Relationships from the Past: [2-3 people from their history who still influence their behavior — mentor, betrayer, lost love, rival, etc.]
```

### Section 4: Psychology

```
Core Motivation: [What they are actively pursuing — the conscious goal driving their actions]
Core Need: [What they actually require to be whole — often different from what they want, and often what the story is really about]
Greatest Fear: [The specific thing they will go to great lengths to avoid — not a generic fear but the precise version that belongs to this character]
Fatal Flaw: [The character trait that creates their problems and must be confronted for growth to occur]
Moral Code: [What they will and will not do, and why — the lines they draw and the reasoning behind them]
Contradictions: [The intentional tensions in their psychology — e.g., "deeply loyal but incapable of asking for help"; "believes in justice but enjoys cruelty toward enemies"]
```

### Section 5: Personality Traits

```
Positive Traits (3-5):
- [TRAIT]: [One sentence on how this manifests in behavior]
- [TRAIT]: [One sentence on how this manifests in behavior]
- [TRAIT]: [One sentence on how this manifests in behavior]

Flaws (2-3):
- [FLAW]: [One sentence on how this creates problems]
- [FLAW]: [One sentence on how this creates problems]

Under Stress: [How they behave when threatened, cornered, or overwhelmed — specific behaviors, not adjectives]
At Ease: [How they behave when safe and comfortable — this is often the version of themselves they protect]
Humor: [Do they have it? What kind? Dry, self-deprecating, dark, absurdist, none? How do they use it?]
Communication Style: [Direct or indirect? Verbose or terse? Do they ask questions or make statements? How do they handle disagreement?]
```

### Section 6: Relationships and Dynamics

```
To the Protagonist: [RELATIONSHIP TYPE and the specific tension or bond that defines it]
To the Antagonist: [RELATIONSHIP TYPE and what they represent to each other]
Allies: [KEY ALLY NAME — what they provide each other, what the friction is]
How They Treat People of Higher Status: [Deferential, challenging, performative, indifferent?]
How They Treat People of Lower Status: [This is often the most revealing behavioral tell — kind, dismissive, transactional, protective?]
How They Treat Strangers: [Default social posture toward people they do not know]
```

### Section 7: Visual Design Rationale

Every design choice must trace to archetype, psychology, or backstory. If a choice cannot be explained here, reconsider it.

```
Primary Color Choice: [COLOR(S)] — [Why these colors? What do they communicate about this character's archetype and emotional state? Reference the 60-30-10 split.]
Shape Language: [DOMINANT SHAPES — circles, squares, triangles, or combinations] — [What does this communicate? How does it reflect their role and personality?]
Costume Rationale: [Why do they dress this way? What does it say about their self-image, their social role, their history?]
Silhouette: [What makes them recognizable at thumbnail size? What is the distinctive shape?]
Color Arc: [If the character changes across the story, how does their palette shift? Desaturation for corruption, brightening for growth, etc.]
Design Contradictions: [Any visual elements that intentionally contradict the dominant read — e.g., a villain with warm colors, a hero with angular features — and why]
```

### Section 8: Voice and Dialogue Guide

```
Sample Dialogue Lines (3-5):
1. "[LINE]" — [Context: when and why they would say this]
2. "[LINE]" — [Context]
3. "[LINE]" — [Context]
4. "[LINE]" — [Context]
5. "[LINE]" — [Context]

Frequent Phrases or Constructions: [Specific words, sentence structures, or rhetorical habits — e.g., "always frames requests as questions", "never uses contractions", "refers to abstract concepts as physical objects"]
Forbidden Phrases: [Words or constructions this character would never use — these are as defining as what they do say]
Speech Patterns: [Pace, interruption habits, how they handle silence, whether they finish other people's sentences, how they signal emotion through speech rather than stating it]
```

### Section 9: Story Function

```
Narrative Role: [What structural function does this character serve in the story? Catalyst, mirror, obstacle, mentor, comic relief, thematic embodiment?]
Arc: [Where do they start? Where do they end? What is the specific change — or the specific refusal to change — that defines their journey?]
Key Scenes: [3-5 scenes this character must appear in for the story to work — the moments that define them]
How They Change: [The specific belief, behavior, or relationship that shifts across the story — or, for static characters, what they represent that does not change and why that matters]
Thematic Function: [What idea or question does this character embody or interrogate?]
```

### Section 10: Do's and Don'ts

Write specific, actionable rules — not generic character advice. "Do not make them cruel without reason" is useless. "Do not have them apologize; they acknowledge mistakes by changing behavior, never by verbal apology" is a consistency contract.

```
DO:
- [SPECIFIC RULE about behavior, speech, or visual representation]
- [SPECIFIC RULE]
- [SPECIFIC RULE]
- [SPECIFIC RULE]
- [SPECIFIC RULE]

DO NOT:
- [SPECIFIC RULE — what this character never does, says, or wears]
- [SPECIFIC RULE]
- [SPECIFIC RULE]
- [SPECIFIC RULE]
- [SPECIFIC RULE]
```

---

## 3. Character Bible JSON Schema

The machine-readable format. Store as `character-bible.json` alongside the markdown bible. Downstream tools — game engines, asset pipelines, localization systems — can parse this directly.

```json
{
  "character": {
    "name": "[CHARACTER NAME]",
    "age": "[AGE or AGE RANGE]",
    "species": "[SPECIES]",
    "gender": "[GENDER]",
    "role": "[PROTAGONIST | ANTAGONIST | MENTOR | ALLY | NPC | VILLAIN | ANTIHERO]",
    "archetype": "[HERO | SAGE | TRICKSTER | SHADOW | INNOCENT | CAREGIVER | EXPLORER | RULER | CREATOR | LOVER | JESTER | EVERYMAN]",
    "essence": "[ONE-LINE ESSENCE]"
  },
  "physical": {
    "height_cm": 0,
    "build": "[LEAN | STOCKY | WIRY | IMPOSING | SLIGHT | ATHLETIC | AVERAGE]",
    "distinguishing_features": ["[FEATURE]", "[FEATURE]"],
    "voice": "[VOICE DESCRIPTION]",
    "mannerisms": ["[MANNERISM]", "[MANNERISM]", "[MANNERISM]"]
  },
  "backstory": {
    "origin": "[ORIGIN]",
    "wound": "[THE WOUND]",
    "turning_point": "[TURNING POINT]",
    "secrets": ["[SECRET]", "[SECRET]"],
    "key_past_relationships": [
      { "name": "[NAME]", "role": "[ROLE]", "influence": "[HOW THEY STILL AFFECT THIS CHARACTER]" }
    ]
  },
  "psychology": {
    "core_motivation": "[MOTIVATION]",
    "core_need": "[NEED]",
    "greatest_fear": "[FEAR]",
    "fatal_flaw": "[FLAW]",
    "moral_code": "[MORAL CODE]",
    "contradictions": ["[CONTRADICTION]", "[CONTRADICTION]"]
  },
  "personality": {
    "positive_traits": ["[TRAIT]", "[TRAIT]", "[TRAIT]"],
    "flaws": ["[FLAW]", "[FLAW]"],
    "under_stress": "[STRESS BEHAVIOR]",
    "at_ease": "[EASE BEHAVIOR]",
    "humor": "[HUMOR TYPE or NONE]",
    "communication_style": "[COMMUNICATION STYLE]"
  },
  "relationships": {
    "to_protagonist": "[RELATIONSHIP]",
    "to_antagonist": "[RELATIONSHIP]",
    "allies": [
      { "name": "[ALLY NAME]", "dynamic": "[DYNAMIC]" }
    ],
    "treats_higher_status": "[BEHAVIOR]",
    "treats_lower_status": "[BEHAVIOR]",
    "treats_strangers": "[BEHAVIOR]"
  },
  "visual_design": {
    "palette": {
      "dominant": { "hex": "#000000", "role": "dominant", "rationale": "[WHY]" },
      "secondary": { "hex": "#000000", "role": "secondary", "rationale": "[WHY]" },
      "accent": { "hex": "#000000", "role": "accent", "rationale": "[WHY]" },
      "shadow_dominant": "#000000",
      "highlight_dominant": "#000000"
    },
    "shape_language": "[CIRCLES | SQUARES | TRIANGLES | CIRCLE_TRIANGLE | SQUARE_CIRCLE | TRIANGLE_SQUARE]",
    "silhouette_notes": "[WHAT MAKES THEM RECOGNIZABLE AT THUMBNAIL]",
    "costume_rationale": "[WHY THEY DRESS THIS WAY]",
    "color_arc": "[HOW PALETTE SHIFTS ACROSS STORY, if applicable]"
  },
  "voice": {
    "sample_lines": [
      { "line": "[LINE]", "context": "[CONTEXT]" },
      { "line": "[LINE]", "context": "[CONTEXT]" },
      { "line": "[LINE]", "context": "[CONTEXT]" }
    ],
    "frequent_phrases": ["[PHRASE OR CONSTRUCTION]"],
    "forbidden_phrases": ["[PHRASE OR CONSTRUCTION]"],
    "speech_patterns": "[SPEECH PATTERN DESCRIPTION]"
  },
  "story_function": {
    "narrative_role": "[STRUCTURAL FUNCTION]",
    "arc": "[START STATE] → [END STATE]",
    "key_scenes": ["[SCENE]", "[SCENE]", "[SCENE]"],
    "thematic_function": "[THEME OR QUESTION EMBODIED]"
  },
  "consistency_rules": {
    "do": ["[RULE]", "[RULE]", "[RULE]"],
    "do_not": ["[RULE]", "[RULE]", "[RULE]"]
  }
}
```

---

## 4. Markdown Character Spec Template

The human-readable deliverable for client handoff, repository storage, and team reference. Structure the document with these top-level sections in order:

```markdown
# [CHARACTER NAME] — Character Bible
**Role:** [ROLE] | **Archetype:** [ARCHETYPE] | **Version:** 1.0
> [ONE-LINE ESSENCE]

## Identity
| Name | Age | Species | Gender | Role | Archetype |
|------|-----|---------|--------|------|-----------|
| [NAME] | [AGE] | [SPECIES] | [GENDER] | [ROLE] | [ARCHETYPE] |

## Physical Description
[HEIGHT], [BUILD]. [DISTINGUISHING FEATURES]. [VOICE DESCRIPTION].
**Mannerisms:** [MANNERISM 1]; [MANNERISM 2]; [MANNERISM 3].

## Character Sheet
![Turnaround](sheets/turnaround.png)
![Expressions](sheets/expressions.png)

## Backstory
**Origin:** [ORIGIN] | **The Wound:** [THE WOUND]
**Turning Point:** [TURNING POINT]
**Secrets:** [SECRET 1]; [SECRET 2]

## Psychology
| Core Motivation | Core Need | Greatest Fear | Fatal Flaw | Moral Code |
|-----------------|-----------|---------------|------------|------------|
| [MOTIVATION] | [NEED] | [FEAR] | [FLAW] | [MORAL CODE] |
**Contradictions:** [CONTRADICTION 1]; [CONTRADICTION 2]

## Personality
**Strengths:** [TRAIT 1], [TRAIT 2], [TRAIT 3] | **Flaws:** [FLAW 1], [FLAW 2]
**Under stress:** [STRESS BEHAVIOR] | **At ease:** [EASE BEHAVIOR]

## Visual Design Rationale
| Role | Hex | Rationale |
|------|-----|-----------|
| Dominant | `[HEX]` | [WHY] |
| Secondary | `[HEX]` | [WHY] |
| Accent | `[HEX]` | [WHY] |
**Shape language:** [SHAPES] — [RATIONALE]
**Costume:** [COSTUME RATIONALE]

## Voice and Dialogue
- "[LINE 1]" — [context]
- "[LINE 2]" — [context]
- "[LINE 3]" — [context]
**Speech patterns:** [PATTERNS] | **Never says:** [FORBIDDEN PHRASES]

## Story Function
**Arc:** [START] → [END]
**Key scenes:** [SCENE 1]; [SCENE 2]; [SCENE 3]
**Thematic function:** [THEME]

## Do's and Don'ts
**Do:** [RULE]; [RULE]; [RULE]
**Do not:** [RULE]; [RULE]; [RULE]
```

---

## 5. Quick Character Card

For NPCs and minor characters who do not warrant a full bible. One page. Complete in under 15 minutes.

```
CHARACTER CARD: [NAME]

Role: [ROLE IN STORY]
Essence: [ONE SENTENCE — who they are and what they want]

Traits:
- [TRAIT]
- [TRAIT]
- [TRAIT]

Visual Summary: [2-3 sentences — build, colors, one distinguishing feature, how they carry themselves]

Sample Line: "[ONE LINE OF DIALOGUE that captures their voice]"

Do Not: [ONE RULE — the single most important consistency constraint]
```

**When to use full bible vs quick card:**

| Character Type | Format |
|----------------|--------|
| Protagonist | Full bible, all 10 sections |
| Antagonist | Full bible, all 10 sections |
| Mentor or foil | Full bible, sections 1-7 minimum |
| Named recurring NPC | Quick card + sections 1, 4, 8, 10 |
| One-scene NPC | Quick card only |
| Background character | Name and visual summary only |

---

## 6. Output File Organization

Deliver each character as a self-contained folder. This structure supports version control, asset pipeline integration, and handoff to other teams.

```
[character-name]/
├── character-bible.md          # Human-readable full bible
├── character-bible.json        # Machine-readable schema
├── sheets/
│   ├── turnaround.png          # Front, 3/4, side, back, 3/4 back
│   ├── expressions.png         # 6+ core expressions
│   ├── poses.png               # T-pose + idle + 2-4 action poses
│   └── details.png             # Face callout, hands, costume details, props
└── palette.json                # Color data only, for pipeline use
```

`palette.json` contains the structured color data extracted from the full JSON schema — useful for tools that need color data without loading the entire character record:

```json
{
  "character": "[CHARACTER NAME]",
  "dominant": { "base": "#000000", "shadow": "#000000", "highlight": "#000000" },
  "secondary": { "base": "#000000", "shadow": "#000000", "highlight": "#000000" },
  "accent": { "base": "#000000", "shadow": "#000000", "highlight": "#000000" }
}
```

---

## 7. Adaptation by Medium

The core 10-section bible applies to all media. Add these medium-specific fields to the JSON schema and markdown document as an 11th section.

**Games**

```
Gameplay Role: [TANK | SUPPORT | DPS | STEALTH | UTILITY | etc.]
Ability Set Summary: [2-3 sentences on what they can do mechanically and why it fits their personality]
Player Fantasy Statement: [The one-sentence answer to "what does it feel like to play as this character?"]
Idle Animations: [2-3 personality-revealing idle behaviors]
```

**Animation**

```
Voice Casting Notes: [Age range, vocal quality, reference performances — not specific actors, but qualities]
Animation Personality Notes: [How do they move? Snappy, fluid, heavy, bouncy? What does their walk cycle communicate?]
Lip Sync Complexity: [SIMPLE | STANDARD | COMPLEX — guides rigging scope]
```

**Comics**

```
Costume Variants: [Civilian outfit, alternate costume, damaged/battle-worn version]
Civilian Outfit: [Description — what do they wear when not in their primary costume?]
Panel Presence: [How do they fill a panel? Do they dominate the frame or recede? What is their default pose?]
```

**TTRPG**

```
Stats Hooks: [Which ability scores or skills are high and low, and why — trace to personality]
Class / Race Suggestions: [2-3 system-agnostic suggestions with rationale]
Roleplaying Notes: [What a player needs to know to portray this character authentically at the table]
```

---

## 8. Quality Checklist for Character Bible

Run this checklist before delivering any character bible. A bible that fails more than two items is not ready for handoff.

**Completeness**
- All 10 sections are filled in with specific content, not placeholder text
- The identity snapshot was written last and accurately reflects the full bible
- The JSON schema validates without errors and all required fields are populated

**Internal Consistency**
- The visual design rationale traces every major design choice back to archetype, psychology, or backstory
- The fatal flaw appears in the personality section, the backstory wound, and the story arc — it is the same flaw, not three different ones
- The do's and don'ts are specific to this character and could not apply to a generic character of the same archetype

**Voice Distinctiveness**
- The sample dialogue lines could not be spoken by any other character in the same project
- The forbidden phrases list contains at least two entries that are specific to this character's psychology, not just generic tone guidance
- The speech patterns section describes observable behaviors, not adjectives

**Narrative Integrity**
- The core motivation and core need are different from each other
- The contradictions in the psychology section are documented as intentional, not accidental
- The story arc specifies a concrete change in belief, behavior, or relationship — not a vague "they grow"

**Visual-Written Alignment**
- The character sheet images and the physical description section describe the same character
- The color palette in the JSON schema matches the colors visible in the character sheets
- The shape language noted in the visual design rationale is visible in the turnaround sheet
