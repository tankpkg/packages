# Video Compression

Sources: FFmpeg official docs (2025-2026), Ozer (Video Encoding by the Numbers), ffmpeg.party AV1 guide

---

## Codec Selection

Pick a codec based on where the file lands, not personal preference. Compatibility beats compression when in doubt.

| Codec | Encoder | Compression vs H.264 | Compatibility | Best For |
|-------|---------|----------------------|---------------|----------|
| H.264/AVC | libx264 | Baseline | Universal | Web delivery, streaming, broad device support |
| H.265/HEVC | libx265 | ~50% smaller | Broad (not all browsers) | 4K, bandwidth-constrained delivery, Apple ecosystem |
| AV1 | libsvtav1 | ~30% smaller than H.265 | Modern browsers, growing | Web-first content, YouTube, long-term storage |

**Decision rule:** H.264 when you need it to play everywhere. H.265 when you need smaller files and control the playback environment. AV1 when encode time is acceptable and the target is a modern browser or streaming platform.

---

## CRF Reference

CRF (Constant Rate Factor) encodes to a target quality level rather than a target bitrate. Lower values produce higher quality and larger files. This is the right default for compression work — use two-pass only when a specific file size or bitrate is required.

| Quality Tier | libx264 CRF | libx265 CRF | libsvtav1 CRF | Notes |
|--------------|-------------|-------------|---------------|-------|
| Web (small file) | 28–32 | 32–36 | 38–45 | Acceptable quality, smallest size |
| Balanced | 23–27 | 28–31 | 30–37 | Default range, good quality/size tradeoff |
| Quality | 18–22 | 22–27 | 22–29 | High quality, larger files |
| Visually lossless | 17–18 | 20–22 | 18–22 | Near-transparent, archival use |

Defaults: x264 CRF 23, x265 CRF 28, SVT-AV1 CRF 30. Start here and adjust based on output size.

---

## H.264 Recipes

H.264 is the safe default. `-pix_fmt yuv420p` is required for compatibility — some sources default to yuv444p or yuv422p which many decoders reject. `-movflags +faststart` moves the MP4 index to the front of the file so browsers can begin playback before the full download completes.

### Web (small file, broad compatibility)

```bash
ffmpeg -i input.mp4 \
  -c:v libx264 -crf 28 -preset fast \
  -pix_fmt yuv420p \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output.mp4
```

### Balanced (default, most content)

```bash
ffmpeg -i input.mp4 \
  -c:v libx264 -crf 23 -preset medium \
  -pix_fmt yuv420p \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output.mp4
```

### Quality (high fidelity, larger file)

```bash
ffmpeg -i input.mp4 \
  -c:v libx264 -crf 18 -preset slow \
  -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  output.mp4
```

### Visually lossless (archival, source preservation)

```bash
ffmpeg -i input.mp4 \
  -c:v libx264 -crf 17 -preset veryslow \
  -pix_fmt yuv420p \
  -c:a aac -b:a 256k \
  -movflags +faststart \
  output.mp4
```

---

## H.265 Recipes

H.265 produces files roughly 50% smaller than H.264 at equivalent quality. `-tag:v hvc1` is required for Apple devices — without it, QuickTime and iOS refuse to play the file even though the codec is supported.

### Web (small file)

```bash
ffmpeg -i input.mp4 \
  -c:v libx265 -crf 32 -preset fast \
  -pix_fmt yuv420p \
  -tag:v hvc1 \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output.mp4
```

### Balanced (default)

```bash
ffmpeg -i input.mp4 \
  -c:v libx265 -crf 28 -preset medium \
  -pix_fmt yuv420p \
  -tag:v hvc1 \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output.mp4
```

### Quality

```bash
ffmpeg -i input.mp4 \
  -c:v libx265 -crf 22 -preset slow \
  -pix_fmt yuv420p \
  -tag:v hvc1 \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  output.mp4
```

### Visually lossless (10-bit, archival)

```bash
ffmpeg -i input.mp4 \
  -c:v libx265 -crf 20 -preset veryslow \
  -pix_fmt yuv420p10le \
  -tag:v hvc1 \
  -c:a aac -b:a 256k \
  -movflags +faststart \
  output.mp4
```

Use `yuv420p10le` for 10-bit output — better for HDR sources and archival. Use `yuv420p` for standard 8-bit delivery.

---

## AV1 Recipes

SVT-AV1 (`libsvtav1`) is the practical AV1 encoder — significantly faster than `libaom-av1` with comparable quality. The `-svtav1-params` string controls scene detection, keyframe interval, and quality tuning.

**Key params:** `keyint=10s` = keyframe every 10s; `tune=0` = visual quality; `enable-overlays=1` = better scene boundaries; `scd=1` = scene change detection; `scm=0` = off for natural video (set 1 for screencasts).

### Web (small file)

```bash
ffmpeg -i input.mp4 \
  -c:v libsvtav1 -crf 40 -preset 8 \
  -svtav1-params keyint=10s:tune=0:enable-overlays=1:scd=1:scm=0 \
  -pix_fmt yuv420p \
  -c:a libopus -b:a 96k \
  output.mp4
```

### Balanced (default)

```bash
ffmpeg -i input.mp4 \
  -c:v libsvtav1 -crf 30 -preset 6 \
  -svtav1-params keyint=10s:tune=0:enable-overlays=1:scd=1:scm=0 \
  -pix_fmt yuv420p \
  -c:a libopus -b:a 128k \
  output.mp4
```

### Quality

```bash
ffmpeg -i input.mp4 \
  -c:v libsvtav1 -crf 22 -preset 4 \
  -svtav1-params keyint=10s:tune=0:enable-overlays=1:scd=1:scm=0 \
  -pix_fmt yuv420p \
  -c:a libopus -b:a 192k \
  output.mp4
```

### Visually lossless (slow, archival)

```bash
ffmpeg -i input.mp4 \
  -c:v libsvtav1 -crf 18 -preset 2 \
  -svtav1-params keyint=10s:tune=0:enable-overlays=1:scd=1:scm=0 \
  -pix_fmt yuv420p10le \
  -c:a libopus -b:a 256k \
  output.mp4
```

AV1 in MP4 has broad support in modern browsers. Use `.webm` with `-c:a libopus` for WebM delivery.

---

## Preset Reference

Presets trade encode time for compression efficiency. A slower preset produces a smaller file at the same CRF value — it does not change visual quality, only how efficiently the encoder finds redundancy.

### x264 / x265 Presets

| Preset | Relative Speed | File Size vs medium | Typical Use |
|--------|---------------|---------------------|-------------|
| ultrafast | ~10× faster | ~30% larger | Testing, live encoding |
| superfast | ~7× faster | ~25% larger | Near-live |
| veryfast | ~4× faster | ~15% larger | Fast batch jobs |
| faster | ~2× faster | ~8% larger | General batch |
| fast | ~1.5× faster | ~4% larger | General batch |
| medium | 1× (baseline) | Baseline | Default |
| slow | ~2× slower | ~5% smaller | High-quality delivery |
| slower | ~4× slower | ~8% smaller | Archival, distribution |
| veryslow | ~8× slower | ~12% smaller | Maximum compression |

For most compression work, `medium` or `fast` is the right choice. `slow` is worth it for final delivery. `veryslow` rarely justifies the encode time.

### SVT-AV1 Presets (0–13)

| Preset | Speed | Quality | Use |
|--------|-------|---------|-----|
| 0–1 | Very slow | Best | Research, archival |
| 2–3 | Slow | High | High-quality delivery |
| 4–5 | Moderate | Good | Quality batch |
| 6–7 | Balanced | Good | Default range |
| 8–9 | Fast | Acceptable | Fast batch |
| 10–11 | Very fast | Lower | Quick previews |
| 12–13 | Fastest | Lowest | Real-time only |

Preset 6 is the practical default. Preset 4 for quality-focused work. Preset 8–9 for fast batch jobs.

---

## Resolution Scaling

Scale video during compression to reduce file size further. The `-vf scale` filter handles this. Use `-2` for the auto-calculated dimension to ensure it stays divisible by 2 (required by most codecs).

```bash
# Scale to 1080p width, auto height
ffmpeg -i input.mp4 -vf scale=1920:-2 -c:v libx264 -crf 23 -preset medium output.mp4

# Scale to 720p width, auto height
ffmpeg -i input.mp4 -vf scale=1280:-2 -c:v libx264 -crf 23 -preset medium output.mp4

# Scale to 480p width, auto height
ffmpeg -i input.mp4 -vf scale=854:-2 -c:v libx264 -crf 23 -preset medium output.mp4

# Scale by height (e.g., 1080p height)
ffmpeg -i input.mp4 -vf scale=-2:1080 -c:v libx264 -crf 23 -preset medium output.mp4
```

### Downscale-Only Pattern

Avoid upscaling — it increases file size without improving quality. Use `min()` expressions to skip scaling when the source is already smaller than the target:

```bash
# Downscale to 1080p only if source is larger; pass through if already smaller
ffmpeg -i input.mp4 \
  -vf "scale='min(1920,iw)':'min(1080,ih)':force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2" \
  -c:v libx264 -crf 23 -preset medium \
  -pix_fmt yuv420p -movflags +faststart \
  output.mp4
```

The `trunc(iw/2)*2` expression ensures width and height are always even numbers, which libx264 requires.

---

## Two-Pass Encoding

Use two-pass when you need to hit a specific file size or bitrate target — for example, a 50 MB upload limit or a streaming platform's ingest spec. CRF is simpler and usually better for general compression; two-pass is for constrained delivery.

Pass 1 analyzes the video and writes statistics. Pass 2 uses those statistics to distribute bits optimally.

### x264 Two-Pass

```bash
ffmpeg -i input.mp4 -c:v libx264 -b:v 2000k -pass 1 -an -f null /dev/null
ffmpeg -i input.mp4 -c:v libx264 -b:v 2000k -pass 2 \
  -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart output.mp4
```

### x265 Two-Pass

x265 uses `-x265-params` for pass control rather than the standard `-pass` flag:

```bash
ffmpeg -i input.mp4 -c:v libx265 -b:v 1500k -x265-params pass=1 -an -f null /dev/null
ffmpeg -i input.mp4 -c:v libx265 -b:v 1500k -x265-params pass=2 \
  -pix_fmt yuv420p -tag:v hvc1 -c:a aac -b:a 128k -movflags +faststart output.mp4
```

Clean up stats after encoding: `rm -f ffmpeg2pass-0.log ffmpeg2pass-0.log.mbtree x265_2pass.log x265_2pass.log.cutree`

---

## Hardware Acceleration

Hardware encoders are faster than software but produce slightly larger files at equivalent quality. Use when encode speed matters more than maximum compression.

### VideoToolbox (macOS)

Apple Silicon and Intel Macs both support VideoToolbox. Quality uses `-q:v` (0–100, higher = better) rather than CRF.

```bash
# H.264 via VideoToolbox
ffmpeg -i input.mp4 \
  -c:v h264_videotoolbox -q:v 65 \
  -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  output.mp4

# H.265 via VideoToolbox
ffmpeg -i input.mp4 \
  -c:v hevc_videotoolbox -q:v 65 \
  -tag:v hvc1 \
  -c:a aac -b:a 128k -movflags +faststart \
  output.mp4
```

### NVENC (NVIDIA)

NVENC uses `-cq` for quality control (similar to CRF, lower = better quality).

```bash
# H.264 via NVENC
ffmpeg -i input.mp4 \
  -c:v h264_nvenc -cq 23 -preset p4 \
  -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart \
  output.mp4

# H.265 via NVENC
ffmpeg -i input.mp4 \
  -c:v hevc_nvenc -cq 28 -preset p4 \
  -tag:v hvc1 \
  -c:a aac -b:a 128k -movflags +faststart \
  output.mp4
```

NVENC presets: `p1` (fastest) through `p7` (slowest/best). `p4` is a reasonable default.

### VAAPI (Linux/Intel/AMD)

VAAPI requires specifying the render device. Quality uses `-qp` (lower = better).

```bash
# H.264 via VAAPI
ffmpeg -vaapi_device /dev/dri/renderD128 \
  -i input.mp4 \
  -vf 'format=nv12,hwupload' \
  -c:v h264_vaapi -qp 23 \
  -c:a aac -b:a 128k -movflags +faststart \
  output.mp4
```

Check available render devices with `ls /dev/dri/`. Use `renderD128` as the default; increment if multiple GPUs are present.

---

## Audio Handling

### Passthrough (no re-encode)

Copy audio without re-encoding when the source is already AAC/MP3 at acceptable quality. Faster and avoids generation loss.

```bash
ffmpeg -i input.mp4 -c:v libx264 -crf 23 -preset medium \
  -pix_fmt yuv420p -c:a copy -movflags +faststart output.mp4
```

### Re-encode Audio

Re-encode when the source codec is incompatible with the output container, or when reducing audio bitrate is part of the size goal.

```bash
-c:a aac -b:a 128k          # standard web (MP4)
-c:a aac -b:a 192k          # high quality (MP4)
-c:a libopus -b:a 128k      # WebM / AV1 (preferred)
-c:a aac -b:a 192k -ac 2    # stereo downmix from surround
```

**Pairing rules:** MP4 + H.264/H.265 → AAC. WebM + AV1 → Opus. Opus is more efficient than AAC at equivalent bitrates, especially below 128k.

For audio-only compression (MP3, AAC, Opus, FLAC), see `audio-compression.md`.

---

## Batch Video Compression

### Sequential bash loop

```bash
for f in *.mp4; do
  ffmpeg -i "$f" \
    -c:v libx264 -crf 23 -preset medium \
    -pix_fmt yuv420p \
    -c:a aac -b:a 128k \
    -movflags +faststart \
    "compressed_${f}"
done
```

### Parallel processing with GNU parallel

Process multiple files simultaneously. Limit jobs to avoid saturating CPU — a good default is half the available cores.

```bash
# Install: brew install parallel (macOS) / apt install parallel (Linux)

ls *.mp4 | parallel -j4 \
  ffmpeg -i {} \
    -c:v libx264 -crf 23 -preset medium \
    -pix_fmt yuv420p \
    -c:a aac -b:a 128k \
    -movflags +faststart \
    compressed_{.}.mp4
```

`{.}` strips the extension from the input filename. `-j4` runs 4 jobs in parallel.

### Recursive batch (subdirectories)

```bash
find . -name "*.mp4" -type f | while read -r f; do
  dir=$(dirname "$f")
  base=$(basename "$f" .mp4)
  ffmpeg -i "$f" -c:v libx264 -crf 23 -preset medium \
    -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart \
    "${dir}/compressed_${base}.mp4"
done
```

---

## Quick Reference: Common Scenarios

| Goal | Codec | CRF | Preset | Extra Flags |
|------|-------|-----|--------|-------------|
| Shrink MP4 for web | libx264 | 28 | fast | `-pix_fmt yuv420p -movflags +faststart` |
| Best quality/size ratio | libx265 | 28 | medium | `-pix_fmt yuv420p -tag:v hvc1 -movflags +faststart` |
| Maximum compression, modern browser | libsvtav1 | 35 | 6 | `-svtav1-params keyint=10s:tune=0:enable-overlays=1:scd=1:scm=0` |
| Fast encode (testing) | libx264 | 23 | ultrafast | `-pix_fmt yuv420p` |
| Apple device delivery | libx265 | 28 | medium | `-tag:v hvc1 -pix_fmt yuv420p` |
| Archival (lossless-ish) | libx264 | 17 | veryslow | `-pix_fmt yuv420p` |
| 4K downscale to 1080p | libx265 | 26 | slow | `-vf scale=1920:-2 -tag:v hvc1` |

---

For audio-only compression (MP3, AAC, Opus, FLAC files), see `audio-compression.md`.
