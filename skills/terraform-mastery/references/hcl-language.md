# HCL Language

Sources: HashiCorp Configuration Language Specification, Terraform Language Documentation (v1.9+), Brikman (Terraform: Up & Running, 3rd ed.), Winkler (Terraform in Action)

Covers: HCL syntax fundamentals, type system, expressions, built-in functions, dynamic blocks, meta-arguments (count, for_each, depends_on, lifecycle), and conditional patterns.

## Syntax Fundamentals

### Block Structure

Every Terraform resource follows the block pattern:

```hcl
block_type "label_1" "label_2" {
  argument = value

  nested_block {
    nested_argument = value
  }
}
```

| Block Type | Labels | Purpose |
|-----------|--------|---------|
| `resource` | type, name | Create infrastructure |
| `data` | type, name | Read existing infrastructure |
| `variable` | name | Declare input |
| `output` | name | Expose value |
| `locals` | (none) | Compute intermediate values |
| `module` | name | Call a child module |
| `provider` | name | Configure a provider |
| `terraform` | (none) | Configure Terraform itself |

### Identifiers and References

```hcl
# Resource reference: <type>.<name>.<attribute>
aws_instance.web.id

# Module output: module.<name>.<output>
module.vpc.vpc_id

# Variable: var.<name>
var.environment

# Local: local.<name>
local.name_prefix

# Data source: data.<type>.<name>.<attribute>
data.aws_ami.ubuntu.id

# Each/count: each.key, each.value, count.index
```

## Type System

### Primitive Types

| Type | Example | Notes |
|------|---------|-------|
| `string` | `"hello"` | Always quoted |
| `number` | `42`, `3.14` | Integer or float |
| `bool` | `true`, `false` | Lowercase only |

### Complex Types

| Type | Syntax | Use Case |
|------|--------|----------|
| `list(type)` | `["a", "b"]` | Ordered collection |
| `set(type)` | `toset(["a", "b"])` | Unordered unique collection |
| `map(type)` | `{ key = "value" }` | Key-value pairs |
| `object({...})` | `{ name = string, port = number }` | Structured data |
| `tuple([...])` | `[string, number]` | Fixed-length mixed types |

### Optional Object Attributes

Use `optional()` with defaults in variable types:

```hcl
variable "config" {
  type = object({
    instance_type = string
    volume_size   = number
    volume_type   = optional(string, "gp3")
    monitoring    = optional(bool, true)
  })
}
```

## Expressions

### String Templates

```hcl
# Interpolation
name = "app-${var.environment}-${var.region}"

# Directive (for loop in string)
config = <<-EOT
%{ for ip in var.server_ips ~}
server ${ip}
%{ endfor ~}
EOT

# Heredoc
user_data = <<-EOF
  #!/bin/bash
  echo "Hello, ${var.environment}"
EOF
```

### Conditional Expression

```hcl
instance_type = var.environment == "production" ? "m5.xlarge" : "t3.micro"
```

### For Expressions

```hcl
# Transform a list
upper_names = [for name in var.names : upper(name)]

# Filter a list
long_names = [for name in var.names : name if length(name) > 5]

# Transform a map
name_to_role = { for user in var.users : user.name => user.role }

# Nested for
all_pairs = flatten([
  for subnet_key, subnet in var.subnets : [
    for sg_key, sg in var.security_groups : {
      subnet_id = subnet.id
      sg_id     = sg.id
    }
  ]
])
```

### Splat Expressions

```hcl
# Equivalent to [for o in aws_instance.web : o.id]
instance_ids = aws_instance.web[*].id

# Attribute-only splat
names = var.users[*].name
```

## Built-in Functions

### String Functions

| Function | Example | Result |
|----------|---------|--------|
| `format` | `format("Hello, %s!", "world")` | `"Hello, world!"` |
| `join` | `join(", ", ["a", "b", "c"])` | `"a, b, c"` |
| `split` | `split(",", "a,b,c")` | `["a", "b", "c"]` |
| `replace` | `replace("hello", "l", "L")` | `"heLLo"` |
| `trimprefix` | `trimprefix("helloworld", "hello")` | `"world"` |
| `regex` | `regex("^(\\w+)@", "user@example.com")` | `"user"` |
| `lower`/`upper` | `lower("HELLO")` | `"hello"` |

### Collection Functions

| Function | Purpose |
|----------|---------|
| `length(list)` | Count elements |
| `flatten(list_of_lists)` | Flatten nested lists |
| `merge(map1, map2)` | Merge maps (later wins) |
| `lookup(map, key, default)` | Safe map access |
| `contains(list, value)` | Membership test |
| `distinct(list)` | Remove duplicates |
| `keys(map)` / `values(map)` | Extract keys or values |
| `zipmap(keys, values)` | Create map from two lists |
| `coalesce(val1, val2)` | First non-null/empty |
| `try(expr, fallback)` | Safe evaluation with fallback |
| `one(list)` | Extract single element or null |

### Networking Functions

| Function | Example | Result |
|----------|---------|--------|
| `cidrsubnet` | `cidrsubnet("10.0.0.0/16", 8, 1)` | `"10.0.1.0/24"` |
| `cidrhost` | `cidrhost("10.0.1.0/24", 5)` | `"10.0.1.5"` |
| `cidrnetmask` | `cidrnetmask("10.0.0.0/16")` | `"255.255.0.0"` |

### Encoding Functions

| Function | Purpose |
|----------|---------|
| `jsonencode` / `jsondecode` | JSON serialization |
| `yamlencode` / `yamldecode` | YAML serialization |
| `base64encode` / `base64decode` | Base64 encoding |
| `templatefile(path, vars)` | Render template file |
| `file(path)` | Read file contents |
| `filebase64(path)` | Read file as base64 |

## Dynamic Blocks

Generate repeated nested blocks from collections:

```hcl
resource "aws_security_group" "web" {
  name = "web-sg"

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
```

Use dynamic blocks sparingly -- they reduce readability. Prefer explicit blocks when the number of blocks is small and fixed.

## Meta-Arguments

### count

```hcl
resource "aws_instance" "web" {
  count = var.create_instances ? var.instance_count : 0
  ami   = var.ami_id
  tags  = { Name = "web-${count.index}" }
}
```

Avoid `count` with lists that may change order. Removing an item from the middle re-indexes all subsequent resources, causing unnecessary destruction and recreation.

### for_each

```hcl
resource "aws_subnet" "private" {
  for_each          = toset(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  availability_zone = each.value
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, index(var.availability_zones, each.value))
  tags              = { Name = "private-${each.key}" }
}
```

Resources are addressed as `aws_subnet.private["us-east-1a"]` -- stable keys survive reordering.

### depends_on

```hcl
resource "aws_instance" "app" {
  depends_on = [aws_iam_role_policy_attachment.app]
}
```

Use `depends_on` only when Terraform cannot infer the dependency from attribute references. Explicit dependencies are a last resort.

### lifecycle

```hcl
resource "aws_instance" "critical" {
  lifecycle {
    prevent_destroy       = true
    create_before_destroy = true
    ignore_changes        = [tags["LastUpdated"]]

    precondition {
      condition     = var.instance_type != "t2.micro"
      error_message = "Production instances must not use t2.micro."
    }

    postcondition {
      condition     = self.public_ip != ""
      error_message = "Instance must have a public IP."
    }
  }
}
```

| Lifecycle Rule | Use Case |
|---------------|----------|
| `prevent_destroy` | Critical resources (databases, state buckets) |
| `create_before_destroy` | Zero-downtime replacements |
| `ignore_changes` | Attributes managed outside Terraform (auto-scaling tags) |
| `replace_triggered_by` | Force replacement when a dependency changes |
| `precondition` | Validate input assumptions before create |
| `postcondition` | Validate resource state after create |

## Conditional Resource Creation

### Toggle with count

```hcl
resource "aws_cloudwatch_log_group" "app" {
  count = var.enable_logging ? 1 : 0
  name  = "/app/${var.name}"
}

# Reference conditionally created resource
log_group_arn = var.enable_logging ? aws_cloudwatch_log_group.app[0].arn : null
```

### Toggle with for_each

```hcl
resource "aws_route53_record" "alias" {
  for_each = var.create_dns ? { "main" = true } : {}
  name     = var.domain_name
  type     = "A"
}
```

## Moved Blocks

Refactor resource addresses without destroying and recreating:

```hcl
moved {
  from = aws_instance.web
  to   = aws_instance.application
}

moved {
  from = aws_instance.app
  to   = module.compute.aws_instance.app
}
```

Run `terraform plan` after adding `moved` blocks to confirm no destruction. Remove `moved` blocks after the next successful apply across all environments.

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| `count` with dynamic lists | Reordering causes recreation | Use `for_each` with stable keys |
| Deeply nested dynamic blocks | Unreadable configuration | Flatten structure or use modules |
| Circular references | Plan fails | Break cycle with `depends_on` or restructure |
| Missing `depends_on` for IAM | Race condition on first apply | Add explicit dependency on policy attachment |
| Sensitive in `for_each` | Error: sensitive values not allowed | Use `nonsensitive()` wrapper or restructure |
| `templatefile` path | Relative to module root | Use `${path.module}/templates/file.tpl` |
