# Organization Strategies

Sources: yafyx/tidyf presets, bhrigu123/classifier, d6o/Gorganizer, productivity methodology research

Covers: organization strategy selection, preset configurations, date-based grouping,
project detection, existing folder awareness, and custom profile creation.

## Strategy Selection

Pick one strategy based on the user's situation. When uncertain, ask.

| Signal | Strategy | Why |
|--------|----------|-----|
| "Organize my Downloads" | downloads | Aggressive cleanup, flag old/temp files |
| "Sort by type" | by-type | Simple extension-based categories |
| "Sort by date" | by-date | Chronological grouping (photos, backups) |
| "Group by project" | by-project | Detect project boundaries from filenames |
| Developer's home folder | developer | Separate code, configs, media, docs |
| "Keep my existing structure" | merge | Respect existing folders, only file loose files |
| No clear signal | by-type | Safe default that works for everyone |

## Strategy: by-type (Default)

Flat category folders at the target level. Simplest and most predictable.

### Structure

```
Target/
├── Images/
├── Videos/
├── Audio/
├── Documents/
├── Spreadsheets/
├── Archives/
├── Code/
├── Applications/
└── Other/
```

### Rules

1. Map each file's extension to a category (see `references/file-categories.md`)
2. Create category folder only if files exist for it (no empty folders)
3. Move files into their category folder
4. Preserve original filename
5. Handle conflicts with numeric suffix: `report.pdf` → `report (1).pdf`

### When to recommend

- Mixed file types in a single folder
- User hasn't expressed a preference
- Folder contains <500 files (larger folders benefit from subcategories)

## Strategy: by-date

Chronological organization using file modification time. Best for photo libraries,
backup dumps, and download folders.

### Structure

```
Target/
├── 2024/
│   ├── 01-January/
│   ├── 02-February/
│   └── ...
├── 2025/
│   ├── 01-January/
│   └── ...
└── Undated/
```

### Rules

1. Read file modification time (`stat -f "%Sm" -t "%Y-%m" file` on macOS,
   `stat -c "%y" file` on Linux)
2. Create `YYYY/MM-MonthName/` structure
3. For photos with EXIF data, prefer EXIF date over filesystem date
   (`exiftool -DateTimeOriginal file` if available)
4. Files with suspiciously old dates (before 2000) go to `Undated/`
5. Optionally combine with type: `2024/01-January/Images/`, `2024/01-January/Documents/`

### When to recommend

- Photo libraries, camera dumps
- User says "sort by date" or "chronological"
- Folder dominated by one file type (all images → date is the useful dimension)

## Strategy: by-project

Group files that belong together based on shared name prefixes, keywords, or
co-occurrence patterns.

### Structure

```
Target/
├── ProjectAlpha/
│   ├── ProjectAlpha-proposal.pdf
│   ├── ProjectAlpha-budget.xlsx
│   └── ProjectAlpha-logo.png
├── TaxReturn2024/
│   ├── W2-2024.pdf
│   ├── tax-return-draft.pdf
│   └── receipts-2024.zip
└── Unsorted/
```

### Detection Heuristics

| Signal | Example | Action |
|--------|---------|--------|
| Shared prefix | `client-acme-*.pdf` | Group under `Client-Acme/` |
| Date cluster | 5 files modified same day | Suggest grouping if related names |
| Keyword match | `invoice`, `receipt`, `contract` | Group under `Financial/` |
| Numbered sequence | `photo-001.jpg` through `photo-050.jpg` | Keep together |

### Rules

1. Extract common prefixes from filenames (split on `-`, `_`, spaces, camelCase)
2. Group files sharing a prefix of 3+ characters with 2+ files
3. Present detected groups to user for confirmation
4. Unmatched files go to `Unsorted/` or fall back to by-type strategy
5. Ask user to name ambiguous groups

### When to recommend

- Work documents with project naming conventions
- Freelancer files organized by client
- User mentions "projects" or "group related files"

## Strategy: developer

Optimized for developer home directories or project dump folders.

### Structure

```
Target/
├── Code/
│   ├── TypeScript/
│   ├── Python/
│   └── Shell/
├── Config/
├── Documents/
├── Design/
├── Data/
├── Archives/
└── Media/
    ├── Images/
    ├── Videos/
    └── Audio/
```

### Rules

1. Code files grouped by language family (see language table below)
2. Config files (json, yaml, toml, env, rc files) separate from code
3. Design files (psd, ai, sketch, fig) in Design/
4. Media collapsed into single Media/ with type subfolders
5. READMEs and docs stay with their project if detectable

### Language Family Grouping

| Family | Extensions |
|--------|-----------|
| TypeScript | ts, tsx, js, jsx, mjs, cjs |
| Python | py, pyw, pyi |
| Go | go |
| Rust | rs |
| Java/Kotlin | java, kt, kts, scala, groovy |
| C/C++ | c, cpp, cc, h, hpp |
| Ruby | rb |
| Shell | sh, bash, zsh, fish |
| Web | html, css, scss, vue, svelte |
| Systems | zig, nim, v |

### When to recommend

- User is a developer (code files present)
- Mix of source code, configs, and media
- Home directory or dev workspace cleanup

## Strategy: downloads

Aggressive organization for Downloads folders with cleanup suggestions.

### Structure

```
Target/
├── Documents/
├── Images/
├── Media/
│   ├── Videos/
│   └── Audio/
├── Archives/
├── Applications/
├── Code/
├── _Review/          ← files needing user decision
│   ├── Old/          ← files >30 days
│   └── Duplicates/   ← detected duplicates
└── _Trash/           ← suggested for deletion (temp/partial files)
```

### Rules

1. Apply by-type categorization first
2. Flag incomplete downloads (`.part`, `.crdownload`) → `_Trash/`
3. Flag duplicate patterns (`file (1).pdf`) → `_Review/Duplicates/`
4. Flag files older than 30 days → `_Review/Old/`
5. Installers already installed → suggest deletion in `_Review/`
6. Present `_Review/` and `_Trash/` contents to user before any deletion

### When to recommend

- User explicitly mentions "Downloads folder"
- Target folder is `~/Downloads` or similar
- Folder contains temp files, duplicates, or old downloads

## Strategy: merge

Preserve existing folder structure. Only organize loose (unfiled) files.

### Rules

1. Scan existing subfolders (up to 3 levels deep, max 100 folders)
2. Present existing structure to user
3. Only move files that are NOT already in a subfolder
4. Suggest existing subfolders as destinations when extension/name matches
5. For files matching no existing folder, offer to create new categories
6. Never reorganize files already in subfolders unless user requests it

### When to recommend

- User says "keep my existing structure" or "don't touch my folders"
- Target folder has a mix of organized subfolders and loose files
- User wants incremental cleanup, not a full reorganization

## Existing Folder Detection

Before proposing any organization plan, scan for existing structure.
This prevents creating duplicate category folders when the user already has
`Photos/` alongside your proposed `Images/`.

### Scan Procedure

```bash
# List existing subfolders (macOS/Linux), max 3 levels, max 100 dirs
find "$TARGET" -maxdepth 3 -type d | head -100 | sort
```

### Matching Rules

| Existing folder | Maps to category | Action |
|----------------|------------------|--------|
| Photos, Pictures | Images | Use existing name |
| Music, Songs | Audio | Use existing name |
| Movies, Films | Videos | Use existing name |
| Docs, Papers | Documents | Use existing name |
| Projects, Work | (project name) | Use existing name |
| Any exact category name | That category | Use existing name |

When an existing folder matches a proposed category, use the existing folder
name rather than creating a new one. Present the mapping to the user:

```
Found existing folders. Proposed mapping:
  Photos/ → will receive image files (instead of creating Images/)
  Docs/   → will receive document files (instead of creating Documents/)
  New:    → Archives/ (no existing match)
  
Proceed? [y/n/edit]
```

## Custom Profiles

For repeat use, save the user's preferences:

```json
{
  "strategy": "by-type",
  "categories": {
    "Work": ["doc", "docx", "pdf", "xlsx", "pptx"],
    "Personal Photos": ["jpg", "jpeg", "png", "heic"],
    "Receipts": ["pdf"]
  },
  "rules": {
    "receipts_pattern": "receipt|invoice|payment",
    "archive_after_days": 60
  }
}
```

Save to `~/.folder-organizer/profiles/` for reuse. Ask the user if they
want to save their choices as a named profile.
