# Workflow Guide

Sources: yafyx/tidyf architecture, bhrigu123/classifier patterns, file management best practices

Covers: the full scan-analyze-propose-confirm-execute workflow, safety mechanisms,
conflict resolution, undo support, and batch processing.

## Workflow Overview

Every folder organization follows five phases. Never skip the confirm phase —
moving files without user approval risks data loss.

```
1. SCAN    → Collect file metadata from target directory
2. ANALYZE → Categorize files, detect patterns, flag issues
3. PROPOSE → Present organization plan to user
4. CONFIRM → Get user approval (with edit options)
5. EXECUTE → Move files, log every operation for undo
```

## Phase 1: Scan

### Input

User provides a target directory. Validate it exists and is readable.

```bash
# Validate target
if [ ! -d "$TARGET" ]; then
  echo "Error: '$TARGET' is not a directory"
  exit 1
fi
```

### Collect File Metadata

List all files (not directories) in the target. Do not recurse into
subdirectories unless the user explicitly requests it.

```bash
# List files with metadata (macOS)
find "$TARGET" -maxdepth 1 -type f -exec stat -f "%N|%z|%Sm" -t "%Y-%m-%d" {} \;

# List files with metadata (Linux)
find "$TARGET" -maxdepth 1 -type f -printf "%p|%s|%TY-%Tm-%Td\n"
```

### Metadata to Collect Per File

| Field | Source | Purpose |
|-------|--------|---------|
| Name | Filename | Category detection, project grouping |
| Extension | Filename suffix | Primary category signal |
| Size | `stat` | Reporting, large file flagging |
| Modified date | `stat` | Date-based sorting, staleness detection |
| MIME type | `file --mime-type -b` | Fallback for missing/wrong extension |

### Performance Considerations

| File count | Approach |
|-----------|----------|
| <100 | Collect all metadata, process in one batch |
| 100-500 | Collect all metadata, present summary first |
| 500-2000 | Sample 50 files for strategy detection, then batch |
| >2000 | Warn user about volume, suggest subdirectory-at-a-time |

### Scan Existing Structure

Before categorizing files, detect existing subfolders to avoid conflicts
and respect the user's current organization:

```bash
find "$TARGET" -maxdepth 3 -mindepth 1 -type d | sort
```

Record existing folder names for the matching logic in
`references/organization-strategies.md`.

## Phase 2: Analyze

### Step 1: Filter Ignorable Files

Remove files matching the ignore list (see `references/file-categories.md`).
Report ignored files count but do not include in the plan.

### Step 2: Detect Temporary/Cleanup Candidates

Flag files that the user probably wants to delete rather than organize:

| Pattern | Signal |
|---------|--------|
| `.part`, `.crdownload`, `.partial` | Incomplete download |
| `.tmp`, `.temp`, `*~` | Temporary file |
| `filename (1).ext`, `filename (2).ext` | Likely duplicate |
| Modified >90 days ago in Downloads | Probably forgotten |

Present these separately as "cleanup candidates" before the organization plan.

### Step 3: Categorize Files

For each remaining file:

1. Extract extension (lowercase, strip leading dot)
2. Look up in extension-to-category mapping (`references/file-categories.md`)
3. If extension is ambiguous, apply disambiguation heuristics
4. If extension is unknown, use MIME type fallback
5. If still unknown, categorize as "Other"

### Step 4: Detect Patterns

Look for grouping opportunities beyond simple extension matching:

| Pattern | Detection | Action |
|---------|-----------|--------|
| Shared prefix | 3+ files with same prefix before `-`, `_`, or space | Suggest project subfolder |
| Date cluster | 5+ files modified same day | Suggest date subfolder |
| Numbered sequence | `name-001`, `name-002`, ... | Keep together |
| Related pairs | `file.psd` + `file.png` | Keep together |

### Step 5: Select Strategy

If user specified a strategy, use it. Otherwise, auto-detect:

| Dominant content | Auto-strategy |
|-----------------|---------------|
| >70% images | by-date (photos likely) |
| >50% code files | developer |
| Target is ~/Downloads | downloads |
| Mix of types | by-type (default) |
| Existing subfolders present | merge |

Present the auto-detected strategy to user for confirmation.

## Phase 3: Propose

Present the organization plan in a clear, scannable format.

### Plan Format

```
## Organization Plan for ~/Downloads

Strategy: by-type
Files to organize: 147
Cleanup candidates: 12 (see below)
Skipped (hidden/system): 3

### Proposed Moves

📁 Documents/ (23 files)
  report-q4.pdf, meeting-notes.docx, todo.txt, ...

📁 Images/ (45 files)
  screenshot-2024-01.png, photo-vacation.jpg, ...

📁 Videos/ (8 files)
  screen-recording.mp4, tutorial.mkv, ...

📁 Archives/ (15 files)
  backup-2024.zip, project-files.tar.gz, ...

📁 Code/ (31 files)
  script.py, config.yaml, index.html, ...

📁 Other/ (13 files)
  unknown-file, mystery.xyz, ...

📁 Applications/ (12 files)
  installer.dmg, setup.exe, ...

### Cleanup Candidates (not moved — your decision)
  🗑 5 incomplete downloads (.part, .crdownload)
  🗑 4 duplicates (file (1).pdf pattern)
  🗑 3 temp files (.tmp)

Delete cleanup candidates? [y/n/review each]
```

### Presenting Large Plans

For >50 files, show category summaries with counts. Offer to list
individual files per category on request.

For >200 files, show only category counts and ask if user wants details:

```
Plan: 847 files → 9 categories
  Documents: 234  |  Images: 198  |  Videos: 45
  Audio: 23       |  Archives: 89 |  Code: 156
  Applications: 34|  Other: 68

Show details for a category? [type name or 'all' or 'proceed']
```

## Phase 4: Confirm

Get explicit user approval before moving anything.

### Confirmation Options

| User says | Action |
|-----------|--------|
| "yes", "proceed", "looks good" | Execute the plan as proposed |
| "no", "cancel", "stop" | Abort, no changes made |
| "edit", "change", "adjust" | Enter edit mode (see below) |
| "move X to Y instead" | Adjust single file/category mapping |
| "skip Other" | Exclude a category from the plan |
| "rename Archives to Compressed" | Change target folder name |
| "combine Audio and Video into Media" | Merge categories |
| "split Code into languages" | Add subcategories |

### Edit Mode

Allow the user to modify the plan interactively:

1. Change which category a file belongs to
2. Rename a target folder
3. Merge two categories into one
4. Split a category into subcategories
5. Exclude specific files from the plan
6. Add a new custom category

After each edit, show the updated plan summary and ask for confirmation again.

### Safety Checks Before Execution

1. Verify target directory still exists and is writable
2. Verify all source files still exist (nothing moved/deleted since scan)
3. Check available disk space (moves within same volume need no extra space)
4. If moving across volumes, verify sufficient space at destination
5. Check for filename conflicts at destination

## Phase 5: Execute

### Move Operations

Use `mv` for same-volume moves (atomic, instant). Use `cp` + verify + `rm`
for cross-volume moves (slower, but safe).

```bash
# Same volume — atomic rename
mv "$SOURCE" "$DEST"

# Cross volume — copy, verify, then remove
cp -p "$SOURCE" "$DEST"           # preserve metadata
cmp -s "$SOURCE" "$DEST" && rm "$SOURCE"  # verify before delete
```

### Conflict Resolution

When a file with the same name exists at the destination:

| Strategy | When to use |
|----------|-------------|
| Numeric suffix | Default: `file.pdf` → `file (1).pdf` |
| Skip | User chose "don't overwrite" |
| Overwrite | Only if user explicitly confirms per-file |
| Rename with date | `file.pdf` → `file-2024-03-15.pdf` |

```bash
# Generate unique name
get_unique_name() {
  local dest="$1"
  local dir=$(dirname "$dest")
  local base=$(basename "$dest")
  local name="${base%.*}"
  local ext="${base##*.}"
  local counter=1
  
  while [ -f "$dest" ]; do
    dest="$dir/${name} (${counter}).${ext}"
    counter=$((counter + 1))
  done
  echo "$dest"
}
```

### Undo Log

Log every move operation to enable full undo. Write the log before
starting moves so partial operations can be reversed.

```bash
# Log format: tab-separated, one operation per line
# TIMESTAMP  SOURCE_PATH  DEST_PATH  STATUS
echo "$(date -Iseconds)\t$SOURCE\t$DEST\tpending" >> "$UNDO_LOG"
```

Log location: `~/.folder-organizer/undo/YYYY-MM-DD_HHMMSS.log`

### Undo Command

To reverse the last organization:

```bash
# Read undo log in reverse, move files back
tac "$UNDO_LOG" | while IFS=$'\t' read -r ts src dest status; do
  if [ "$status" = "done" ] && [ -f "$dest" ]; then
    mv "$dest" "$src"
    echo "Restored: $src"
  fi
done
```

After undo, remove empty category folders that were created:

```bash
find "$TARGET" -maxdepth 1 -type d -empty -delete
```

### Progress Reporting

For large batches (>50 files), show progress:

```
Moving files...
 [####------] 45/120 (37%) — Documents/report-q4.pdf
```

### Error Handling

| Error | Action |
|-------|--------|
| Permission denied | Skip file, report at end |
| Disk full | Stop immediately, report what was moved |
| File disappeared | Skip, note in log as "missing" |
| Destination not writable | Abort before starting |
| Filename too long | Truncate name, preserve extension |

After completion, report:
- Files moved successfully
- Files skipped (with reasons)
- Empty folders created (if any)
- Undo log location

### Post-Execution

```
✓ Organization complete

Moved: 135 files into 7 folders
Skipped: 3 (permission denied)
Cleanup: 12 files flagged in _Review/

Undo this operation:
  "Undo the last folder organization"
  (log: ~/.folder-organizer/undo/2024-03-15_143022.log)

Empty source folder? The original location has 0 remaining files.
```

## Batch Processing

For organizing multiple directories in sequence:

1. Run scan on each directory
2. Present combined plan showing all directories
3. Single confirmation for all
4. Execute in order, one directory at a time
5. Single undo log covers all directories

## Dry Run Mode

When user is cautious or testing:

```
Dry run — no files will be moved.

Would move:
  report.pdf → Documents/report.pdf
  photo.jpg → Images/photo.jpg
  ...

Run for real? [y/n]
```

Generate the full plan and log, but skip the actual `mv` commands.
Present the dry run output as if it were the proposal step, then
ask for confirmation to execute for real.

## Platform Differences

| Operation | macOS | Linux |
|-----------|-------|-------|
| File modified time | `stat -f "%Sm" -t "%Y-%m-%d" file` | `stat -c "%y" file` |
| MIME detection | `file --mime-type -b file` | `file --mime-type -b file` |
| Open folder after | `open "$TARGET"` | `xdg-open "$TARGET"` |
| Trash instead of delete | `mv file ~/.Trash/` | `gio trash file` or `trash-put file` |
| EXIF date | `mdls -name kMDItemContentCreationDate file` | `exiftool -DateTimeOriginal file` |

Detect platform with `uname -s` and use appropriate commands.
