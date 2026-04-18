---
name: "@tank/folder-organizer"
description: |
  Scan any directory, categorize files by type/date/project, propose an
  organization plan, get user confirmation on decisions, then move files
  into clean folder structures. Supports messy Downloads folders, Desktops,
  unsorted dumps, and developer workspaces. Handles conflict resolution,
  duplicate detection, undo logging, and existing folder awareness.
  Synthesizes patterns from classifier, Gorganizer, tidyf, and file
  management best practices.

  Trigger phrases: "organize my folder", "clean up my downloads",
  "sort my files", "organize my desktop", "folder organizer",
  "tidy up my files", "sort files by type", "sort files by date",
  "organize directory", "file organizer", "clean up folder",
  "move files into folders", "categorize my files", "declutter",
  "messy folder", "organize my documents", "sort this directory"
---

# Folder Organizer

## Core Philosophy

1. **Never move without confirmation** — Present the full plan, get explicit
   approval. One wrong move can lose hours of search time.
2. **Respect existing structure** — Scan for existing subfolders before
   proposing new ones. Use the user's folder names, not yours.
3. **Extension is the fast path, AI is the slow path** — 90% of files
   categorize instantly by extension. Use judgment only for ambiguous cases
   like `data.json` vs `package.json`.
4. **Always log for undo** — Write every move to an undo log before
   executing. The user must be able to reverse any organization.
5. **Suggest, never auto-delete** — Flag cleanup candidates (temp files,
   duplicates, old downloads) but let the user decide.

## Quick-Start: Common Problems

### "Organize my Downloads folder"

1. Scan `~/Downloads` for all files (non-recursive)
2. Detect existing subfolders to avoid conflicts
3. Filter out system files (.DS_Store, Thumbs.db)
4. Flag cleanup candidates (incomplete downloads, duplicates, old files)
5. Categorize remaining files by extension
   -> See `references/file-categories.md`
6. Select the `downloads` strategy (aggressive cleanup mode)
   -> See `references/organization-strategies.md`
7. Present plan with categories, file counts, and cleanup candidates
8. Get user confirmation (approve / edit / cancel)
9. Execute moves with undo log
   -> See `references/workflow-guide.md`

### "Sort these files by date"

1. Scan target directory
2. Collect modification dates for all files
3. Apply `by-date` strategy: `YYYY/MM-MonthName/` structure
4. For photos, prefer EXIF date over filesystem date if available
5. Present plan, confirm, execute
   -> See `references/organization-strategies.md`

### "Group files by project"

1. Scan target directory
2. Detect shared prefixes in filenames (split on `-`, `_`, spaces)
3. Group files with common prefixes (3+ chars, 2+ files)
4. Present detected groups, ask user to name ambiguous ones
5. Unmatched files fall back to by-type categorization
   -> See `references/organization-strategies.md`

### "Undo the last organization"

1. Find latest undo log in `~/.folder-organizer/undo/`
2. Show what will be reversed (file count, original locations)
3. Confirm with user
4. Move files back to original locations
5. Remove empty category folders
   -> See `references/workflow-guide.md`

## The Five-Phase Workflow

Every organization follows this sequence. Never skip Phase 4 (Confirm).

| Phase | Action | Key output |
|-------|--------|------------|
| 1. Scan | Collect file metadata from target | File list with names, sizes, dates |
| 2. Analyze | Categorize, detect patterns, flag issues | Category assignments, cleanup candidates |
| 3. Propose | Present organization plan | Formatted plan with counts per category |
| 4. Confirm | Get user approval with edit options | Approved plan (possibly modified) |
| 5. Execute | Move files, log operations | Moved files + undo log path |

-> See `references/workflow-guide.md` for detailed procedures.

## Decision Trees

### Strategy Selection

| Signal | Strategy |
|--------|----------|
| User says "by type" or no preference | `by-type` — flat category folders |
| User says "by date" or folder is mostly photos | `by-date` — YYYY/MM/ structure |
| User says "by project" or files share name prefixes | `by-project` — group by detected projects |
| Target is ~/Downloads | `downloads` — aggressive with cleanup |
| User says "keep my structure" | `merge` — only file loose files |
| Lots of code files detected | `developer` — language-aware grouping |

### Conflict Resolution

| Situation | Default action |
|-----------|---------------|
| Same filename exists at destination | Add numeric suffix: `file (1).pdf` |
| User says "don't overwrite" | Skip the file |
| User says "overwrite" | Replace (per-file confirmation) |
| Filename too long for filesystem | Truncate name, preserve extension |

### File Ambiguity

| Extension | If filename matches... | Category |
|-----------|----------------------|----------|
| .md | README, CHANGELOG, CONTRIBUTING | Code |
| .md | Everything else | Documents |
| .json | package.json, tsconfig.json, etc. | Code |
| .json | export.json, backup.json, etc. | Data |
| .csv | Near code files (package.json nearby) | Code |
| .csv | Standalone | Spreadsheets |

When uncertain, ask the user rather than guessing.

## Safety Rules

- Write undo log BEFORE starting any moves
- Never auto-delete files — only suggest cleanup
- Verify source files still exist before each move
- Check disk space before cross-volume moves
- Report skipped files with reasons after completion
- Show undo log path in completion message

## Reference Index

| File | Contents |
|------|----------|
| `references/file-categories.md` | Extension-to-category mapping, MIME fallbacks, ambiguous files, ignore lists |
| `references/organization-strategies.md` | Strategy selection, presets (by-type, by-date, by-project, developer, downloads, merge) |
| `references/workflow-guide.md` | Five-phase workflow details, conflict resolution, undo support, batch processing |
