# Audio Compression

Sources: FFmpeg official docs, Xiph.org Opus Recommended Settings, EBU R128 standard

---

## Codec Decision Guide

| Codec | Container | Best For | Avoid When |
|-------|-----------|----------|------------|
| Opus (libopus) | OGG, WebM, MKV | Voice, podcast, music streaming, web delivery | Need MP4 container, legacy device support |
| AAC (libfdk_aac / aac) | MP4, M4A, MOV | Apple ecosystem, MP4 video audio, broad compatibility | Lowest bitrate voice (Opus wins there) |
| MP3 (libmp3lame) | MP3 | Legacy players, maximum compatibility, old hardware | Any new project where Opus or AAC is viable |
| FLAC | FLAC, MKV | Archival, lossless backup, source for re-encoding | Distribution, streaming, storage-constrained |

**Key facts:**
- Opus beats AAC and MP3 at equal bitrates — Xiph.org listening tests show Opus at 96k matches AAC at 128k
- AAC is required for MP4 container; browsers and Apple devices expect it
- `libfdk_aac` outperforms the built-in `aac` encoder at bitrates below 128k; use it when available
- MP3 is legacy — only choose it when the target device or platform cannot handle Opus or AAC
- FLAC is lossless; compression level affects encode speed, not audio quality

---

## Quality Tier Reference

| Tier | Opus | AAC (libfdk_aac) | AAC (native) | MP3 (VBR) | MP3 (CBR) | FLAC |
|------|------|-----------------|--------------|-----------|-----------|------|
| Web / small | 64k | 96k | 128k | -q:a 4 (~165k) | 128k | — |
| Balanced | 96–128k | 128k | 192k | -q:a 2 (~190k) | 192k | -compression_level 5 |
| Quality | 160k | 192k | 256k | -q:a 0 (~245k) | 256k | -compression_level 8 |
| Archival / transparent | 192k | 256k | 320k | -q:a 0 (~245k) | 320k | -compression_level 8 |

MP3 VBR scale: 0 = best (~245 kbps), 9 = worst (~45 kbps). `-q:a 2` (~190 kbps) is the standard recommendation for transparent-enough quality.

---

## Opus Recipes

Opus is the best general-purpose lossy codec for new work. Use OGG for standalone audio files, WebM for web video.

**Voice and podcast (24–64k):**

```bash
# Minimum viable voice — phone quality
ffmpeg -i input.wav -c:a libopus -b:a 24k -application voip output.ogg

# Podcast mono — clear speech, small file
ffmpeg -i input.wav -c:a libopus -b:a 32k -application voip -ac 1 output.ogg

# Podcast stereo — good quality
ffmpeg -i input.wav -c:a libopus -b:a 64k -application voip output.ogg
```

`-application voip` tunes the encoder for speech: optimizes for intelligibility over music fidelity.

**Music streaming (96–128k):**

```bash
# Standard music streaming — OGG container
ffmpeg -i input.flac -c:a libopus -b:a 96k output.ogg

# Higher quality music — OGG container
ffmpeg -i input.flac -c:a libopus -b:a 128k output.ogg

# WebM container (for web video or HTML5 audio)
ffmpeg -i input.flac -c:a libopus -b:a 128k output.webm
```

**Transparent (192k):**

```bash
# Perceptually transparent — indistinguishable from lossless in most tests
ffmpeg -i input.flac -c:a libopus -b:a 192k output.ogg

# WebM transparent
ffmpeg -i input.flac -c:a libopus -b:a 192k output.webm
```

---

## AAC Recipes

AAC is the standard for MP4 containers. Use `libfdk_aac` when available; fall back to the built-in `aac` encoder otherwise.

**Check if libfdk_aac is available:**

```bash
ffmpeg -encoders 2>/dev/null | grep fdk
```

**Standard MP4 audio (libfdk_aac):**

```bash
# Balanced — good for most MP4 video audio
ffmpeg -i input.wav -c:a libfdk_aac -b:a 128k output.m4a

# High quality
ffmpeg -i input.wav -c:a libfdk_aac -b:a 192k output.m4a

# VBR mode — 1 (lowest) to 5 (highest); VBR 4 ≈ 128k average
ffmpeg -i input.wav -c:a libfdk_aac -vbr 4 output.m4a
ffmpeg -i input.wav -c:a libfdk_aac -vbr 5 output.m4a
```

**Standard MP4 audio (native aac fallback):**

```bash
# Native aac needs higher bitrate to match libfdk_aac quality
ffmpeg -i input.wav -c:a aac -b:a 192k output.m4a

# High quality native
ffmpeg -i input.wav -c:a aac -b:a 256k output.m4a
```

**HE-AAC for low-bitrate speech (libfdk_aac only):**

```bash
# HE-AAC v2 — 32–64k speech, uses spectral band replication + parametric stereo
ffmpeg -i input.wav -c:a libfdk_aac -profile:a aac_he_v2 -b:a 48k output.m4a
```

Use HE-AAC v2 only for speech at very low bitrates. For music, standard AAC at 128k+ sounds better.

---

## MP3 Recipes

Use MP3 only for legacy compatibility. For any new project, prefer Opus or AAC.

**VBR (recommended for MP3):**

```bash
# Transparent — highest VBR quality (~245 kbps average)
ffmpeg -i input.wav -c:a libmp3lame -q:a 0 output.mp3

# Recommended — good quality, smaller than -q:a 0 (~190 kbps average)
ffmpeg -i input.wav -c:a libmp3lame -q:a 2 output.mp3

# Smaller file — acceptable quality (~165 kbps average)
ffmpeg -i input.wav -c:a libmp3lame -q:a 4 output.mp3
```

**CBR (when exact bitrate is required):**

```bash
# Maximum CBR — legacy players, guaranteed bitrate
ffmpeg -i input.wav -c:a libmp3lame -b:a 320k output.mp3

# Standard CBR
ffmpeg -i input.wav -c:a libmp3lame -b:a 192k output.mp3

# Minimum acceptable CBR
ffmpeg -i input.wav -c:a libmp3lame -b:a 128k output.mp3
```

VBR `-q:a 2` is the standard recommendation: better quality than 192k CBR at similar or smaller file size.

---

## FLAC Recipes

FLAC is lossless — compression level only affects encode speed and file size, never audio quality. Higher levels produce smaller files but take longer to encode.

```bash
# Default compression — fast encode, reasonable size
ffmpeg -i input.wav -c:a flac output.flac

# Maximum compression — slowest encode, smallest lossless file
ffmpeg -i input.wav -c:a flac -compression_level 8 output.flac

# Fast compression — quick encode for large batches
ffmpeg -i input.wav -c:a flac -compression_level 0 output.flac
```

**When to use FLAC:**
- Archiving original recordings before lossy distribution encodes
- Source files for re-encoding to other formats later
- Situations where lossless is contractually or technically required
- Intermediate files in a processing pipeline

**When not to use FLAC:**
- Web delivery (use Opus or AAC)
- Streaming (use Opus or AAC)
- Storage-constrained environments (FLAC is 50–60% of uncompressed WAV, not dramatically smaller)

---

## Extract Audio from Video

**Stream copy — fastest, no quality loss, preserves original codec:**

```bash
# Copy audio stream as-is (output format must match codec)
ffmpeg -i input.mp4 -vn -c:a copy output.aac

# Copy from MKV (may contain various codecs — check first)
ffmpeg -i input.mkv -vn -c:a copy output.mka

# Check what audio codec is in the file before copying
ffmpeg -i input.mp4 2>&1 | grep Audio
```

`-vn` disables video output. `-c:a copy` copies the audio stream without re-encoding. The output container must be compatible with the source codec.

**Re-encode during extraction:**

```bash
# Extract and convert to Opus
ffmpeg -i input.mp4 -vn -c:a libopus -b:a 128k output.ogg

# Extract and convert to MP3
ffmpeg -i input.mp4 -vn -c:a libmp3lame -q:a 2 output.mp3

# Extract to lossless WAV (for editing or archiving)
ffmpeg -i input.mp4 -vn -c:a pcm_s16le output.wav

# Extract specific audio stream (when file has multiple)
ffmpeg -i input.mkv -map 0:a:1 -vn -c:a copy output.ac3
```

Use stream copy when the source codec matches the target. Re-encode when changing format or when the source audio needs quality improvement.

---

## Re-encode Video Audio (Keep Video)

Replace or transcode the audio track while preserving the video stream exactly.

**Keep video, replace audio codec:**

```bash
# Keep video, re-encode audio to AAC (standard for MP4)
ffmpeg -i input.mkv -c:v copy -c:a aac -b:a 192k output.mp4

# Keep video, re-encode audio to libfdk_aac
ffmpeg -i input.mkv -c:v copy -c:a libfdk_aac -b:a 128k output.mp4

# Keep video, re-encode audio to Opus (for MKV or WebM)
ffmpeg -i input.mkv -c:v copy -c:a libopus -b:a 128k output.mkv
```

`-c:v copy` copies the video stream without re-encoding — fast and lossless for the video. Only the audio is processed.

**Replace audio with external file:**

```bash
# Swap audio track entirely
ffmpeg -i video.mp4 -i new_audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k output.mp4
```

`-map 0:v` takes video from the first input, `-map 1:a` takes audio from the second input.

---

## Sample Rate and Channels

**Sample rate (`-ar`):**

```bash
# Downsample to 44.1 kHz (CD quality — sufficient for most audio)
ffmpeg -i input.wav -ar 44100 output.wav

# Downsample to 22.05 kHz (voice, reduces file size further)
ffmpeg -i input.wav -ar 22050 output.wav

# Upsample to 48 kHz (video standard — required for some video containers)
ffmpeg -i input.wav -ar 48000 output.wav
```

Downsampling reduces file size and is appropriate when the source has no meaningful content above the new Nyquist frequency. Voice content above 8 kHz is minimal; 22 kHz sample rate is sufficient for voice-only files.

**Channels (`-ac`):**

```bash
# Stereo to mono — halves file size, appropriate for voice
ffmpeg -i stereo.wav -ac 1 mono.wav

# Mono to stereo (duplicates channel — does not add stereo information)
ffmpeg -i mono.wav -ac 2 stereo.wav

# 5.1 surround to stereo downmix
ffmpeg -i surround.ac3 -ac 2 stereo.wav
```

Use mono (`-ac 1`) for voice recordings, podcasts, and phone audio. Stereo is only meaningful when the source has actual stereo content.

**Combined sample rate and channel reduction for voice:**

```bash
# Podcast-optimized: mono, 22 kHz, Opus voice mode
ffmpeg -i input.wav -ac 1 -ar 22050 -c:a libopus -b:a 32k -application voip output.ogg
```

---

## Batch Audio Compression

**Convert a folder of WAV files to Opus:**

```bash
for f in *.wav; do
  ffmpeg -i "$f" -c:a libopus -b:a 128k "${f%.wav}.ogg"
done
```

**Convert a folder of FLAC files to AAC (MP4):**

```bash
for f in *.flac; do
  ffmpeg -i "$f" -c:a libfdk_aac -b:a 128k "${f%.flac}.m4a"
done
```

**Convert a folder of MP3 files to Opus (re-encode):**

```bash
for f in *.mp3; do
  ffmpeg -i "$f" -c:a libopus -b:a 96k "${f%.mp3}.ogg"
done
```

**Recursive batch — all WAV files in subdirectories:**

```bash
find . -name "*.wav" -exec sh -c '
  out="${1%.wav}.ogg"
  ffmpeg -i "$1" -c:a libopus -b:a 128k "$out"
' _ {} \;
```

**Parallel batch with GNU parallel (faster on multi-core):**

```bash
ls *.flac | parallel ffmpeg -i {} -c:a libopus -b:a 128k {.}.ogg
```

**Batch with output directory:**

```bash
mkdir -p compressed
for f in *.wav; do
  ffmpeg -i "$f" -c:a libopus -b:a 128k "compressed/${f%.wav}.ogg"
done
```

---

## Cross-Reference

For combined video and audio compression in a single pass, see `video-compression.md`. That file covers CRF-based video encoding with simultaneous audio transcoding, container selection, and `-movflags +faststart` for web delivery.

Audio normalization (EBU R128 loudnorm, two-pass measurement) and audio editing operations (mixing, fading, silence removal, EQ) are outside the scope of this file — those are covered in the ffmpeg-mastery skill's `audio-processing.md`.
