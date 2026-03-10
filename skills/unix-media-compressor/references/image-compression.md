# Image Compression

Sources: ffmpeg docs, Google WebP docs, libavif docs, mozjpeg project, Addy Osmani (Essential Image Optimization)

## Format Selection Guide

Choose the output format based on content type and target environment, not habit.

| Format | Best For | Lossy | Lossless | Alpha | Browser Support |
|--------|----------|-------|----------|-------|-----------------|
| JPEG | Photos, gradients, complex scenes | Yes | No | No | Universal |
| PNG | Screenshots, logos, text, sharp edges | No | Yes | Yes | Universal |
| WebP | Web delivery of photos or graphics | Yes | Yes | Yes | 97%+ (all modern) |
| AVIF | Web delivery, highest compression | Yes | Yes | Yes | 93%+ (Chrome, Firefox, Safari 16+) |
| GIF | Simple animations, legacy icons | No | Yes | Partial | Universal |

**Decision rule:** Serve WebP for web photos and graphics where AVIF is not yet required. Use AVIF when maximum compression matters and Safari 16+ is acceptable. Keep PNG for assets requiring lossless fidelity. JPEG remains the safe fallback for email and legacy systems.

---

## JPEG Optimization

### mozjpeg — cjpeg (re-encode from source)

`cjpeg` re-encodes from a raw or lossless source. Always re-encode from the original, never from an already-compressed JPEG.

```bash
# Web preset (quality 75-80)
cjpeg -quality 78 -optimize -progressive -outfile output.jpg input.png

# Balanced preset (quality 85)
cjpeg -quality 85 -optimize -progressive -outfile output.jpg input.png

# Quality preset (quality 92)
cjpeg -quality 92 -optimize -progressive -outfile output.jpg input.png

```

Key flags: `-optimize` enables Huffman table optimization. `-progressive` creates progressive JPEG (loads blurry-to-sharp, perceived as faster). Both add a small encode cost but reduce file size. Metadata stripping is not a cjpeg flag — strip at source using ImageMagick (`convert -strip`) or handle with jpegtran post-encode.

### mozjpeg — jpegtran (lossless re-optimization)

`jpegtran` optimizes an existing JPEG without re-encoding. Use when you cannot re-encode from source.

```bash
# Lossless optimization + progressive conversion
jpegtran -copy none -optimize -progressive -outfile output.jpg input.jpg

# Strip all metadata, keep progressive
jpegtran -copy none -optimize -progressive -perfect -outfile output.jpg input.jpg
```

`-copy none` strips all EXIF/IPTC/XMP metadata. `-perfect` aborts if lossless transform is not possible (safe guard).

### jpegoptim — batch-friendly optimizer

```bash
# Lossy: set maximum quality (web preset)
jpegoptim --max=80 --strip-all --all-progressive image.jpg

# Lossy: balanced preset
jpegoptim --max=85 --strip-all --all-progressive image.jpg

# Target file size (useful for upload limits)
jpegoptim --size=200k --strip-all image.jpg

# Batch: optimize all JPEGs in directory, output to separate dir
jpegoptim --max=85 --strip-all --all-progressive --dest=./optimized/ *.jpg
```

`--strip-all` removes EXIF, IPTC, and ICC profiles. `--all-progressive` converts to progressive encoding. `--dest` writes output to a different directory, preserving originals.

**Gotcha:** jpegoptim modifies files in-place by default. Always use `--dest` or work on copies.

---

## PNG Optimization

### Recommended pipeline: pngquant + oxipng

Run pngquant first (lossy palette reduction), then oxipng (lossless re-compression). This two-stage pipeline consistently achieves 60-80% size reduction on typical PNGs.

```bash
# Stage 1: pngquant — lossy palette quantization
pngquant --quality 65-80 --speed 1 --force --ext .png input.png

# Stage 2: oxipng — lossless re-compression
oxipng -o 3 -i 0 --strip safe input.png
```

**Full pipeline in one command:**

```bash
pngquant --quality 65-80 --speed 1 --force --ext .png input.png && \
  oxipng -o 3 -i 0 --strip safe input.png
```

### pngquant flags

```bash
# Web preset (aggressive reduction)
pngquant --quality 60-75 --speed 1 --force --ext .png input.png

# Balanced preset
pngquant --quality 65-80 --speed 1 --force --ext .png input.png

# Quality preset (minimal loss)
pngquant --quality 80-90 --speed 1 --force --ext .png input.png

# Output to new file (preserve original)
pngquant --quality 65-80 --speed 1 --output output.png input.png
```

`--speed 1` is the slowest/best compression (1-11 scale). `--force` overwrites existing output. `--ext .png` overwrites the input file in-place (use `--output` to avoid this).

**Gotcha:** pngquant converts 24-bit PNG to 8-bit palette (256 colors max). This is lossy. Do not use on images requiring full color fidelity — use oxipng alone instead.

### oxipng flags

```bash
# Standard optimization (recommended)
oxipng -o 3 -i 0 --strip safe input.png

# Maximum compression (slow)
oxipng -o 6 --zopfli -i 0 --strip safe input.png

# Recursive directory optimization
oxipng -o 3 -i 0 --strip safe -r ./images/

# Preserve original, write to new file
oxipng -o 3 -i 0 --strip safe --out output.png input.png
```

`-o 3` is the optimization level (0-6). `-i 0` removes interlacing (interlaced PNGs are larger and slower to decode in browsers). `--strip safe` removes non-essential metadata while preserving color profiles. `--zopfli` uses the Zopfli deflate algorithm for maximum compression at significant speed cost.

### optipng — simpler alternative

```bash
# Standard optimization
optipng -o5 -strip all input.png

# Batch
find . -name "*.png" | xargs optipng -o5 -strip all
```

`-o5` is the optimization level (0-7). `-strip all` removes all metadata. optipng is slower than oxipng at equivalent quality and does not support Zopfli. Use oxipng unless optipng is the only available tool.

---

## WebP Conversion

### cwebp — lossy conversion

```bash
# Web preset (quality 75-80)
cwebp -q 78 -mt -strip input.jpg -o output.webp

# Balanced preset (quality 85)
cwebp -q 85 -mt -strip input.jpg -o output.webp

# Quality preset (quality 92)
cwebp -q 92 -mt -strip input.jpg -o output.webp
```

`-mt` enables multithreaded encoding. `-strip` removes all metadata (EXIF, XMP, ICC). `-q` sets quality (0-100, higher = better quality and larger file).

### cwebp — lossless conversion

```bash
# Lossless (for PNG sources with transparency)
cwebp -lossless -z 9 -mt -strip input.png -o output.webp

# Near-lossless (visually lossless, smaller than lossless)
cwebp -near_lossless 60 -mt -strip input.png -o output.webp
```

`-lossless` produces a lossless WebP. `-z 9` sets the compression level (0-9, 9 = smallest file, slowest). `-near_lossless 60` applies preprocessing to reduce file size while remaining visually indistinguishable (0 = no preprocessing, 100 = maximum preprocessing).

### cwebp — resize during conversion

```bash
# Resize to max width 1200px, maintain aspect ratio
cwebp -q 85 -resize 1200 0 -mt -strip input.jpg -o output.webp
```

`-resize width height` — set either dimension to 0 to maintain aspect ratio.

### ffmpeg WebP fallback

```bash
# ffmpeg WebP (when cwebp is unavailable)
ffmpeg -i input.jpg -quality 85 output.webp

# Lossless via ffmpeg
ffmpeg -i input.png -lossless 1 output.webp
```

**Gotcha:** ffmpeg's WebP encoder is less efficient than cwebp. Prefer cwebp when available.

---

## AVIF Conversion

### avifenc — primary tool

```bash
# Web preset (quality 60, speed 6)
avifenc --quality 60 --speed 6 --jobs 8 input.jpg output.avif

# Balanced preset (quality 50, speed 6)
avifenc --quality 50 --speed 6 --jobs 8 input.jpg output.avif

# Quality preset (quality 35, speed 4)
avifenc --quality 35 --speed 4 --jobs 8 input.jpg output.avif

# Lossless
avifenc --lossless --jobs 8 input.png output.avif
```

`--quality` ranges 0-100 (lower = smaller file, more loss — inverse of JPEG). `--speed` ranges 0-10 (0 = slowest/best, 10 = fastest/worst). `--jobs 8` enables parallel encoding threads.

**Gotcha:** avifenc quality scale is inverted relative to JPEG/WebP. Quality 50 in AVIF is roughly equivalent to JPEG quality 85 in visual output.

### avifenc — chroma subsampling

```bash
# 4:2:0 (default, smaller, good for photos)
avifenc --quality 50 --speed 6 --yuv 420 --jobs 8 input.jpg output.avif

# 4:4:4 (larger, better for text/graphics)
avifenc --quality 50 --speed 6 --yuv 444 --jobs 8 input.png output.avif
```

Use `--yuv 444` for images with sharp text or fine color detail. Use `--yuv 420` for photographs.

### ffmpeg libaom-av1 fallback

```bash
# AVIF via ffmpeg (when avifenc is unavailable)
ffmpeg -i input.jpg -c:v libaom-av1 -crf 30 -still-picture 1 output.avif

# Higher quality
ffmpeg -i input.jpg -c:v libaom-av1 -crf 20 -still-picture 1 output.avif
```

`-still-picture 1` disables temporal prediction, which is required for single-frame AVIF. `-crf` ranges 0-63 (lower = better quality).

**Gotcha:** libaom-av1 is significantly slower than avifenc. Use avifenc for batch work.

---

## GIF Optimization

### gifsicle — lossless optimization

```bash
# Lossless re-optimization
gifsicle -O3 --batch input.gif

# Output to new file
gifsicle -O3 input.gif -o output.gif
```

`-O3` is the highest optimization level (1-3). `--batch` modifies files in-place.

### gifsicle — lossy optimization

```bash
# Lossy (web preset, significant size reduction)
gifsicle -O3 --lossy=80 input.gif -o output.gif

# Lossy with color reduction
gifsicle -O3 --lossy=80 --colors 64 input.gif -o output.gif

# Aggressive lossy (smallest file)
gifsicle -O3 --lossy=120 --colors 32 input.gif -o output.gif
```

`--lossy=N` sets the lossy compression level (20-200, higher = more loss and smaller file). `--colors N` reduces the color palette (2-256). Reducing colors from 256 to 64 typically cuts file size 30-50% with minimal visible impact on simple animations.

### gifsicle — resize

```bash
# Resize to max width 480px
gifsicle -O3 --lossy=80 --resize-width 480 input.gif -o output.gif
```

**Gotcha:** `--batch` modifies in-place. Always use `-o output.gif` when preserving originals.

---

## Quality Tier Presets

| Format | Web | Balanced | Quality |
|--------|-----|----------|---------|
| JPEG (cjpeg) | `-quality 78 -optimize -progressive` | `-quality 85 -optimize -progressive` | `-quality 92 -optimize -progressive` |
| JPEG (jpegoptim) | `--max=80 --strip-all --all-progressive` | `--max=85 --strip-all --all-progressive` | `--max=92 --strip-all --all-progressive` |
| PNG (pngquant) | `--quality 60-75 --speed 1` | `--quality 65-80 --speed 1` | `--quality 80-90 --speed 1` |
| PNG (oxipng) | `-o 3 -i 0 --strip safe` | `-o 3 -i 0 --strip safe` | `-o 6 --zopfli -i 0 --strip safe` |
| WebP (cwebp) | `-q 78 -mt -strip` | `-q 85 -mt -strip` | `-q 92 -mt -strip` |
| AVIF (avifenc) | `--quality 60 --speed 6` | `--quality 50 --speed 6` | `--quality 35 --speed 4` |
| GIF (gifsicle) | `-O3 --lossy=80 --colors 64` | `-O3 --lossy=60 --colors 128` | `-O3 --lossy=30` |

**Note on AVIF quality:** Lower numbers mean higher quality (inverse of JPEG/WebP). Quality 35 is visually near-lossless for most content.

---

## Batch Processing

### JPEG batch

```bash
# jpegoptim: all JPEGs in directory, preserve originals
mkdir -p optimized
jpegoptim --max=85 --strip-all --all-progressive --dest=./optimized/ *.jpg *.jpeg

# cjpeg: re-encode from lossless source
for f in *.png; do
  cjpeg -quality 85 -optimize -progressive -outfile "optimized/${f%.*}.jpg" "$f"
done
```

### PNG batch pipeline (pngquant + oxipng)

```bash
mkdir -p optimized
for f in *.png; do
  [ -f "$f" ] || continue
  cp "$f" "optimized/$f"
  pngquant --quality 65-80 --speed 1 --force --ext .png "optimized/$f"
  oxipng -o 3 -i 0 --strip safe "optimized/$f"
done
```

### WebP and AVIF batch with find + xargs

```bash
# WebP: all JPEGs and PNGs recursively, 4 parallel jobs
find . -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" \) | \
  xargs -P4 -I{} sh -c 'cwebp -q 85 -mt -strip "{}" -o "${1%.*}.webp"' _ {}

# AVIF: all JPEGs recursively
find . -type f \( -name "*.jpg" -o -name "*.jpeg" \) | \
  xargs -P4 -I{} sh -c 'avifenc --quality 50 --speed 6 --jobs 4 "{}" "${1%.*}.avif"' _ {}
```

### Mixed format batch (route by extension)

```bash
mkdir -p optimized
for f in images/*; do
  ext="${f##*.}"
  base="optimized/$(basename "$f")"
  case "${ext,,}" in
    jpg|jpeg) jpegoptim --max=85 --strip-all --all-progressive --dest=./optimized/ "$f" ;;
    png)
      cp "$f" "$base"
      pngquant --quality 65-80 --speed 1 --force --ext .png "$base"
      oxipng -o 3 -i 0 --strip safe "$base" ;;
    gif)  gifsicle -O3 --lossy=80 "$f" -o "$base" ;;
    webp) cwebp -q 85 -mt -strip "$f" -o "$base" ;;
  esac
done
```

### Before/after size reporting

```bash
# Report savings for a single file
before=$(stat -f%z "$input" 2>/dev/null || stat -c%s "$input")
# ... run compression command ...
after=$(stat -f%z "$output" 2>/dev/null || stat -c%s "$output")
echo "${input}: ${before} -> ${after} bytes ($(( (before - after) * 100 / before ))% saved)"
```

---

## Cross-Reference

For video compression (H.264, H.265, AV1, VP9), see `video-compression.md`.

For audio compression (MP3, AAC, Opus, FLAC), see `audio-compression.md`.

For PDF compression (Ghostscript, qpdf), see `pdf-compression.md`.

For tool installation and availability checks, see `tool-setup.md`.
