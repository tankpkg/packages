# Search Protocol — Trust the User, Never Substitute

Sources: Hugging Face Hub docs, Ollama library conventions, vendor release patterns (Meta, Qwen, Mistral, DeepSeek, Google, xAI, 01.AI, Cohere), observed LLM hallucination modes (2024–2026).

Covers: the exact-string rule, resolution order, zero-result fallback, versioning traps, and the specific failure mode where models "correct" a user's brand-new model name to an older one.

## 1. The Core Rule

**The user typed a model name. That string is ground truth.** Your job is to find what they meant, not to decide what they meant.

The OSS model ecosystem ships new checkpoints weekly. Your training cutoff is months or years behind the user's message. A model you have never heard of is overwhelmingly likely to be a real model that postdates your weights, not a typo or confusion.

### The Failure Mode This Prevents

Real example, every day:

```
User: "Can I run Qwen3-Next-80B on my 4090?"
BAD agent: "I think you mean Qwen2.5-72B. Here is what I know about it..."
GOOD agent: Searches "Qwen3-Next-80B" on HF. Finds Qwen/Qwen3-Next-80B-A3B-Instruct. Answers about that.
```

```
User: "Will Llama 4.5 Maverick fit in 48 GB?"
BAD agent: "Llama 4.5 does not exist. The latest is Llama 3.1. Did you mean Llama-3.1-70B?"
GOOD agent: Searches "Llama 4.5 Maverick". If found, answers. If not, asks for a link — does NOT substitute.
```

```
User: "How fast is DeepSeek-V4 on M3 Ultra?"
BAD agent: "DeepSeek-V3 is the latest…"
GOOD agent: Searches "DeepSeek-V4" verbatim before saying anything.
```

### Why You Hallucinate the Older Version

Your weights encode frequent patterns. Older model names appear thousands of times in training data; a week-old model name appears zero times. The gradient of "what's most likely next?" points at the familiar name. You must consciously override that pull with a search.

## 2. Resolution Order (Do All Of These Before Giving Up)

Search the **exact user string in quotes**, not a normalized version.

| # | Source | URL pattern | What to look for |
| --- | --- | --- | --- |
| 1 | Hugging Face | `https://huggingface.co/models?search=<exact>` | Any repo whose name matches. Favor the vendor's own org. |
| 2 | Hugging Face full-text | `https://huggingface.co/search/full-text?q=<exact>` | Catches models linked from READMEs, quant repos. |
| 3 | Ollama library | `https://ollama.com/library/<lowercase-name>` | Canonical short tag; try with/without version suffix. |
| 4 | Vendor site | Qwen chat, mistral.ai, deepseek.com, ai.meta.com, ai.google.dev, x.ai, cohere.com | Release blog or model card. |
| 5 | GitHub | `https://github.com/search?q=%22<exact>%22&type=repositories` | Inference forks, reference implementations. |
| 6 | Web search | Exact string in double quotes | News, tweets, papers announcing the release. |
| 7 | arXiv | `https://arxiv.org/search/?query=<exact>` | For research releases (e.g. MoE papers). |

### Vendor Org Slugs on Hugging Face

Quick lookup table so you search the right org:

| Vendor | HF org |
| --- | --- |
| Meta (Llama) | `meta-llama` |
| Mistral AI | `mistralai` |
| Qwen (Alibaba) | `Qwen` |
| DeepSeek | `deepseek-ai` |
| Google (Gemma) | `google` |
| Microsoft (Phi) | `microsoft` |
| xAI (Grok) | `xai-org` |
| Cohere | `CohereForAI` |
| Yi (01.AI) | `01-ai` |
| Nous Research | `NousResearch` |
| Hermes | `NousResearch` |
| Teknium | `teknium` |
| Unsloth quants | `unsloth` |
| TheBloke (legacy quants) | `TheBloke` |
| Bartowski (GGUF quants) | `bartowski` |
| MLX community | `mlx-community` |

Common aggregators for quants: `bartowski`, `unsloth`, `lmstudio-community`, `mlx-community`, `turboderp` (EXL2).

## 3. Version Suffix Traps

Versions carry meaning. Never drop them.

| User string | Meaning | Don't confuse with |
| --- | --- | --- |
| `Llama-3.1-70B-Instruct` | July 2024 release | `Llama-3-70B` (April 2024) |
| `Llama-3.2-11B-Vision` | Multimodal | `Llama-3.2-3B` (text-only small) |
| `Llama-3.3-70B` | Late 2024 update | `Llama-3.1-70B` |
| `Qwen2.5-72B` | Q4 2024 | `Qwen2-72B` (June 2024) |
| `Qwen3-Next-80B-A3B` | 2025 MoE, 3B active | `Qwen3-80B` if ever released |
| `DeepSeek-V3` | Dec 2024 MoE | `DeepSeek-V2` |
| `DeepSeek-R1` | Jan 2025 reasoning | `DeepSeek-V3` |
| `DeepSeek-R1-Distill-Qwen-32B` | Distill, not the full R1 | `DeepSeek-R1` (671B MoE) |
| `Mistral-Small-3` | 24B, Jan 2025 | `Mistral-7B` |
| `Mixtral-8x22B` | MoE | `Mixtral-8x7B` |
| `Gemma-2-27B` | 2024 | `Gemma-3-27B` (2025) |
| `Phi-4` | 14B, late 2024 | `Phi-3-medium` |

**Rule:** If the user says `X.Y`, you search `X.Y`, not `X`. If the user says `X-Next`, `X-Turbo`, `X-Pro`, `X-Max`, `X-Mini`, you keep that suffix.

## 4. MoE Naming Patterns

MoE models encode two numbers. Preserve both.

| Pattern | Meaning |
| --- | --- |
| `Mixtral-8x7B` | 8 experts × 7B each, 2 active → ~13B active, ~47B total |
| `Qwen3-Next-80B-A3B` | 80B total, 3B active per token |
| `DeepSeek-V3` (671B/37B) | 671B total, 37B active |
| `Llama-4-Scout` / `-Maverick` | Check current card; MoE configs vary |

If the user says `A3B` or `A37B`, that is the active-param count. You need it for throughput math (see `memory-math.md` and `throughput-estimation.md`).

## 5. Quantization Tags in Repo Names

Many community repos encode the quant in the repo name itself. Reading it is enough to know what you're getting.

| Tag | Meaning |
| --- | --- |
| `-GGUF` | llama.cpp format; quant is inside the filename (Q4_K_M, Q5_K_M, ...) |
| `-AWQ` | Activation-aware 4-bit, GPU |
| `-GPTQ` | Post-training 4-bit, GPU |
| `-EXL2` | ExLlamaV2, variable bpw (look for `4.65bpw`, `5.0bpw`, ...) |
| `-MLX` / `mlx-community/` | Apple Silicon, often `-4bit`, `-6bit`, `-8bit` |
| `-FP8` | NVIDIA Hopper/Ada FP8 |
| `-bnb-4bit` | bitsandbytes, Transformers loading |

## 6. Zero-Result Fallback (Only After Exhaustive Search)

You have searched all seven sources in §2 with the exact string, and nothing matched. Now — and only now:

1. Check for obvious typos **without correcting silently**. If you see a candidate, surface it:
   > "I couldn't find `Lllama-3.1-70B` on HF or Ollama. Did you mean `Llama-3.1-70B`? (Extra 'l'.) If not, could you share a link?"
2. Ask for a link. Do not substitute.
3. If the user insists the model exists and you still can't find it, say so honestly:
   > "I searched HF, Ollama, GitHub, and the web for the exact string and didn't find a public release. Can you share where you heard about it or a repo URL?"

What you **must not** do:

- Silently pick a similarly-named older model.
- Answer about a different model without disclosing the swap.
- Declare the model "doesn't exist" based on your training knowledge alone.
- Say "the latest is X" — you don't know what the latest is.

## 7. When You Do Recognize the Name

Still search. Quants, context windows, tokenizer versions, and repo moves happen. The model card today is authoritative; your memory of it is not. At minimum, confirm:

- Parameter count (dense, or active+total for MoE)
- Native precision (FP16 / BF16 / FP8)
- Context window
- Whether community quants exist (GGUF, EXL2, MLX, AWQ)

## 8. Vendor Version Conventions (Know the Shape)

Each vendor has its own versioning grammar. Knowing the grammar lets you recognize legitimate new releases instead of dismissing them as typos.

| Vendor | Grammar | Examples |
| --- | --- | --- |
| Meta | `Llama-<major>.<minor>-<params>B[-Instruct \| -Vision]` | `Llama-3.1-70B-Instruct`, `Llama-3.2-11B-Vision`, `Llama-3.3-70B`, `Llama-4-Scout`, `Llama-4-Maverick` |
| Qwen (Alibaba) | `Qwen<major>[.<minor>][-<variant>]-<params>B[-A<active>B][-Instruct]` | `Qwen2.5-14B-Instruct`, `Qwen3-Next-80B-A3B`, `Qwen2.5-Coder-32B` |
| Mistral | `Mistral-<size>-<version>` or `Mixtral-<experts>x<params>B` | `Mistral-Small-3`, `Mistral-Large-2411`, `Mixtral-8x22B` |
| DeepSeek | `DeepSeek-V<n>` or `DeepSeek-R<n>[-Distill-<base>-<params>B]` | `DeepSeek-V3`, `DeepSeek-R1`, `DeepSeek-R1-Distill-Llama-70B` |
| Google | `Gemma-<major>-<params>B[-IT \| -PT]` | `Gemma-2-27B-IT`, `Gemma-3-27B` |
| Microsoft | `Phi-<major>[-<variant>]` | `Phi-3-medium`, `Phi-3.5-mini`, `Phi-4` |
| xAI | `Grok-<major>[-<variant>]` | `Grok-1`, `Grok-2` |
| 01.AI | `Yi-<params>B[-Chat]` / `Yi-1.5-<params>B` | `Yi-34B`, `Yi-1.5-34B-Chat` |
| Cohere | `command-r[-plus][-<version>]` | `command-r-plus-08-2024` |
| NVIDIA | `Nemotron-<family>-<params>B` | `Llama-3.1-Nemotron-70B-Instruct` |
| Anthropic (closed) | `Claude <family> <major>[.<minor>]` | `Claude Opus 4.7`, `Claude Sonnet 4.5` |
| OpenAI (closed) | `GPT-<major>[-<variant>]` or `o<n>[-<variant>]` | `GPT-5`, `o3-mini`, `o4` |

Closed-source names (Claude, GPT, Grok) appear in "can I run this locally?" questions only as misunderstandings. If a user asks "can I run Claude Opus 4.7 locally?" the answer is no — no weights exist — but **do not** dismiss the version number as fake. Confirm the closed-source fact, not the (non-)existence.

**Seeing a suffix you don't recognize is the default case, not an error.** A, B, Mini, Nano, Flash, Turbo, Pro, Max, Ultra, Next, Coder, Math, Thinking, Reasoning, Distill — all are live suffix conventions across the ecosystem as of 2025–2026. Expect new ones.

## 9. Exact-String Search Templates

Copy these. Don't paraphrase.

```
# Hugging Face (web)
https://huggingface.co/models?search=<EXACT>

# Hugging Face (API)
curl "https://huggingface.co/api/models?search=<EXACT>&limit=10"

# Ollama
curl -sI "https://ollama.com/library/<lowercase-dashed>" | head -1
# (HTTP 200 = exists, 404 = not yet in Ollama's library even if model exists)

# GitHub
https://github.com/search?q=%22<EXACT>%22&type=repositories

# Web (Google)
"<EXACT>" site:huggingface.co
"<EXACT>" model card
"<EXACT>" release

# Vendor-specific
site:qwenlm.github.io "<EXACT>"
site:mistral.ai "<EXACT>"
site:deepseek.com "<EXACT>"
site:ai.meta.com "<EXACT>"
site:developers.googleblog.com "<EXACT>"
site:x.ai "<EXACT>"
```

If you have web access, run 2–3 of these in parallel before answering.

## 10. Reading a Model Card — What to Extract

Every HF model card has the facts you need. Pull these explicitly:

| Field | Where to find it | Why it matters |
| --- | --- | --- |
| Params | README header, config.json (`num_parameters` or sum from weights) | Memory math |
| Architecture | `config.json` → `model_type` (e.g. `qwen2`, `llama`, `mixtral`, `deepseek_v2`) | KV formula choice |
| Layers | `num_hidden_layers` | KV cache |
| KV heads | `num_key_value_heads` (GQA) or `num_attention_heads` (MHA) | KV cache |
| Head dim | `hidden_size / num_attention_heads` | KV cache |
| Context | `max_position_embeddings` | Fit at long context |
| Native dtype | `torch_dtype` in config | Native upper bound |
| MoE active/total | `num_local_experts`, `num_experts_per_tok`, or model card | Throughput math |
| Tokenizer | `tokenizer_config.json` | Chat template, context counting |

## 11. Checklist Before You Answer

- [ ] I used the user's exact string in search.
- [ ] I looked at HF and at least one other source.
- [ ] I have a URL I can cite for the params, context, and precision.
- [ ] I have not silently replaced the model with an older one.
- [ ] If I asked for clarification, I offered specifics, not a substitution.
- [ ] I read the config.json / model card, not just the repo name.

If any box is unchecked, do not answer the fit question yet.
