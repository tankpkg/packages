# Slack Formatting and Special Message Syntax

Sources: Slack Help Center, "Format your messages in Slack" and "Format your messages in Slack with markup"; Slack Developer Docs, "Formatting message text," `chat.postMessage`, Markdown block, and Rich text block (verified 2026-09-02)

Covers: mode selection, current syntax, special parsing, safe notification behavior, accessibility, limits, and validation for clipboard and API-authored Slack messages.

## Source Links

- https://slack.com/help/articles/202288908-Format-your-messages-in-Slack
- https://slack.com/help/articles/360039953113-Format-your-messages-in-Slack-with-markup
- https://docs.slack.dev/messaging/formatting-message-text/
- https://docs.slack.dev/reference/methods/chat.postMessage/
- https://docs.slack.dev/reference/block-kit/blocks/markdown-block/
- https://docs.slack.dev/reference/block-kit/blocks/rich-text-block/

Slack evolves multiple formatting systems independently. Treat the delivery
surface as the first formatting decision, not as an implementation detail.

## The Four Formatting Modes

| Mode | Intended surface | Syntax family | Primary use |
|---|---|---|---|
| Composer rich text | Human types or pastes into default Slack composer | WYSIWYG rich text | Manual messages edited in Slack |
| Composer markup | Human sends from Slack with markup preference enabled | Slack client markup | Clipboard-ready plain text |
| API `mrkdwn` | App sends `text` or `mrkdwn` text objects | Slack custom `mrkdwn` | App messages with Slack entities |
| API standard Markdown | App sends `markdown_text` or `markdown` blocks | Standard Markdown subset | LLM output, tables, task lists, headers |

The `rich_text` Block Kit block is a structured representation rather than a
plain-text syntax. Slack's WYSIWYG composer emits this format, and Slack now
strongly prefers it for user-defined formatted text in Block Kit payloads.

### Default for this skill

Use pasted Markdown (see below) for ordinary requests: the message is copied as
plain text and pasted into the default composer, which converts standard Markdown
on paste. Keep the message understandable even if a composer shows the delimiters.

Use API formats only when the user asks for a payload, app message, webhook,
Block Kit structure, Slack SDK call, or explicit API special syntax.

## Slack Composer: Clipboard Messages

The default Slack composer provides a formatting toolbar and previews the
rendered result. It supports bold, italics, underline, strikethrough, inline
code, block quotes, code blocks, ordered lists, and bulleted lists.

Slack's markup preference is configured under:

1. Open the profile menu.
2. Select **Preferences**.
3. Select **Advanced**.
4. Toggle **Format messages with markup**.

When markup mode is enabled:

- Formatting appears after the message is sent.
- Copied and pasted content appears as plain text in the composer.
- Automatic list formatting is not applied.

That behavior is why clipboard output should carry explicit, conservative
markup and should not depend on copied rich-text attributes.

### Pasted Markdown (default composer, clipboard default)

Verified 2026-11-02 in the Slack desktop app with the default composer: pasted
plain text is parsed as **standard Markdown**, and the composer ignores the
clipboard's HTML version. Typed composer markup does not apply to pasted text.

| Intent | Pasted syntax | Pasted result |
|---|---|---|
| Bold | `**text**` | Bold |
| Italic | `_text_` | Italic |
| Single asterisks | `*text*` | **Italic**, not bold: never use for bold when pasting |
| Strikethrough | `~~text~~` | Strikethrough |
| Bulleted list | `- item` | List |
| Link | `[label](URL)` | Link |

Pasted `@Name` text does not become a mention; the user must re-type mentions.

### Official composer markup (typed, or markup preference on)

Use this only when the user types the message or has **Format messages with
markup** enabled; in that mode pasted text stays plain and markup applies on send.

| Intent | Syntax | Example |
|---|---|---|
| Bold | `*text*` | `*Launch approved*` |
| Italic | `_text_` | `_Tentative_` |
| Strikethrough | `~text~` | `~Old deadline~` |
| Inline code | Backticks | ``Run `bun test` `` |
| Block quote | `>` at line start | `>Customer report` |
| Code block | Triple backticks | A fenced command or log excerpt |
| Link | `[label](URL)` | `[Open the PR](https://example.com)` |

Slack's help page does not list heading markup for composer mode. Create visual
hierarchy with a bold first line instead of Markdown `#` headings.

Slack's help page also states that ordered and bulleted lists can be created in
the rich-text composer by typing `1.` or `*` followed by a space. In markup mode,
automatic list formatting is disabled. Use literal `- ` lines in clipboard text
because they remain readable whether or not Slack converts them.

### Composer line breaks

Slack documents `Shift+Enter` as the default way to start a new line. Clipboard
text already contains newline characters, so preserve them directly. Use blank
lines between conceptual sections, not between every sentence.

### Clipboard-safe hierarchy

Use this order when the message needs structure:

1. Bold headline stating the outcome, request, or state.
2. One short context line if necessary.
3. Parallel facts as a list with bold labels.
4. One action, deadline, or next update.
5. One source-of-truth link.

Keep the whole message to about 5 lines, and bold 1 to 3 key words per line
(actions, owners, dates, statuses, numbers) so the bold text alone reads as a
summary. Use bold, not italics or underline, for emphasis.

In clipboard messages, write bold as `**text**` (pasted Markdown), never `*text*`.

## API `mrkdwn`

Slack calls its custom API syntax `mrkdwn`, not Markdown. It is the default
formatting method for top-level message text and many Block Kit text objects.

### Basic `mrkdwn` styles

| Intent | `mrkdwn` syntax |
|---|---|
| Bold | `*bold*` |
| Italic | `_italic_` |
| Strikethrough | `~strike~` |
| Inline code | Backticks |
| Code block | Triple backticks |
| Quote | `>` at the start of each quoted line |
| Newline in JSON string | `\n` |

Code spans and code blocks suppress other formatting inside them. Use this to
show literal asterisks, underscores, identifiers, commands, or snippets.

There is no dedicated list syntax in app-published `mrkdwn`. Slack recommends
mimicking lists with ordinary bullet characters or hyphens plus line breaks.

### `mrkdwn` links

| Intent | Syntax |
|---|---|
| Bare URL | `https://docs.slack.dev/` |
| Explicit URL | `<https://docs.slack.dev/>` |
| Labeled link | `<https://docs.slack.dev/|Slack developer docs>` |
| Email link | `<mailto:person@example.com|Email Person>` |

Remove spaces from URLs. Slack automatically links ordinary URLs unless parsing
controls disable that behavior.

### Escaping control characters

In API text objects, escape only these literal characters when they are not
part of Slack special syntax:

| Literal | Entity |
|---|---|
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |

Do not HTML-encode the whole message. Slack decodes only these control entities
for display, and broad encoding can damage URLs and special references.

## Special Slack Entities

Special entities are API syntax. Do not place them in ordinary clipboard output
unless the user explicitly wants an API-ready string.

### User mention

```text
<@U012AB3CD>
```

Use the stable Slack user ID. App-published mentions notify the referenced user.
Never guess an ID from a display name or email address.

### Channel link

```text
<#C123ABC456>
```

Slack resolves the channel ID to its current name. A viewer without access to a
private channel sees an unclickable private-channel label.

### User-group mention

```text
<!subteam^SAZ94GDB8>
```

This notifies every member of the user group. Require an explicit group ID and
explicit notification intent.

### Broad special mentions

| Mention | API syntax | Effect |
|---|---|---|
| Active channel members | `<!here>` | Notifies active members |
| All channel members | `<!channel>` | Notifies active and inactive members |
| General-channel membership | `<!everyone>` | Notifies every non-guest workspace member |

Slack explicitly recommends using broad mentions sparingly. Prefer an individual
or narrower user group whenever it will reach the needed audience.

### Localized dates and times

Use Slack date syntax so each reader sees the timestamp in the local timezone of
the device displaying Slack:

```text
<!date^timestamp^token_string^optional_link|fallback_text>
```

Components:

- `timestamp`: Unix timestamp in seconds.
- `token_string`: Plain text plus Slack date tokens.
- `optional_link`: Fully qualified URL, preceded by `^`.
- `fallback_text`: Required readable text for clients that cannot render it.

Useful tokens:

| Token | Meaning |
|---|---|
| `{date_num}` | Numeric date such as `2014-02-18` |
| `{date}` | Long date with context-sensitive year |
| `{date_short}` | Short date with context-sensitive year |
| `{date_long}` | Weekday plus long date |
| `{date_pretty}` | Date with today, tomorrow, or yesterday when applicable |
| `{date_short_pretty}` | Short pretty date |
| `{date_long_pretty}` | Long pretty date |
| `{time}` | Local time with client 12-hour or 24-hour preference |
| `{time_secs}` | Local time including seconds |
| `{ago}` | Relative time such as `3 minutes ago` |

Example:

```text
<!date^1788352200^{date_long_pretty} at {time}|September 2, 2026 at 17:30 UTC>
```

Include timezone information in fallback text. Slack uses the observing device's
timezone for the rendered value, not the timezone preference stored in Slack.

## Automatic Parsing and Notification Safety

Slack can automatically parse some human-looking references, but its developer
docs recommend manual ID-based syntax for app messages.

Reasons:

1. Conversation and user-group names can change; IDs remain stable.
2. Explicit syntax shows exactly which strings become links or notifications.
3. Untrusted input can contain `@everyone` or another accidental notification.
4. Automatic user-name parsing is already deprecated.

### Parsing controls

| Surface | Enable automatic parsing | Disable automatic parsing |
|---|---|---|
| Block Kit text object | `verbatim: false` (default) | `verbatim: true` |
| Top-level `text` or attachment | `link_names: 1` | Omit `link_names` |
| Ordinary URL linking | Default behavior | `parse: "none"` |

For top-level `mrkdwn`, Slack's `parse` behavior is counterintuitive: default or
`none` applies `mrkdwn`; `full` ignores `mrkdwn`. Prefer explicit examples from
the current method reference instead of inferring behavior from the parameter name.

When any content originated outside the trusted application boundary:

- Escape literal control characters.
- Disable broad automatic parsing.
- Resolve approved mentions to IDs yourself.
- Never transform free-form `@channel`, `@here`, or `@everyone` text into a mention.

## Standard Markdown for API Messages

Slack currently supports standard Markdown through either:

- The `markdown_text` argument to `chat.postMessage`.
- A Block Kit block with `type: "markdown"`.

`markdown_text` cannot be used together with `blocks` or `text` and has a
12,000-character limit. The cumulative text across all `markdown` blocks in one
payload also has a 12,000-character limit.

The Markdown block supports syntax not available in `mrkdwn`, including:

- `**bold**` or `__bold__`.
- Standard ordered and unordered lists.
- Heading markers; all heading levels render at the same size.
- Fenced code with language syntax highlighting.
- Horizontal rules.
- Markdown tables.
- Task lists with checkboxes.
- Standard `[label](URL)` links.
- Backslash escaping of Markdown punctuation.

Images written as Markdown image syntax become ordinary hyperlink text; they do
not render as inline images.

Slack positions the Markdown block for apps using platform AI features when an
LLM's standard Markdown could otherwise be lost in translation. Slack may turn
one submitted Markdown block into multiple rendered blocks.

### Never translate blindly

The same characters have different meanings across formats:

| Meaning | Composer markup / `mrkdwn` | Standard Markdown block |
|---|---|---|
| Bold | `*bold*` | `**bold**` |
| Italic | `_italic_` | `*italic*` or `_italic_` |
| Strike | `~strike~` | `~~strike~~` |
| Labeled link | `<URL|label>` in `mrkdwn`; `[label](URL)` in composer markup | `[label](URL)` |
| Lists | Visual imitation in `mrkdwn` | Native Markdown lists |

Choose the target first, then generate that syntax directly.

## Rich Text and Block Kit

Use `rich_text` when an app must reproduce user-defined formatted content or
needs structured lists, quotes, preformatted text, and styled text sections.

A rich-text block contains an `elements` array. Supported top-level element
families include:

- `rich_text_section`
- `rich_text_list`
- `rich_text_preformatted`
- `rich_text_quote`

Rich-text blocks can be nested. A list may contain sections whose individual text
runs carry styles. This is more expressive and less ambiguous than translating
everything into `mrkdwn`.

Use simpler message text when interactivity or structured layout does not improve
the reader's task. A polished one-paragraph update should not become a large Block
Kit payload merely because blocks are available.

## Accessibility and Fallback Text

For `chat.postMessage` with `blocks`, the top-level `text` field is notification
fallback text. Screen readers default to that top-level field and do not read the
interior blocks as the message's primary accessible representation.

Choose one strategy:

1. Include every necessary fact in concise top-level `text`.
2. Omit top-level `text` and let Slack attempt to derive it from supported blocks.

Prefer explicit fallback text when correctness matters. It should communicate the
state, impact or requested action, and destination link without relying on color,
emoji, image alt text, visual columns, or button placement.

Accessibility checks:

- Do not encode meaning only through emoji.
- Bold key words so the message scans; use bold, not italics or underline, for
  emphasis (dyslexia style guidance).
- Give links descriptive labels.
- Put critical content in reading order.
- Avoid side-by-side fields when sequence matters.
- Include alt text for image blocks.
- Ensure the fallback still works as a push notification.

## Length, Threads, and Link Unfurls

Slack recommends limiting top-level `text` to about 4,000 characters for best
results and truncates messages over 40,000 characters. For longer material, link
to a document or use an appropriate file or snippet workflow.

Block-specific limits still apply when using Block Kit.

Use `thread_ts` to reply to a parent message. Set `reply_broadcast: true` only when
the reply is important enough to notify the channel beyond thread participants.

Slack unfurls links by default. For app messages where previews add noise or leak
unwanted context, set both `unfurl_links` and `unfurl_media` to `false`.

## Mode-Specific Preflight

### Clipboard composer

- The first line carries the point.
- Markup uses composer syntax, not API-only syntax.
- Literal hyphen lists remain understandable without conversion.
- Dates include an explicit timezone when readers may differ.
- No code fence surrounds the copied message.
- The clipboard contains only the final body.

### API `mrkdwn`

- `&`, `<`, and `>` are escaped unless intentionally used as control syntax.
- Links use `<URL|label>` when labeled.
- User, channel, and group references use verified IDs.
- Broad mentions are explicitly authorized.
- Date syntax includes a readable fallback and timezone.
- Untrusted text cannot trigger automatic mentions.

### API Markdown

- `markdown_text` is not combined with `text` or `blocks`.
- Markdown blocks stay within the cumulative 12,000-character limit.
- Standard Markdown syntax is used consistently.
- Image syntax is not expected to render an image.
- Translation into multiple rendered blocks is acceptable.

### Block Kit

- Use `rich_text` when structured user-formatted content is the real need.
- Keep `block_id` unique for every message or update iteration.
- Include or intentionally delegate accessible top-level fallback text.
- Verify the payload in Block Kit Builder when layout is material.
- Keep the notification useful without opening the full message.

## Source Freshness

These rules were verified against official Slack documentation on 2026-09-02.
When implementing a production API integration, re-check the linked method and
block references for field conflicts, character limits, and newly introduced block
types. Do not change clipboard composer syntax based on generic Markdown behavior;
Slack's own Help Center remains the authority for human-authored messages.
