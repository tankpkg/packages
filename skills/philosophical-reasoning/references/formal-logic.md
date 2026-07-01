# Formal Logic Systems

Sources: Copi/Cohen/McMahon (Introduction to Logic, 14th ed), McInerny (Being Logical), Hurley (A Concise Introduction to Logic)

Covers: propositional logic, predicate logic, categorical syllogisms, truth tables, rules of inference, modal logic basics, argument validity testing.

## Propositional Logic

### Atomic Propositions and Connectives

| Symbol | Name | English | Truth Condition |
|--------|------|---------|-----------------|
| p, q, r | Variables | Any declarative sentence | Assigned T or F |
| ~p or ¬p | Negation | "not p" | True when p is false |
| p ∧ q | Conjunction | "p and q" | True when both true |
| p ∨ q | Disjunction | "p or q" | True when at least one true |
| p → q | Conditional | "if p then q" | False only when p true, q false |
| p ↔ q | Biconditional | "p if and only if q" | True when both same value |

### Rules of Inference (Valid Argument Forms)

These are the fundamental moves in deductive reasoning. Each preserves
truth — if premises are true, conclusion must be true.

| Rule | Form | Natural Language |
|------|------|------------------|
| Modus Ponens | p → q, p ∴ q | If it rains, the ground is wet. It rains. Therefore, the ground is wet. |
| Modus Tollens | p → q, ¬q ∴ ¬p | If it rains, the ground is wet. The ground is not wet. Therefore, it didn't rain. |
| Hypothetical Syllogism | p → q, q → r ∴ p → r | Chain conditionals: if A implies B, and B implies C, then A implies C. |
| Disjunctive Syllogism | p ∨ q, ¬p ∴ q | It's either A or B. It's not A. Therefore B. |
| Constructive Dilemma | (p → q) ∧ (r → s), p ∨ r ∴ q ∨ s | Two conditionals plus disjunction of antecedents yields disjunction of consequents. |
| Conjunction | p, q ∴ p ∧ q | Combine independent truths. |
| Simplification | p ∧ q ∴ p | Extract one conjunct. |
| Addition | p ∴ p ∨ q | Weaken a claim by adding alternatives. |
| Absorption | p → q ∴ p → (p ∧ q) | If A implies B, then A implies both A and B. |

### Rules of Replacement (Equivalence Rules)

These allow substituting logically equivalent expressions:

| Rule | Equivalence |
|------|-------------|
| Double Negation | ¬¬p ≡ p |
| De Morgan's Laws | ¬(p ∧ q) ≡ ¬p ∨ ¬q; ¬(p ∨ q) ≡ ¬p ∧ ¬q |
| Commutation | p ∧ q ≡ q ∧ p; p ∨ q ≡ q ∨ p |
| Distribution | p ∧ (q ∨ r) ≡ (p ∧ q) ∨ (p ∧ r) |
| Contraposition | p → q ≡ ¬q → ¬p |
| Material Implication | p → q ≡ ¬p ∨ q |
| Exportation | (p ∧ q) → r ≡ p → (q → r) |
| Tautology | p ≡ p ∨ p; p ≡ p ∧ p |

### Truth Table Method

To test validity: construct a truth table for all variables. An argument
is valid if there is NO row where all premises are true and the conclusion
is false.

| p | q | p → q | p | q (conclusion) |
|---|---|-------|---|----------------|
| T | T | T | T | T |
| T | F | F | T | - (premise false) |
| F | T | T | F | - (premise false) |
| F | F | T | F | - (premise false) |

Only the first row has all premises true — and the conclusion is also true.
Therefore Modus Ponens is valid.

### Common Invalid Forms (Formal Fallacies)

| Fallacy | Form | Why It Fails |
|---------|------|--------------|
| Affirming the Consequent | p → q, q ∴ p | The ground can be wet for other reasons (sprinkler) |
| Denying the Antecedent | p → q, ¬p ∴ ¬q | No rain doesn't guarantee dry ground |

These look similar to valid forms — the difference is which part is affirmed or denied.

## Predicate Logic

Extends propositional logic to handle internal structure of propositions.

### Quantifiers

| Symbol | Name | English | Example |
|--------|------|---------|---------|
| ∀x | Universal | "for all x" | ∀x(Dog(x) → Animal(x)) — All dogs are animals |
| ∃x | Existential | "there exists an x" | ∃x(Dog(x) ∧ Black(x)) — Some dogs are black |

### Quantifier Rules

| Rule | From | To |
|------|------|----|
| Universal Instantiation (UI) | ∀x P(x) | P(a) for any specific a |
| Universal Generalization (UG) | P(a) for arbitrary a | ∀x P(x) |
| Existential Instantiation (EI) | ∃x P(x) | P(c) for a new constant c |
| Existential Generalization (EG) | P(a) for some specific a | ∃x P(x) |

### Translating Natural Language

| English | Predicate Logic |
|---------|-----------------|
| "All humans are mortal" | ∀x(Human(x) → Mortal(x)) |
| "Some students passed" | ∃x(Student(x) ∧ Passed(x)) |
| "No reptiles are mammals" | ∀x(Reptile(x) → ¬Mammal(x)) |
| "Only members may enter" | ∀x(MayEnter(x) → Member(x)) |

Note the "all" vs "some" trap: "all" uses →, "some" uses ∧.

## Categorical Syllogisms

The oldest formal logic system (Aristotle). Reasons about categories
using three terms: major, minor, and middle.

### Standard Form

```
All M are P.     (major premise)
All S are M.     (minor premise)
∴ All S are P.   (conclusion)
```

### Four Standard-Form Propositions

| Type | Form | Example | Diagram |
|------|------|---------|---------|
| A | All S are P | All dogs are animals | S fully inside P |
| E | No S are P | No dogs are cats | S and P don't overlap |
| I | Some S are P | Some dogs are brown | S and P partially overlap |
| O | Some S are not P | Some dogs are not brown | Part of S outside P |

### Testing Validity with Venn Diagrams

1. Draw three overlapping circles (S, P, M)
2. Diagram the premises (shade excluded regions, mark existing members)
3. Check if the conclusion is already shown — if yes, valid; if not, invalid

### Commonly Valid Syllogisms

| Name | Form |
|------|------|
| Barbara | All M are P, All S are M ∴ All S are P |
| Celarent | No M are P, All S are M ∴ No S are P |
| Darii | All M are P, Some S are M ∴ Some S are P |
| Ferio | No M are P, Some S are M ∴ Some S are not P |

## Modal Logic (Basics)

Extends propositional logic with necessity and possibility operators.

| Symbol | Meaning | Example |
|--------|---------|---------|
| □p | "Necessarily p" | It is necessarily true that 2+2=4 |
| ◇p | "Possibly p" | It is possible that it rains tomorrow |

### Key Modal Relationships

- □p → p (what is necessary is actual)
- p → ◇p (what is actual is possible)
- □p ↔ ¬◇¬p (necessary = not possibly not)
- ◇p ↔ ¬□¬p (possible = not necessarily not)

Modal logic is essential for analyzing claims about what must be, could be,
or cannot be — frequent in philosophical arguments about God, free will,
morality, and metaphysics.

## Practical Application: Argument Validity Testing

### Quick Validity Check Process

1. **Identify the conclusion** — what is being argued for?
2. **List all premises** — including implicit ones
3. **Symbolize** — translate to logical notation
4. **Check form** — does it match a valid inference rule?
5. **If unclear** — construct a truth table or Venn diagram
6. **Assess soundness** — are the premises actually true?

### Validity vs. Soundness

| Term | Definition | Example |
|------|-----------|---------|
| Valid | Conclusion follows from premises | "All cats fly. Socrates is a cat. ∴ Socrates flies." (Valid, unsound) |
| Sound | Valid AND premises are true | "All humans are mortal. Socrates is human. ∴ Socrates is mortal." |
| Invalid | Conclusion doesn't follow | "Some dogs bark. Rex barks. ∴ Rex is a dog." |

A valid argument with false premises tells you nothing about the conclusion's
truth. Soundness is what matters in practice.

## When to Formalize

| Situation | Formalize? | Reason |
|-----------|-----------|--------|
| Checking if a conclusion actually follows | Yes | Formal validity testing catches hidden gaps |
| Everyday moral/political argument | Usually no | Most real arguments are informal; Toulmin model is more practical |
| Spotting structural fallacies | Yes | Affirming consequent, denying antecedent are structural errors |
| Mathematical or logical claims | Yes | These domains demand formal rigor |
| "It just feels wrong" | Try it | Formalizing reveals whether the intuition tracks a real logical error |
