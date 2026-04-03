# Forms and Validation

Sources: shadcn/ui forms documentation (ui.shadcn.com 2025-2026), react-hook-form documentation (react-hook-form.com), zod documentation (zod.dev), @hookform/resolvers documentation

Covers: react-hook-form + zod + Field component integration, form setup, validation modes, error display, working with different field types (input, textarea, select, checkbox, radio, switch), array fields with useFieldArray, complex multi-section forms.

## Form Architecture

shadcn/ui forms use three layers:
1. **react-hook-form** -- performant form state management with `useForm` hook
2. **zod** -- schema-based validation via `zodResolver`
3. **Field component** -- accessible form layout with labels, descriptions, and error messages

### Dependencies

```bash
npx shadcn@latest add field input label
npm i react-hook-form @hookform/resolvers zod
```

## Form Setup

### Step 1: Define the Schema

```typescript
import { z } from "zod"

const formSchema = z.object({
  title: z.string().min(1, "Title is required").max(100),
  description: z.string().max(500).optional(),
  priority: z.enum(["low", "medium", "high"]),
  notify: z.boolean().default(false),
})

type FormValues = z.infer<typeof formSchema>
```

### Step 2: Create the Form Instance

```typescript
import { useForm, Controller } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"

const form = useForm<FormValues>({
  resolver: zodResolver(formSchema),
  defaultValues: {
    title: "",
    description: "",
    priority: "medium",
    notify: false,
  },
})
```

Always provide `defaultValues` -- react-hook-form needs them for controlled components and reset behavior.

### Step 3: Build the Form

```tsx
<form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
  <Controller
    control={form.control}
    name="title"
    render={({ field, fieldState }) => (
      <Field data-invalid={!!fieldState.error}>
        <FieldLabel>Title</FieldLabel>
        <Input {...field} aria-invalid={!!fieldState.error} />
        <FieldError>{fieldState.error?.message}</FieldError>
      </Field>
    )}
  />
  <Button type="submit">Submit</Button>
</form>
```

## Field Component Anatomy

The `Field` component provides accessible form layout:

```tsx
<Field data-invalid={!!fieldState.error}>
  <FieldLabel>Label text</FieldLabel>
  {/* Form control: Input, Select, Textarea, etc. */}
  <FieldDescription>Helper text below the control</FieldDescription>
  <FieldError>{fieldState.error?.message}</FieldError>
</Field>
```

| Sub-component | Purpose |
|---------------|---------|
| `Field` | Container with spacing and error styling via `data-invalid` |
| `FieldLabel` | Accessible label connected to the control |
| `FieldDescription` | Helper text (hidden when error shows) |
| `FieldError` | Error message (visible when `data-invalid` is true) |

Mark errors with two attributes:
- `data-invalid` on `<Field>` for styling the container
- `aria-invalid` on the form control for screen readers

## Validation Modes

Configure when validation triggers:

```typescript
const form = useForm<FormValues>({
  resolver: zodResolver(formSchema),
  mode: "onBlur",       // Validate on blur
  defaultValues: { /* ... */ },
})
```

| Mode | Behavior | Best For |
|------|----------|----------|
| `"onSubmit"` | Validate only on form submit (default) | Simple forms, fewer distractions |
| `"onBlur"` | Validate when field loses focus | Long forms, field-by-field feedback |
| `"onChange"` | Validate on every keystroke | Real-time validation (expensive) |
| `"onTouched"` | First blur triggers, then every change | Best of onBlur + onChange |
| `"all"` | Validate on both blur and change | Maximum feedback |

Recommendation: Use `"onBlur"` for most forms. Use `"onSubmit"` for short forms. Avoid `"onChange"` unless the UX specifically demands real-time feedback.

## Working with Field Types

### Input Fields

Spread the `field` object directly onto `<Input>`:

```tsx
<Controller
  control={form.control}
  name="username"
  render={({ field, fieldState }) => (
    <Field data-invalid={!!fieldState.error}>
      <FieldLabel>Username</FieldLabel>
      <Input {...field} aria-invalid={!!fieldState.error} />
      <FieldDescription>3-20 characters, letters and numbers only.</FieldDescription>
      <FieldError>{fieldState.error?.message}</FieldError>
    </Field>
  )}
/>
```

### Textarea

Spread `field` onto `<Textarea>`:

```tsx
<Controller
  control={form.control}
  name="description"
  render={({ field, fieldState }) => (
    <Field data-invalid={!!fieldState.error}>
      <FieldLabel>Description</FieldLabel>
      <Textarea {...field} aria-invalid={!!fieldState.error} />
      <FieldError>{fieldState.error?.message}</FieldError>
    </Field>
  )}
/>
```

### Select

Use `field.value` and `field.onChange` on the `<Select>` component:

```tsx
<Controller
  control={form.control}
  name="priority"
  render={({ field, fieldState }) => (
    <Field data-invalid={!!fieldState.error}>
      <FieldLabel>Priority</FieldLabel>
      <Select value={field.value} onValueChange={field.onChange}>
        <SelectTrigger aria-invalid={!!fieldState.error}>
          <SelectValue placeholder="Select priority" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="low">Low</SelectItem>
          <SelectItem value="medium">Medium</SelectItem>
          <SelectItem value="high">High</SelectItem>
        </SelectContent>
      </Select>
      <FieldError>{fieldState.error?.message}</FieldError>
    </Field>
  )}
/>
```

### Checkbox

For a single boolean checkbox:

```tsx
<Controller
  control={form.control}
  name="acceptTerms"
  render={({ field, fieldState }) => (
    <Field data-invalid={!!fieldState.error}>
      <div className="flex items-center gap-2">
        <Checkbox
          checked={field.value}
          onCheckedChange={field.onChange}
          aria-invalid={!!fieldState.error}
        />
        <FieldLabel>Accept terms and conditions</FieldLabel>
      </div>
      <FieldError>{fieldState.error?.message}</FieldError>
    </Field>
  )}
/>
```

For checkbox groups (array of values), manage the array manually:

```tsx
<Controller
  control={form.control}
  name="features"
  render={({ field }) => (
    <Field>
      <FieldLabel>Features</FieldLabel>
      <FieldGroup data-slot="checkbox-group">
        {["analytics", "backup", "support"].map((feature) => (
          <div key={feature} className="flex items-center gap-2">
            <Checkbox
              checked={field.value?.includes(feature)}
              onCheckedChange={(checked) => {
                const updated = checked
                  ? [...(field.value || []), feature]
                  : field.value?.filter((v: string) => v !== feature)
                field.onChange(updated)
              }}
            />
            <Label>{feature}</Label>
          </div>
        ))}
      </FieldGroup>
    </Field>
  )}
/>
```

### Radio Group

Use `field.value` and `field.onChange` on `<RadioGroup>`:

```tsx
<Controller
  control={form.control}
  name="plan"
  render={({ field, fieldState }) => (
    <Field data-invalid={!!fieldState.error}>
      <FieldLabel>Plan</FieldLabel>
      <RadioGroup value={field.value} onValueChange={field.onChange}>
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="starter" aria-invalid={!!fieldState.error} />
          <Label>Starter</Label>
        </div>
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="pro" aria-invalid={!!fieldState.error} />
          <Label>Pro</Label>
        </div>
      </RadioGroup>
      <FieldError>{fieldState.error?.message}</FieldError>
    </Field>
  )}
/>
```

### Switch

Use `field.value` and `field.onChange` on `<Switch>`:

```tsx
<Controller
  control={form.control}
  name="mfaEnabled"
  render={({ field, fieldState }) => (
    <Field data-invalid={!!fieldState.error}>
      <div className="flex items-center justify-between">
        <FieldLabel>Multi-factor authentication</FieldLabel>
        <Switch
          checked={field.value}
          onCheckedChange={field.onChange}
          aria-invalid={!!fieldState.error}
        />
      </div>
      <FieldDescription>Secure your account with MFA.</FieldDescription>
    </Field>
  )}
/>
```

## Array Fields

Use `useFieldArray` for dynamic lists of fields:

### Schema

```typescript
const schema = z.object({
  emails: z.array(
    z.object({
      value: z.string().email("Invalid email"),
    })
  ).min(1, "At least one email required").max(5, "Maximum 5 emails"),
})
```

### Hook Setup

```typescript
const form = useForm({
  resolver: zodResolver(schema),
  defaultValues: { emails: [{ value: "" }] },
})

const { fields, append, remove } = useFieldArray({
  control: form.control,
  name: "emails",
})
```

### Rendering

```tsx
<FieldSet>
  <FieldLegend>Email Addresses</FieldLegend>
  <FieldDescription>Add up to 5 email addresses.</FieldDescription>
  {fields.map((field, index) => (
    <Controller
      key={field.id}
      control={form.control}
      name={`emails.${index}.value`}
      render={({ field: inputField, fieldState }) => (
        <Field data-invalid={!!fieldState.error}>
          <div className="flex gap-2">
            <Input {...inputField} aria-invalid={!!fieldState.error} />
            {fields.length > 1 && (
              <Button variant="outline" size="icon" onClick={() => remove(index)}>
                <Trash className="h-4 w-4" />
              </Button>
            )}
          </div>
          <FieldError>{fieldState.error?.message}</FieldError>
        </Field>
      )}
    />
  ))}
  {fields.length < 5 && (
    <Button type="button" variant="outline" onClick={() => append({ value: "" })}>
      Add Email
    </Button>
  )}
</FieldSet>
```

Use `field.id` (not `index`) as the React key -- TanStack generates stable IDs.

## Resetting Forms

```typescript
// Reset to default values
form.reset()

// Reset to specific values
form.reset({ title: "New Title", priority: "high" })
```

## Common Zod Patterns

| Pattern | Schema |
|---------|--------|
| Required string | `z.string().min(1, "Required")` |
| Optional string | `z.string().optional()` |
| Email | `z.string().email("Invalid email")` |
| URL | `z.string().url("Invalid URL")` |
| Number range | `z.number().min(1).max(100)` |
| Enum | `z.enum(["a", "b", "c"])` |
| Boolean with required true | `z.literal(true, { errorMap: () => ({ message: "Must accept" }) })` |
| Date | `z.date()` |
| Conditional field | `z.string().optional().refine(...)` with `.superRefine()` |
| Password confirm | `.refine((data) => data.password === data.confirm, { path: ["confirm"] })` |
