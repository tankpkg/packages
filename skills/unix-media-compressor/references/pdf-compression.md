# PDF Compression

Sources: Ghostscript official docs, Transloadit Ghostscript CLI guide, qpdf documentation

Ghostscript re-renders the PDF through its interpreter and recompresses all content. It can
dramatically reduce file size by downsampling images, subsetting fonts, and removing redundant
data, but it cannot make already-optimized or text-only PDFs smaller.

---

## Quality Preset Overview

| Preset | DPI | Use Case | Typical Size Reduction |
|---|---|---|---|
| `/screen` | 72 | Screen viewing only, email attachments | 70-90% |
| `/ebook` | 150 | General sharing, tablets, web download | 50-75% |
| `/printer` | 300 | Desktop printing, office documents | 20-40% |
| `/prepress` | 300 + ICC | Commercial printing, color-critical work | 10-25% |

Percentages apply to image-heavy PDFs. Text-only PDFs may see little or no reduction.

**Default recommendation: `/ebook`** — 150 DPI balances quality and size for everyday use.
Use `/screen` only when file size is the absolute priority and print quality is irrelevant.

---

## Ghostscript Core Command

```bash
gs \
  -sDEVICE=pdfwrite \
  -dCompatibilityLevel=1.4 \
  -dPDFSETTINGS=/ebook \
  -dNOPAUSE \
  -dQUIET \
  -dBATCH \
  -sOutputFile=output.pdf \
  input.pdf
```

Flag breakdown:

| Flag | Purpose |
|---|---|
| `-sDEVICE=pdfwrite` | Output device: write a PDF file |
| `-dCompatibilityLevel=1.4` | PDF version; 1.4 is widely compatible, 2.0 enables better compression |
| `-dPDFSETTINGS=/ebook` | Quality preset controlling DPI and compression aggressiveness |
| `-dNOPAUSE` | Do not pause between pages (required for batch/scripted use) |
| `-dQUIET` | Suppress informational output to stderr |
| `-dBATCH` | Exit after processing; do not wait for more input |
| `-sOutputFile=output.pdf` | Destination file path |

Flag order matters: `-sOutputFile` and `-sDEVICE` must appear before the input file.

---

## Quality Preset Recipes

### /screen — Maximum compression, screen only

```bash
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/screen \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=output-screen.pdf input.pdf
```

72 DPI. Text stays sharp; photos blur when zoomed. Not suitable for printing.

### /ebook — Recommended default

```bash
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=output-ebook.pdf input.pdf
```

150 DPI. Good for sharing, tablets, and casual printing. The right choice for most situations.

### /printer — Print quality

```bash
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/printer \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=output-printer.pdf input.pdf
```

300 DPI. Smaller reduction than `/ebook` but preserves detail for printed output.

### /prepress — Commercial print

```bash
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/prepress \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=output-prepress.pdf input.pdf
```

300 DPI with ICC color profile preservation. Least compression of all presets. Use only for
professional print workflows where color accuracy is critical.

---

## Advanced Optimization Flags

Add any of these to a preset command for additional size reduction.

### Duplicate image detection

```bash
-dDetectDuplicateImages=true
```

Detects identical images embedded multiple times and replaces duplicates with references to a
single copy. Effective for template-based PDFs where the same logo appears on every page.

### Font compression and subsetting

```bash
-dCompressFonts=true \
-dSubsetFonts=true
```

`-dCompressFonts=true` compresses embedded font data. `-dSubsetFonts=true` removes unused
glyphs from embedded fonts — if a PDF embeds a full font family but only uses 40 characters,
subsetting discards the other 200+ glyphs. This can save several megabytes in documents that
embed large CJK or decorative fonts.

### Remove unused resources

```bash
-dRemoveUnusedResources=true
```

Strips resources (fonts, images, color profiles) that are defined in the PDF but never
referenced by any page content. Common in PDFs exported from design tools.

### Custom DPI control

Override the DPI set by the preset for more precise control:

```bash
-dColorImageResolution=150 \
-dGrayImageResolution=150 \
-dMonoImageResolution=300
```

Monochrome (black and white bitmap) images tolerate higher DPI without significant size cost,
so 300 DPI preserves sharpness for scanned text and line art. To use custom DPI without a
preset, omit `-dPDFSETTINGS` and set all three resolution flags manually.

---

## Maximum Compression Recipe

Smallest possible output. Use when the PDF contains images, repeated graphics, or embedded fonts.

```bash
gs -sDEVICE=pdfwrite \
   -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/screen \
   -dNOPAUSE -dQUIET -dBATCH \
   -dDetectDuplicateImages=true \
   -dCompressFonts=true \
   -dSubsetFonts=true \
   -dRemoveUnusedResources=true \
   -dColorImageResolution=72 \
   -dGrayImageResolution=72 \
   -dMonoImageResolution=150 \
   -sOutputFile=output-max.pdf \
   input.pdf
```

For slightly better quality at still-aggressive compression, swap `/screen` for `/ebook` and
set color/gray resolution to 120.

---

## qpdf — Web Optimization and Stream Compression

qpdf is a structural PDF transformer, not a re-renderer. It does not downsample images or
re-encode content — it reorganizes PDF structure and applies lossless stream compression.

### Linearization (fast web view)

```bash
qpdf --linearize input.pdf output-web.pdf
```

Reorganizes the PDF so the first page displays before the full file downloads. Does not reduce
file size significantly, but improves perceived load time for PDFs served over HTTP. Apply as
a post-processing step after Ghostscript compression.

### Stream compression

```bash
qpdf --compress-streams=y input.pdf output.pdf
```

Applies zlib compression to uncompressed streams. Effective on PDFs assembled by older tools
that skip compression.

### Object stream generation

```bash
qpdf --object-streams=generate input.pdf output.pdf
```

Packs multiple PDF objects into compressed object streams (PDF 1.5+ output). Combine with
linearization:

```bash
qpdf --linearize --compress-streams=y --object-streams=generate \
     input.pdf output-optimized.pdf
```

### Combined Ghostscript + qpdf pipeline

```bash
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -dDetectDuplicateImages=true -dCompressFonts=true -dSubsetFonts=true \
   -sOutputFile=tmp-compressed.pdf input.pdf
qpdf --linearize --compress-streams=y tmp-compressed.pdf output-final.pdf
rm tmp-compressed.pdf
```

---

## Batch PDF Compression

### Loop over all PDFs in a folder

```bash
for f in *.pdf; do
  gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
     -dNOPAUSE -dQUIET -dBATCH \
     -dDetectDuplicateImages=true -dCompressFonts=true -dSubsetFonts=true \
     -sOutputFile="${f%.pdf}-compressed.pdf" "$f"
done
```

Writes `document-compressed.pdf` alongside each `document.pdf`. `${f%.pdf}` strips the
extension before appending the suffix.

### Shell function for reuse

```bash
compress_pdf() {
  local input="$1"
  local output="${2:-${input%.pdf}-compressed.pdf}"
  local preset="${3:-/ebook}"
  gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS="$preset" \
     -dNOPAUSE -dQUIET -dBATCH \
     -dDetectDuplicateImages=true -dCompressFonts=true -dSubsetFonts=true \
     -sOutputFile="$output" "$input"
  echo "Compressed: $input -> $output"
}
# compress_pdf report.pdf
# compress_pdf report.pdf report-small.pdf /screen
```

Add to `~/.bashrc` or `~/.zshrc` for persistent availability.

---

## Quality Tier Mapping

Map user-facing language to Ghostscript presets:

| User Request | Ghostscript Preset | Notes |
|---|---|---|
| "web", "email", "small", "maximum" | `/screen` | 72 DPI, aggressive |
| "balanced", "default", "normal" | `/ebook` | 150 DPI, recommended |
| "quality", "print", "high" | `/printer` | 300 DPI, moderate reduction |
| "professional", "commercial", "prepress" | `/prepress` | 300 DPI + color profiles |

---

## Real-World Results

Typical outcomes. Results vary significantly based on original content.

| Document Type | Original Size | /screen | /ebook | /printer |
|---|---|---|---|---|
| Image-heavy report (photos) | 25 MB | 2.5 MB | 5 MB | 12 MB |
| Scanned document (300 DPI scan) | 8 MB | 0.9 MB | 1.8 MB | 4 MB |
| Mixed (charts + text) | 5 MB | 0.8 MB | 1.5 MB | 3 MB |
| Text-only (no images) | 1.2 MB | 1.0 MB | 1.1 MB | 1.15 MB |
| Already-optimized PDF | 800 KB | 850 KB | 820 KB | 810 KB |

The last two rows show the key limitation: Ghostscript cannot compress what is already compact.
Already-optimized PDFs may grow slightly due to re-encoding overhead.

---

## Troubleshooting

### Output is larger than input

Ghostscript re-encodes everything, including already-compressed content. Common causes:
- Text-only PDFs (no images to downsample)
- PDFs already processed by Ghostscript
- PDFs with very few pages

If the input is under 500 KB, compression is unlikely to help. Compare sizes before replacing:

```bash
ls -lh input.pdf output.pdf
```

If output is larger, discard it and keep the original.

### Font rendering issues after compression

Symptoms: garbled characters, missing glyphs, substituted fonts.

`-dSubsetFonts=true` occasionally causes issues with non-standard font embeddings. Disable it
as a first diagnostic step:

```bash
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -dSubsetFonts=false \
   -sOutputFile=output.pdf input.pdf
```

### Color space problems

`/prepress` preserves ICC profiles; other presets may convert or discard them. If color
accuracy matters, use `/prepress` or add `-dUseCIEColor=false`.

### Errors on encrypted PDFs

Ghostscript cannot process password-protected PDFs. Decrypt first with qpdf:

```bash
qpdf --decrypt --password="owner-password" input.pdf decrypted.pdf
# Then compress the decrypted file
gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=output.pdf decrypted.pdf
rm decrypted.pdf
```

### Slow processing on large PDFs

Ghostscript processes PDFs page by page. A 500-page document with high-resolution images can
take several minutes — expected behavior. No parallel processing option exists.

---

For tool installation and availability checks, see `tool-setup.md`.

For image compression (JPEG, PNG, WebP, AVIF), see `image-compression.md`.
