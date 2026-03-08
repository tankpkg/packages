# Testing Linters, Codemods, and AST Transforms

Sources: Noback/Votruba (Rector: Automated Refactoring), ESLint RuleTester documentation, jscodeshift testUtils, ast-grep test framework, production test suites from React/Next.js/Angular, 2025-2026 testing patterns

## The Testing Philosophy

A codemod is a pure function: it takes source text (or an AST) and returns transformed source text. Test it like a pure function — fixed input, deterministic output, no side effects.

Three properties every transform must satisfy:

- **Correctness** — the output matches the expected transformation exactly
- **Idempotency** — running the transform twice produces the same result as running it once
- **Scope discipline** — the transform only modifies what it claims to modify; unrelated code is untouched

These properties map directly to test types: fixture tests verify correctness, idempotency tests verify stability, and no-op tests verify scope discipline.

---

## Fixture-Based Testing for Codemods

The standard pattern across React, Next.js, and Angular codemods: one input file and one output file per edge case, stored in a `__testfixtures__` directory alongside the transform. Structure:

```
transforms/remove-forward-ref.ts
__tests__/remove-forward-ref.test.ts
__testfixtures__/remove-forward-ref/
  function-expression.input.ts   function-expression.output.ts
  arrow-function.input.ts        arrow-function.output.ts
  typescript-generics.input.tsx  typescript-generics.output.tsx
```

One fixture per edge case. Name fixtures after the syntactic variant they cover, not after the rule — failures become self-documenting.

### defineTest from jscodeshift/testUtils

```typescript
import { defineTest, defineInlineTest } from 'jscodeshift/dist/testUtils';

// Reads from __testfixtures__ relative to __dirname
describe('remove-forward-ref', () => {
  const tests = [
    'function-expression',
    'arrow-function',
    'typescript-generics',
    'already-transformed',  // no-op case
  ];

  tests.forEach(test =>
    defineTest(
      __dirname,
      'remove-forward-ref',
      null,                                    // options
      `remove-forward-ref/${test}`             // fixture name
    )
  );
});
```

For TypeScript fixtures, override the parser in a nested describe:

```typescript
describe('typescript', () => {
  beforeEach(() => {
    jest.mock('../remove-forward-ref', () =>
      Object.assign(
        jest.requireActual('../remove-forward-ref'),
        { parser: 'tsx' }
      )
    );
  });
  afterEach(() => jest.resetModules());

  tsTests.forEach(test =>
    defineTest(__dirname, 'remove-forward-ref', null, `remove-forward-ref/ts/${test}`)
  );
});
```

For quick inline cases without fixture files, use `defineInlineTest(transform, options, input, expectedOutput, testName)` from the same package.

---

## ESLint RuleTester

### Basic Setup

```typescript
import { RuleTester } from 'eslint';
import rule from '../../src/rules/no-var';

const ruleTester = new RuleTester({
  languageOptions: { ecmaVersion: 2022, sourceType: 'module' },
});

ruleTester.run('no-var', rule, {
  valid: [
    'const x = 1;',
    { code: 'let x = 1;', options: [{ allowLet: true }] },
  ],
  invalid: [
    {
      code: 'var x = 1;',
      output: 'let x = 1;',          // expected output after --fix
      errors: [{ messageId: 'unexpectedVar', line: 1, column: 1 }],
    },
  ],
});
```

The `output` field is the complete file content after applying the fix — not a diff. If the rule reports but does not fix, omit `output`. When multiple errors appear in one file, all their fixes are applied in a single pass; `output` reflects the combined result.

### Testing Suggestions

Suggestions appear in editors as quick-fix options but are not applied by `--fix`. Test them with the `suggestions` array inside each error:

```typescript
{
  code: 'a == b',
  errors: [
    {
      messageId: 'useTripleEquals',
      suggestions: [
        {
          messageId: 'replaceOperator',
          data: { expected: '===', actual: '==' },
          output: 'a === b',          // output after applying this suggestion
        },
      ],
    },
  ],
},
```

### TypeScript-Aware RuleTester and Vitest Integration

For rules that use `requiresTypeChecking: true`, use `@typescript-eslint/rule-tester` with a real tsconfig:

```typescript
import { RuleTester } from '@typescript-eslint/rule-tester';
import { afterAll, describe, it } from 'vitest';

// Wire into Vitest (or Jest — same API)
RuleTester.afterAll = afterAll;
RuleTester.describe = describe;
RuleTester.it = it;

const ruleTester = new RuleTester({
  languageOptions: {
    parserOptions: { project: './tsconfig.json', tsconfigRootDir: __dirname },
  },
});

ruleTester.run('no-unnecessary-type-assertion', rule, {
  valid: [`const x = 1 as number;`],
  invalid: [
    {
      code: `const x = 3 as number;`,
      errors: [{ messageId: 'unnecessaryAssertion' }],
      output: `const x = 3;`,
    },
  ],
});
```

---

## ast-grep YAML Test Format

ast-grep tests live in a `tests/` directory mirroring the `rules/` structure. Each test file is YAML with `valid` and `invalid` sections. For rules with fixes, add a `fixed` field.

```yaml
# tests/typescript/security/jwt-simple-noverify-typescript.yml
id: jwt-simple-noverify-typescript
valid:
  - |
    const jwt = require('jwt-simple');
    jwt.decode(token, secret);          # no noverify flag — valid
  - |
    import jwt from 'jsonwebtoken';
    jwt.verify(token, secret);          # different library — valid

invalid:
  - code: |
      const jwt = require('jwt-simple');
      jwt.decode(token, secret, true);
  - code: |
      console.log(x)
    fixed: |
      logger.info(x)
```

Run with `sg test` or `sg test --filter jwt`. The `sgconfig.yml` at the repo root must declare `testConfigs: [{ testDir: tests }]`.

---

## ts-morph Codemod Testing

ts-morph transforms operate on a `Project` object. For testing, create an in-memory project — no disk I/O, no tsconfig required for simple cases.

```typescript
import { Project } from 'ts-morph';
import { applyTransform } from '../src/my-transform';

function createProject(source: string): Project {
  const project = new Project({ useInMemoryFileSystem: true });
  project.createSourceFile('test.ts', source);
  return project;
}

it('adds private modifier to unused members', async () => {
  const project = createProject(`class Foo { bar() {} private baz() { this.bar(); } }`);
  await applyTransform(project);
  expect(project.getSourceFileOrThrow('test.ts').getFullText()).toContain('private bar()');
});

it('does not modify already-private members', async () => {
  const input = `class Foo { private bar() {} }`;
  const project = createProject(input);
  await applyTransform(project);
  expect(project.getSourceFileOrThrow('test.ts').getFullText()).toBe(input);
});
```

For transforms that require real type information, point to a real tsconfig. After the transform, check diagnostics directly:

```typescript
const project = new Project({ tsConfigFilePath: './tsconfig.test.json' });
project.addSourceFileAtPath('./fixtures/input.ts');
await applyTransform(project);
const diagnostics = project.getPreEmitDiagnostics();
expect(diagnostics.length).toBe(0);
```

---

## Snapshot Testing

Use snapshots when output is large and structure matters more than exact text. Avoid them when output is under 20 lines — explicit assertions catch regressions more precisely and make failures readable without opening a snapshot file.

Snapshot pitfalls to avoid:
- Snapshots updated on every change provide no protection — they become documentation, not tests
- Whitespace differences cause false failures across OS and formatter versions
- Large snapshots obscure what actually changed in a failing test

For jscodeshift, prefer fixture files over snapshots. The `defineTest` utility already provides the fixture-based workflow that snapshots attempt to replicate, with the added benefit that fixture files are readable as standalone code.

---

## Idempotency Testing

A transform is idempotent if applying it twice produces the same result as applying it once. The Rector book identifies idempotency as a required property of every rule. The test is mechanical:

```typescript
function assertIdempotent(transform: Transform, input: string): void {
  const firstPass = transform(input);
  const secondPass = transform(firstPass ?? input);
  expect(secondPass).toEqual(firstPass ?? input);
}

it('is idempotent', () => {
  assertIdempotent(myTransform, `var x = 1;`);
  assertIdempotent(myTransform, `let x = 1;`);   // already transformed — no-op
});
```

For jscodeshift, the second pass must return `null` when the file was already transformed. Include an `already-transformed` fixture in every fixture suite.

Common causes of non-idempotency:
- Adding an import without checking if it already exists
- Wrapping a node without checking if it is already wrapped
- Inserting a comment that the transform then detects as a signal to transform again

---

## Type Checking Validation

Running `tsc --noEmit` after a transform is the strongest correctness check available. A transform that introduces type errors has broken the codebase even if all fixture tests pass.

For jscodeshift transforms, write the output to a temp file and type-check it:

```typescript
import { execSync } from 'child_process';
import { writeFileSync, unlinkSync } from 'fs';

function assertTypeCorrect(source: string): void {
  const tmp = '/tmp/transform-output.ts';
  writeFileSync(tmp, source);
  try {
    execSync(`npx tsc --noEmit --strict ${tmp}`, { stdio: 'pipe' });
  } catch (err: any) {
    throw new Error(`Type errors in transform output:\n${err.stdout}`);
  } finally {
    unlinkSync(tmp);
  }
}

it('produces type-correct output', () => assertTypeCorrect(applyTransform(input)));
```

For ts-morph transforms, use the project's diagnostics directly (shown in the ts-morph section above).

---

## Edge Case Test Catalog

Every codemod should have fixtures covering these cases. Cases marked "no-op" should return `null` (jscodeshift) or the unchanged source.

| Case | Description | Expected Behavior |
|------|-------------|-------------------|
| Empty file | File with no content | No-op |
| Comments only | File with only block/line comments | No-op |
| Already transformed | Output of a previous run | No-op (idempotency) |
| Target pattern absent | File that does not contain the pattern | No-op |
| Named import | `import { foo } from 'x'` | Transform |
| Default import | `import foo from 'x'` | Transform |
| Namespace import | `import * as foo from 'x'` | Transform |
| Re-export | `export { foo } from 'x'` | Transform or no-op per rule |
| TypeScript generics | `forwardRef<Ref, Props>(...)` | Transform with type params |
| JSX | Pattern inside JSX attribute or child | Transform |
| Template literals | Pattern inside `` `${expr}` `` | Transform |
| Destructuring | `const { a, b } = obj` | Transform |
| Spread | `{ ...rest }` or `[...items]` | Transform |
| Optional chaining | `obj?.method?.()` | Transform |
| Nested scope | Pattern inside nested function | Transform with scope awareness |
| Class method | Pattern as class method body | Transform |
| Arrow function | Pattern as arrow function body | Transform |
| Async function | Pattern inside `async` function | Transform |
| Multiple occurrences | Pattern appears 3+ times in one file | Transform all |
| Mixed valid/invalid | Some occurrences match, some do not | Transform only matching |

---

## CI Integration

Run codemod tests in CI the same way you run unit tests — they are unit tests. Add a TypeScript version matrix when the transform touches TypeScript-specific syntax, because the TypeScript AST changes between minor versions:

```yaml
strategy:
  matrix:
    node-version: [20, 22]
    typescript-version: ['5.3', '5.4', '5.5']
steps:
  - run: npm ci
  - run: npm install typescript@${{ matrix.typescript-version }}
  - run: npm test
  - run: npx tsc --noEmit   # type-check the transform itself
```

For ESLint plugins, test against each ESLint version declared as a peer dependency:

```bash
npm install eslint@8 && npm test
npm install eslint@9 && npm test
```

Keep fixture files in version control. When a transform changes behavior, the fixture diff makes the change explicit and reviewable. Never auto-update fixtures in CI — treat fixture changes as intentional code changes requiring human review.
