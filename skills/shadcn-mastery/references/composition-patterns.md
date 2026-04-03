# Component Composition Patterns

Sources: shadcn/ui official documentation (ui.shadcn.com 2025-2026), Radix UI composition patterns, cmdk documentation, production patterns from shadcn examples and blocks

Covers: Dialog + Form composition, Command palette (cmdk), Combobox (Command + Popover), Sheet patterns, Sidebar component, toast/sonner integration, responsive overlays, nested overlays, component selection guide.

## Dialog + Form

Combine Dialog with a form for modal data entry. The form lives inside the Dialog content:

```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

function CreateItemDialog() {
  const [open, setOpen] = React.useState(false)
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", description: "" },
  })

  function onSubmit(values: FormValues) {
    // Save data
    setOpen(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Create Item</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Item</DialogTitle>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <Controller
            control={form.control}
            name="name"
            render={({ field, fieldState }) => (
              <Field data-invalid={!!fieldState.error}>
                <FieldLabel>Name</FieldLabel>
                <Input {...field} aria-invalid={!!fieldState.error} />
                <FieldError>{fieldState.error?.message}</FieldError>
              </Field>
            )}
          />
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Save</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
```

Reset the form when the dialog closes to prevent stale state:

```tsx
<Dialog open={open} onOpenChange={(isOpen) => {
  setOpen(isOpen)
  if (!isOpen) form.reset()
}}>
```

## Command Palette

The Command component (powered by cmdk) provides a searchable command launcher:

```bash
npx shadcn@latest add command dialog
```

### Basic Command Menu

```tsx
import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator } from "@/components/ui/command"

function CommandMenu() {
  const [open, setOpen] = React.useState(false)

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }
    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [])

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Navigation">
          <CommandItem onSelect={() => { router.push("/dashboard"); setOpen(false) }}>
            Dashboard
          </CommandItem>
          <CommandItem onSelect={() => { router.push("/settings"); setOpen(false) }}>
            Settings
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Actions">
          <CommandItem onSelect={() => { setTheme("dark"); setOpen(false) }}>
            Toggle Dark Mode
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
```

`CommandDialog` wraps Command inside a Dialog automatically. For inline command lists (not in a dialog), use `<Command>` directly.

## Combobox (Searchable Select)

Compose Command + Popover for a searchable dropdown:

```bash
npx shadcn@latest add command popover button
```

```tsx
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Check, ChevronsUpDown } from "lucide-react"

const frameworks = [
  { value: "next", label: "Next.js" },
  { value: "remix", label: "Remix" },
  { value: "astro", label: "Astro" },
  { value: "nuxt", label: "Nuxt" },
]

function Combobox() {
  const [open, setOpen] = React.useState(false)
  const [value, setValue] = React.useState("")

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" role="combobox" aria-expanded={open} className="w-[200px] justify-between">
          {value ? frameworks.find((f) => f.value === value)?.label : "Select framework..."}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0">
        <Command>
          <CommandInput placeholder="Search framework..." />
          <CommandList>
            <CommandEmpty>No framework found.</CommandEmpty>
            <CommandGroup>
              {frameworks.map((framework) => (
                <CommandItem
                  key={framework.value}
                  value={framework.value}
                  onSelect={(currentValue) => {
                    setValue(currentValue === value ? "" : currentValue)
                    setOpen(false)
                  }}
                >
                  <Check className={cn("mr-2 h-4 w-4", value === framework.value ? "opacity-100" : "opacity-0")} />
                  {framework.label}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
```

For form integration, wrap the Combobox in a Controller and call `field.onChange` from `onSelect`.

## Sheet Patterns

Sheet slides content from an edge. Use for secondary navigation, filters, or detail panels:

```tsx
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetFooter } from "@/components/ui/sheet"

<Sheet>
  <SheetTrigger asChild>
    <Button variant="outline">Open Filters</Button>
  </SheetTrigger>
  <SheetContent side="right" className="w-[400px]">
    <SheetHeader>
      <SheetTitle>Filters</SheetTitle>
    </SheetHeader>
    {/* Filter form content */}
    <SheetFooter>
      <Button>Apply Filters</Button>
    </SheetFooter>
  </SheetContent>
</Sheet>
```

Side options: `"top"`, `"right"`, `"bottom"`, `"left"`.

### Sheet vs Dialog vs Drawer

| Overlay | Use When |
|---------|----------|
| Dialog | Focused task requiring attention (confirm, form, alert) |
| AlertDialog | Blocking confirmation (cannot dismiss by clicking outside) |
| Sheet | Supplementary content, filters, detail panel |
| Drawer | Mobile-friendly bottom panel with swipe-to-dismiss |

## Sidebar Component

shadcn provides a full Sidebar component with collapsible groups, navigation, and responsive behavior:

```bash
npx shadcn@latest add sidebar
```

```tsx
import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"

function AppLayout({ children }) {
  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Application</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <a href="/dashboard">Dashboard</a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
      </Sidebar>
      <main className="flex-1">
        <SidebarTrigger />
        {children}
      </main>
    </SidebarProvider>
  )
}
```

The Sidebar uses its own CSS variable tokens (`sidebar`, `sidebar-foreground`, `sidebar-primary`, etc.) for independent theming.

## Toast / Sonner

shadcn wraps `sonner` for toast notifications:

```bash
npx shadcn@latest add sonner
```

Add the Toaster to the root layout:

```tsx
import { Toaster } from "@/components/ui/sonner"

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  )
}
```

Trigger toasts from anywhere:

```tsx
import { toast } from "sonner"

toast("Event created")
toast.success("Saved successfully")
toast.error("Something went wrong")
toast.promise(saveData(), {
  loading: "Saving...",
  success: "Saved!",
  error: "Failed to save",
})
```

## Nested Overlays

Radix manages overlay stacking. A Dialog inside a Dialog works without manual z-index management:

```tsx
<Dialog>
  <DialogContent>
    <p>Parent dialog content</p>
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="destructive">Delete</Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogTitle>Confirm deletion?</AlertDialogTitle>
        <AlertDialogAction>Confirm</AlertDialogAction>
        <AlertDialogCancel>Cancel</AlertDialogCancel>
      </AlertDialogContent>
    </AlertDialog>
  </DialogContent>
</Dialog>
```

Radix handles focus trapping, escape key propagation, and overlay backdrop for nested overlays.

## Date Picker

Compose Calendar + Popover:

```bash
npx shadcn@latest add calendar popover button
```

```tsx
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { format } from "date-fns"
import { CalendarIcon } from "lucide-react"

function DatePicker() {
  const [date, setDate] = React.useState<Date>()

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" className={cn("w-[240px] justify-start text-left font-normal", !date && "text-muted-foreground")}>
          <CalendarIcon className="mr-2 h-4 w-4" />
          {date ? format(date, "PPP") : <span>Pick a date</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar mode="single" selected={date} onSelect={setDate} initialFocus />
      </PopoverContent>
    </Popover>
  )
}
```

This pattern is reusable for date range pickers (`mode="range"`) and date-time pickers (Calendar + time input).
