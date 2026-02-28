# MFA Implementation

Sources: RFC 6238 (TOTP), RFC 4226 (HOTP), W3C WebAuthn Level 2 specification, NIST SP 800-63B Digital Identity Guidelines, OWASP Authentication Cheat Sheet, how2.sh WebAuthn implementation guide, thehgtech.com FIDO2 enterprise guide

Covers: MFA factor types, TOTP algorithm and storage, WebAuthn/FIDO2 passkeys, SMS OTP weaknesses, backup codes, step-up authentication, enrollment flows, and account recovery.

## MFA Factor Categories

Authentication factors are classified by what proves identity. MFA combines two or more factor categories.

| Category | Also Called | Examples |
|----------|-------------|---------|
| Knowledge | Something you know | Password, PIN, security questions |
| Possession | Something you have | TOTP app, hardware key (YubiKey), phone (SMS) |
| Inherence | Something you are | Fingerprint, face ID, retina scan |

Combining factors from different categories provides defense in depth. Two knowledge factors (password + security question) is not true MFA.

### MFA Methods by Strength

| Method | Category | Phishing Resistant? | SIM Swap Resistant? | Recommended? |
|--------|----------|--------------------|--------------------|--------------|
| Hardware key (FIDO2) | Possession | Yes — origin-bound | Yes | Highest — privileged accounts |
| Passkey (synced FIDO2) | Possession + Inherence | Yes | Yes | High — consumer apps |
| TOTP authenticator app | Possession | No — codes can be phished | Yes | Good — practical baseline |
| Push notification | Possession | No — MFA fatigue attacks | Yes | Acceptable with number matching |
| Email OTP | Possession | No | Depends on email provider | Weak — use only as fallback |
| SMS OTP | Possession | No | No | Weak — avoid for high-risk |
| Security questions | Knowledge | No | N/A | Never use as MFA |

## TOTP (Time-Based One-Time Passwords)

TOTP (RFC 6238) generates 6-8 digit codes that change every 30 seconds. Works offline. Wide app support (Google Authenticator, Authy, 1Password).

### Algorithm

TOTP is HMAC-OTP (RFC 4226) with a time counter instead of an event counter.

```
T = floor(current_unix_time / 30)    # 30-second step
HOTP = HMAC-SHA1(secret, T)          # 20-byte HMAC output
Truncate:
  offset = HOTP[19] & 0xf            # Last byte, low nibble
  P = HOTP[offset..offset+3] & 0x7fffffff  # 4 bytes, drop top bit
  code = P mod 10^6                  # 6-digit code (or 8 for 10^8)
```

The shared secret never changes per enrollment. Both server and client compute the same code independently for the same time window.

### TOTP Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Algorithm | SHA-1 (default), SHA-256, SHA-512 | Most authenticator apps only support SHA-1 |
| Period | 30 seconds | Standard; 60s also supported |
| Digits | 6 | Standard; 8 for higher security |
| Window tolerance | ±1 window (90 seconds total) | Handles clock skew |

Allow ±1 window on validation to accommodate clock skew between server and user device. Do not allow larger windows — each additional window is a brute-force opportunity.

### TOTP Secret Storage

| Requirement | Implementation |
|-------------|---------------|
| Secret encoding | Base32 (for QR code / manual entry compatibility) |
| Secret entropy | 160 bits minimum (20 random bytes) |
| Storage | Encrypted at rest using AES-256 with application-layer key |
| Key management | Store encryption key in secret manager, not in app config |
| Never log | TOTP secrets must never appear in logs or error messages |

**Secret provisioning**: Generate 20 random bytes, base32-encode for display, store encrypted form in database. Display as QR code (`otpauth://totp/{issuer}:{account}?secret={base32}&issuer={issuer}`).

### TOTP Replay Prevention

A used code is valid for its 30-second window. An attacker who observes a code can replay it within that window.

**Prevention**: Store the last-used counter value per user. Reject a code if it matches the previously used counter. This limits each code to one use per window.

```
On validation:
  compute_counter = floor(now / 30)
  for window in [-1, 0, +1]:
    code = totp(secret, compute_counter + window)
    if code == submitted_code:
      if (compute_counter + window) <= user.last_used_counter:
        reject (replay)
      user.last_used_counter = compute_counter + window
      return success
reject (invalid code)
```

### TOTP Enrollment Flow

1. Generate a new TOTP secret for the user
2. Display as QR code + text fallback (for accessibility)
3. Require user to enter a valid code before marking enrollment complete (confirms app is configured correctly)
4. Store encrypted secret in database, linked to user
5. Invalidate any existing TOTP secret (re-enrollment replaces old)
6. Issue backup codes at enrollment time

## WebAuthn / FIDO2 (Passkeys)

WebAuthn (W3C Level 2) is the browser API for FIDO2 authentication. Passkeys are WebAuthn credentials that sync across devices. Passkeys are phishing-resistant because the credential is bound to the origin domain — they will not work on a fake site.

### Core Concepts

| Term | Definition |
|------|-----------|
| Relying Party (RP) | Your server — defines `rpId` (your domain) and `rpName` |
| Authenticator | Device that holds the private key — platform (Face ID, Windows Hello) or roaming (YubiKey) |
| Credential | Public/private key pair generated per RP per authenticator |
| Attestation | Authenticator proves its type during registration (optional; complex to verify) |
| Assertion | Authenticator proves possession of private key during authentication |
| `rpId` | Domain scope — credential only works for this exact domain |

### Registration Flow

```
Server:
  1. Generate challenge = random 32 bytes
  2. Store challenge in session (one-time use)
  3. Return PublicKeyCredentialCreationOptions:
     { rp: { id: "example.com", name: "Example" },
       user: { id: userId, name: email, displayName: name },
       challenge: challenge,
       pubKeyCredParams: [{ type: "public-key", alg: -7 }],  // ES256
       authenticatorSelection: {
         residentKey: "required",     // enables discoverable credentials
         userVerification: "preferred"
       },
       timeout: 60000,
       attestation: "none"  // "none" for most apps; skip attestation verification complexity
     }

Client (browser):
  4. navigator.credentials.create(options) → prompts user for biometric/PIN
  5. Returns PublicKeyCredential with clientDataJSON + attestationObject

Server:
  6. Verify clientDataJSON.challenge matches session challenge
  7. Verify clientDataJSON.origin matches your domain
  8. Verify clientDataJSON.type == "webauthn.create"
  9. Parse attestationObject → extract public key + credentialId
  10. Store: { userId, credentialId, publicKey, signCount: 0, createdAt }
  11. Clear session challenge
```

### Authentication Flow

```
Server:
  1. Generate challenge = random 32 bytes
  2. Store in session
  3. Return PublicKeyCredentialRequestOptions:
     { challenge: challenge,
       rpId: "example.com",
       allowCredentials: [{ id: credentialId, type: "public-key" }],
       userVerification: "preferred",
       timeout: 60000
     }

Client (browser):
  4. navigator.credentials.get(options) → prompts biometric/PIN
  5. Returns assertion with authenticatorData + clientDataJSON + signature

Server:
  6. Verify challenge from clientDataJSON matches session
  7. Verify origin matches your domain
  8. Verify rpIdHash in authenticatorData = sha256(rpId)
  9. Verify signature over authenticatorData + clientDataJSON hash using stored public key
  10. Check signCount > stored signCount (prevents cloned authenticator replay)
  11. Update stored signCount
  12. Establish session
```

### Discoverable Credentials (Usernameless Login)

Setting `residentKey: "required"` stores a resident credential on the authenticator. Users can authenticate without providing a username — just tap the key or use biometrics, and the device presents available credentials.

This enables the full passkey UX. Required for "Sign in with passkey" flows.

### Platform vs Roaming Authenticators

| Type | Examples | Synced? | Use Case |
|------|---------|---------|----------|
| Platform | Face ID, Touch ID, Windows Hello | Yes (via iCloud/Google Password Manager) | Consumer apps — best UX |
| Roaming (cross-platform) | YubiKey, Titan Key | No — device-bound | Enterprise, privileged accounts |

Platform authenticators sync via the OS keychain (iCloud Keychain, Google Password Manager). A passkey registered on one iPhone is available on all iCloud devices. Plan for credential recovery when the platform account is unavailable.

### `signCount` and Clone Detection

Each authentication increments the authenticator's sign counter. If the server observes a presented `signCount` ≤ stored value, the credential may be cloned.

**Policy on clone detection**:
- Treat as a security event: require re-registration and notify user
- Note: some authenticators return `signCount: 0` always (no counter) — do not flag these as cloned; check for zero before enforcing

## SMS OTP — When and Why to Avoid

SMS OTP delivers a one-time code via text message. It is a possession factor but with known weaknesses.

### Weaknesses

| Attack | Mechanism | Practical Risk |
|--------|-----------|---------------|
| SIM swapping | Attacker convinces carrier to port victim's number to attacker's SIM | High — documented attacks on crypto, email accounts |
| SS7 interception | Telecom protocol exploitation to reroute SMS | High capability barrier; nation-state level |
| Malware | Android SMS-reading malware forwards codes | Moderate |
| Real-time phishing | Proxy site relays victim's SMS code to real site instantly | High — kits widely available |

### When SMS OTP Is Acceptable

- Low-risk applications where no higher factor is practical
- Phone number verification (not authentication)
- Fallback during account recovery when better options are unavailable
- Legacy user populations without smartphones (use voice OTP)

Always prefer TOTP or WebAuthn over SMS. If SMS must be used, implement rate limiting and account lockout on code attempts.

## Backup Codes

Backup codes allow account recovery when the primary MFA device is unavailable.

### Generation

```
Generate 8-12 codes (10 is standard)
Each code: 8-10 random alphanumeric characters (case-insensitive)
Example: XKCD-7842, WQRT-5529
Entropy: 50+ bits per code
Format: group with hyphen for readability
```

### Storage

Store only the hash of each code (bcrypt or SHA-256 with salt). Never store plaintext. Show codes exactly once at generation — user must save them.

### Usage

Each code is single-use. Mark as used immediately on successful verification. On use, log the event and notify user via email ("a backup code was used to access your account").

Implement usage limit alerts: if user has ≤2 remaining backup codes, prompt them to regenerate.

### Regeneration

Allow users to regenerate backup codes (invalidates all old codes). Require authentication confirmation before regenerating — prevents an attacker who briefly has access from locking out the real user.

## Step-Up Authentication

Require additional authentication factors for sensitive operations, even within an already-authenticated session.

| Operation | Step-Up Required? |
|-----------|-------------------|
| View account details | No |
| Change password | Yes — re-authenticate with current password |
| Change email | Yes — verify new email + re-auth |
| Add payment method | Yes — MFA |
| Transfer funds | Yes — MFA |
| Change MFA settings | Yes — existing MFA + password |
| Delete account | Yes — MFA + explicit confirmation |
| Access admin panel | Yes — MFA every session |

Implement step-up as a separate authentication challenge, not a full login flow. Store step-up timestamp in session; challenge again after expiry (e.g., 15 minutes for sensitive operations).

## MFA Enrollment UX

Enrollment success rate determines actual security posture. Poor enrollment UX = users skip MFA.

| Practice | Rationale |
|----------|-----------|
| Show QR code + text secret for TOTP | Accessibility fallback; key managers need text |
| Verify enrollment before saving | Ensures user's app is correctly configured |
| Offer multiple MFA methods | Different users have different devices |
| Issue backup codes at enrollment | Immediate safety net |
| Explain each method briefly | Users choose the method that suits them |
| Allow testing before enforcement | Reduces support tickets |

For enterprise enforced MFA: give users a grace period (3-7 days) to enroll before blocking access. Send reminder emails.

## Account Recovery Without MFA Device

Recovery must be secure — it is the bypass path attackers target.

| Recovery Method | Security | Notes |
|----------------|---------|-------|
| Backup codes | High | Best option if user saved them |
| Admin-initiated reset | High | Requires identity verification through other channel |
| Email OTP | Medium | Depends on email account security |
| Identity document verification | High | Slow; for high-value accounts |
| Support ticket | Variable | Needs strong identity verification procedure |

Document your recovery procedure and train support staff. A weak recovery flow negates the entire MFA investment.

**Never use security questions for recovery** — answers are often guessable or found on social media.

## MFA Implementation Checklist

| Item | Status |
|------|--------|
| TOTP secrets encrypted at rest | — |
| TOTP replay prevention (last-used counter) | — |
| Backup codes hashed, single-use | — |
| WebAuthn challenge is random, one-time | — |
| WebAuthn origin and rpId validated | — |
| WebAuthn signCount checked | — |
| SMS rate limited (max 3 sends per hour per number) | — |
| MFA enrollment verified before saving | — |
| Backup codes issued at enrollment | — |
| Step-up auth on sensitive operations | — |
| Account recovery procedure documented | — |
| MFA bypass logging and alerting | — |
