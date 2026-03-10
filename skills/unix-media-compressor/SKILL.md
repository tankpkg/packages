---
name: unix-media-compressor
description: |
  Compress and optimize any file on macOS and Linux. Covers the full
  compression stack: images (JPEG via mozjpeg/jpegoptim, PNG via
  pngquant+oxipng, WebP via cwebp, AVIF via avifenc, GIF via gifsicle),
  video (H.264/H.265/AV1 with ffmpeg CRF encoding, resolution scaling,
  hardware acceleration), audio (MP3/AAC/Opus/FLAC codec selection and
  quality tiers), PDFs (Ghostscript quality presets, qpdf optimization),
  and archives (zip, tar.gz, tar.xz, tar.zst, 7z, brotli with format
  selection guidance and parallel compression). Auto-detects installed
  tools, guides installation of missing ones, supports batch processing
  with before/after size reporting. Synthesizes ffmpeg official docs,
  Ghostscript docs, Google WebP/AVIF docs, Xiph.org Opus docs, and
  production compression guides.

  Trigger phrases: "compress", "shrink", "optimize", "reduce file size",
  "make smaller", "image compression", "video compression", "audio
  compression", "compress PDF", "optimize PDF", "zip", "archive",
  "tar", "gzip", "7z", "zstd", "brotli", "convert to WebP",
  "convert to AVIF", "ffmpeg compress", "reduce video size",
  "optimize images", "optimize PNG", "optimize JPEG", "batch compress",
  "pngquant", "oxipng", "jpegoptim", "mozjpeg", "cwebp", "avifenc",
  "gifsicle", "ghostscript", "compress video for web", "smaller file",
  "file too large", "reduce size", "lossy compression", "lossless
  compression", "CRF", "quality preset", "compress folder",
  "make video smaller", "make image smaller", "shrink PDF"
---

# Unix Media Compressor

Compress any file to its smallest practical size on macOS and Linux.

## Core Philosophy

1. **Right tool for the job** — Each file type has a best-in-class compressor.
   JPEG and PNG need different tools. Video and audio need different codecs.
   Match the tool to the content.
2. **Quality tiers, not magic numbers** — Three tiers for every domain: "web"
   (aggressive, smallest), "balanced" (good quality, reasonable size), and
   "quality" (visually/audibly lossless). Pick a tier, get the right settings.
3. **Detect before compressing** — Run `scripts/check-tools.sh` first. Know
   what tools are available. Install missing ones. Do not guess.
4. **Preserve originals by default** — Output to a new file unless the user
   explicitly asks to overwrite. Compression is lossy and irreversible for
   most formats.
5. **Show the results** — Always report before/after file sizes and percentage
   reduction. Compression without measurement is guessing.

## Quick-Start

### What are you compressing?

| File Type | Best Tool | Start Here |
|-----------|-----------|------------|
| JPEG photos | mozjpeg or jpegoptim | `references/image-compression.md` |
| PNG graphics | pngquant + oxipng | `references/image-compression.md` |
| Convert to WebP | cwebp | `references/image-compression.md` |
| Convert to AVIF | avifenc | `references/image-compression.md` |
| GIF animation | gifsicle | `references/image-compression.md` |
| Video (any format) | ffmpeg (libx264/libx265/libsvtav1) | `references/video-compression.md` |
| Audio (any format) | ffmpeg (libopus/aac/libmp3lame) | `references/audio-compression.md` |
| PDF documents | Ghostscript (gs) | `references/pdf-compression.md` |
| Folder / multiple files | zip, tar.zst, 7z | `references/archive-formats.md` |
| Missing tools? | check-tools.sh | `references/tool-setup.md` |

### Quality Tier Quick Reference

| Tier | Images | Video (H.264) | Audio (Opus) | PDF |
|------|--------|---------------|--------------|-----|
| Web | cwebp -q 75 | CRF 28, fast | 64-96k | /screen (72 DPI) |
| Balanced | cwebp -q 85 | CRF 22, slow | 128k | /ebook (150 DPI) |
| Quality | cwebp -q 92 | CRF 18, veryslow | 192k | /printer (300 DPI) |

## Common Workflows

### Compress all images in a folder

```bash
# Check tools first
bash scripts/check-tools.sh

# JPEG: optimize in-place
jpegoptim --max=85 --strip-all *.jpg

# PNG: lossy + lossless pipeline
pngquant --quality 65-80 --force --ext .png *.png
oxipng -o 3 -i 0 --strip safe *.png

# Convert all to WebP
for f in *.jpg *.png; do cwebp -q 85 "$f" -o "${f%.*}.webp"; done
```

### Compress a video for web

```bash
ffmpeg -i input.mov -c:v libx264 -crf 23 -preset medium \
  -pix_fmt yuv420p -c:a aac -b:a 128k \
  -movflags +faststart output.mp4
```

### Compress a PDF

```bash
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH -sOutputFile=output.pdf input.pdf
```

### Archive a folder (best speed/ratio)

```bash
tar -cf - ./folder/ | zstd -3 -T0 -o folder.tar.zst
```

## Decision Trees

### Which video codec?

| Priority | Codec | Encoder | When |
|----------|-------|---------|------|
| Max compatibility | H.264 | libx264 | Web, mobile, legacy devices |
| Better compression | H.265 | libx265 | 4K, storage savings, modern devices |
| Best compression | AV1 | libsvtav1 | Modern web, encode time acceptable |

### Which archive format?

| Priority | Format | When |
|----------|--------|------|
| Cross-platform | zip | Sharing with Windows/Mac users |
| Best speed+ratio | tar.zst | Backups, pipelines, general use |
| Maximum ratio | 7z | Archival, maximum compression needed |
| Web assets | brotli | Pre-compressing JS/CSS for HTTP |

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "command not found" | Tool not installed | Run `bash scripts/check-tools.sh --install` |
| Output larger than input | Already optimized or wrong settings | Try different quality tier or tool |
| Video has no audio | Missing -c:a flag | Add `-c:a aac -b:a 128k` |
| H.265 won't play on iPhone | Missing tag | Add `-tag:v hvc1` |
| PNG barely shrinks | Already optimized or few colors | Try pngquant (lossy) before oxipng |
| ffmpeg "width not divisible by 2" | Odd resolution | Use `scale=WIDTH:-2` |
| Ghostscript font errors | Missing fonts | Add `-dSubsetFonts=true` |

## Reference Files

| File | Contents |
|------|----------|
| `references/image-compression.md` | JPEG (mozjpeg, jpegoptim), PNG (pngquant+oxipng), WebP (cwebp), AVIF (avifenc), GIF (gifsicle), format selection, quality presets, batch processing |
| `references/video-compression.md` | H.264/H.265/AV1 codecs, CRF quality tiers, resolution scaling, two-pass encoding, hardware acceleration, audio handling, batch video |
| `references/audio-compression.md` | MP3/AAC/Opus/FLAC codecs, quality tiers, codec selection guide, extract audio from video, batch audio |
| `references/pdf-compression.md` | Ghostscript quality presets (/screen through /prepress), advanced optimization flags, qpdf, batch PDF compression |
| `references/archive-formats.md` | zip, tar.gz, tar.xz, tar.zst, 7z, brotli, format comparison, parallel compression (pigz, pbzip2), format selection guide |
| `references/tool-setup.md` | Tool detection, macOS/Linux installation, batch processing patterns, before/after reporting, preserving originals |

## Scripts

| Script | Usage |
|--------|-------|
| `scripts/check-tools.sh` | Detect installed tools, suggest missing. Flags: `--json` (JSON output), `--install` (auto-install missing via brew/apt) |
