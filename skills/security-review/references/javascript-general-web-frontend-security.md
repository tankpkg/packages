# JavaScript Frontend Web Security

Sources: OWASP Frontend Security Guidelines, MDN Web Security

## Scope
This guide focuses on frontend JavaScript and TypeScript running in browsers.
It covers XSS, CSRF, CSP, storage, and safe interaction with untrusted inputs.
It does not replace backend protections and should be used with server controls.
Avoid recommending HSTS unless explicitly required by policy.
Avoid over-asserting TLS needs for local development contexts.

## Threat model essentials
Assume any data rendered to the DOM can be malicious.
Assume query params, hash fragments, and storage values are attacker-controlled.
Assume third-party scripts can change behavior if compromised.
Assume browser extensions can read page content.
Focus on preventing injection and limiting data exposure.

## XSS prevention overview
Treat any HTML string as unsafe by default.
Prefer DOM APIs that create text nodes instead of HTML injection.
Avoid building HTML with string concatenation.
Use trusted templating that auto-escapes by default.
Adopt a strict Content Security Policy with no inline scripts when possible.

## Output encoding guidance
Encode data when inserting into HTML, attributes, and URLs.
Do not reuse URL encoding as HTML encoding.
Avoid dangerouslySetInnerHTML unless content is sanitized.
Ensure templating libraries are configured to escape by default.
When in doubt, output text content and let the browser escape.

## DOMPurify usage
Sanitize only when you must render rich HTML.
Prefer a strict profile and disallow dangerous tags.
Do not allow inline event handlers.
Do not allow javascript: or data: URLs for link targets.
Example usage with safe defaults:

```javascript
import DOMPurify from "dompurify";

const dirty = userProvidedHtml;
const clean = DOMPurify.sanitize(dirty, {
  USE_PROFILES: { html: true },
  ALLOWED_URI_REGEXP: /^(https?|mailto):/i,
  FORBID_TAGS: ["style", "iframe"],
  FORBID_ATTR: ["style", "onerror", "onclick"],
});

container.innerHTML = clean;
```

## CSP configuration
Use CSP to block inline scripts and only allow trusted sources.
Prefer strict-dynamic with nonces for modern applications.
Avoid allowing unsafe-inline for scripts.
Use report-only first to validate policy changes.
Example CSP header for a SPA:

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-abc123'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; img-src 'self' https: data:; style-src 'self' 'unsafe-inline'; connect-src 'self' https://api.example.com
```

## CSP in HTML
Use meta tags only if headers are not possible.
Headers are preferred because they cannot be overridden by injection.
Example meta tag for local development:

```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'nonce-abc123'; object-src 'none'" />
```

## Nonce handling
Generate a fresh nonce per response on the server.
Inject nonce into script tags at render time.
Do not reuse nonces across responses.
Never store nonces in localStorage.
Keep nonce value out of URLs.

## CSRF protection
CSRF is primarily a backend issue, but frontend choices matter.
Prefer SameSite cookies for session cookies.
Use anti-CSRF tokens for unsafe methods.
Double-submit cookie is acceptable when sessions are cookie-based.
Do not attach credentials to cross-site requests unless required.

## SameSite cookie guidance
SameSite=Lax is a safe default for most session cookies.
Use SameSite=Strict if cross-site navigation is not required.
Use SameSite=None only when cross-site embedding is intended.
If SameSite=None is used, Secure is required in modern browsers.
Avoid breaking local dev by forcing Secure on non-TLS contexts.

## Cookie attributes
Use HttpOnly to prevent JavaScript access to cookies.
Use Secure only when TLS is used in that environment.
Limit Path to the minimum required scope.
Consider domain scoping to avoid subdomain leakage.
Avoid storing access tokens in cookies accessible to JS.

## Storage guidance
localStorage and sessionStorage are readable by any script on the page.
Do not store access tokens in localStorage.
Prefer HttpOnly cookies for session identifiers.
If you must store a token client-side, reduce scope and lifetime.
Clear storage on logout and on session expiration.

## Sensitive data exposure
Do not store passwords, secrets, or long-lived tokens in the browser.
Minimize PII stored in client state.
Avoid embedding secrets in bundled JavaScript.
Do not assume source maps are private in production.
Consider redacting sensitive data in client logs.

## URL parameter handling
Treat location.search and location.hash as untrusted input.
Avoid using query params to construct HTML.
Validate and whitelist allowed parameter values.
Avoid passing user-controlled values into eval or Function.
Normalize and encode before using in URLs.

## Open redirect prevention
Do not redirect based on arbitrary query params.
Use a whitelist of allowed redirect targets.
Prefer relative paths over absolute URLs.
Reject protocol-relative URLs.
Log suspicious redirect attempts.

## postMessage security
Always specify targetOrigin in postMessage.
Validate event.origin on message receipt.
Validate message schema and types.
Avoid executing commands from messages without authorization.
Example safe pattern:

```javascript
const targetOrigin = "https://widgets.example.com";
iframe.contentWindow.postMessage({ type: "PING" }, targetOrigin);

window.addEventListener("message", (event) => {
  if (event.origin !== targetOrigin) return;
  if (typeof event.data !== "object" || event.data.type !== "PONG") return;
  handlePong(event.data);
});
```

## Third-party scripts
Minimize third-party script usage.
Prefer loading from your own domain when possible.
Lock versions and integrity hashes.
Monitor for supply chain compromise.
Use Content Security Policy to limit third-party access.

## Subresource integrity (SRI)
Use SRI for external scripts and styles.
Update integrity hashes when updating versions.
Do not use SRI for resources that change dynamically.
Example SRI usage:

```html
<script src="https://cdn.example.com/lib.min.js" integrity="sha384-abc..." crossorigin="anonymous"></script>
```

## React-specific risks
Avoid using dangerouslySetInnerHTML unless sanitized.
Do not construct href attributes with untrusted input.
Do not use `javascript:` URLs in links.
Prefer `rel="noreferrer noopener"` on external links.
Avoid rendering untrusted markdown without sanitization.

## Vue and template safety
Vue escapes by default, but v-html is unsafe without sanitization.
Treat v-html like dangerouslySetInnerHTML.
Avoid using untrusted input in v-bind:href.
Prefer computed properties that sanitize inputs.
Audit directives that build HTML or URLs.

## Angular template safety
Angular sanitizes certain bindings by default.
Bypassing sanitizer APIs should be rare and documented.
Do not trust [innerHTML] with user input.
Avoid DomSanitizer.bypassSecurityTrustHtml without review.
Prefer safe pipes for URL and HTML content.

## Clickjacking defense
Use frame-ancestors in CSP to prevent embedding.
If supported, set X-Frame-Options via backend.
Avoid embedding in untrusted domains.
In-app defenses should be secondary to headers.
Do not rely on JS frame-busting alone.

## CORS and fetch usage
Avoid cross-origin requests unless required.
Do not include credentials unless needed.
Use fetch with `credentials: "include"` only for trusted origins.
Use explicit allowlists and never use wildcard with credentials.
Frontends should not assume server will block unsafe origins.

## Service workers
Treat service workers as privileged code.
Do not cache sensitive API responses.
Validate all cached content.
Version and revoke old service workers.
Avoid enabling service workers on untrusted subdomains.

## Client-side routing
Do not treat route params as safe.
Validate before using in queries or rendering HTML.
Encode route params when building URLs.
Avoid storing sensitive data in route state.
Prefer server-side validation for authorization.

## Forms and input handling
Use input type constraints for user feedback, not security.
Always validate on the server as the source of truth.
On the client, still validate to reduce accidental unsafe input.
Do not reflect raw form input back into HTML without escaping.
Avoid `innerHTML` for error messages.

## Client-side crypto
Avoid rolling your own cryptography in the browser.
If you must use crypto, use Web Crypto API.
Do not store private keys in localStorage.
Do not use crypto as a substitute for server validation.
Treat client-side encryption as defense-in-depth only.

## File handling
Never trust file name or MIME type from the browser.
Do not render uploaded images directly without validation.
Avoid displaying user-controlled SVG without sanitization.
Prefer server-side content scanning.
Strip EXIF data if images are exposed.

## Logging and error UI
Avoid leaking stack traces to users.
Hide internal error details in production.
Sanitize error messages displayed to users.
Avoid logging tokens or secrets to the console.
Use feature flags for verbose debugging.

## Development considerations
Do not require Secure cookies for non-TLS local dev.
Avoid forcing TLS warnings as findings in dev contexts.
Prefer environment flags to toggle secure-only behavior.
Document dev-only exceptions clearly.
Keep security features consistent across environments when possible.

## Review checklist
Use this table to assess implementations quickly.
Fill in specific code paths during a review.
Prioritize fixes that reduce remote code execution and data theft.

| Security Check | Implementation | Priority |
| --- | --- | --- |
| Output encoding by default | Template engine auto-escapes and no unsafe HTML rendering | High |
| DOMPurify for rich HTML | Sanitize untrusted HTML with strict allowlist | High |
| CSP enforced | Header-based CSP with no unsafe-inline for scripts | High |
| Cookie flags | HttpOnly and SameSite=Lax or Strict where possible | High |
| No tokens in localStorage | Use HttpOnly cookies for sessions | High |
| CSRF protections | SameSite cookies and anti-CSRF tokens for unsafe methods | High |
| Safe redirects | Allowlist or relative-only redirects | Medium |
| postMessage validation | Check origin and schema | Medium |
| SRI on third-party scripts | Integrity hashes for CDN resources | Medium |
| Clickjacking defense | CSP frame-ancestors set | Medium |
| Client logging hygiene | No tokens or secrets in logs | Medium |
| Route param validation | Validate and encode route params | Medium |
| Service worker scope | Cache sanitized public assets only | Low |
| Error UI sanitization | No stack traces in production UI | Low |
