# File Categories

Sources: bhrigu123/classifier, d6o/Gorganizer, yafyx/tidyf, IANA media types registry

Covers: extension-to-category mapping, MIME type fallbacks, ambiguous file handling,
ignore lists, and category customization.

## Canonical Categories

Use these 13 categories as defaults. Users may request custom categories — adapt
the mapping accordingly while keeping the extension table as a baseline.

| Category | Description | Target users |
|----------|-------------|--------------|
| Images | Photos, screenshots, graphics, design files | Everyone |
| Videos | Movies, recordings, screen captures | Everyone |
| Audio | Music, podcasts, voice memos, sound effects | Everyone |
| Documents | PDFs, word processors, plain text, markdown | Everyone |
| Spreadsheets | Tabular data, financial files | Office workers |
| Presentations | Slide decks | Office workers |
| Archives | Compressed files, disk images | Everyone |
| Ebooks | Digital books | Readers |
| Applications | Installers, packages, executables | Everyone |
| Code | Source code, configs, scripts | Developers |
| Fonts | Typeface files | Designers |
| Data | Databases, structured data dumps | Developers |
| Other | Unrecognized extensions | Catch-all |

## Extension-to-Category Mapping

### Images

```
jpg, jpeg, png, gif, svg, webp, bmp, tiff, tif, ico, heic, heif,
raw, cr2, cr3, nef, arw, dng, orf, rw2, pef, sr2,
psd, ai, sketch, fig, xd, xcf, kra, indd, afdesign, afphoto
```

### Videos

```
mp4, mkv, avi, mov, webm, flv, ogv, mpg, mpeg, m4v, wmv,
3gp, 3g2, ts, vob, mts, m2ts, divx, f4v, asf, rm, rmvb
```

### Audio

```
mp3, aac, flac, ogg, oga, wma, m4a, aiff, aif, wav, amr,
opus, alac, ape, mid, midi, wv, mka, ac3, dts
```

### Documents

```
pdf, doc, docx, odt, txt, rtf, pages, wpd, wps, tex, latex,
log, nfo, srt, sub, ass, vtt
```

### Spreadsheets

```
xls, xlsx, csv, tsv, ods, numbers, xlsm, xlsb, xltx
```

### Presentations

```
ppt, pptx, key, odp, ppsx, pps, potx
```

### Archives

```
zip, rar, 7z, gz, bz2, tar, tgz, xz, zst, lz, lzma,
iso, cpio, cab, arj, lzh, z, ace, apk
```

Note: `dmg` belongs in Applications (macOS installer), not Archives.

### Ebooks

```
epub, mobi, azw, azw3, chm, djvu, fb2, ibooks, lit, lrf, pdb
```

### Applications

```
exe, msi, dmg, pkg, app, deb, rpm, appimage, snap, flatpak,
ipa, apk, xapk, aab, bat, cmd, com, gadget, inf, jar, run, wsf
```

### Code

```
ts, tsx, js, jsx, mjs, cjs, py, pyw, rb, go, rs, java, kt, kts,
c, cpp, cc, cxx, h, hpp, hxx, cs, swift, scala, clj, cljs,
lua, pl, pm, php, r, R, jl, ex, exs, erl, hrl, hs, lhs,
dart, groovy, v, zig, nim, cr, ml, mli, fs, fsi, fsx,
html, htm, css, scss, sass, less, styl,
vue, svelte, astro,
sh, bash, zsh, fish, ps1, psm1,
sql, graphql, gql, proto, thrift,
makefile, dockerfile, vagrantfile, jenkinsfile, rakefile, gemfile
```

### Configuration (sub-category of Code)

These are technically code but often treated as project metadata:

```
json, jsonc, json5, yaml, yml, toml, ini, cfg, conf, env,
editorconfig, gitignore, gitattributes, dockerignore, npmrc,
eslintrc, prettierrc, babelrc, tsconfig, pyproject
```

Decision: group with Code by default. If user asks to separate configs, create
a "Config" category.

### Fonts

```
ttf, otf, woff, woff2, eot, fnt, fon, pfb, pfm
```

### Data

```
db, sqlite, sqlite3, mdb, accdb, dbf, sav, rec, parquet, avro, arrow
```

## Ambiguous Extensions

Some extensions belong to different categories depending on context.
Use filename analysis and surrounding files as disambiguation signals.

| Extension | Context A | Context B | Heuristic |
|-----------|----------|----------|-----------|
| md | Code (README.md, CHANGELOG.md) | Documents (notes, reports) | Filename contains README/CONTRIBUTING/CHANGELOG → Code |
| csv | Spreadsheets (data.csv) | Code (test-fixtures.csv) | In a project dir with package.json → Code |
| json | Code (package.json, tsconfig.json) | Data (export.json, backup.json) | Known config names → Code, otherwise → Data |
| xml | Code (pom.xml, web.xml) | Documents (sitemap.xml) | Known config names → Code |
| log | Documents (access.log) | Temporary (debug.log) | Offer to delete if >30 days old |
| dmg | Applications (installer.dmg) | Archives (backup.dmg) | Default to Applications |
| svg | Images (illustration.svg) | Code (icon component) | Default to Images |

When uncertain, ask the user rather than guessing.

## Ignore List

Skip these files entirely — do not move or categorize:

```
.DS_Store, desktop.ini, Thumbs.db, .Spotlight-V100, .Trashes,
.fseventsd, .TemporaryItems, .localized, Icon\r,
*.tmp, *.temp, *.swp, *.swo, *~,
*.part, *.crdownload, *.partial, *.download
```

### Flagged for Deletion (suggest, do not auto-delete)

| Pattern | Reason |
|---------|--------|
| `*.part`, `*.crdownload`, `*.partial` | Incomplete downloads |
| `*.tmp`, `*.temp` | Temporary files |
| `file (1).ext`, `file (2).ext` | Likely duplicates |
| Files >90 days in Downloads | Probably forgotten |

Present these to the user as "candidates for cleanup" before organizing.

## Category Customization

Users may request non-standard categories. Common custom setups:

| User type | Custom categories |
|-----------|-------------------|
| Photographer | Raw/, Edited/, Export/, Timelapse/ |
| Student | Semester-1/, Semester-2/, Assignments/, Notes/ |
| Freelancer | Client-A/, Client-B/, Invoices/, Contracts/ |
| Musician | Samples/, Projects/, Stems/, Exports/ |

When user requests custom categories:
1. Ask which categories they want
2. Ask which extensions or filename patterns map to each
3. Fall back to default categories for unmatched files
4. Confirm the full mapping before execution

## MIME Type Fallback

When extension is missing or ambiguous, use the `file` command for MIME detection:

```bash
file --mime-type -b "filename"
```

| MIME prefix | Category |
|-------------|----------|
| image/ | Images |
| video/ | Videos |
| audio/ | Audio |
| text/plain | Documents |
| text/html, text/css, text/javascript | Code |
| application/pdf | Documents |
| application/zip, application/x-tar | Archives |
| application/x-executable | Applications |
| font/ | Fonts |

Files with no extension AND no recognizable MIME type go to Other.

## Size-Based Flagging

Large files deserve special attention during organization. Flag them
for user review rather than silently moving them.

| Size threshold | Action |
|---------------|--------|
| >100 MB | Flag as "large file" in the plan |
| >1 GB | Warn user explicitly, confirm before moving |
| >10 GB | Suggest reviewing before moving (may be VM, backup, etc.) |

Common large file types:

| Extension | Typical size | Category | Note |
|-----------|-------------|----------|------|
| iso | 1-8 GB | Archives | OS/software image |
| vmdk, vdi, qcow2 | 5-50 GB | Data | Virtual machine disk |
| pst, ost | 1-20 GB | Data | Outlook archive |
| bak, backup | varies | Archives | Database/system backup |
| raw, cr2, nef | 20-60 MB each | Images | Camera RAW (batch = large) |
| mov, mp4 (4K) | 1-10 GB | Videos | High-res recordings |

## Filename Pattern Recognition

Beyond extensions, filenames contain organizational signals.

### Screenshot Detection

| Platform | Pattern | Example |
|----------|---------|---------|
| macOS | `Screenshot YYYY-MM-DD at HH.MM.SS` | Screenshot 2024-03-15 at 14.23.45.png |
| Windows | `Screenshot (N)` or `Screenshot YYYY-MM-DD HHMMSS` | Screenshot (3).png |
| Linux | `Screenshot from YYYY-MM-DD HH-MM-SS` | Screenshot from 2024-03-15 12-30-00.png |
| iOS | `IMG_NNNN` | IMG_4523.HEIC |
| Android | `YYYY-MM-DD_HH-MM-SS` or `PXL_YYYYMMDD_HHMMSS` | PXL_20240315_142345.jpg |

Screenshots can be sub-grouped under `Images/Screenshots/` when the
user has many of them.

### Download Artifact Patterns

| Pattern | Meaning | Suggestion |
|---------|---------|------------|
| `(1)`, `(2)`, `(3)` suffix | Duplicate download | Flag as duplicate |
| `-latest`, `-final`, `-v2` | Version progression | Keep latest, flag older |
| `Untitled`, `New Document` | Never renamed | Ask user for proper name |
| UUID in filename | Auto-generated | Flag for review |

### Invoice and Receipt Detection

| Pattern | Signal |
|---------|--------|
| `invoice`, `inv-`, `INV` | Financial document |
| `receipt`, `rcpt` | Financial document |
| `statement`, `stmt` | Financial document |
| `payment`, `pmt` | Financial document |
| `W-2`, `1099`, `tax` | Tax document |

Financial documents can be sub-grouped under `Documents/Financial/` when
multiple are detected.

## Extensionless Files

Some files have no extension at all. Common in developer contexts.

| Filename | Category | Reasoning |
|----------|----------|-----------|
| Makefile | Code | Build system |
| Dockerfile | Code | Container definition |
| Vagrantfile | Code | VM definition |
| Gemfile, Rakefile | Code | Ruby project files |
| LICENSE, LICENCE | Documents | Legal text |
| CODEOWNERS | Code | GitHub config |
| Procfile | Code | Heroku config |
| Brewfile | Code | Homebrew bundle |

For unknown extensionless files, use MIME type detection as primary signal.
If MIME returns `text/plain`, check the first line for shebang (`#!/`):

```bash
head -1 "$file" | grep -q '^#!' && echo "Code (script)"
```

A shebang line indicates an executable script — categorize as Code.
