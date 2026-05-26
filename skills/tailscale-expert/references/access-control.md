# Tailscale Access Control

Sources: Tailscale official documentation (2025-2026)

## Overview

The tailnet policy file is the single source of truth for access control,
written in HuJSON — JSON with C-style comments (`//`, `/* */`) and trailing
commas. Edit it in the admin console under Access Controls or via the
Tailscale API. Changes take effect immediately across all tailnet devices.

Top-level keys recognized by the policy parser:

| Key | Purpose |
|-----|---------|
| `groups` | Named sets of users |
| `tagOwners` | Who may assign each tag |
| `hosts` | IP address aliases |
| `acls` | Legacy access rules (action/src/dst) |
| `grants` | Next-generation access rules |
| `autoApprovers` | Automatic route and exit-node approval |
| `ssh` | Tailscale SSH rules |
| `tests` | Policy test assertions |
| `postures` | Device posture attribute definitions |
| `ipsets` | Named network segments |
| `nodeAttrs` | Per-device capability attributes |

## ACLs vs Grants

Grants are the recommended syntax for new policies. Legacy ACLs remain
supported indefinitely and coexist with grants in the same file.

| Dimension | Legacy ACLs | Grants |
|-----------|-------------|--------|
| Syntax key | `acls` | `grants` |
| Direction | Bidirectional | Unidirectional (src -> dst) |
| Application-layer permissions | Not supported | Supported via `app` key |
| Port specification | Embedded in `dst` field | Separate `ip` key |
| `via` relay node | Not supported | Supported |
| Recommended for new policies | No | Yes |
| Will be removed | No | N/A |

Use grants for new policies; use legacy ACLs only when migrating
incrementally.

## Grants Syntax

A grant allows traffic from `src` to `dst`. All other fields are optional.

```hujson
{
  "grants": [
    {
      // IP-level: group:dev reaches tag:prod on TCP 443.
      "src": ["group:dev"],
      "dst": ["tag:prod"],
      "ip":  ["tcp:443"],
    },
    {
      // Application-layer: group:ops SSHes into tag:prod as any user.
      "src": ["group:ops"],
      "dst": ["tag:prod"],
      "app": {
        "tailscale.com/cap/ssh": [{"action": "accept", "users": ["*"]}],
      },
    },
    {
      // Via relay: tag:sensor reaches collector through a relay node.
      "src": ["tag:sensor"],
      "dst": ["192.0.2.50:9000"],
      "via": ["tag:collector-relay"],
    },
  ],
}
```

### Grant Fields

| Field | Type | Description |
|-------|------|-------------|
| `src` | array | Sources: users, groups, tags, CIDRs, `*` |
| `dst` | array | Destinations: tags, hosts, CIDRs, `host:port` |
| `ip` | array | Protocols/ports: `tcp:443`, `udp:53`, `icmp`, `*` |
| `app` | object | Application-layer capability map |
| `via` | array | Relay nodes that must be traversed |
| `srcPosture` | array | Posture requirements for the source device |

When `ip` and `app` are both omitted, the grant allows all IP traffic.

## Legacy ACL Syntax

```hujson
{
  "acls": [
    // Allow group:dev to reach tag:staging on ports 22 and 443.
    {
      "action": "accept",
      "src": ["group:dev"],
      "dst": ["tag:staging:22", "tag:staging:443"],
    },
    // Allow tag:monitoring to scrape any device on port 9100.
    {"action": "accept", "src": ["tag:monitoring"], "dst": ["*:9100"]},
  ],
}
```

| Field | Values | Description |
|-------|--------|-------------|
| `action` | `"accept"` | Only accepted value; unmatched traffic is denied |
| `src` | array | Sources: users, groups, tags, CIDRs, `*` |
| `dst` | array | `"target:port"` or `"target:*"` for all ports |

Port ranges use a hyphen: `"tag:db:5432-5433"`. Protocol defaults to TCP.

## Groups

Groups are named sets of users (prefix `group:`). Groups can nest other
groups and are evaluated at policy-parse time.

```hujson
{
  "groups": {
    "group:dev":          ["alice@example.com", "bob@example.com"],
    "group:ops":          ["carol@example.com"],
    "group:all-engineers": ["group:dev", "group:ops"],
  },
}
```

### Autogroups

Built-in groups that require no declaration:

| Autogroup | Members |
|-----------|---------|
| `autogroup:admin` | Tailnet administrators |
| `autogroup:member` | All authenticated tailnet members |
| `autogroup:tagged` | All tagged devices |
| `autogroup:nonroot` | Any OS username that is not `root` |
| `autogroup:internet` | The public internet (exit-node rules) |

## Tags and tagOwners

Tags are labels applied to devices, not users. Declare tags in `tagOwners`
before assigning them. An empty list means only admins may assign the tag.

```hujson
{
  "tagOwners": {
    "tag:prod":       ["group:ops"],
    "tag:staging":    ["group:dev", "group:ops"],
    "tag:k8s":        ["autogroup:admin"],
    "tag:restricted": [],
  },
}
```

### Tags vs Groups

| Dimension | Tags | Groups |
|-----------|------|--------|
| Applied to | Devices | Users |
| Assigned via | `tailscale up --advertise-tags` | Policy file only |
| Survives user leaving | Yes | No |
| Key expiry | Disabled when tagged | Normal expiry |
| Use case | Server identity, CI nodes | Human access control |

Tagged devices lose their user association and have key expiry disabled by
default — appropriate for long-running servers and CI nodes.

## Hosts

`hosts` defines IP address aliases for use in ACL and grant `dst` fields.
Aliases do not affect MagicDNS or device registration. Example:
`"corp-db": "100.64.0.10"`, `"on-prem-range": "10.0.0.0/8"`.

## autoApprovers

Eliminates the manual approval step for subnet routes and exit nodes.

```hujson
{
  "autoApprovers": {
    "routes": {
      "10.0.0.0/8":     ["tag:subnet-router"],
      "192.168.0.0/16": ["tag:subnet-router"],
    },
    "exitNode": ["tag:exit-node"],
  },
}
```

Without this section, an admin must manually approve each advertised route.

## SSH Rules

Tailscale SSH rules control who can SSH into which devices, bypassing
traditional SSH keys. Rules live in the `ssh` top-level key.

```hujson
{
  "ssh": [
    {
      // ops must re-authenticate before SSHing into prod.
      "action": "check",
      "src":    ["group:ops"],
      "dst":    ["tag:prod"],
      "users":  ["root", "*"],
    },
    {
      // dev can SSH into staging as non-root without re-auth.
      "action": "accept",
      "src":    ["group:dev"],
      "dst":    ["tag:staging"],
      "users":  ["autogroup:nonroot"],
    },
    {"action": "deny", "src": ["*"], "dst": ["*"], "users": ["*"]},
  ],
}
```

| Field | Values | Description |
|-------|--------|-------------|
| `action` | `accept`, `check`, `deny` | `check` requires SSO re-authentication |
| `src` | array | Who is connecting |
| `dst` | array | Target devices |
| `users` | array | OS usernames; `*` means any |

Session recording is configured via the admin console or API, not in the policy file.

## Tests

Test assertions are evaluated before the policy is saved. A failing test
blocks the save, preventing lockouts.

```hujson
{
  "tests": [
    // alice (group:dev) can reach staging on 443.
    {"src": "alice@example.com", "dst": "tag:staging", "accept": ["tcp:443"]},
    // alice cannot reach prod on 22.
    {"src": "alice@example.com", "dst": "tag:prod",    "deny":   ["tcp:22"]},
    // carol (group:ops) can reach prod on 22.
    {"src": "carol@example.com", "dst": "tag:prod",    "accept": ["tcp:22"]},
  ],
}
```

| Field | Description |
|-------|-------------|
| `src` | A specific user email or tag |
| `dst` | A tag, host alias, or CIDR |
| `accept` | Protocols/ports that must be permitted |
| `deny` | Protocols/ports that must be blocked |

Write at least one test per rule, including negative tests for sensitive
resources. Tests also run via the Tailscale API validate endpoint.

## Postures

Device postures define compliance conditions sourced from device registration
data and third-party integrations (CrowdStrike, Kolide).

```hujson
{
  "postures": {
    "posture:compliant": {
      "tailscale.com/device/os-version": {"minimum": "14.0"},
      "tailscale.com/device/fde":        {"eq": true},
    },
  },
  "grants": [
    {
      "src":        ["group:dev"],
      "dst":        ["tag:prod"],
      "ip":         ["tcp:443"],
      "srcPosture": ["posture:compliant"],
    },
  ],
}
```

Posture enforcement requires a plan that includes device posture features.

## ipsets

`ipsets` define named sets of IPs or CIDRs for use in grants and ACLs.
They are a readability aid evaluated at policy-parse time.

```hujson
{
  "ipsets": {
    "ipset:internal": ["10.10.0.0/16", "172.16.0.0/12"],
    "ipset:dns":      ["8.8.8.8", "1.1.1.1"],
  },
  "grants": [
    {"src": ["group:dev"], "dst": ["ipset:internal"], "ip": ["tcp:443"]},
  ],
}
```

## nodeAttrs

`nodeAttrs` apply capability attributes to devices or groups. The primary use
case is enabling Funnel. Without a `funnel` entry, `tailscale funnel` fails
even for admins — this is an intentional safety gate.

```hujson
{
  "nodeAttrs": [
    {"target": ["tag:public"],          "attr": ["funnel"]},
    {"target": ["alice@example.com"],   "attr": ["funnel"]},
  ],
}
```

## Visual Policy Editor

The admin console Access Controls page provides a visual editor alongside the
raw HuJSON editor, exposing group management, tag configuration, an ACL rule
builder, SSH rules, and a test runner. Both editors are synchronized. Use the
visual editor for onboarding; use the raw editor for GitOps workflows.

## GitOps Workflow

Manage the policy file as code using the Tailscale API.

| Operation | Method | Path |
|-----------|--------|------|
| Read policy | GET | `/api/v2/tailnet/{tailnet}/acl` |
| Write policy | POST | `/api/v2/tailnet/{tailnet}/acl` |
| Preview diff | POST | `/api/v2/tailnet/{tailnet}/acl/preview` |
| Run tests | POST | `/api/v2/tailnet/{tailnet}/acl/validate` |

Set `Content-Type: application/hujson` when writing. Use an API key or OAuth
client with the `acl:write` scope. In CI, run validate before write; a
non-zero exit from validate blocks the apply step.

## Complete Policy Example

```hujson
{
  "groups": {
    "group:dev": ["alice@example.com", "bob@example.com"],
    "group:ops": ["carol@example.com"],
  },
  "tagOwners": {
    "tag:prod":    ["group:ops"],
    "tag:staging": ["group:dev", "group:ops"],
    "tag:ci":      ["autogroup:admin"],
  },
  "hosts": {"corp-db": "100.64.0.10"},
  "autoApprovers": {
    "routes":   {"10.0.0.0/8": ["tag:prod"]},
    "exitNode": ["tag:prod"],
  },
  "grants": [
    // dev reaches staging on web ports.
    {"src": ["group:dev"], "dst": ["tag:staging"], "ip": ["tcp:80", "tcp:443"]},
    // ops reaches prod on web and DB ports.
    {"src": ["group:ops"], "dst": ["tag:prod"],    "ip": ["tcp:443", "tcp:5432"]},
    // ops SSHes into prod with re-auth check.
    {
      "src": ["group:ops"],
      "dst": ["tag:prod"],
      "app": {"tailscale.com/cap/ssh": [{"action": "check", "users": ["*"]}]},
    },
    // ci tag reaches staging for deployment.
    {"src": ["tag:ci"], "dst": ["tag:staging"], "ip": ["tcp:22", "tcp:443"]},
  ],
  "ssh": [
    {"action": "check",  "src": ["group:ops"], "dst": ["tag:prod"],    "users": ["*"]},
    {"action": "accept", "src": ["group:dev"], "dst": ["tag:staging"], "users": ["autogroup:nonroot"]},
  ],
  "tests": [
    {"src": "alice@example.com", "dst": "tag:staging", "accept": ["tcp:443"]},
    {"src": "alice@example.com", "dst": "tag:prod",    "deny":   ["tcp:443"]},
    {"src": "carol@example.com", "dst": "tag:prod",    "accept": ["tcp:443"]},
  ],
}
```

## Common Patterns

### Dev / Staging / Prod Separation

Tag devices by environment. Dev accesses staging only; ops accesses all.

```hujson
{
  "tagOwners": {
    "tag:dev-env": ["group:dev"],
    "tag:staging": ["group:dev", "group:ops"],
    "tag:prod":    ["group:ops"],
  },
  "grants": [
    {"src": ["group:dev"], "dst": ["tag:dev-env", "tag:staging"], "ip": ["*"]},
    {"src": ["group:ops"], "dst": ["tag:dev-env", "tag:staging", "tag:prod"], "ip": ["*"]},
  ],
}
```

### Contractor Access

Contractors get a dedicated group with narrow access and a deny test
confirming they cannot reach production.

```hujson
{
  "groups": {"group:contractors": ["vendor@partner.com"]},
  "tagOwners": {"tag:contractor-target": ["autogroup:admin"]},
  "grants": [
    {"src": ["group:contractors"], "dst": ["tag:contractor-target"], "ip": ["tcp:443"]},
  ],
  "tests": [
    {"src": "vendor@partner.com", "dst": "tag:prod", "deny": ["tcp:443"]},
  ],
}
```

### SSH-Only Access

Grant SSH access without IP-level permissions for bastion-style access.

```hujson
{
  "grants": [
    {
      "src": ["group:ops"],
      "dst": ["tag:bastion"],
      "app": {
        "tailscale.com/cap/ssh": [{"action": "accept", "users": ["ubuntu"]}],
      },
    },
  ],
  "ssh": [
    {"action": "accept", "src": ["group:ops"], "dst": ["tag:bastion"], "users": ["ubuntu"]},
  ],
}
```

### Monitoring Scraper

Tag scrapes metrics from all devices without interactive access:

```hujson
{"tagOwners": {"tag:monitoring": ["autogroup:admin"]},
 "grants": [{"src": ["tag:monitoring"], "dst": ["*"], "ip": ["tcp:9100", "tcp:9090"]}]}
```
