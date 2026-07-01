# Form Integration with React Hook Form

Sources: Zod v4 official documentation (zod.dev), @hookform/resolvers documentation, React Hook Form documentation (react-hook-form.com)

Covers: zodResolver setup, type-safe forms, field-level error display, conditional validation, field arrays, multi-step forms, server actions, and progressive enhancement.

## Setup

Install the required packages:

```bash
npm install react-hook-form @hookform/resolvers zod
```

## Basic Integration

### Define Schema and Infer Types

```typescript
import * as z from "zod";

const LoginSchema = z.object({
  email: z.email({ error: "Enter a valid email" }),
  password: z.string().min(8, { error: "At least 8 characters" }),
});

type LoginForm = z.infer<typeof LoginSchema>;
// { email: string; password: string }
```

### Connect to React Hook Form

```typescript
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

function LoginPage() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(LoginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (data: LoginForm) => {
    // data is fully typed and validated
    await login(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("email")} />
      {errors.email && <span>{errors.email.message}</span>}

      <input type="password" {...register("password")} />
      {errors.password && <span>{errors.password.message}</span>}

      <button type="submit" disabled={isSubmitting}>Log In</button>
    </form>
  );
}
```

### How It Works

1. `zodResolver(schema)` wraps Zod's `safeParse` in React Hook Form's resolver interface
2. On submit (or on change/blur depending on `mode`), the resolver validates the form data
3. Validation errors are mapped to `errors` by field path
4. Valid data is passed to the `onSubmit` handler with the inferred type

## Validation Modes

| Mode | Validates On | Best For |
|------|-------------|----------|
| `"onSubmit"` (default) | Submit button press | Simple forms |
| `"onBlur"` | Field loses focus | Field-by-field feedback |
| `"onChange"` | Every keystroke | Real-time validation |
| `"onTouched"` | First blur, then onChange | Progressive disclosure |
| `"all"` | All events | Maximum feedback |

```typescript
useForm<LoginForm>({
  resolver: zodResolver(LoginSchema),
  mode: "onBlur",
});
```

Prefer `"onBlur"` or `"onTouched"` for production forms — `"onChange"` can cause performance issues on large forms.

## Optional Fields and Defaults

```typescript
const ProfileSchema = z.object({
  name: z.string().min(1, { error: "Name is required" }),
  bio: z.string().max(500).optional(),
  newsletter: z.boolean().default(false),
  age: z.coerce.number().min(13).optional(),
});

type ProfileForm = z.infer<typeof ProfileSchema>;
// { name: string; bio?: string; newsletter: boolean; age?: number }
```

HTML inputs always produce strings. Use `z.coerce.number()` for numeric fields:

```typescript
<input type="number" {...register("age")} />
// Without coerce: age is "25" (string) -> validation fails
// With z.coerce.number(): "25" -> 25 -> validation passes
```

## Cross-Field Validation

Validate field relationships at the object level:

```typescript
const SignupSchema = z.object({
  password: z.string().min(8),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"], // error appears on confirmPassword field
});
```

## Conditional Validation with Discriminated Unions

Use discriminated unions for forms where fields depend on a selection:

```typescript
const PaymentSchema = z.discriminatedUnion("method", [
  z.object({
    method: z.literal("credit_card"),
    cardNumber: z.string().min(16).max(19),
    expiry: z.string().regex(/^\d{2}\/\d{2}$/),
    cvv: z.string().length(3),
  }),
  z.object({
    method: z.literal("bank_transfer"),
    accountNumber: z.string().min(8),
    routingNumber: z.string().length(9),
  }),
  z.object({
    method: z.literal("paypal"),
    paypalEmail: z.email(),
  }),
]);
```

Render fields conditionally based on the watched value:

```typescript
function PaymentForm() {
  const { register, watch, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(PaymentSchema),
  });

  const method = watch("method");

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <select {...register("method")}>
        <option value="credit_card">Credit Card</option>
        <option value="bank_transfer">Bank Transfer</option>
        <option value="paypal">PayPal</option>
      </select>

      {method === "credit_card" && (
        <>
          <input {...register("cardNumber")} placeholder="Card Number" />
          {errors.cardNumber && <span>{errors.cardNumber.message}</span>}
          {/* ... expiry, cvv */}
        </>
      )}
      {method === "bank_transfer" && (
        <>
          <input {...register("accountNumber")} />
          <input {...register("routingNumber")} />
        </>
      )}
      {method === "paypal" && (
        <input {...register("paypalEmail")} placeholder="PayPal Email" />
      )}
      <button type="submit">Pay</button>
    </form>
  );
}
```

## Field Arrays

Validate dynamic lists of items:

```typescript
const OrderSchema = z.object({
  customerName: z.string().min(1),
  items: z.array(
    z.object({
      product: z.string().min(1),
      quantity: z.coerce.number().int().positive(),
      price: z.coerce.number().positive(),
    })
  ).min(1, { error: "At least one item required" }),
});
```

```typescript
import { useFieldArray } from "react-hook-form";

function OrderForm() {
  const { register, control, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(OrderSchema),
    defaultValues: { customerName: "", items: [{ product: "", quantity: 1, price: 0 }] },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "items" });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("customerName")} />
      {fields.map((field, index) => (
        <div key={field.id}>
          <input {...register(`items.${index}.product`)} />
          <input type="number" {...register(`items.${index}.quantity`)} />
          <input type="number" step="0.01" {...register(`items.${index}.price`)} />
          <button type="button" onClick={() => remove(index)}>Remove</button>
        </div>
      ))}
      <button type="button" onClick={() => append({ product: "", quantity: 1, price: 0 })}>
        Add Item
      </button>
      <button type="submit">Place Order</button>
    </form>
  );
}
```

## Multi-Step Forms

Split a large form into steps, validate each step independently:

```typescript
const Step1Schema = z.object({
  name: z.string().min(1),
  email: z.email(),
});

const Step2Schema = z.object({
  address: z.string().min(1),
  city: z.string().min(1),
  zip: z.string().regex(/^\d{5}$/),
});

const Step3Schema = z.object({
  cardNumber: z.string().min(16),
  expiry: z.string(),
});

// Full schema for final submission
const FullSchema = Step1Schema.extend({
  ...Step2Schema.shape,
  ...Step3Schema.shape,
});

type FullForm = z.infer<typeof FullSchema>;
```

Use `trigger()` to validate only the current step's fields:

```typescript
function MultiStepForm() {
  const [step, setStep] = useState(1);
  const form = useForm<FullForm>({
    resolver: zodResolver(FullSchema),
    mode: "onTouched",
  });

  const nextStep = async () => {
    const fieldsToValidate = step === 1
      ? ["name", "email"]
      : step === 2
      ? ["address", "city", "zip"]
      : ["cardNumber", "expiry"];

    const valid = await form.trigger(fieldsToValidate as any);
    if (valid) setStep((s) => s + 1);
  };

  // Render current step fields...
}
```

## Server Actions (Next.js App Router)

Validate form data on the server with Zod:

```typescript
// app/actions.ts
"use server";
import * as z from "zod";

const ContactSchema = z.object({
  name: z.string().min(1),
  email: z.email(),
  message: z.string().min(10).max(1000),
});

export async function submitContact(formData: FormData) {
  const result = ContactSchema.safeParse({
    name: formData.get("name"),
    email: formData.get("email"),
    message: formData.get("message"),
  });

  if (!result.success) {
    return { errors: result.error.flatten().fieldErrors };
  }

  await sendEmail(result.data);
  return { success: true };
}
```

### With useActionState (React 19)

```typescript
"use client";
import { useActionState } from "react";
import { submitContact } from "./actions";

function ContactForm() {
  const [state, formAction, isPending] = useActionState(submitContact, null);

  return (
    <form action={formAction}>
      <input name="name" />
      {state?.errors?.name && <span>{state.errors.name[0]}</span>}

      <input name="email" />
      {state?.errors?.email && <span>{state.errors.email[0]}</span>}

      <textarea name="message" />
      {state?.errors?.message && <span>{state.errors.message[0]}</span>}

      <button type="submit" disabled={isPending}>Send</button>
    </form>
  );
}
```

## Form Error Display Patterns

| Pattern | When |
|---------|------|
| Inline below field | Default — most forms |
| Toast/banner | Form-level errors (network, auth) |
| Summary at top | Accessibility requirement (link to field) |
| Tooltip on hover | Space-constrained UIs |

## Common Gotchas

| Gotcha | Cause | Fix |
|--------|-------|-----|
| Number field validates as string | HTML inputs return strings | Use `z.coerce.number()` |
| Checkbox always `"on"` | HTML checkbox value | Use `z.coerce.boolean()` or transform |
| Optional field gets `""` not `undefined` | Empty string from input | Use `.transform(v => v === "" ? undefined : v)` or `.optional()` chained with preprocess |
| Cross-field errors not showing | Missing `path` in `.refine()` | Add `path: ["fieldName"]` |
| Default values cause hydration mismatch | SSR form defaults differ | Set `defaultValues` in `useForm` |
| `mode: "onChange"` is slow | Validates every keystroke | Use `"onBlur"` or `"onTouched"` |
