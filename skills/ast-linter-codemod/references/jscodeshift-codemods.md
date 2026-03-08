# jscodeshift Codemod Patterns

Sources: facebook/jscodeshift documentation, reactjs/react-codemod, vercel/next.js codemods, Airbnb engineering, 2025-2026 production patterns

## 1. The Transform Function

Every jscodeshift codemod exports a default function:

```ts
export default function transformer(
  file: FileInfo,   // { path: string, source: string }
  api: API,         // { jscodeshift, stats, report }
  options: Options  // CLI flags passed via --option=value
): string | null | undefined {
  const j = api.jscodeshift;
  const root = j(file.source);
  // ... transform ...
  return root.toSource();
}
```

Return semantics: **string** → file is written; **null/undefined** → file is skipped; **throw** → file is marked as error.

Declare the parser alongside the transform when the default (`babel`) is wrong:

```ts
export const parser = 'tsx'; // 'babel' | 'ts' | 'tsx' | 'flow'
export default function transformer(file, api) { ... }
```

---

## 2. The Collection API

`j(source)` returns a **Collection** — a chainable wrapper around an array of AST paths. Workflow: find → filter → act.

**Finding nodes**

```ts
root.find(j.ImportDeclaration)
root.find(j.ImportDeclaration, { source: { value: 'react' } })
root.findJSXElements('Link')
root.findVariableDeclarators('myVar')
```

**Filtering and inspecting**

```ts
collection.filter(path => path.node.kind === 'const')
collection.some(path => path.node.source.value === 'react')
collection.closest(j.FunctionDeclaration)
collection.closestScope()
collection.size()       // count
collection.nodes()      // raw AST nodes
collection.get()        // first path
collection.at(-1)       // last path
```

**Transforming**

```ts
collection.replaceWith(path => newNode)
collection.insertBefore(newNode)
collection.insertAfter(newNode)
collection.remove()
```

**Path object properties**

| Property | Value |
|---|---|
| `path.node` | The AST node |
| `path.parent` | Parent path |
| `path.parent.node` | Parent AST node |
| `path.name` | Property name in parent (`'body'`, `'arguments'`, …) |
| `path.scope` | Scope information |

---

## 3. AST Builder Functions

`j` doubles as a factory for every AST node type.

```ts
// Identifiers and literals
j.identifier('myVar')
j.stringLiteral('hello')
j.numericLiteral(42)
j.booleanLiteral(true)

// Imports
j.importDeclaration([j.importDefaultSpecifier(j.identifier('React'))], j.stringLiteral('react'))
j.importSpecifier(j.identifier('useState'))
j.importNamespaceSpecifier(j.identifier('NS'))

// Expressions and statements
j.callExpression(callee, args)
j.memberExpression(j.identifier('obj'), j.identifier('prop'))
j.arrowFunctionExpression(params, body)
j.variableDeclaration('const', [j.variableDeclarator(j.identifier('x'), j.numericLiteral(1))])

// JSX
j.jsxElement(openingEl, closingEl, children)
j.jsxAttribute(j.jsxIdentifier('className'), j.stringLiteral('foo'))
j.jsxExpressionContainer(j.identifier('value'))

// Comments
j.commentBlock(' license header ', true, false)
j.commentLine(' inline comment', true, false)
```

For complex nodes, extract builder functions by name — keeps the transform body readable and the construction logic testable.

---

## 4. Formatting Preservation

jscodeshift wraps **recast**. When recast parses source, it records the original source positions of every token. When printing, it uses the **original source text** for any node that was not modified — only modified nodes are re-printed by the code generator. Whitespace, comments, and style are preserved for untouched code.

```ts
root.toSource({ quote: 'single' })              // 'single' | 'double' | 'auto'
root.toSource({ trailingComma: true, tabWidth: 2 })
```

Formatting degrades when you replace a node with a freshly built node (recast has no original text to preserve). To preserve quote style on string literals, reuse the original node:

```ts
const originalSource = importPath.value.source;  // original StringLiteral node
j.importDeclaration(newSpecifiers, originalSource);
```

---

## 5. The hasModifications Pattern

Return `null` when no changes were made. This prevents unnecessary file writes and keeps runner output clean (`ok` vs `skip`).

```ts
export default function transformer(file, api) {
  const j = api.jscodeshift;
  const root = j(file.source);
  let hasModifications = false;

  root.find(j.MethodDefinition).forEach(path => {
    if (DEPRECATED_APIS[path.node.key.name]) {
      path.value.key.name = DEPRECATED_APIS[path.node.key.name];
      hasModifications = true;
    }
  });

  return hasModifications ? root.toSource({ quote: 'single' }) : null;
}
```

Use `||=` to accumulate the flag across multiple passes:

```ts
hasModifications ||= root.find(j.ImportDeclaration, { source: { value: '@next/font' } }).size() > 0;
```

---

## 6. Import Manipulation

**Finding and classifying specifiers**

```ts
root.find(j.ImportDeclaration, { source: { value: 'react' } })
  .forEach(path => {
    path.value.specifiers?.forEach(spec => {
      if (j.ImportDefaultSpecifier.check(spec)) { /* default import */ }
      if (j.ImportNamespaceSpecifier.check(spec)) { /* namespace import */ }
      if (j.ImportSpecifier.check(spec)) { /* named import */ }
    });
  });
```

**Adding an import** — prepend to `program.body` or insert relative to an existing import:

```ts
root.get().node.program.body.unshift(
  j.importDeclaration([j.importSpecifier(j.identifier('createRoot'))], j.literal('react-dom/client'))
);
// or:
root.find(j.ImportDeclaration).at(0).insertBefore(newImport);
```

**Removing a specifier**

```ts
root.find(j.ImportSpecifier, { imported: { name: 'forwardRef' } }).remove();
// Remove the entire declaration if it becomes empty after specifier removal.
```

**Renaming an import source** — direct mutation is cleaner than `replaceWith` for simple property changes:

```ts
root.find(j.ImportDeclaration, { source: { value: '@next/font' } })
  .forEach(path => { path.node.source = j.stringLiteral('next/font'); hasModifications = true; });
```

---

## 7. Production Patterns from React/Next.js Codemods

### a. Handle all syntactic variants

The same logical concept can appear as different AST node types. `rename-unsafe-lifecycles` covers five variants of the same lifecycle method:

```ts
const renameDeprecatedApis = path => {
  const name = path.node.key.name;
  if (DEPRECATED_APIS[name]) { path.value.key.name = DEPRECATED_APIS[name]; hasModifications = true; }
};

root.find(j.MethodDefinition).forEach(renameDeprecatedApis);  // ES6 class
root.find(j.ClassMethod).forEach(renameDeprecatedApis);        // Babel class
root.find(j.ClassProperty).forEach(renameDeprecatedApis);      // Arrow fn prop
root.find(j.Property).forEach(renameDeprecatedApis);           // createReactClass
root.find(j.MemberExpression).forEach(renameDeprecatedCallExpressions);
```

Audit every syntactic form before shipping a codemod.

### b. Preserve first-node comments

When the first node in a file is removed or replaced, comments attached to it (license headers, `@flow`, `@format`) are lost:

```ts
function getFirstNode() { return root.find(j.Program).get('body', 0).node; }
const firstNode = getFirstNode();
const { comments } = firstNode;

// ... transformations ...

const newFirstNode = getFirstNode();
if (newFirstNode !== firstNode) { newFirstNode.comments = comments; }
```

### c. Insert TODO comments for unresolvable cases

When a transform cannot safely automate a case, insert a comment marker rather than silently skipping:

```ts
linkPath.node.children.unshift(
  j.jsxText('\n'),
  j.jsxExpressionContainer.from({
    expression: j.jsxEmptyExpression.from({
      comments: [j.commentBlock.from({
        value: ` TODO: This Link previously used legacyBehavior. Verify the child does not render an <a>. `,
      })],
    }),
  })
);
```

This pattern (from `next-codemod/new-link`) leaves a searchable marker developers can grep for and resolve manually.

### d. Chain transforms via reduce

When a migration requires multiple independent passes, compose them so each pass receives the output of the previous:

```ts
export default function transform(file: FileInfo, api: API) {
  const transforms = [transformDynamicProps, transformDynamicAPI];
  return transforms.reduce<string>((source, fn) => {
    const result = fn(source, api, file.path);
    return result ?? source;
  }, file.source);
}
```

---

## 8. TypeScript Support

**Parser selection**

```ts
export const parser = 'tsx';  // static declaration in transform file

// Or dynamically by file extension (Next.js pattern):
function createParserFromPath(filePath: string) {
  if (filePath.endsWith('.tsx')) return require('jscodeshift/parser/tsx');
  if (filePath.endsWith('.ts')) return require('jscodeshift/parser/ts');
  return require('jscodeshift/parser/babel');
}
```

**Type annotation transforms** — use the `TS*` builder family:

```ts
j.tsTypeAnnotation(
  j.tsIntersectionType([
    propType,
    j.tsTypeLiteral([
      j.tsPropertySignature.from({
        key: j.identifier('ref'),
        typeAnnotation: j.tsTypeAnnotation(
          j.tsTypeReference.from({
            typeName: j.tsQualifiedName(j.identifier('React'), j.identifier('RefObject')),
            typeParameters: j.tsTypeParameterInstantiation([refType]),
          })
        ),
      }),
    ]),
  ])
)
```

**Common TypeScript node types**

| Node | Description |
|---|---|
| `TSTypeAnnotation` | `: Type` annotation |
| `TSTypeReference` | `Foo<Bar>` type reference |
| `TSAsExpression` | `x as Type` |
| `TSNonNullExpression` | `x!` |
| `TSInterfaceDeclaration` | `interface Foo {}` |
| `TSTypeAliasDeclaration` | `type Foo = ...` |
| `TSUnionType` | `A \| B` |
| `TSIntersectionType` | `A & B` |
| `TSTypeParameterDeclaration` | `<T>` generic params |
| `TSTypeParameterInstantiation` | `<string>` generic args |

---

## 9. Running Codemods

```bash
jscodeshift -t transform.js src/
jscodeshift -t transform.ts --parser=tsx src/**/*.tsx
```

| Flag | Purpose |
|---|---|
| `--dry` | Print what would change without writing |
| `--print` | Print transformed output to stdout |
| `--extensions=ts,tsx` | Limit to file extensions |
| `--ignore-pattern="**/*.test.ts"` | Skip matching files |
| `--cpus=8` | Worker count (default: CPU count) |
| `--verbose=2` | Detailed output per file |

Recommended workflow: run `--dry --print` on one file → review → run on a small subset → `git diff` → run full codemod → run tests and type-check.

Via codemod.com registry:

```bash
npx codemod react/19/remove-forward-ref --dry-run --target ./src
```

---

## 10. Common Codemod Templates

**Rename API**

```ts
const RENAMES = { componentWillMount: 'UNSAFE_componentWillMount' };
export default function transformer(file, api) {
  const j = api.jscodeshift;
  const root = j(file.source);
  let hasModifications = false;
  root.find(j.Identifier).forEach(path => {
    if (RENAMES[path.node.name]) { path.node.name = RENAMES[path.node.name]; hasModifications = true; }
  });
  return hasModifications ? root.toSource() : null;
}
```

**Wrap with function**

```ts
// Before: render(el, container)  →  After: createRoot(container)
root.find(j.CallExpression, { callee: { name: 'render' } })
  .replaceWith(path => j.callExpression(j.identifier('createRoot'), [path.node.arguments[1]]));
```

**Unwrap HOC**

```ts
// Before: forwardRef(fn)  →  After: fn
root.find(j.CallExpression, { callee: { name: 'forwardRef' } })
  .replaceWith(path => path.node.arguments[0]);
```

**Change import source**

```ts
root.find(j.ImportDeclaration, { source: { value: 'old-package' } })
  .forEach(path => { path.node.source = j.stringLiteral('new-package'); hasModifications = true; });
```

**Add / remove JSX prop**

```ts
// Remove
root.findJSXElements('Link').find(j.JSXAttribute, { name: { name: 'legacyBehavior' } }).remove();

// Add
root.findJSXElements('Image').forEach(path => {
  path.node.openingElement.attributes.push(j.jsxAttribute(j.jsxIdentifier('priority'), null));
});
```

---

## Testing

jscodeshift ships `jscodeshift/dist/testUtils` with `defineTest`. The standard structure uses input/output fixture pairs:

```
transforms/my-transform.ts
__tests__/my-transform-test.ts
__testfixtures__/my-transform/
  basic.input.ts  /  basic.output.ts
  edge-case.input.ts  /  edge-case.output.ts
```

```ts
import { defineTest } from 'jscodeshift/dist/testUtils';
const tests = ['basic', 'edge-case'];
describe('my-transform', () => {
  tests.forEach(name => defineTest(__dirname, 'my-transform', null, `my-transform/${name}`));
});
```

Each edge case — different syntactic variant, comment preservation, no-op file — gets its own fixture pair. See `testing-transforms.md` for the full testing reference.
