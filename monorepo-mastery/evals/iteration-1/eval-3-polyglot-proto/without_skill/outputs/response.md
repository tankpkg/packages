# Short answer

Use **one monorepo** with:

- `buf` as the source-of-truth pipeline for Protobuf linting, breaking checks, and codegen
- language-specific generated SDK packages (`go`, `ts`, `python`) from the same `.proto` files
- a root task runner (`turbo` or `nx`, plus `make`/`task`) to orchestrate Go, Node, and Python commands
- strict proto versioning and CI checks so backend/frontend/ML never drift

This is usually the most reliable setup for a Go + React + Python stack.

---

## Recommended repo structure

```text
monorepo/
├─ proto/
│  ├─ buf.yaml
│  ├─ buf.gen.yaml
│  ├─ buf.lock
│  └─ acme/
│     └─ v1/
│        ├─ common.proto
│        ├─ user.proto
│        └─ feature_store.proto
├─ gen/
│  ├─ go/
│  │  ├─ go.mod
│  │  └─ acme/v1/*.pb.go
│  ├─ ts/
│  │  ├─ package.json
│  │  └─ src/gen/*.ts
│  └─ python/
│     ├─ pyproject.toml
│     └─ acme/v1/*_pb2.py
├─ services/
│  ├─ user-api/           # Go gRPC/Connect service
│  └─ billing-api/        # Go service
├─ apps/
│  └─ web/                # React app (Vite/Next)
├─ ml/
│  └─ pipeline/           # Python training/inference jobs
├─ package.json           # workspace + task scripts
├─ pnpm-workspace.yaml
├─ go.work
├─ turbo.json
└─ Makefile
```

Notes:

- Keep `proto/` as the only hand-written API contract source.
- Generate per language into `gen/*` so every runtime consumes identical schemas.
- Treat generated code as read-only.

---

## Why this tooling mix works

1. **Buf gives contract discipline**
   - Linting rules for API consistency.
   - Breaking-change detection against `main` (or a Buf registry module).
   - Reproducible plugin versions in `buf.gen.yaml`.

2. **Language-native consumption**
   - Go services import Go-generated types directly.
   - React imports TS-generated message/client code.
   - Python ML imports generated Python message classes for batch IO/events.

3. **Fast CI and local dev**
   - One command to regen all stubs.
   - Cached task runner (`turbo`/`nx`) avoids rerunning unaffected jobs.

---

## Proto authoring conventions

Example `proto/acme/v1/user.proto`:

```proto
syntax = "proto3";

package acme.v1;

option go_package = "acme.dev/mono/gen/go/acme/v1;acmev1";

message User {
  string id = 1;
  string email = 2;
  int64 created_at_unix = 3;
}

message GetUserRequest {
  string id = 1;
}

message GetUserResponse {
  User user = 1;
}

service UserService {
  rpc GetUser(GetUserRequest) returns (GetUserResponse);
}
```

Rules that save pain:

- Never reuse field numbers.
- Reserve removed fields: `reserved 4; reserved "old_name";`.
- Use package versioning (`acme.v1`, then `acme.v2` for breaking changes).
- Keep common types in `common.proto` to avoid copy/paste drift.

---

## Buf config (core of the setup)

`proto/buf.yaml`

```yaml
version: v2
modules:
  - path: .
lint:
  use:
    - STANDARD
breaking:
  use:
    - FILE
```

`proto/buf.gen.yaml`

```yaml
version: v2
plugins:
  # Go messages
  - remote: buf.build/protocolbuffers/go
    out: ../gen/go
    opt:
      - paths=source_relative

  # Go gRPC stubs
  - remote: buf.build/grpc/go
    out: ../gen/go
    opt:
      - paths=source_relative

  # TypeScript messages (ES)
  - remote: buf.build/bufbuild/es
    out: ../gen/ts/src/gen
    opt:
      - target=ts

  # Connect-Web/Connect client stubs for React
  - remote: buf.build/connectrpc/es
    out: ../gen/ts/src/gen
    opt:
      - target=ts

  # Python messages
  - remote: buf.build/protocolbuffers/python
    out: ../gen/python

  # Python gRPC stubs
  - remote: buf.build/grpc/python
    out: ../gen/python
```

Typical commands:

```bash
cd proto
buf dep update
buf lint
buf breaking --against '.git#branch=main,subdir=proto'
buf generate
```

---

## Go workspace wiring

Root `go.work`:

```go
go 1.23

use (
  ./services/user-api
  ./services/billing-api
  ./gen/go
)
```

`gen/go/go.mod`:

```go
module acme.dev/mono/gen/go

go 1.23

require (
  google.golang.org/grpc v1.67.1
  google.golang.org/protobuf v1.35.1
)
```

Then in a service:

```go
import acmev1 "acme.dev/mono/gen/go/acme/v1"
```

---

## React/TypeScript wiring

`gen/ts/package.json`:

```json
{
  "name": "@acme/proto",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "./src/gen/index.ts",
  "types": "./src/gen/index.ts",
  "dependencies": {
    "@bufbuild/protobuf": "^2.2.0",
    "@connectrpc/connect": "^1.6.1",
    "@connectrpc/connect-web": "^1.6.1"
  }
}
```

`apps/web/package.json` (relevant part):

```json
{
  "dependencies": {
    "@acme/proto": "workspace:*"
  }
}
```

Usage in React:

```ts
import { createPromiseClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { UserService } from "@acme/proto/src/gen/acme/v1/user_connect";

const transport = createConnectTransport({ baseUrl: "/api" });
const client = createPromiseClient(UserService, transport);
```

---

## Python ML wiring

`gen/python/pyproject.toml`:

```toml
[project]
name = "acme-proto"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "protobuf>=5.28.0",
  "grpcio>=1.66.0"
]

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
```

`ml/pipeline/pyproject.toml` (relevant):

```toml
[project]
name = "acme-ml-pipeline"
version = "0.1.0"
dependencies = [
  "acme-proto",
  "pandas",
  "scikit-learn"
]

[tool.uv.sources]
acme-proto = { path = "../../gen/python", editable = true }
```

Usage:

```python
from acme.v1.user_pb2 import User

u = User(id="123", email="ml@acme.dev", created_at_unix=1730000000)
payload = u.SerializeToString()
```

---

## Root orchestration (important for developer UX)

`pnpm-workspace.yaml`:

```yaml
packages:
  - "apps/*"
  - "gen/ts"
  - "packages/*"
```

Root `package.json` scripts:

```json
{
  "private": true,
  "scripts": {
    "proto:lint": "cd proto && buf lint",
    "proto:breaking": "cd proto && buf breaking --against '.git#branch=main,subdir=proto'",
    "proto:gen": "cd proto && buf generate",
    "build": "turbo run build",
    "test": "turbo run test"
  },
  "devDependencies": {
    "turbo": "^2.0.0"
  }
}
```

`turbo.json`:

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "proto:gen": {
      "outputs": ["gen/**"]
    },
    "build": {
      "dependsOn": ["^build", "proto:gen"],
      "outputs": ["dist/**", "build/**"]
    },
    "test": {
      "dependsOn": ["proto:gen"]
    }
  }
}
```

Optional `Makefile` wrapper:

```makefile
.PHONY: proto lint test build

proto:
	pnpm run proto:gen

lint:
	pnpm run proto:lint
	cd services/user-api && go vet ./...
	cd apps/web && pnpm lint
	cd ml/pipeline && uv run ruff check .

test:
	cd services/user-api && go test ./...
	cd apps/web && pnpm test
	cd ml/pipeline && uv run pytest

build: proto
	cd services/user-api && go build ./...
	cd apps/web && pnpm build
```

---

## CI pipeline shape

At minimum in CI:

1. `buf lint`
2. `buf breaking --against main`
3. `buf generate`
4. fail if generated artifacts differ (`git diff --exit-code`)
5. run Go/TS/Python tests

This catches schema drift before it hits runtime.

---

## Practical recommendations

- **Use ConnectRPC for browser clients** instead of raw gRPC-web unless you have a hard requirement otherwise.
- **Pin plugin/runtime versions** (Buf plugins, protobuf libs, grpc libs).
- **Decide generated-code policy early**:
  - Commit generated code if you want easier consumer onboarding and deterministic reviews.
  - Don’t commit generated code if you prefer smaller diffs and strict reproducibility in CI.
- **Keep protobuf ownership clear**: one team/review path for `proto/`.

---

## A solid default stack (if you want one opinionated answer)

- Proto: `buf`
- Go backend: `grpc-go` or `connect-go`
- Web client: `React + @connectrpc/connect-web + bufbuild/es`
- Python ML: `protobuf + grpcio` generated via Buf
- Orchestration: `turbo + pnpm`, `go.work`, `uv` for Python

If you implement the structure above, you get a single contract source, consistent generated types in all three ecosystems, and CI-enforced compatibility guarantees.
