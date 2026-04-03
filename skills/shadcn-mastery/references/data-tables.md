# Data Tables

Sources: shadcn/ui data table documentation (ui.shadcn.com 2025-2026), TanStack Table v8 documentation (tanstack.com/table), TanStack Table headless UI guide

Covers: TanStack Table integration with shadcn Table component, column definitions, cell formatting, row actions, pagination, sorting, filtering, column visibility, row selection, reusable table components.

## Architecture

shadcn/ui does not ship a data table component. Instead, it provides a guide for building custom data tables using the headless `@tanstack/react-table` library and the shadcn `<Table />` component. Each table is unique -- different data, sorting, filtering, and display requirements.

### Setup

```bash
npx shadcn@latest add table
npm i @tanstack/react-table
```

### Project Structure

```
app/payments/
  columns.tsx      # Column definitions (client component)
  data-table.tsx   # DataTable component (client component)
  page.tsx         # Data fetching and rendering (server component)
```

Separate column definitions from the table component. This keeps responsibilities clear and enables column reuse.

## Column Definitions

Columns define what data is displayed and how. Each column has an `accessorKey` (data field) or `accessorFn` (computed), a `header`, and an optional `cell` renderer.

### Basic Columns

```typescript
"use client"

import { ColumnDef } from "@tanstack/react-table"

export type Payment = {
  id: string
  amount: number
  status: "pending" | "processing" | "success" | "failed"
  email: string
}

export const columns: ColumnDef<Payment>[] = [
  {
    accessorKey: "status",
    header: "Status",
  },
  {
    accessorKey: "email",
    header: "Email",
  },
  {
    accessorKey: "amount",
    header: "Amount",
  },
]
```

### Cell Formatting

Format cell values with custom renderers:

```typescript
{
  accessorKey: "amount",
  header: () => <div className="text-right">Amount</div>,
  cell: ({ row }) => {
    const amount = parseFloat(row.getValue("amount"))
    const formatted = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount)
    return <div className="text-right font-medium">{formatted}</div>
  },
}
```

## Basic DataTable Component

```typescript
"use client"

import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
}

export function DataTable<TData, TValue>({
  columns,
  data,
}: DataTableProps<TData, TValue>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(header.column.columnDef.header, header.getContext())}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} data-state={row.getIsSelected() && "selected"}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                No results.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  )
}
```

## Row Actions

Add a dropdown menu to each row for actions like edit, delete, copy:

```typescript
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { MoreHorizontal } from "lucide-react"

{
  id: "actions",
  cell: ({ row }) => {
    const payment = row.original
    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-8 w-8 p-0">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => navigator.clipboard.writeText(payment.id)}>
            Copy payment ID
          </DropdownMenuItem>
          <DropdownMenuItem>View details</DropdownMenuItem>
          <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    )
  },
}
```

Access the full row data with `row.original`.

## Pagination

Add `getPaginationRowModel` to enable automatic client-side pagination:

```typescript
import { getPaginationRowModel } from "@tanstack/react-table"

const table = useReactTable({
  data,
  columns,
  getCoreRowModel: getCoreRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
})
```

Pagination controls:

```tsx
<div className="flex items-center justify-end space-x-2 py-4">
  <Button
    variant="outline"
    size="sm"
    onClick={() => table.previousPage()}
    disabled={!table.getCanPreviousPage()}
  >
    Previous
  </Button>
  <Button
    variant="outline"
    size="sm"
    onClick={() => table.nextPage()}
    disabled={!table.getCanNextPage()}
  >
    Next
  </Button>
</div>
```

Default page size is 10. Customize with `initialState`:

```typescript
const table = useReactTable({
  // ...
  initialState: { pagination: { pageSize: 20 } },
})
```

## Sorting

Add `getSortedRowModel` and manage sorting state:

```typescript
import { SortingState, getSortedRowModel } from "@tanstack/react-table"

const [sorting, setSorting] = React.useState<SortingState>([])

const table = useReactTable({
  data,
  columns,
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  onSortingChange: setSorting,
  state: { sorting },
})
```

Make a column header sortable:

```typescript
{
  accessorKey: "email",
  header: ({ column }) => (
    <Button
      variant="ghost"
      onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
    >
      Email
      <ArrowUpDown className="ml-2 h-4 w-4" />
    </Button>
  ),
}
```

## Filtering

Add `getFilteredRowModel` and manage filter state:

```typescript
import { ColumnFiltersState, getFilteredRowModel } from "@tanstack/react-table"

const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])

const table = useReactTable({
  data,
  columns,
  getCoreRowModel: getCoreRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
  onColumnFiltersChange: setColumnFilters,
  state: { columnFilters },
})
```

Add a filter input:

```tsx
<Input
  placeholder="Filter emails..."
  value={(table.getColumn("email")?.getFilterValue() as string) ?? ""}
  onChange={(event) => table.getColumn("email")?.setFilterValue(event.target.value)}
  className="max-w-sm"
/>
```

## Column Visibility

Add visibility state to hide/show columns:

```typescript
import { VisibilityState } from "@tanstack/react-table"

const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})

const table = useReactTable({
  // ...
  onColumnVisibilityChange: setColumnVisibility,
  state: { columnVisibility },
})
```

Toggle with a DropdownMenu:

```tsx
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="outline">Columns</Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    {table.getAllColumns().filter((col) => col.getCanHide()).map((col) => (
      <DropdownMenuCheckboxItem
        key={col.id}
        checked={col.getIsVisible()}
        onCheckedChange={(value) => col.toggleVisibility(!!value)}
      >
        {col.id}
      </DropdownMenuCheckboxItem>
    ))}
  </DropdownMenuContent>
</DropdownMenu>
```

## Row Selection

Add a checkbox column and selection state:

```typescript
import { Checkbox } from "@/components/ui/checkbox"

// Add as first column:
{
  id: "select",
  header: ({ table }) => (
    <Checkbox
      checked={table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && "indeterminate")}
      onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
      aria-label="Select all"
    />
  ),
  cell: ({ row }) => (
    <Checkbox
      checked={row.getIsSelected()}
      onCheckedChange={(value) => row.toggleSelected(!!value)}
      aria-label="Select row"
    />
  ),
  enableSorting: false,
  enableHiding: false,
}
```

Manage selection state:

```typescript
const [rowSelection, setRowSelection] = React.useState({})

const table = useReactTable({
  // ...
  onRowSelectionChange: setRowSelection,
  state: { rowSelection },
})
```

Display count:

```tsx
<div className="text-sm text-muted-foreground">
  {table.getFilteredSelectedRowModel().rows.length} of{" "}
  {table.getFilteredRowModel().rows.length} row(s) selected.
</div>
```

## Reusable Table Components

Extract common patterns into shared components when the same table UI appears in multiple places.

### Column Header Component

A sortable, hideable column header:

```typescript
import { Column } from "@tanstack/react-table"
import { cn } from "@/lib/utils"
import { ArrowDown, ArrowUp, ChevronsUpDown, EyeOff } from "lucide-react"

interface DataTableColumnHeaderProps<TData, TValue>
  extends React.HTMLAttributes<HTMLDivElement> {
  column: Column<TData, TValue>
  title: string
}

export function DataTableColumnHeader<TData, TValue>({
  column,
  title,
  className,
}: DataTableColumnHeaderProps<TData, TValue>) {
  if (!column.getCanSort()) {
    return <div className={cn(className)}>{title}</div>
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="-ml-3 h-8">
          <span>{title}</span>
          {column.getIsSorted() === "desc" ? (
            <ArrowDown className="ml-2 h-4 w-4" />
          ) : column.getIsSorted() === "asc" ? (
            <ArrowUp className="ml-2 h-4 w-4" />
          ) : (
            <ChevronsUpDown className="ml-2 h-4 w-4" />
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuItem onClick={() => column.toggleSorting(false)}>Asc</DropdownMenuItem>
        <DropdownMenuItem onClick={() => column.toggleSorting(true)}>Desc</DropdownMenuItem>
        <DropdownMenuItem onClick={() => column.toggleVisibility(false)}>Hide</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

Use in column definitions: `header: ({ column }) => <DataTableColumnHeader column={column} title="Email" />`
