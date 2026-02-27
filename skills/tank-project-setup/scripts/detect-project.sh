#!/usr/bin/env bash
# detect-project.sh — Scan a project directory and output detected stack as JSON.
# Usage: detect-project.sh [directory]
# Default directory: current working directory

set -euo pipefail

DIR="${1:-.}"

if [ ! -d "$DIR" ]; then
  echo "Error: Directory '$DIR' does not exist" >&2
  exit 1
fi

# Arrays for detected items
LANGUAGES=()
FRAMEWORKS=()
TOOLS=()
INFRA=()
CI_PLATFORM="none"
SKILLS=()

# Helper: check if file/glob exists
has_file() { [ -e "$DIR/$1" ] 2>/dev/null; }
has_glob() { compgen -G "$DIR/$1" > /dev/null 2>&1; }

# --- Tier 1: Framework-specific ---

if has_glob "next.config.*"; then
  FRAMEWORKS+=("nextjs")
fi

if has_file "angular.json" || has_file ".angular-cli.json"; then
  FRAMEWORKS+=("angular")
fi

if has_glob "nuxt.config.*"; then
  FRAMEWORKS+=("nuxtjs")
fi

if has_glob "svelte.config.*"; then
  FRAMEWORKS+=("sveltekit")
fi

if has_glob "astro.config.*"; then
  FRAMEWORKS+=("astro")
fi

if has_glob "remix.config.*"; then
  FRAMEWORKS+=("remix")
fi

# --- Tier 2: Tooling ---

if has_file "tsconfig.json"; then
  LANGUAGES+=("typescript")
fi

if has_glob "tailwind.config.*"; then
  TOOLS+=("tailwind")
fi

if has_glob "playwright.config.*"; then
  TOOLS+=("playwright")
fi

if has_glob "cypress.config.*" || has_file "cypress.json"; then
  TOOLS+=("cypress")
fi

if has_glob "jest.config.*" || has_glob "vitest.config.*"; then
  TOOLS+=("unit-testing")
fi

if has_file "prisma/schema.prisma"; then
  TOOLS+=("prisma")
fi

if has_glob "drizzle.config.*"; then
  TOOLS+=("drizzle")
fi

# --- Tier 3: Language & Runtime ---

if has_file "package.json"; then
  LANGUAGES+=("javascript")

  # Deep inspect package.json for frameworks
  if command -v jq &> /dev/null; then
    PKG="$DIR/package.json"
    DEPS=$(jq -r '(.dependencies // {}) + (.devDependencies // {}) | keys[]' "$PKG" 2>/dev/null || true)

    if echo "$DEPS" | grep -qx "react"; then
      FRAMEWORKS+=("react")
    fi
    if echo "$DEPS" | grep -qx "express"; then
      # Only flag as Express API if no frontend framework detected
      if ! echo "$DEPS" | grep -qxE "next|@angular/core|vue|nuxt"; then
        FRAMEWORKS+=("express")
      fi
    fi
    if echo "$DEPS" | grep -qx "vue"; then
      FRAMEWORKS+=("vue")
    fi
    if echo "$DEPS" | grep -qxE "prisma|@prisma/client"; then
      TOOLS+=("prisma")
    fi
    if echo "$DEPS" | grep -qx "drizzle-orm"; then
      TOOLS+=("drizzle")
    fi
    if echo "$DEPS" | grep -qx "@playwright/test"; then
      TOOLS+=("playwright")
    fi
    if echo "$DEPS" | grep -qx "cypress"; then
      TOOLS+=("cypress")
    fi
  fi
fi

if has_file "pyproject.toml" || has_file "requirements.txt" || has_file "setup.py"; then
  LANGUAGES+=("python")

  if has_file "pyproject.toml" && command -v grep &> /dev/null; then
    if grep -q "fastapi" "$DIR/pyproject.toml" 2>/dev/null; then
      FRAMEWORKS+=("fastapi")
    fi
    if grep -q "django" "$DIR/pyproject.toml" 2>/dev/null; then
      FRAMEWORKS+=("django")
    fi
    if grep -q "flask" "$DIR/pyproject.toml" 2>/dev/null; then
      FRAMEWORKS+=("flask")
    fi
    if grep -q "sqlalchemy" "$DIR/pyproject.toml" 2>/dev/null; then
      TOOLS+=("sqlalchemy")
    fi
  fi
fi

if has_file "Cargo.toml"; then
  LANGUAGES+=("rust")
fi

if has_file "go.mod"; then
  LANGUAGES+=("go")
fi

# --- Tier 4: Infrastructure ---

if has_file ".github"; then
  CI_PLATFORM="github-actions"
  INFRA+=("github")
fi

if has_file ".gitlab-ci.yml"; then
  CI_PLATFORM="gitlab-ci"
  INFRA+=("gitlab")
fi

if has_file "Dockerfile" || has_file "docker-compose.yml" || has_file "docker-compose.yaml"; then
  INFRA+=("docker")
fi

if has_file "vercel.json"; then
  INFRA+=("vercel")
fi

# --- Map to skills ---

# Deduplicate arrays
LANGUAGES=($(printf '%s\n' "${LANGUAGES[@]}" | sort -u))
FRAMEWORKS=($(printf '%s\n' "${FRAMEWORKS[@]}" | sort -u))
TOOLS=($(printf '%s\n' "${TOOLS[@]}" | sort -u))
INFRA=($(printf '%s\n' "${INFRA[@]}" | sort -u))

# Always recommend clean-code
SKILLS+=('{"name":"@tank/clean-code","version":"^3.0.0","reason":"Universal code quality"}')

# Language-based
for lang in "${LANGUAGES[@]}"; do
  case "$lang" in
    python) SKILLS+=('{"name":"@tank/python","version":"^2.0.0","reason":"Python detected"}') ;;
  esac
done

# Framework-based
for fw in "${FRAMEWORKS[@]}"; do
  case "$fw" in
    react|nextjs) SKILLS+=('{"name":"@tank/react","version":"^2.0.0","reason":"React/Next.js detected"}') ;;
    express) SKILLS+=('{"name":"@tank/node-express","version":"^2.0.0","reason":"Express detected"}') ;;
    angular|vue|sveltekit|astro|remix|nuxtjs) SKILLS+=('{"name":"@tank/frontend-craft","version":"*","reason":"Frontend framework detected"}') ;;
    fastapi|django|flask) SKILLS+=('{"name":"@tank/python","version":"^2.0.0","reason":"Python web framework detected"}') ;;
  esac
done

# Tooling-based
for tool in "${TOOLS[@]}"; do
  case "$tool" in
    tailwind) SKILLS+=('{"name":"@tank/frontend-craft","version":"*","reason":"Tailwind detected"}') ;;
    playwright|cypress) SKILLS+=('{"name":"@tank/bdd-e2e-testing","version":"^1.0.0","reason":"E2E testing detected"}')
                        SKILLS+=('{"name":"@tank/tdd-workflow","version":"^2.0.0","reason":"Testing framework detected"}') ;;
    unit-testing) SKILLS+=('{"name":"@tank/tdd-workflow","version":"^2.0.0","reason":"Unit testing detected"}') ;;
    prisma|drizzle|sqlalchemy) SKILLS+=('{"name":"@tank/relational-db-mastery","version":"^1.0.0","reason":"Database ORM detected"}') ;;
  esac
done

# React also gets frontend-craft
for fw in "${FRAMEWORKS[@]}"; do
  if [[ "$fw" == "react" || "$fw" == "nextjs" ]]; then
    SKILLS+=('{"name":"@tank/frontend-craft","version":"*","reason":"React frontend detected"}')
    break
  fi
done

# Infrastructure-based
for infra in "${INFRA[@]}"; do
  case "$infra" in
    github) SKILLS+=('{"name":"@tank/github-docs","version":"*","reason":"GitHub repository detected"}') ;;
  esac
done

# Deduplicate skills by name
UNIQUE_SKILLS=()
SEEN_NAMES=()
for skill in "${SKILLS[@]}"; do
  NAME=$(echo "$skill" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
  if [[ ! " ${SEEN_NAMES[*]} " =~ " ${NAME} " ]]; then
    UNIQUE_SKILLS+=("$skill")
    SEEN_NAMES+=("$NAME")
  fi
done

# --- Output JSON ---

json_array() {
  local arr=("$@")
  if [ ${#arr[@]} -eq 0 ]; then
    echo "[]"
    return
  fi
  local result="["
  local first=true
  for item in "${arr[@]}"; do
    if [ "$first" = true ]; then
      first=false
    else
      result+=","
    fi
    result+="\"$item\""
  done
  result+="]"
  echo "$result"
}

json_obj_array() {
  local arr=("$@")
  if [ ${#arr[@]} -eq 0 ]; then
    echo "[]"
    return
  fi
  local result="["
  local first=true
  for item in "${arr[@]}"; do
    if [ "$first" = true ]; then
      first=false
    else
      result+=","
    fi
    result+="$item"
  done
  result+="]"
  echo "$result"
}

cat <<EOF
{
  "languages": $(json_array "${LANGUAGES[@]}"),
  "frameworks": $(json_array "${FRAMEWORKS[@]}"),
  "tools": $(json_array "${TOOLS[@]}"),
  "infrastructure": $(json_array "${INFRA[@]}"),
  "ci_platform": "$CI_PLATFORM",
  "recommended_skills": $(json_obj_array "${UNIQUE_SKILLS[@]}")
}
EOF
