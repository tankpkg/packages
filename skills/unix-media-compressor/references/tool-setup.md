# Tool Setup and Operations

Sources: Homebrew docs, Debian/Ubuntu package repositories, tool official documentation

---

## Tool Inventory

| Tool | Compresses | Check Command | Status |
|------|-----------|---------------|--------|
| ffmpeg | video, audio, images (WebP, AVIF, PNG, JPEG) | `ffmpeg -version` | Required |
| gs (ghostscript) | PDF | `gs --version` | Required |
| cwebp | PNG/JPEG → WebP | `cwebp -version` | Recommended |
| avifenc | PNG/JPEG → AVIF | `avifenc --version` | Recommended |
| pngquant | PNG (lossy palette reduction) | `pngquant --version` | Recommended |
| oxipng | PNG (lossless re-encoding) | `oxipng --version` | Recommended |
| jpegoptim | JPEG (lossy or lossless strip) | `jpegoptim --version` | Recommended |
| zstd | archives (tar.zst) | `zstd --version` | Recommended |
| gifsicle | GIF | `gifsicle --version` | Optional |
| optipng | PNG (lossless, slower than oxipng) | `optipng --version` | Optional |
| pigz | gzip archives (parallel) | `pigz --version` | Optional |
| pbzip2 | bzip2 archives (parallel) | `pbzip2 --version` | Optional |
| brotli | web assets (.br) | `brotli --version` | Optional |
| 7z | archives (highest ratio) | `7z i` | Optional |
| qpdf | PDF (linearize, stream compress) | `qpdf --version` | Optional |

---

## Detection

Check whether a tool is available before invoking it:

```bash
command -v ffmpeg &>/dev/null && echo "found" || echo "missing"
```

Check all required tools and collect missing ones:

```bash
check_tools() {
    local missing=()
    for tool in ffmpeg gs; do
        command -v "$tool" &>/dev/null || missing+=("$tool")
    done
    [[ ${#missing[@]} -gt 0 ]] && { echo "Missing: ${missing[*]}" >&2; return 1; }
}
```

Report which optional tools are available:

```bash
for tool in cwebp avifenc pngquant oxipng jpegoptim zstd gifsicle optipng pigz pbzip2 brotli 7z qpdf; do
    command -v "$tool" &>/dev/null && echo "[x] $tool" || echo "[ ] $tool"
done
```

Version check patterns for non-standard flags:

```bash
ffmpeg -version 2>&1 | head -1     # ffmpeg version 6.x ...
gs --version                        # 10.x.x
7z i 2>&1 | grep "7-Zip"           # 7-Zip 23.x ...
```

---

## macOS Installation (Homebrew)

Install individually as needed:

```bash
brew install ffmpeg          # Required
brew install ghostscript     # Required
brew install webp            # cwebp + dwebp
brew install libavif         # avifenc + avifdec
brew install pngquant
brew install oxipng
brew install jpegoptim
brew install zstd
brew install gifsicle
brew install optipng
brew install pigz
brew install pbzip2
brew install brotli
brew install p7zip           # provides 7z
brew install qpdf
```

Install everything at once:

```bash
brew install ffmpeg ghostscript webp libavif pngquant oxipng jpegoptim zstd gifsicle optipng pigz pbzip2 brotli p7zip qpdf
```

If tools are not found after install, confirm Homebrew is on your PATH:

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"   # Apple Silicon
```

---

## Linux Installation (Debian/Ubuntu)

Install individually:

```bash
sudo apt install ffmpeg ghostscript webp libavif-bin pngquant jpegoptim optipng gifsicle zstd pigz pbzip2 brotli p7zip-full qpdf
```

Install everything available via apt at once:

```bash
sudo apt install ffmpeg ghostscript webp libavif-bin pngquant jpegoptim optipng gifsicle zstd pigz pbzip2 brotli p7zip-full qpdf
```

oxipng is not in standard apt repositories. Install via Cargo:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
cargo install oxipng
```

---

## Minimal vs Full Install

**Minimal** — two tools cover the most common tasks:

- `ffmpeg` — video, audio, and image format conversion (WebP, AVIF, JPEG)
- `gs` — PDF compression

**Recommended additions** — each fills a gap ffmpeg alone cannot match:

- `pngquant` + `oxipng` — PNG pipeline; pngquant reduces palette (lossy), oxipng re-encodes losslessly. Together they outperform ffmpeg for PNG.
- `jpegoptim` — strips JPEG metadata and applies targeted quality reduction without full re-encode.
- `cwebp` / `avifenc` — finer control over WebP/AVIF encoding than ffmpeg's output.
- `zstd` — fast archive compression with excellent ratio; preferred over gzip for new archives.

**Optional** — situational:

- `gifsicle` — the only reliable tool for GIF optimization.
- `pigz` / `pbzip2` — parallel gzip/bzip2; useful for large archives on multi-core machines.
- `brotli` — web asset pre-compression for servers that serve `.br` files.
- `7z` — highest compression ratio; slow, useful for archival storage.
- `qpdf` — PDF linearization; complements ghostscript for web-optimized PDFs.

---

## Before/After Size Comparison

`stat` syntax differs between macOS and Linux; use a fallback:

```bash
original_size=$(stat -f%z "$input" 2>/dev/null || stat -c%s "$input")
# ... compress ...
new_size=$(stat -f%z "$output" 2>/dev/null || stat -c%s "$output")
reduction=$(( (original_size - new_size) * 100 / original_size ))
echo "  ${original_size} → ${new_size} bytes (${reduction}% reduction)"
```

Accumulate totals across a batch:

```bash
total_original=0; total_new=0

# After each file:
total_original=$(( total_original + orig ))
total_new=$(( total_new + new ))

# Summary:
total_reduction=$(( (total_original - total_new) * 100 / total_original ))
echo "Total: $(numfmt --to=iec $total_original) → $(numfmt --to=iec $total_new) (${total_reduction}% reduction)"
```

---

## Batch Processing Patterns

**find + xargs** — parallel processing with `-P`:

```bash
find . -name "*.jpg" -print0 | xargs -0 -P4 -I{} jpegoptim --max=85 {}
find . -name "*.png" -print0 | xargs -0 -P4 -I{} pngquant --quality 65-80 --force --ext .png {}
```

**bash for loop** — control over input/output paths:

```bash
for f in *.mp4; do
    ffmpeg -i "$f" -crf 28 -preset slow "${f%.mp4}-compressed.mp4"
done
```

**GNU parallel** — best throughput, built-in progress:

```bash
find . -name "*.png" | parallel --progress pngquant --quality 65-80 --force --ext .png {}
find . -name "*.mp4" | parallel -j2 ffmpeg -i {} -crf 28 {.}-compressed.mp4
```

**Recursive with preserved directory structure**:

```bash
input_dir="./originals"; output_dir="./compressed"
find "$input_dir" -name "*.jpg" | while read -r file; do
    relative="${file#$input_dir/}"
    out="$output_dir/$relative"
    mkdir -p "$(dirname "$out")"
    jpegoptim --max=85 --dest="$(dirname "$out")" "$file"
done
```

---

## Progress and Reporting

Counter during batch:

```bash
files=( $(find . -name "*.png") )
total=${#files[@]}; count=0
for f in "${files[@]}"; do
    count=$(( count + 1 ))
    printf "[%d/%d] %s\n" "$count" "$total" "$f"
    pngquant --quality 65-80 --force --ext .png "$f"
done
```

Summary after completion:

```bash
echo "Processed: $count files"
echo "Skipped:   $skipped files"
echo "Total saved: $(numfmt --to=iec $(( total_original - total_new )))"
echo "Reduction:   ${total_reduction}%"
```

---

## Safety: Preserving Originals

**Output to a new file** (safest — original untouched):

```bash
ffmpeg -i input.mp4 -crf 28 output.mp4
cwebp -q 80 input.png -o output.webp
```

**Output to a separate directory**:

```bash
jpegoptim --max=85 --dest=./compressed/ input.jpg
```

**In-place with backup and size check** (restore if compression made it larger):

```bash
cp "$f" "${f}.bak"
pngquant --quality 65-80 --force --ext .png "$f"
new=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f")
orig=$(stat -f%z "${f}.bak" 2>/dev/null || stat -c%s "${f}.bak")
[[ $new -lt $orig ]] && rm "${f}.bak" || mv "${f}.bak" "$f"
```

**Skip if output already exists** (idempotent batch runs):

```bash
[[ -f "$out" ]] && continue
```

---

## Common Issues

**Tool not found after installation**

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"   # Homebrew (Apple Silicon)
source "$HOME/.cargo/env"                   # Cargo (oxipng)
which ffmpeg                                # verify
```

**brew or apt ships an outdated ffmpeg** (missing AV1, AVIF codecs)

```bash
ffmpeg -version 2>&1 | head -1
ffmpeg -codecs 2>/dev/null | grep -E "hevc|av1|vp9"
# macOS: brew upgrade ffmpeg
# Ubuntu: sudo add-apt-repository ppa:savoury1/ffmpeg4 && sudo apt update && sudo apt install ffmpeg
```

**ghostscript produces a larger file than the input**

Already-optimized PDFs or vector-heavy PDFs can grow. Check before keeping:

```bash
[[ $new_size -lt $original_size ]] || cp "$input" "$output"
```

**pngquant refuses to overwrite**

Always pass `--force` in batch scripts:

```bash
pngquant --quality 65-80 --force --ext .png "$f"
```

**oxipng not found on Linux**

Install via Cargo (see Linux Installation section), or fall back to optipng:

```bash
command -v oxipng &>/dev/null \
    && oxipng -o 3 -i 0 --strip safe "$f" \
    || optipng -o5 -strip all "$f"
```

**Permission denied on output directory**

```bash
mkdir -p "$output_dir" && chmod 755 "$output_dir"
```

---

For domain-specific compression commands, see `image-compression.md`, `video-compression.md`, `audio-compression.md`, `pdf-compression.md`, and `archive-formats.md`.
