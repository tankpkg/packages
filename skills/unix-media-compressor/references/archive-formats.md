# Archive Formats and File Compression

Sources: zstd official docs, 7-Zip documentation, GNU tar manual, Google Brotli docs

---

## Format Comparison Table

| Format | Ext | Ratio | Compress Speed | Decompress Speed | Parallel | Best Use Case |
|--------|-----|-------|----------------|------------------|----------|---------------|
| zip | .zip | Fair | Fast | Fast | No (native) | Cross-platform sharing, Windows users |
| tar+gzip | .tar.gz | Good | Medium | Fast | pigz | General Unix archives, wide compatibility |
| tar+bzip2 | .tar.bz2 | Better | Slow | Slow | pbzip2 | Legacy systems, slightly better ratio than gz |
| tar+xz | .tar.xz | Excellent | Very Slow | Medium | pixz / -T0 | Distribution packages, max ratio with time |
| tar+zstd | .tar.zst | Excellent | Very Fast | Very Fast | Built-in -T0 | **Recommended default** — best speed/ratio balance |
| 7z | .7z | Best | Slow | Medium | Partial | Maximum compression, encrypted archives |
| brotli | .br | Excellent | Medium | Very Fast | No | Web assets only — HTTP pre-compression |

Ratio scale: Fair < Good < Better < Excellent < Best (all relative to uncompressed size)

---

## Format Selection Guide

```
Need Windows users to open without extra tools?
  → zip

Compressing for web delivery (JS, CSS, HTML, fonts)?
  → brotli -q 9 (pre-compress, serve via nginx/CDN)

Need maximum compression ratio, time not a concern?
  → 7z -mx=9

Need password-protected archive?
  → 7z -p

Archiving for distribution / package manager?
  → tar.zst (Arch Linux, Fedora use this natively)

Everything else (backups, transfers, general use)?
  → tar.zst with zstd -3 -T0  ← recommended default
```

---

## zip

Standard format. No external tools needed on Windows, macOS, or Linux.

**Create:**
```bash
# Basic archive
zip archive.zip file1 file2

# Recursive directory
zip -r archive.zip directory/

# Max compression
zip -9 -r archive.zip directory/

# No compression (store only, fast for already-compressed files)
zip -0 -r archive.zip directory/

# Exclude patterns
zip -r archive.zip directory/ -x "*.DS_Store" -x "__pycache__/*" -x "*.pyc"

# Exclude a subdirectory
zip -r archive.zip directory/ -x "directory/node_modules/*"
```

**Extract:**
```bash
unzip archive.zip
unzip archive.zip -d /target/directory/
unzip -l archive.zip          # list contents without extracting
```

**Compression levels:** 0 (store) through 9 (max). Default is 6. Level 9 rarely worth the time cost.

---

## tar + gzip

The classic Unix archive format. Widely supported everywhere.

**Create:**
```bash
tar -czf archive.tar.gz directory/
tar -czf archive.tar.gz file1 file2 file3

# Verbose (shows files as they're added)
tar -czvf archive.tar.gz directory/

# Exclude patterns
tar -czf archive.tar.gz directory/ --exclude="*.pyc" --exclude=".git"
tar -czf archive.tar.gz directory/ --exclude-vcs
```

**Extract:**
```bash
tar -xzf archive.tar.gz
tar -xzf archive.tar.gz -C /target/directory/
tar -xzvf archive.tar.gz    # verbose
```

**Parallel with pigz** (drop-in gzip replacement, uses all cores):
```bash
tar -cf - directory/ | pigz -9 > archive.tar.gz
tar -cf - directory/ | pigz -p 8 > archive.tar.gz   # explicit 8 threads

# Extract with pigz
pigz -dc archive.tar.gz | tar -xf -
```

pigz is a drop-in replacement — same flags as gzip. Install: `brew install pigz` / `apt install pigz`.

---

## tar + bzip2

Better compression ratio than gzip, but significantly slower. Largely superseded by xz and zstd.

**Create:**
```bash
tar -cjf archive.tar.bz2 directory/
tar -cjvf archive.tar.bz2 directory/   # verbose
tar -cjf archive.tar.bz2 directory/ --exclude="*.log"
```

**Extract:**
```bash
tar -xjf archive.tar.bz2
tar -xjf archive.tar.bz2 -C /target/directory/
```

**Parallel with pbzip2:**
```bash
tar -cf - directory/ | pbzip2 -9 > archive.tar.bz2
tar -cf - directory/ | pbzip2 -p8 > archive.tar.bz2   # 8 threads

# Extract
pbzip2 -dc archive.tar.bz2 | tar -xf -
```

Use bzip2 only when the recipient specifically requires it. For new archives, prefer zstd.

---

## tar + xz

Excellent compression ratio. Slow to compress, moderate to decompress. Used by many Linux distributions for package distribution.

**Create:**
```bash
tar -cJf archive.tar.xz directory/
tar -cJvf archive.tar.xz directory/   # verbose

# Multi-threaded via xz directly
tar -cf - directory/ | xz -T0 -9 > archive.tar.xz
# -T0 = use all available CPU threads
# -9 = max compression (levels 0-9)
```

**Extract:**
```bash
tar -xJf archive.tar.xz
tar -xJf archive.tar.xz -C /target/directory/

# Multi-threaded extract
xz -T0 -dc archive.tar.xz | tar -xf -
```

**Parallel with pixz:**
```bash
tar -Ipixz -cf archive.tar.xz directory/
tar -Ipixz -xf archive.tar.xz
```

xz -T0 is built into modern xz (5.2+). pixz adds better parallelism for older versions.

---

## tar + zstd (Recommended)

Best overall choice for most use cases. Compresses faster than gzip at better ratios. Decompresses extremely fast. Parallel support is built in — no wrapper tool needed.

**Why zstd is recommended:**
- Compression speed rivals gzip at level 3, with better ratios
- Decompression is 3-5x faster than gzip, 10x faster than xz
- `-T0` parallel flag is native, no external tool required
- Adopted by Arch Linux (pacman), Fedora (rpm), and Facebook's infrastructure
- Levels 1-22 give fine-grained control from ultra-fast to ultra-compressed

**Create:**
```bash
# Recommended default: level 3, all threads
tar -cf - directory/ | zstd -3 -T0 > archive.tar.zst

# Using tar's built-in zstd support (GNU tar 1.31+)
tar --zstd -cf archive.tar.zst directory/

# Higher compression
tar -cf - directory/ | zstd -9 -T0 > archive.tar.zst

# Max compression (slow, use for archival)
tar -cf - directory/ | zstd -19 -T0 > archive.tar.zst

# Verbose
tar -cf - directory/ | zstd -3 -T0 -v > archive.tar.zst
```

**Extract:**
```bash
zstd -dc archive.tar.zst | tar -xf -

# GNU tar built-in
tar --zstd -xf archive.tar.zst
tar --zstd -xf archive.tar.zst -C /target/directory/
```

**Compression levels:**
- Level 1: Fastest, ~gzip ratio
- Level 3: Default — good balance (use this)
- Level 9: Better ratio, still fast
- Level 19: Near-max ratio, slow
- Level 22: Ultra (requires `--ultra` flag): `zstd --ultra -22 -T0`

---

## 7z

Highest compression ratio of any common format. Supports encryption, split volumes, and self-extracting archives. No native Unix streaming — works on complete files.

**Create:**
```bash
# Standard archive
7z a archive.7z directory/

# Maximum compression
7z a -mx=9 archive.7z directory/

# Compression levels: -mx=0 (store) through -mx=9 (ultra)
7z a -mx=5 archive.7z directory/   # balanced

# Exclude files
7z a -mx=9 archive.7z directory/ -xr!"*.pyc" -xr!".git"

# Password encryption (AES-256)
7z a -mx=9 -p"yourpassword" archive.7z directory/
# Encrypt file headers too (hides filenames)
7z a -mx=9 -p"yourpassword" -mhe=on archive.7z directory/

# Split into volumes (e.g., 100MB each)
7z a -mx=9 -v100m archive.7z directory/
# Creates: archive.7z.001, archive.7z.002, ...
```

**Extract:**
```bash
7z x archive.7z
7z x archive.7z -o/target/directory/

# Test archive integrity
7z t archive.7z

# Extract with password
7z x -p"yourpassword" archive.7z
```

**When to use 7z:** Maximum compression for archival storage, encrypted archives, or when recipients are on Windows (7-Zip is free and widely installed). Not suitable for streaming or piping.

---

## brotli

Designed for HTTP pre-compression of web assets. Decompresses faster than gzip at better ratios. Browsers decompress brotli natively when served over HTTPS with `Content-Encoding: br`.

brotli is not a general-purpose archive format — use it only for web asset pre-compression.

**Single file:**
```bash
brotli -q 9 file.js           # creates file.js.br
brotli -q 11 file.css         # max compression (slow)
brotli -d file.js.br          # decompress
```

**Batch compress web assets:**
```bash
# Compress all JS and CSS files in a directory
find dist/ -type f \( -name "*.js" -o -name "*.css" \) -exec brotli -q 9 {} \;

# Compress HTML, JS, CSS, SVG, fonts
find dist/ -type f \( -name "*.html" -o -name "*.js" -o -name "*.css" \
  -o -name "*.svg" -o -name "*.woff2" \) -exec brotli -q 9 {} \;

# Keep original files (brotli -k keeps originals)
find dist/ -type f -name "*.js" -exec brotli -k -q 9 {} \;
```

**Quality levels:**
- `-q 1`: Fastest, minimal compression
- `-q 9`: Recommended for production (good ratio, reasonable speed)
- `-q 11`: Maximum compression, very slow — use for static assets that rarely change

**nginx configuration for pre-compressed brotli:**
```nginx
brotli_static on;   # serves .br files if they exist
```

---

## Parallel Compression Tools

| Tool | Replaces | Install (macOS) | Install (Linux) | Notes |
|------|----------|-----------------|-----------------|-------|
| pigz | gzip | `brew install pigz` | `apt install pigz` | Drop-in replacement, same flags |
| pbzip2 | bzip2 | `brew install pbzip2` | `apt install pbzip2` | Drop-in replacement |
| pixz | xz | `brew install pixz` | `apt install pixz` | Parallel + indexed xz |
| zstd | — | `brew install zstd` | `apt install zstd` | Parallel built-in with -T0 |

**When to use parallel tools:**
- Files larger than ~500MB benefit significantly from parallelism
- On machines with 4+ cores, pigz/pbzip2 can be 3-8x faster than single-threaded
- zstd -T0 is always worth using — no downside, automatic thread count

**Check available threads:**
```bash
nproc          # Linux
sysctl -n hw.logicalcpu   # macOS
```

---

## Single File Compression

For compressing individual files (not creating archives), use these tools directly without tar.

**zstd (recommended):**
```bash
zstd -3 -T0 largefile.sql          # creates largefile.sql.zst
zstd -d largefile.sql.zst          # decompress
zstd -3 -T0 -k largefile.sql       # keep original with -k
```

**gzip:**
```bash
gzip -9 file.log                   # creates file.log.gz, removes original
gzip -9 -k file.log                # keep original
gzip -d file.log.gz                # decompress
```

**xz:**
```bash
xz -9 -T0 database.dump            # creates database.dump.xz
xz -d database.dump.xz             # decompress
xz -T0 -k -9 database.dump        # keep original
```

Single-file compression is useful for log files, database dumps, and large text files before transfer.

---

## Compression Level Guidance

| Tool | Fast | Balanced | Max | Notes |
|------|------|----------|-----|-------|
| zip | `-1` | `-6` (default) | `-9` | Level 9 rarely worth it |
| gzip / pigz | `-1` | `-6` (default) | `-9` | Same scale |
| bzip2 / pbzip2 | `-1` | `-6` (default) | `-9` | All levels are slow |
| xz | `-0` | `-6` (default) | `-9` | -9 is very slow; -6 is good |
| zstd | `-1` | `-3` (recommended) | `--ultra -22` | Sweet spot is 3; 19 for archival |
| 7z | `-mx=1` | `-mx=5` | `-mx=9` | -mx=9 for archival only |
| brotli | `-q 1` | `-q 9` | `-q 11` | -q 11 for static assets |

**Rules of thumb:**
- Default levels are calibrated for general use — only override when you have a specific reason
- "Fast" levels are useful when compressing many small files or when CPU is the bottleneck
- "Max" levels are for archival storage where you compress once and decompress rarely
- zstd -3 beats gzip -9 in both speed and ratio — it is the correct default for new work

---

## Quick Reference: Common Tasks

```bash
# Backup a directory (recommended)
tar -cf - mydir/ | zstd -3 -T0 > mydir-backup.tar.zst

# Share with Windows users
zip -9 -r archive.zip mydir/

# Maximum compression for archival
7z a -mx=9 archive.7z mydir/

# Pre-compress web assets
find dist/ -type f \( -name "*.js" -o -name "*.css" \) -exec brotli -k -q 9 {} \;

# Fast parallel gzip
tar -cf - mydir/ | pigz -9 > archive.tar.gz

# Compress a single large file
zstd -3 -T0 -k database.dump
```

---

For tool installation and availability checks, see `tool-setup.md`.

For compressing individual media files before archiving, see `image-compression.md`, `video-compression.md`, or `audio-compression.md`.
