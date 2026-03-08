# ESLint Custom Rules with Auto-Fix

Sources: ESLint official documentation, typescript-eslint documentation, production rules from n8n, puppeteer, twenty, storybook, 2025-2026 ecosystem research

## 1. Rule Architecture

Every ESLint rule exports an object with two required properties: `meta` and `create`.

```typescript
module.exports = {
  meta: {
    type: "problem",       // "problem" | "suggestion" | "layout"
    fixable: "code",       // required when rule provides auto-fixes
    hasSuggestions: true,  // required when rule provides suggestions
    docs: { description: "Disallow bad pattern", recommended: false },
    messages: { avoidBad: "Avoid '{{name}}'. Use '{{replacement}}' instead." },
    schema: [{ type: "object", properties: { allow: { type: "boolean" } },
               additionalProperties: false }],
  },
  create(context) {
    return { CallExpression(node) { /* visitor logic */ } };
  },
};
```

`meta.type` signals intent: `"problem"` for likely bugs, `"suggestion"` for style, `"layout"` for whitespace. Omitting `fixable` when a rule calls fixer methods causes ESLint to throw at runtime.

### Key APIs

| API | Description |
|---|---|
| `context.sourceCode` | `SourceCode` instance — primary inspection API |
| `context.options` | Array of rule options from config |
| `context.report(descriptor)` | Report a problem with optional fix |
| `sourceCode.getText(node)` | Raw source text of a node |
| `sourceCode.getFirstToken(node)` | First token in node |
| `sourceCode.getTokenBefore(node)` | Token immediately before node |
| `sourceCode.getTokenAfter(node)` | Token immediately after node |
| `sourceCode.getScope(node)` | Scope at this node |
| `sourceCode.getAncestors(node)` | All ancestor nodes (root first) |

### Node Visitor Patterns

`create()` returns an object whose keys are visitor selectors (CSS-like syntax, see section 5):

```typescript
return {
  Identifier(node) { },                                     // enter
  "FunctionDeclaration:exit"(node) { },                     // leave (after children)
  "TryStatement CallExpression"(node) { },                  // descendant combinator
  "FunctionDeclaration, ArrowFunctionExpression"(node) { }, // multiple types (OR)
  "IfStatement:has(ReturnStatement)"(node) { },             // has descendant
};
```

---

## 2. The Fixer API

The `fixer` object is passed to the `fix` function inside `context.report()`. All methods return a fix descriptor. Return `null` to skip the fix while still reporting the error.

| Method | Description |
|---|---|
| `fixer.replaceText(node, text)` | Replace a node's full source text |
| `fixer.replaceTextRange([start, end], text)` | Replace by character range |
| `fixer.insertTextBefore(node, text)` | Insert text before a node |
| `fixer.insertTextAfter(node, text)` | Insert text after a node |
| `fixer.insertTextBeforeRange([start, end], text)` | Insert before a range start |
| `fixer.insertTextAfterRange([start, end], text)` | Insert after a range end |
| `fixer.remove(node)` | Remove a node entirely |
| `fixer.removeRange([start, end])` | Remove by character range |

Every AST node carries `range: [startIndex, endIndex]` — character offsets into the source string. Use ranges to operate on text between nodes (punctuation, whitespace) that has no dedicated AST node:

```typescript
// Remove " as Type" from "value as Type"
const tokenBeforeAs = sourceCode.getTokenBefore(asKeyword, { includeComments: true });
return fixer.removeRange([tokenBeforeAs.range[1], node.range[1]]);
```

### Generator Fixes — Multiple Operations

When a fix requires more than one edit, use a generator. ESLint applies all yielded operations atomically; conflicting operations cause the fix to be skipped for that pass.

```typescript
context.report({
  node, messageId: "convertImport",
  *fix(fixer) {
    yield fixer.insertTextAfter(importKeyword, " type");
    yield fixer.replaceText(importDecl.source, `'new-package'`);
    yield fixer.remove(importDecl.specifiers[0]);
  },
});
```

Return `null` from `fix` to report the error without applying a fix.

---

## 3. Auto-Fixable Rule Pattern

A complete minimal fixable rule. `fixable: "code"` in `meta` is required — ESLint throws without it.

```typescript
module.exports = {
  meta: {
    type: "suggestion",
    fixable: "code",
    messages: { unexpectedVar: "Unexpected var, use let or const instead." },
    schema: [],
  },
  create(context) {
    const sourceCode = context.sourceCode;
    return {
      "VariableDeclaration:exit"(node) {
        if (node.kind !== "var") return;
        context.report({
          node,
          messageId: "unexpectedVar",
          fix(fixer) {
            const varToken = sourceCode.getFirstToken(node, {
              filter: t => t.value === "var",
            });
            return fixer.replaceText(varToken, "let");
          },
        });
      },
    };
  },
};
```

**Get-transform-replace** is the most common fix pattern: `sourceCode.getText(node)` → transform string → `fixer.replaceText(node, result)`.

---

## 4. Suggestion API

Suggestions appear in editors as "quick fix" options but are not applied by `eslint --fix`. Use suggestions when the fix might change semantics, when multiple valid fixes exist, or when the transform is risky. Do not set `fixable: "code"` on suggestion-only rules.

```typescript
meta: { hasSuggestions: true, messages: { unexpected: "...", replaceOp: "..." } },
create(context) {
  return {
    BinaryExpression(node) {
      if (node.operator !== "==") return;
      context.report({
        node, messageId: "unexpected",
        data: { expected: "===", actual: "==" },
        suggest: [{
          messageId: "replaceOp",
          data: { expected: "===", actual: "==" },
          fix(fixer) { return fixer.replaceText(operatorToken, "==="); },
        }],
      });
    },
  };
},
```

The react-hooks `exhaustive-deps` rule uses suggestions because auto-adding dependencies can cause infinite render loops — the canonical example of when `suggest` beats `fix`.

---

## 5. CSS Selector Syntax

ESLint uses [esquery](https://github.com/estools/esquery) for visitor key matching:

```
"CallExpression[callee.name='require']"          attribute match
"CallExpression > MemberExpression"              direct child
"TryStatement CallExpression"                    descendant (any depth)
"VariableDeclaration ~ ReturnStatement"          adjacent sibling
":not(FunctionDeclaration)"                      negation
":first-child"  ":last-child"  ":nth-child(2)"  position pseudo-classes
":has(ReturnStatement)"                          has descendant
"FunctionDeclaration:exit"                       fires after children visited
"FunctionDeclaration, ArrowFunctionExpression"   multiple types (OR)
```

Complex selectors have a performance cost proportional to their specificity. Prefer simple type selectors; use attribute selectors only when necessary.

---

## 6. typescript-eslint Rules

Use `@typescript-eslint/utils` for typed rule authoring. `ESLintUtils.RuleCreator` provides full TypeScript inference over `context`, options, and message IDs.

```typescript
import { ESLintUtils } from '@typescript-eslint/utils';

const createRule = ESLintUtils.RuleCreator(name => `https://example.com/rules/${name}`);

export const rule = createRule<[{ allow?: boolean }], 'myMessage'>({
  name: 'my-rule',
  meta: {
    type: 'suggestion', fixable: 'code',
    docs: { description: 'Description here.' },
    messages: { myMessage: 'Message with {{name}} placeholder.' },
    schema: [{ type: 'object', properties: { allow: { type: 'boolean' } },
               additionalProperties: false }],
  },
  defaultOptions: [{ allow: false }],
  create(context, [options]) {
    return {
      Identifier(node) {
        if (!options.allow && node.name === 'bad')
          context.report({ messageId: 'myMessage', node, data: { name: node.name },
                           fix: fixer => fixer.replaceText(node, 'good') });
      },
    };
  },
});
```

### TypeScript-Specific AST Node Types

```
AST_NODE_TYPES.TSTypeAnnotation          : string
AST_NODE_TYPES.TSAsExpression            value as Type
AST_NODE_TYPES.TSNonNullExpression       value!
AST_NODE_TYPES.TSTypeAssertionExpression <Type>value
AST_NODE_TYPES.TSInterfaceDeclaration    interface Foo {}
AST_NODE_TYPES.TSTypeAliasDeclaration    type Foo = ...
AST_NODE_TYPES.TSEnumDeclaration         enum Foo {}
AST_NODE_TYPES.TSUnionType               A | B
AST_NODE_TYPES.TSIntersectionType        A & B
AST_NODE_TYPES.TSConditionalType         A extends B ? C : D
AST_NODE_TYPES.TSMappedType              { [K in T]: V }
```

---

## 7. Typed Linting

Typed rules access the TypeScript type checker to reason about types, not just syntax. Mark them with `requiresTypeChecking: true` so tooling warns users who run without `parserOptions.project`.

```typescript
import { ESLintUtils } from '@typescript-eslint/utils';
import * as tsutils from 'ts-api-utils';

create(context) {
  const services = ESLintUtils.getParserServices(context);
  const checker = services.program.getTypeChecker();
  return {
    AwaitExpression(node) {
      const type = services.getTypeAtLocation(node.argument);
      if (!tsutils.isThenableType(checker, node, type))
        context.report({ node, messageId: 'await' });
    },
  };
},
```

| API | Description |
|---|---|
| `services.esTreeNodeToTSNodeMap.get(esNode)` | ESTree → TypeScript AST node |
| `services.getTypeAtLocation(esNode)` | TypeScript type at ESTree node |
| `services.program.getTypeChecker()` | TypeScript TypeChecker |
| `tsutils.isNullableType(type)` | Check nullability |
| `tsutils.isThenableType(checker, node, type)` | Check Promise/thenable |
| `tsutils.isTypeFlagSet(type, ts.TypeFlags.Any)` | Check type flags |
| `ESLintUtils.getConstrainedTypeAtLocation(services, node)` | Resolve generic constraints |

Typed rules require a full TypeScript compilation pass. Reserve them for checks that genuinely need type information — nullability, promise handling, type compatibility.

---

## 8. Complex Fix Patterns

When replacing a node that may have leading comments, extend the range to include them. When removing an array element, also remove its trailing comma:

```typescript
// Preserve leading comments
fix(fixer) {
  const comments = sourceCode.getCommentsBefore(node);
  const start = comments.length > 0 ? comments[0].range[0] : node.range[0];
  return fixer.replaceTextRange([start, node.range[1]], newText);
}

// Remove element + trailing comma
fix(fixer) {
  const isLast = node.parent.elements.indexOf(node) === node.parent.elements.length - 1;
  const after = sourceCode.getTokenAfter(node);
  return (!isLast && after?.value === ",")
    ? fixer.removeRange([node.range[0], after.range[1]]) : fixer.remove(node);
}
```

### Deferred Reporting with `Program:exit`

Collect data across the whole file, then report once traversal is complete. Required for rules that need global context — duplicate imports, file-level limits, cross-node relationships.

```typescript
create(context) {
  const seen = new Map<string, Node[]>();
  return {
    ImportDeclaration(node) {
      const src = node.source.value as string;
      (seen.get(src) ?? seen.set(src, []).get(src)!).push(node);
    },
    "Program:exit"() {
      for (const [src, decls] of seen)
        if (decls.length > 1)
          context.report({ node: decls[1], messageId: "duplicateImport", data: { source: src } });
    },
  };
},
```

---

## 9. RuleTester

`RuleTester` runs rule logic against code strings and asserts on errors, messages, and fix output. It throws synchronously on assertion failure, making it compatible with any test runner.

```typescript
const { RuleTester } = require("eslint");
const tester = new RuleTester({ languageOptions: { ecmaVersion: 2022, sourceType: "module" } });

tester.run("no-var", rule, {
  valid: ["const foo = 'bar';", { code: "let foo;", options: [{ allowLet: true }] }],
  invalid: [{
    code: "var foo = bar;",
    output: "let foo = bar;",          // expected source after --fix
    errors: [{ messageId: "unexpectedVar", line: 1, column: 1 }],
  }],
});
```

Test suggestions by asserting on the `suggestions` array inside each error object:

```typescript
errors: [{
  messageId: "unexpected",
  suggestions: [{ messageId: "replaceOperator", output: "a === b" }],
}],
```

For typed rules, use `@typescript-eslint/rule-tester` with `parserOptions.project`. Integrate with Vitest by assigning `RuleTester.afterAll`, `RuleTester.describe`, `RuleTester.it`.

---

## 10. Plugin Scaffolding

Structure: `eslint-plugin-<name>/index.ts` (entry point) + `lib/rules/*.ts`. `package.json` must include `"eslint"` in `peerDependencies` and `"eslintplugin"` in `keywords`.

```typescript
// index.ts — build configs after plugin is defined so it can self-reference
const plugin = {
  meta: { name: 'eslint-plugin-my-plugin', version: '1.0.0' },
  rules: { 'rule-one': ruleOne, 'rule-two': ruleTwo },
  configs: {} as Record<string, TSESLint.FlatConfig.Config>,
};
Object.assign(plugin.configs, {
  recommended: {
    plugins: { 'my-plugin': plugin },
    rules: { 'my-plugin/rule-one': 'error', 'my-plugin/rule-two': 'warn' },
  },
});
export default plugin;
```

```javascript
// eslint.config.js (flat config)
import myPlugin from 'eslint-plugin-my-plugin';
export default [
  myPlugin.configs.recommended,
  { rules: { 'my-plugin/rule-one': ['error', { option: true }] } },
];
```

---

## 11. Real-World Pattern Catalog

### Ban a Function Call
```typescript
CallExpression(node) {
  if (node.callee.type !== "MemberExpression") return;
  if (node.callee.object.name !== "console" || node.callee.property.name !== "log") return;
  context.report({ node, messageId: "noConsoleLog",
    fix: fixer => node.parent.type === "ExpressionStatement"
      ? fixer.remove(node.parent) : null });
},
```

### Enforce Import Style
```typescript
ImportDeclaration(node) {
  if (!banned.includes(node.source.value)) return;
  const def = node.specifiers.find(s => s.type === "ImportDefaultSpecifier");
  if (!def) return;
  context.report({ node: def, messageId: "useNamedImport", data: { name: def.local.name },
    fix: fixer => fixer.replaceText(def, `{ ${def.local.name} }`) });
},
```

### Scope Analysis
```typescript
"Program:exit"(node) {
  for (const v of context.sourceCode.getScope(node).variables) {
    if (v.references.length === 0 && v.defs.length > 0)
      context.report({ node: v.defs[0].name, messageId: "unusedVar", data: { name: v.name } });
  }
},
```

### State Tracking Across Visitors
```typescript
create(context) {
  const stack: number[] = [];
  return {
    FunctionDeclaration() { stack.push(0); },
    "FunctionDeclaration:exit"() { stack.pop(); },
    IfStatement(node) {
      if (stack.length && ++stack[stack.length - 1] > 4)
        context.report({ node, messageId: "tooNested" });
    },
  };
},
```

### Typed Rule — Remove Unnecessary Non-Null Assertion
```typescript
TSNonNullExpression(node) {
  const type = ESLintUtils.getConstrainedTypeAtLocation(services, node.expression);
  if (!tsutils.isNullableType(type)) {
    context.report({ node, messageId: "unnecessaryAssertion",
      fix(fixer) {
        const bang = sourceCode.getLastToken(node, t => t.value === "!");
        return bang ? fixer.removeRange(bang.range) : null;
      } });
  }
},
```

---

## Rule Authoring Checklist

- Declare `fixable: "code"` in `meta` before calling any fixer method
- Declare `hasSuggestions: true` in `meta` before using `suggest`
- Use `messageId` + `messages` map rather than inline message strings
- Return `null` from `fix` when the transform is not safe to apply automatically
- Use generator `*fix` for multi-node edits that must apply atomically
- Use `"Program:exit"` for whole-file analysis requiring global context
- Use `suggest` instead of `fix` when the change could alter runtime semantics
- Mark typed rules with `requiresTypeChecking: true` in `docs`
