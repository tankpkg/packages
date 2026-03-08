# ts-morph Patterns for Linters and Codemods

Sources: dsherret/ts-morph v27 documentation, Syed (TypeScript Deep Dive), Rametta (TypeScript Compiler API), 2025-2026 production implementations

ts-morph wraps the TypeScript Compiler API with a high-level, mutable API. The raw compiler API is read-only; ts-morph adds node tracking across edits, named navigation methods, and import management. Use it when you need type information alongside mutation — the combination that raw compiler API and jscodeshift each handle only half of.

---

## 1. Project Setup

Create a `Project` from a tsconfig to inherit the same compiler options your codebase uses. This ensures type resolution matches what the TypeScript compiler sees.

```typescript
import { Project, SyntaxKind, Node } from "ts-morph";

// From tsconfig — recommended for real projects
const project = new Project({ tsConfigFilePath: "tsconfig.json" });

// Manual options — useful for targeted scripts
const project = new Project({
  compilerOptions: { strict: true, target: ScriptTarget.ES2022 },
  skipLoadingLibFiles: true,   // faster startup, no type info
});

// In-memory — ideal for testing codemods
const project = new Project({ useInMemoryFileSystem: true });
const sf = project.createSourceFile("test.ts", `const x: string = 42;`);
```

Add source files and save:

```typescript
project.addSourceFilesAtPaths("src/**/*.ts");
project.addSourceFilesAtPaths(["src/**/*.ts", "!src/**/*.test.ts"]);
const sf = project.getSourceFileOrThrow("src/index.ts"); // throws if missing

await project.save(); // write all modified files atomically at the end
```

---

## 2. Node Navigation

Every node in ts-morph extends `Node<ts.Node>`. The two primary traversal strategies are kind-based search and the visitor pattern.

**Kind-based search** — returns all matching descendants in document order:

```typescript
const calls = sf.getDescendantsOfKind(SyntaxKind.CallExpression);
const first = sf.getFirstDescendantByKindOrThrow(SyntaxKind.ImportDeclaration);
```

**Visitor pattern** — use `forEachDescendant` when you need traversal control:

```typescript
node.forEachDescendant((node, traversal) => {
  if (Node.isClassDeclaration(node)) traversal.skip();  // skip class internals
  if (Node.isFunctionDeclaration(node)) traversal.stop(); // halt entirely
  if (Node.isImportDeclaration(node)) return node;        // stop and return value
});
```

**Type guards** narrow the node type without casting:

```typescript
if (Node.isCallExpression(node))          { /* node: CallExpression */ }
if (Node.isPropertyAccessExpression(node)) { /* node: PropertyAccessExpression */ }
if (Node.isIdentifier(node))              { /* node: Identifier */ }
```

**Parent and child navigation**: `node.getParent()`, `node.getParentOrThrow()`, `node.getParentIfKind(SyntaxKind.X)` (typed parent or undefined), `node.getChildren()` (all children including tokens), `node.forEachChild(cb)` (property children only).

Position for violation reporting: `node.getStartLineNumber()` (1-indexed), `node.getStartColumn()` (0-indexed), `node.getSourceFile().getFilePath()`.

---

## 3. Type System Access

ts-morph exposes the full TypeScript type checker through `node.getType()`. Type checks require `skipLoadingLibFiles: false` and a valid tsconfig.

```typescript
const type = variableDecl.getType();
type.isString()       // string
type.isAny()          // any
type.isUnion()        // A | B
type.isArray()        // T[]
type.getText()        // "string | undefined"
type.getUnionTypes()  // Type[] for union members

// Assignability (ts-morph v22+)
const stringType = project.getTypeChecker().getStringType();
if (type.isAssignableTo(stringType)) { /* ... */ }
```

For linter rules that check return types or parameter types:

```typescript
// Find functions missing explicit return type annotation
for (const fn of sf.getFunctions()) {
  if (!fn.getReturnTypeNode()) {
    // getReturnType() gives the inferred type; getReturnTypeNode() gives the annotation
    report(fn, "Missing explicit return type");
  }
}
```

---

## 4. Linter Pattern

A ts-morph linter iterates source files, applies rule functions, and collects violations. Rules are pure functions: they receive a `SourceFile` and return an array of issues.

```typescript
interface Violation {
  file: string;
  line: number;
  column: number;
  message: string;
  fix?: () => void;  // optional auto-fix closure
}

type Rule = (sf: SourceFile) => Violation[];
```

Runner — iterate source files, apply each rule, optionally apply fixes, then save once:

```typescript
async function lint(tsconfig: string, rules: Rule[], applyFixes = false) {
  const project = new Project({ tsConfigFilePath: tsconfig });
  const all: Violation[] = [];
  for (const sf of project.getSourceFiles())
    for (const rule of rules) {
      const found = rule(sf);
      all.push(...found);
      if (applyFixes) found.forEach(v => v.fix?.());
    }
  if (applyFixes) await project.save();
  return all;
}
```

Example rule — no `console` calls:

```typescript
const noConsole: Rule = (sf) => {
  const violations: Violation[] = [];
  for (const call of sf.getDescendantsOfKind(SyntaxKind.CallExpression)) {
    const expr = call.getExpression();
    if (Node.isPropertyAccessExpression(expr)) {
      const obj = expr.getExpression();
      if (Node.isIdentifier(obj) && obj.getText() === "console") {
        violations.push({
          file: sf.getFilePath(),
          line: call.getStartLineNumber(),
          column: call.getStartColumn(),
          message: "Unexpected console statement",
          fix: () => call.getParentIfKind(SyntaxKind.ExpressionStatement)?.remove(),
        });
      }
    }
  }
  return violations;
};
```

---

## 5. Codemod Patterns

The primary mutation operations:

| Operation | API | Notes |
|-----------|-----|-------|
| Replace node text | `node.replaceWithText("new text")` | Returns new node; old node is forgotten |
| Remove node | `node.remove()` | Removes node and surrounding whitespace |
| Rename (cross-file) | `node.rename("newName")` | Updates all references in the project |
| Add import | `sf.addImportDeclaration({...})` | Merges with existing if possible |
| Remove import | `importDecl.remove()` | Or `namedImport.remove()` |
| Set body | `fn.setBodyText("return 42;")` | Replaces entire function body |
| Add statement | `fn.addStatements("doThing();")` | Appends to body |
| Set declaration kind | `stmt.setDeclarationKind(VariableDeclarationKind.Const)` | var → const/let |

**replaceWithText** is the workhorse for structural changes:

```typescript
// Wrap an object argument in a { where: ... } envelope
const arg = callExpr.getArguments()[0];
const original = arg.getText();           // "{ name: 'Lisa' }"
arg.replaceWithText(`{ where: ${original} }`);
// arg is now forgotten — do not use it again
```

**rename** propagates across all files in the project:

```typescript
classDecl.rename("NewClassName", {
  renameInComments: true,
  renameInStrings: true,
});
```

**Low-level text operations** (`insertText`, `replaceText`) invalidate all previously navigated descendants. Re-navigate after using them.

---

## 6. The "Analyze Then Transform" Rule

Mixing type queries and mutations in the same loop is the most common ts-morph performance mistake. Every mutation resets the type checker's internal cache. If you call `getType()` after a `remove()` in the same loop, the type checker rebuilds from scratch for each iteration.

Collect first, transform second:

```typescript
// Collect nodes that need transformation
const toRemove: ClassDeclaration[] = [];
for (const sf of project.getSourceFiles()) {
  for (const cls of sf.getClasses()) {
    if (shouldRemove(cls)) toRemove.push(cls);  // type checks here
  }
}

// Apply transformations after all analysis is complete
for (const cls of toRemove) {
  if (!cls.wasForgotten()) cls.remove();
}
```

This pattern also applies within a single file. Gather all nodes matching your criteria, then mutate. The same principle appears in Angular's migration framework (Tsurge): a separate `analyze` phase produces a list of `Replacement[]` text spans, and a `migrate` phase applies them — never interleaved.

---

## 7. Node Forgetting

When ts-morph mutates the AST, it marks affected nodes as "forgotten." Accessing a forgotten node throws. This is the most common runtime error in codemods.

```typescript
const param = callExpr.getFirstDescendantByKind(SyntaxKind.ObjectLiteralExpression);
const text = param.getText();                    // capture text BEFORE mutation
param.replaceWithText(`{ where: ${text} }`);
// param.getText() here would throw — param is forgotten

// Guard with wasForgotten() in loops
for (const node of nodes) {
  if (node.wasForgotten()) continue;
  // safe to use node
}
```

Release nodes you no longer need to reduce tracking overhead:

```typescript
cls.forget();  // stop tracking cls and all its descendants
```

---

## 8. Import Management

ts-morph provides high-level import helpers that handle the bookkeeping of adding, removing, and deduplicating imports.

```typescript
// Add a new import declaration
sf.addImportDeclaration({
  namedImports: ["useState", "useEffect"],
  moduleSpecifier: "react",
});

// Add a named import to an existing declaration
const reactImport = sf.getImportDeclaration("react");
reactImport?.addNamedImport("useCallback");

// Remove a specific named import
const namedImport = reactImport?.getNamedImports()
  .find(n => n.getName() === "forwardRef");
namedImport?.remove();

// Remove the entire import if it becomes empty
if (reactImport?.getNamedImports().length === 0) {
  reactImport.remove();
}

// Organize imports (equivalent to IDE "organize imports")
sf.organizeImports();

// Auto-add imports for identifiers that are used but not imported
sf.fixMissingImports();
```

**Import detection before transformation** — always check what name a module was imported under before searching for usages. A codemod that assumes `forwardRef` is always named `forwardRef` will miss `import { forwardRef as fRef }`.

```typescript
const imp = sf.getImportDeclaration("react");
const forwardRefName = imp?.getNamedImports()
  .find(n => n.getName() === "forwardRef")
  ?.getAliasNode()?.getText() ?? "forwardRef";
// Now search for forwardRefName, not the literal string "forwardRef"
```

---

## 9. Cross-File Operations

`findReferencesAsNodes()` is ts-morph's most powerful feature for cross-file analysis. It uses the TypeScript language service to find every reference to a declaration across the entire project.

```typescript
// Find all usages of a class across all files
const cls = sf.getClassOrThrow("UserService");
const refs = cls.findReferencesAsNodes();

for (const ref of refs) {
  const refFile = ref.getSourceFile().getFilePath();
  const line = ref.getStartLineNumber();
  console.log(`${refFile}:${line}`);
}
```

---

## 10. Performance

| Technique | When to Use |
|-----------|-------------|
| `skipLoadingLibFiles: true` | Analysis only, no type checking needed |
| `skipFileDependencyResolution: true` | No cross-file type resolution needed |
| Batch additions: `sf.addClasses([...])` | Adding multiple nodes at once |
| `sf.transform(traversal => ...)` | Bulk text changes without type info |
| `node.forget()` | Release nodes after use in large files |
| Collect then mutate | Any loop mixing type queries and mutations |

**Transform API** — for bulk changes where you do not need type information, the transform API avoids re-parsing between each change:

```typescript
import { ts } from "ts-morph";

sf.transform(traversal => {
  const node = traversal.visitChildren(); // visit children first
  if (ts.isStringLiteral(node) && node.text.startsWith("old-")) {
    return traversal.factory.createStringLiteral(
      node.text.replace("old-", "new-")
    );
  }
  return node;
});
// All previously wrapped descendants are forgotten after transform
```

---

## 11. Complete Linter Example — Unused Exports

This linter finds exported functions with no references outside their own file. It combines the linter pattern from section 4 with the cross-file reference API from section 9.

```typescript
import { Project } from "ts-morph";

const project = new Project({ tsConfigFilePath: "tsconfig.json" });
const violations: string[] = [];

for (const sf of project.getSourceFiles()) {
  for (const fn of sf.getFunctions()) {
    if (!fn.isExported()) continue;
    const externalRefs = fn.findReferencesAsNodes().filter(
      ref => ref.getSourceFile().getFilePath() !== sf.getFilePath()
    );
    if (externalRefs.length === 0) {
      violations.push(
        `${sf.getFilePath()}:${fn.getStartLineNumber()} ` +
        `'${fn.getName()}' exported but never imported`
      );
    }
  }
}

violations.forEach(v => console.log(v));
process.exit(violations.length > 0 ? 1 : 0);
```

Call `findReferencesAsNodes()` once per function, not once per reference. Filter by file path to distinguish internal from external usage.

---

## 12. Complete Codemod Example — API Rename

This codemod migrates `OldClient` from `old-sdk` to `NewClient` from `new-sdk`. The three-phase structure — detect import, collect usages, transform — prevents the type-checker reset problem described in section 6.

```typescript
import { Project, SyntaxKind } from "ts-morph";

const project = new Project({ tsConfigFilePath: "tsconfig.json" });

for (const sf of project.getSourceFiles()) {
  const oldImport = sf.getImportDeclaration("old-sdk");
  if (!oldImport) continue;

  const specifier = oldImport.getNamedImports()
    .find(n => n.getName() === "OldClient");
  if (!specifier) continue;

  // Resolve local alias: handles `import { OldClient as OC }`
  const localName = specifier.getAliasNode()?.getText() ?? "OldClient";

  // Phase 1: collect before mutating
  const toRename = sf.getDescendantsOfKind(SyntaxKind.Identifier)
    .filter(id => id.getText() === localName);

  // Phase 2: swap imports
  specifier.remove();
  if (oldImport.getNamedImports().length === 0) oldImport.remove();
  sf.addImportDeclaration({ namedImports: ["NewClient"], moduleSpecifier: "new-sdk" });

  // Phase 3: rename usages
  for (const id of toRename) {
    if (!id.wasForgotten()) id.replaceWithText("NewClient");
  }
}

await project.save();
```

---

## API Quick Reference

| Task | API |
|------|-----|
| Create project | `new Project({ tsConfigFilePath })` |
| Add files | `project.addSourceFilesAtPaths("src/**/*.ts")` |
| Get all files | `project.getSourceFiles()` |
| Find by kind | `node.getDescendantsOfKind(SyntaxKind.X)` |
| Visitor traversal | `node.forEachDescendant((n, t) => { t.skip() })` |
| Type guard | `Node.isCallExpression(node)` |
| Get type | `node.getType()` |
| Get line/col | `node.getStartLineNumber()`, `node.getStartColumn()` |
| Replace node | `node.replaceWithText("new text")` |
| Remove node | `node.remove()` |
| Rename cross-file | `node.rename("newName")` |
| Add import | `sf.addImportDeclaration({ namedImports, moduleSpecifier })` |
| Find references | `node.findReferencesAsNodes()` |
| Check forgotten | `node.wasForgotten()` |
| Release node | `node.forget()` |
| Organize imports | `sf.organizeImports()` |
| Fix missing imports | `sf.fixMissingImports()` |
| Bulk transform | `sf.transform(traversal => ...)` |
| Save all changes | `await project.save()` |
| Get diagnostics | `project.getPreEmitDiagnostics()` |

Use https://ts-ast-viewer.com to explore the AST of any TypeScript snippet before writing a codemod. Paste code, identify the `SyntaxKind` values you need, then write the traversal.
