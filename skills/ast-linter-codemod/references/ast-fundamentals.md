# AST Fundamentals and Tool Selection

Sources: Nystrom (Crafting Interpreters), Kyle (Babel Plugin Handbook), ESTree Specification, 2025-2026 ecosystem research

This reference is the entry point for the skill. Read it before any tool-specific reference.
It covers the mental model, the universal pipeline, and the decision logic for choosing tools.
Examples use TypeScript unless otherwise noted.

---

## 1. The AST Mental Model

Source code is text. Linters and codemods cannot reliably work on text — a regex cannot
distinguish a function call from a comment containing the same characters. Parsers solve
this by converting text into an **Abstract Syntax Tree**: a tree of typed nodes where each
node represents a syntactic construct (a function, an import, a binary expression).

The word "abstract" means the tree captures structure, not formatting. Whitespace, semicolons,
and parentheses used only for grouping are discarded. What remains is the semantic skeleton.

Every linter and codemod operates on this skeleton:
- A linter **reads** the tree, finds nodes matching a pattern, and reports violations.
- A codemod **reads** the tree, mutates matching nodes, and serializes the result back to text.

The tree is the shared interface. Understanding its shape is the prerequisite for everything else.

---

## 2. The Parse → Transform → Generate Pipeline

Every AST tool — ESLint, jscodeshift, ts-morph, Babel, ast-grep — implements the same
three-phase pipeline internally. Knowing the phases explains why tools behave as they do.

```
SOURCE TEXT
    │
    ▼  PARSE: Lexer → token stream → Parser → AST
    │         (TypeScript: recursive descent; Babel: Babylon; ast-grep: tree-sitter)
    ▼  TRANSFORM / ANALYZE: Traverse AST via Visitor pattern
    │         Linters: read + report violations
    │         Codemods: read + mutate nodes
    ▼  GENERATE: Serialize AST back to source text
               Naive: pretty-print everything (Babel generator)
               Smart: reprint only changed nodes (recast, used by jscodeshift)
    ▼
OUTPUT TEXT (or diagnostic report)
```

**Why the generate phase matters for codemods**: naive generators reformat the entire file.
`recast` (used by jscodeshift) tracks which nodes were modified and reprints only those,
preserving the original formatting of everything else. This is why jscodeshift codemods
produce minimal diffs. ts-morph uses a similar strategy via the TypeScript printer.

**TypeScript's pipeline adds two extra phases** between parse and transform:
- **Binder**: walks the AST and creates a symbol table (maps identifiers to declarations)
- **Checker**: uses the symbol table to perform type inference and validation

ts-morph and the raw TypeScript Compiler API expose the Checker, giving access to resolved
types. jscodeshift and ast-grep do not — they are syntactic-only tools.

---

## 3. AST Node Types Reference

### ESTree Nodes (JavaScript / TypeScript base)

ESTree is the community standard for JavaScript ASTs. Babel, ESLint, jscodeshift, and
acorn all use ESTree-compatible node shapes. TypeScript extends ESTree with `TS*` prefixed
nodes.

| Node Type | Represents | Key Properties |
|-----------|-----------|----------------|
| `Program` | Root of the file | `body: Statement[]` |
| `ImportDeclaration` | `import { X } from 'y'` | `specifiers`, `source` |
| `ExportNamedDeclaration` | `export const x = ...` | `declaration`, `specifiers` |
| `ExportDefaultDeclaration` | `export default ...` | `declaration` |
| `FunctionDeclaration` | `function foo() {}` | `id`, `params`, `body`, `async` |
| `ArrowFunctionExpression` | `() => {}` | `params`, `body`, `async` |
| `ClassDeclaration` | `class Foo {}` | `id`, `superClass`, `body` |
| `MethodDefinition` | Method inside a class | `key`, `value`, `kind`, `static` |
| `VariableDeclaration` | `const x = 1` | `declarations`, `kind` |
| `VariableDeclarator` | `x = 1` (inside declaration) | `id`, `init` |
| `ExpressionStatement` | A statement wrapping an expression | `expression` |
| `CallExpression` | `foo(a, b)` | `callee`, `arguments` |
| `MemberExpression` | `obj.prop` | `object`, `property`, `computed` |
| `Identifier` | Any name: `foo`, `x`, `React` | `name` |
| `Literal` / `StringLiteral` | `'hello'`, `42`, `true` | `value` |
| `TemplateLiteral` | `` `Hello ${name}` `` | `quasis`, `expressions` |
| `ObjectExpression` | `{ a: 1, b: 2 }` | `properties` |
| `ArrayExpression` | `[1, 2, 3]` | `elements` |
| `BinaryExpression` | `a + b`, `x === y` | `left`, `operator`, `right` |
| `AwaitExpression` | `await fetch(url)` | `argument` |
| `ReturnStatement` | `return x` | `argument` |
| `IfStatement` | `if (x) {}` | `test`, `consequent`, `alternate` |
| `BlockStatement` | `{ ... }` | `body: Statement[]` |
| `JSXElement` | `<Button />` | `openingElement`, `closingElement`, `children` |
| `JSXAttribute` | `className="foo"` | `name`, `value` |

### TypeScript-Specific Nodes

| Node Type | Represents | Key Properties |
|-----------|-----------|----------------|
| `TSTypeAnnotation` | `: string` after a binding | `typeAnnotation` |
| `TSTypeReference` | `Array<string>`, `Foo` | `typeName`, `typeParameters` |
| `TSInterfaceDeclaration` | `interface Foo {}` | `id`, `body`, `extends` |
| `TSTypeAliasDeclaration` | `type Foo = string` | `id`, `typeAnnotation` |
| `TSAsExpression` | `value as string` | `expression`, `typeAnnotation` |
| `TSArrayType` | `string[]` | `elementType` |
| `TSUnionType` | `string \| number` | `types` |
| `TSIntersectionType` | `A & B` | `types` |
| `TSPropertySignature` | Property in an interface | `key`, `typeAnnotation`, `optional` |
| `TSMethodSignature` | Method in an interface | `key`, `params`, `returnType` |
| `TSEnumDeclaration` | `enum Direction {}` | `id`, `members` |
| `TSNonNullExpression` | `value!` | `expression` |
| `Decorator` | `@Injectable()` | `expression` |

**Practical tip**: Use [AST Explorer](https://astexplorer.net/) to inspect the exact node
shape for any code snippet before writing a transform. Select the parser that matches your
tool (Babel for jscodeshift, TypeScript for ts-morph/ESLint with typescript-eslint).

---

## 4. The Visitor Pattern

The Visitor pattern is how every AST tool traverses the tree. Instead of writing recursive
traversal code, you declare handlers for node types. The traversal engine calls your handler
when it encounters a matching node.

### How Visitors Work

```
Traversal engine walks the tree depth-first.
For each node:
  1. Call visitor[node.type].enter (or visitor[node.type] if no enter/exit split)
  2. Recurse into children
  3. Call visitor[node.type].exit
```

In Babel and ESLint, visitors are plain objects:

```typescript
// Babel plugin visitor
visitor: {
  CallExpression(path) {
    // called on enter (before children are visited)
  },
  FunctionDeclaration: {
    enter(path) { /* before children */ },
    exit(path)  { /* after children */ },
  }
}
```

**Enter vs exit**: Use `enter` (the default) when you need to inspect a node before its
children are processed. Use `exit` when you need to know the final state of a subtree —
for example, checking whether a function contains any `await` expressions.

### Path vs Node

The `path` object wraps a node and provides the mutation API. The `node` is the raw AST
data. This distinction matters:

| `path` | `node` |
|--------|--------|
| Wrapper with traversal context | Raw AST data object |
| Has `.parent`, `.scope`, `.key` | Has `.type`, `.start`, `.end` |
| Has mutation methods: `.replaceWith()`, `.remove()`, `.insertAfter()` | Immutable data |
| Has type predicates: `.isIdentifier()`, `.isCallExpression()` | No methods |

Always mutate through `path`, not by directly reassigning `node` properties — except for
simple in-place edits like `path.node.source.value = 'new-module'`, which work because
recast tracks the node reference.

### Scope and Bindings

Scope tracks which identifiers are declared where. This is essential for safe transforms:
renaming a variable without scope awareness can accidentally rename a different variable
with the same name in a different scope.

```typescript
// Babel: scope-aware rename
path.scope.rename('oldName', 'newName');
// Renames only the binding in the current scope and its references

// ESLint: access scope manager
const scope = context.sourceCode.getScope(node);
const variable = scope.variables.find(v => v.name === 'target');
```

ts-morph handles scope automatically through the TypeScript type system — `rename()` and
`findReferencesAsNodes()` are scope-aware by construction.

---

## 5. Tool Selection Decision Tree

Start here. The wrong tool choice costs hours. The right tool makes the task trivial.

```
What is the primary goal?
│
├── FIND patterns (read-only search)
│   ├── Any language, structural search → ast-grep (sg run -p '...')
│   ├── TypeScript with type resolution → TypeScript Language Server / ts-morph
│   └── Simple text search → ripgrep (not an AST tool)
│
├── LINT (report violations, optionally fix)
│   ├── Standard JS/TS rules, editor integration → ESLint custom rule
│   ├── Structural patterns, YAML config, no JS needed → ast-grep YAML rules
│   ├── Security scanning across languages → Semgrep
│   └── Type-aware lint (needs type info) → ESLint + typescript-eslint
│
├── CODEMOD (transform source files)
│   │
│   ├── Does the transform need TYPE INFORMATION?
│   │   ├── Yes (e.g., "add return type", "find all callers of this method") → ts-morph
│   │   └── No → continue below
│   │
│   ├── Is the pattern SIMPLE (one-to-one replacement)?
│   │   ├── Yes → ast-grep --rewrite (fastest, no code needed)
│   │   └── No → continue below
│   │
│   ├── Is the codebase JAVASCRIPT or TYPESCRIPT (no type info needed)?
│   │   ├── Yes, complex logic → jscodeshift
│   │   └── Yes, declarative style → Putout
│   │
│   └── Is this a BUILD-TIME transform (runs on every compile)?
│       ├── Performance critical → SWC plugin (Rust)
│       └── Ecosystem/plugins matter → Babel plugin
│
└── MIGRATE large codebase
    ├── Flow → TypeScript → flow-to-typescript-codemod (Stripe/Pinterest pattern)
    ├── JS → TypeScript → ts-migrate (Airbnb)
    ├── React class → hooks → react-codemod (jscodeshift)
    ├── Angular @Input/@Output → signals → Angular Schematics (TypeScript Compiler API)
    └── Custom migration → jscodeshift + recast (syntax) or ts-morph (type-aware)
```

### Quick Scenario Reference

| Scenario | Tool | Reason |
|----------|------|--------|
| Find all async functions without try/catch | ast-grep | Structural, no type info needed |
| Rename a function across 500 files | ts-morph | Needs cross-file reference tracking |
| Migrate `lodash` imports to `lodash-es` | jscodeshift | Import string replacement, complex specifier logic |
| Remove all `console.log` calls | ast-grep `--rewrite` | Simple pattern replacement |
| Convert class components to hooks | jscodeshift (react-codemod) | Complex AST restructuring |
| Add return types to all functions | ts-morph | Needs type inference to determine the type |
| Enforce `import type` for type-only imports | ESLint + typescript-eslint | Needs type checker, editor integration |
| Detect hardcoded secrets in config objects | ast-grep YAML rule | Structural pattern, no type info |
| Build-time JSX transform | Babel plugin | Compile-time, ecosystem compatibility |
| AI agent code search | ast-grep | CLI-first, declarative, LLM-friendly |

---

## 6. Tool Comparison Matrix

| Tool | Type Info | Formatting Preservation | Speed | Learning Curve | Best Fit |
|------|-----------|------------------------|-------|----------------|----------|
| **ast-grep** | None (syntactic) | Yes (tree-sitter) | Fastest (Rust) | Low (YAML) | Search, lint, simple transforms, AI agents |
| **jscodeshift** | None | Yes (via recast) | Medium | Medium | Complex JS/TS codemods |
| **ts-morph** | Full TypeScript | Partial | Medium | Medium | TypeScript-specific transforms, cross-file analysis |
| **ESLint custom rule** | Optional (via typescript-eslint) | N/A (reports only) | Fast | Low–Medium | Linting with editor/CI integration |
| **Babel plugin** | None | No (use recast wrapper) | Medium | Medium | Build-time transforms, transpilation |
| **TypeScript Compiler API** | Full | No (use printer) | Medium | High | Deep TypeScript tooling, Angular-style migrations |
| **SWC plugin** | None | No | Fastest (Rust/WASM) | High (Rust) | Build-time, performance-critical transforms |
| **Putout** | None | Yes (via recast) | Medium | Low | Declarative codemods, ESLint-compatible |
| **recast** | None | Best-in-class | Medium | Low | Formatting preservation layer (used by others) |

**Type info** is the most important differentiator. If you need to know the resolved type
of an expression, only ts-morph and the raw TypeScript Compiler API can provide it.
Everything else is syntactic — it sees the shape of the code, not what types flow through it.

**Formatting preservation** matters for codemods that will be reviewed in PRs. ast-grep
and jscodeshift (via recast) preserve formatting of unchanged nodes. Babel's generator
reformats everything — use recast as a wrapper if you need formatting preservation with Babel.

---

## 7. Common AST Operations Cheat Sheet

These are the operations every linter and codemod performs. The pseudocode shows the
conceptual pattern; tool-specific syntax is in the tool reference files.

### Finding Imports

```
Goal: find all files that import from 'old-library'

jscodeshift:
  root.find(ImportDeclaration)
      .filter(path => path.node.source.value === 'old-library')

ts-morph:
  sourceFile.getImportDeclarations()
            .filter(d => d.getModuleSpecifierValue() === 'old-library')

ast-grep:
  pattern: import $$$SPECIFIERS from 'old-library'
  or: kind: import_statement + has: string_fragment regex: ^old-library$

ESLint visitor:
  ImportDeclaration(node) {
    if (node.source.value === 'old-library') { ... }
  }
```

### Finding Function Calls

```
Goal: find all calls to console.log(...)

jscodeshift:
  root.find(CallExpression, {
    callee: { object: { name: 'console' }, property: { name: 'log' } }
  })

ts-morph:
  sourceFile.getDescendantsOfKind(SyntaxKind.CallExpression)
            .filter(c => c.getExpression().getText() === 'console.log')

ast-grep:
  pattern: console.log($$$ARGS)

ESLint visitor:
  CallExpression(node) {
    if (node.callee.type === 'MemberExpression'
        && node.callee.object.name === 'console'
        && node.callee.property.name === 'log') { ... }
  }
```

### Finding Class Patterns

```
Goal: find class declarations that extend a specific base class

jscodeshift:
  root.find(ClassDeclaration)
      .filter(path => path.node.superClass?.name === 'Component')

ts-morph:
  sourceFile.getClasses()
            .filter(c => c.getBaseClass()?.getName() === 'Component')

ast-grep:
  pattern: class $NAME extends Component { $$$BODY }

ESLint visitor:
  ClassDeclaration(node) {
    if (node.superClass?.name === 'Component') { ... }
  }
```

### Checking Types (ts-morph / TypeScript Compiler API only)

```
Goal: find function parameters that have no type annotation

ts-morph:
  sourceFile.getFunctions().forEach(fn => {
    fn.getParameters().forEach(param => {
      if (!param.getTypeNode()) {
        // parameter has no explicit type annotation
      }
    })
  })

TypeScript Compiler API:
  const checker = program.getTypeChecker();
  const type = checker.getTypeAtLocation(node);
  const typeString = checker.typeToString(type);
  // typeString is the inferred type, even without annotation
```

### Renaming Across Files

```
Goal: rename a function and update all call sites

ts-morph (preferred — type-aware, handles all reference forms):
  const fn = sourceFile.getFunctionOrThrow('oldName');
  fn.rename('newName');
  await project.save();

jscodeshift (syntactic — misses dynamic references, renames by identifier name only):
  root.find(Identifier, { name: 'oldName' })
      .forEach(path => { path.node.name = 'newName'; })
```

### Applying Fixes in ESLint Rules

```
Goal: report a violation with an auto-fix

ESLint rule:
  context.report({
    node,
    message: 'Use === instead of ==',
    fix(fixer) {
      return fixer.replaceText(node, node.getText().replace('==', '==='));
      // or surgical range replacement:
      return fixer.replaceTextRange([node.range[0], node.range[1]], '===');
    }
  });

// For risky fixes, use suggest instead of fix:
  context.report({
    node,
    message: 'Dependency array may be incomplete',
    suggest: [{
      desc: 'Add missing dependency',
      fix(fixer) { return fixer.replaceText(depsNode, newDeps); }
    }]
  });
```

---

## Key Principles

**Detect imports before transforming.** Never assume a library symbol has a specific local
name. Users write `import { Component as C } from 'react'`. Always scan `ImportDeclaration`
nodes first to collect the actual local names, then use those names in subsequent searches.
This pattern appears in every production codemod (React, Next.js, Angular).

**Use dirty flags in jscodeshift.** Return `undefined` (not the source) when no changes
were made. This prevents jscodeshift from writing unchanged files, keeping diffs clean.

**Prefer in-place mutation over node replacement.** Changing `path.node.source.value`
preserves surrounding formatting. Replacing the entire node with `replaceWith()` forces
recast to reprint that node, potentially changing quote style or spacing.

**Suggest, do not fix, when the transform is ambiguous.** The React hooks exhaustive-deps
rule uses `suggest` instead of `fix` because auto-fixing dependency arrays can introduce
infinite render loops. When a transform could be wrong in some cases, let the user approve.

**Insert error comments when a transform cannot be automated.** Next.js codemods insert
`// NEXT_CODEMOD_ERROR: ...` comments when they encounter patterns they cannot safely
transform. This is better than silently skipping or producing incorrect output.
