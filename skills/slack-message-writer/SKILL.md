---
name: "@tank/slack-message-writer"
description: |
  Write short, polished Slack messages with the key words in bold so they scan
  fast (including for dyslexic readers), choose the right Slack formatting mode,
  and automatically copy the finished message to the local clipboard. Covers
  pasted Markdown, composer markup, API mrkdwn, Markdown blocks, mentions,
  localized dates, accessibility fallbacks, announcements, status updates,
  incidents, decisions, requests, handoffs, and review asks. Synthesizes current
  official Slack Help Center and Slack developer formatting guidance.

  Trigger phrases: "write a Slack message", "draft a Slack message", "Slack copy",
  "copy this to my clipboard", "message the team", "Slack announcement",
  "Slack status update", "Slack incident update", "Slack review request",
  "Slack handoff", "format this for Slack", "Slack mrkdwn", "special Slack message",
  "make this Slack-ready", "send this on Slack", "compose a Slack reply",
  "scannable Slack message", "ADHD scannable", "dyslexia friendly"
---

# Slack Message Writer

Write Slack-native messages that are short, easy to scan, hard to misunderstand,
and ready to paste. Copy the final artifact to the clipboard unless the user opts out.

## Core Philosophy

1. **Lead with the point.** Put the decision, request, outcome, or state in the
   first line. Context follows the headline.
2. **Keep it short.** Every line must earn its place. Cut background the reader
   already has, and link to a document instead of explaining it.
3. **Bold the key words.** A reader who reads only the bold text should still get
   who, what, and when. This makes messages scannable, especially for dyslexic
   and ADHD readers.
4. **Match the paste target's syntax.** Text pasted into Slack's default composer
   is parsed as standard Markdown: `**bold**`, not `*bold*`.
5. **Notify deliberately.** Mention the smallest useful audience. Never add
   `@channel`, `@here`, `@everyone`, or a user-group mention without explicit intent.

## Workflow

1. Infer audience, purpose, desired action, deadline, and tone from context.
2. Ask one concise question only when a missing fact materially changes the message.
3. Pick a delivery mode below. Default to **Clipboard (pasted Markdown)**.
4. Draft with the relevant recipe, then cut it to the **Length Budget**.
5. Bold the key words in every line (see **Bold Key Words**).
6. Check names, links, dates, identifiers, and notification scope. Invent none.
7. Display the final message in one fenced `text` block.
8. Pipe the exact unfenced text to `scripts/copy-to-clipboard.sh`.
9. Report `Copied to clipboard.` and remind the user to re-type `@mentions`.
   Never say `sent` unless a separate Slack tool sent it.

## Length Budget

| Rule | Target |
|---|---|
| Whole message | About 5 lines; more than 8 needs a reason |
| Sentence | One idea, about 15 words or fewer |
| Context | At most one short line |
| List | At most 5 items, unless the list is the content (tickets, owners) |
| Detail that does not fit | A link, not more paragraphs |

Prefer a label and a fragment (`**Next:** **rehearsal** on **Thursday**`) over a
full sentence. Do not repeat in the body what the headline already said.

## Bold Key Words

Bold the words that carry meaning, so the bold text alone reads as a summary:
the **action** the reader must take, **owners**, **deadlines and times**,
**status** words, **numbers that matter**, and the line's **subject** when unclear.

- Bold 1 to 3 short phrases per line; past about a third of a line, nothing stands out.
- Bold whole words or phrases, never a full sentence, filler words, or code.
- Emphasize with bold, not italics or underline: British Dyslexia Association
  guidance says italics and underline make letters harder to read.
- Syntax follows the mode: `**bold**` when pasting and in API Markdown; `*bold*`
  only in API `mrkdwn` or typed composer markup. Pasted `*single*` renders italic.

## Delivery Modes

| User intent | Output mode | Formatting |
|---|---|---|
| Write, draft, reply, announce, copy | Clipboard (pasted Markdown) | `**bold**`, `_italic_`, `~~strike~~`, code, `- ` lists, `>` quotes, `[label](url)` |
| User types it, or has markup preference on | Composer markup | `*bold*`, `_italic_`, `~strike~`, code, quotes, Markdown-style links |
| Web API message using `text` | API `mrkdwn` | `<url|label>`, ID-based mentions, `<!date...>` |
| Preserve an LLM's standard Markdown | API Markdown | `markdown_text` or a `markdown` block |
| Structured app message | API rich layout | Block Kit `rich_text` plus accessible fallback text |

Do not mix syntaxes. Clipboard output never contains API-only forms such as
`<@U123>` or `<!date...>` unless the user asked for an API payload.

## Quick-Start: Common Messages

### "Ask for action or review"

Request first, deadline, focus, link.

```text
**Review requested: onboarding copy**
Please **review** it by **Thursday 14:00**, focusing on **value clarity** and **missing objections**.
[Open the draft](https://example.com)
```

### "Share a status update"

State, done, next, risk. Omit empty sections.

```text
**Project Atlas: on track for Friday**
- **Done:** **import flow** and validation
- **Next:** **migration rehearsal**
- **Risk:** legal copy due **Thursday**
```

### "Announce a change"

What changed, who is affected, when, action, source of truth.

```text
**New expense approval flow starts Monday**
Requests **over $1,000** need **Finance approval**. Existing requests are **unchanged**.
**Action:** use the **new form** from **Monday**. [Guide](https://example.com)
```

### "Post an incident update"

Status, impact, action underway, next update, with an absolute time and timezone.

```text
**Investigating: delayed report generation**
**Impact:** reports **20-30 minutes late**, **no data loss**.
**Now:** draining the **worker queue**. **Next update:** **15:30 UTC**
```

### "Record a decision or hand off work"

Decision or current state, reason, exact next action and owner, known risk.

```text
**Decision: keep the launch behind the existing flag**
**Why:** the rollback path is **proven**; a second flag adds **risk**.
**Next:** **Maya** raises it from **10% to 25%** after tomorrow's error review.
```

## Formatting Judgment

| Signal | Use | Avoid |
|---|---|---|
| One key takeaway | Bold first-line headline | Multiple competing headings |
| Three or more parallel facts | Bulleted list | Bullets for a single sentence |
| Commands, IDs, literal values | Inline code or code block | Bold code-like text |
| One primary action | A labeled action line | Several unlabeled links |
| Urgent operational change | Explicit impact and next update | Emoji-only urgency |

Use at most one or two purposeful emoji. Never let emoji alone carry status,
urgency, approval, or failure.

## Clipboard Delivery

Send only the final message body over standard input:

```bash
bash scripts/copy-to-clipboard.sh <<'SLACK_MESSAGE'
**Final Slack message**
Exact text to copy.
SLACK_MESSAGE
```

Never copy analysis, alternatives, the code fence, or the completion note. Slack's
default composer parses pasted plain text as standard Markdown and ignores the
clipboard's HTML (verified in the desktop app, 2026-11-02), so the script copies
plain text. Pasted `@Name` text never becomes a real mention.

## Decision Trees

| Question | If yes | If no |
|---|---|---|
| Did the user request API JSON or Block Kit? | Use API mode and load the reference | Use clipboard (pasted Markdown) |
| Is there one explicit action? | Put it in the first two lines, in bold | Lead with the outcome or state |
| Does a mention notify many people? | Require explicit user intent | Use the narrow mention |
| Is a date viewed across timezones? | Localized API date syntax in API mode | Include an explicit timezone |
| Is the message over the length budget? | Cut detail or link to a document | Keep it self-contained |
| Does the bold alone miss who, what, or when? | Bold the missing key words | Keep the bold as it is |
| Is the content sensitive or surprising? | Keep neutral wording; ask before adding names | Draft directly |

## Scripts

| Script | Usage |
|---|---|
| `scripts/copy-to-clipboard.sh` | Copy non-empty UTF-8 text from standard input as literal macOS plain text; rejects missing input, invalid UTF-8, and unsupported arguments |

## Reference Index

| File | Contents |
|---|---|
| `references/slack-formatting.md` | Pasted Markdown behavior, composer markup, API `mrkdwn`, standard Markdown blocks, rich text, mentions, dates, escaping, parsing controls, accessibility, limits, and mode-specific checks |
