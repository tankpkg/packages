# Angular Signals Migration

Sources: Angular Blog (signal-input-migrations), angular.dev/reference/migrations, angular-university.io (signal-components guide), angularspace.com (migrating-to-signals), dev.to (signals v17.3 to v21 operator's manual)

Covers: signal adoption path from decorators to signal functions, version-by-version API timeline, migration schematics, RxJS interop, and architectural patterns for signal-based Angular apps.

## Signal API Timeline

| API | Introduced | Dev Preview | Stable | Migration Schematic |
|-----|-----------|-------------|--------|-------------------|
| `signal()` | v16 | v16 | v17 | N/A (new API) |
| `computed()` | v16 | v16 | v17 | N/A (new API) |
| `effect()` | v16 | v16-v19 | v20 | N/A (new API) |
| `input()` | v17.1 | v17.1-v18 | v19 | `signal-input-migration` |
| `input.required()` | v17.1 | v17.1-v18 | v19 | `signal-input-migration` |
| `output()` | v17.3 | v17.3-v18 | v19 | `output-migration` |
| `model()` | v17.2 | v17.2-v18 | v19 | Manual |
| `viewChild()` | v17.2 | v17.2-v18 | v19 | `signal-queries-migration` |
| `viewChildren()` | v17.2 | v17.2-v18 | v19 | `signal-queries-migration` |
| `contentChild()` | v17.2 | v17.2-v18 | v19 | `signal-queries-migration` |
| `contentChildren()` | v17.2 | v17.2-v18 | v19 | `signal-queries-migration` |
| `linkedSignal()` | v19 | v19 | v20 | N/A (new API) |
| `resource()` | v19 | v19 | v20 | N/A (new API) |
| `rxResource()` | v19 | v19 | v20 | N/A (new API) |
| `toSignal()` | v16 | v16-v19 | v20 | N/A (interop) |
| `toObservable()` | v16 | v16-v19 | v20 | N/A (interop) |
| Signal Forms | v21 | v21 (experimental) | TBD | N/A (new API) |

## Migration 1: @Input() to input()

### Before (Decorator-Based)

```typescript
@Component({...})
export class UserCard {
  @Input() name: string = '';
  @Input({ required: true }) userId!: string;
  @Input({ alias: 'color' }) themeColor: string = 'blue';
  @Input({ transform: booleanAttribute }) disabled: boolean = false;
}
```

### After (Signal-Based)

```typescript
@Component({...})
export class UserCard {
  name = input<string>('');
  userId = input.required<string>();
  themeColor = input<string>('blue', { alias: 'color' });
  disabled = input(false, { transform: booleanAttribute });
}
```

### Key Differences

| Aspect | `@Input()` | `input()` |
|--------|-----------|-----------|
| Reading value | `this.name` | `this.name()` (function call) |
| Type | `string` | `InputSignal<string>` |
| Reactivity | None (need `ngOnChanges`) | Reactive (use in `computed`/`effect`) |
| Required | `!` assertion | `input.required<T>()` |
| Transform | Same | Same |
| Alias | Same | Same |

### Automated Migration

```bash
ng generate @angular/core:signal-input-migration
```

The schematic:
- Converts `@Input()` declarations to `input()`
- Updates template references (adds `()` to input reads)
- Updates component class references
- Preserves types, defaults, aliases, transforms

### Common Issue: Type Narrowing in Templates

Signal inputs in `@if` blocks may cause type narrowing issues:

```html
<!-- May fail: compiler narrows type after @if check -->
@if (user()) {
  <span>{{ user()!.name }}</span>  <!-- Add ! for narrowing -->
}
```

### Third-Party Alternative: ngxtension

```bash
npx ng add ngxtension
npx ng g ngxtension:convert-signal-inputs
npx ng g ngxtension:convert-signal-inputs --path=libs/feature-xyz
```

## Migration 2: @Output() to output()

### Before

```typescript
@Component({...})
export class SearchBar {
  @Output() search = new EventEmitter<string>();
  @Output('changed') valueChanged = new EventEmitter<string>();

  onSearch(term: string) {
    this.search.emit(term);
  }
}
```

### After

```typescript
@Component({...})
export class SearchBar {
  search = output<string>();
  valueChanged = output<string>({ alias: 'changed' });

  onSearch(term: string) {
    this.search.emit(term);
  }
}
```

### Key Differences

| Aspect | `@Output() + EventEmitter` | `output()` |
|--------|---------------------------|-----------|
| Type | `EventEmitter<T>` (extends Subject) | `OutputEmitterRef<T>` |
| RxJS dependency | Yes (EventEmitter extends Subject) | No |
| `.emit()` | Same | Same |
| `.subscribe()` | Available (anti-pattern) | Not available |
| Alias | Same | Same |

### Automated Migration

```bash
ng generate @angular/core:output-migration
```

### RxJS Interop for Outputs

Bridge between RxJS and the new output API:

```typescript
import { outputFromObservable, outputToObservable } from '@angular/core/rxjs-interop';

// Convert Observable to output
search$ = new Subject<string>();
search = outputFromObservable(this.search$);

// Convert output to Observable
searchObservable$ = outputToObservable(this.search);
```

## Migration 3: @ViewChild/@ContentChild to Signal Queries

### Before

```typescript
@Component({...})
export class TabPanel {
  @ViewChild('container') container!: ElementRef;
  @ViewChildren(TabComponent) tabs!: QueryList<TabComponent>;
  @ContentChild(HeaderComponent) header?: HeaderComponent;
  @ContentChildren(ItemComponent) items!: QueryList<ItemComponent>;
}
```

### After

```typescript
@Component({...})
export class TabPanel {
  container = viewChild.required<ElementRef>('container');
  tabs = viewChildren(TabComponent);
  header = contentChild(HeaderComponent);
  items = contentChildren(ItemComponent);
}
```

### Key Differences

| Aspect | Decorator Query | Signal Query |
|--------|----------------|-------------|
| Type | `ElementRef` / `QueryList<T>` | `Signal<ElementRef>` / `Signal<readonly T[]>` |
| Reading | `this.container` | `this.container()` |
| Required | `!` assertion | `.required()` variant |
| Lifecycle | Available after `ngAfterViewInit` | Available as signal immediately |
| Change detection | Manual (QueryList.changes) | Reactive (signal updates) |

### Automated Migration

```bash
ng generate @angular/core:signal-queries-migration
```

## Migration 4: Constructor DI to inject()

### Before

```typescript
@Component({...})
export class UserService {
  constructor(
    private http: HttpClient,
    @Inject(API_URL) private apiUrl: string,
    @Optional() private logger?: LoggerService
  ) {}
}
```

### After

```typescript
@Component({...})
export class UserService {
  private http = inject(HttpClient);
  private apiUrl = inject(API_URL);
  private logger = inject(LoggerService, { optional: true });
}
```

### Automated Migration

```bash
ng generate @angular/core:inject
```

## Migration 5: BehaviorSubject to Signal (Manual)

No schematic exists — this is a manual architectural migration.

### Before (RxJS State)

```typescript
@Injectable({ providedIn: 'root' })
export class CartService {
  private items$ = new BehaviorSubject<CartItem[]>([]);
  readonly items = this.items$.asObservable();
  readonly total$ = this.items$.pipe(
    map(items => items.reduce((sum, i) => sum + i.price, 0))
  );

  addItem(item: CartItem) {
    this.items$.next([...this.items$.value, item]);
  }
}
```

### After (Signal State)

```typescript
@Injectable({ providedIn: 'root' })
export class CartService {
  private _items = signal<CartItem[]>([]);
  readonly items = this._items.asReadonly();
  readonly total = computed(() =>
    this._items().reduce((sum, i) => sum + i.price, 0)
  );

  addItem(item: CartItem) {
    this._items.update(list => [...list, item]);
  }
}
```

### When to Migrate to Signals vs Keep RxJS

| Use Case | Use Signals | Use RxJS |
|----------|------------|---------|
| Component-local UI state | Yes | No |
| Derived/computed values | Yes (`computed()`) | No |
| Simple service state | Yes | No |
| HTTP requests | No | Yes (`HttpClient`) |
| WebSocket streams | No | Yes |
| Complex async orchestration | No | Yes (operators) |
| Debounce/throttle/retry | No | Yes (operators) |
| Router events | No | Yes (then `toSignal()`) |
| Form value streams | Depends | Reactive Forms: Yes |
| Global state (NgRx) | Hybrid | Yes (NgRx still RxJS) |

### RxJS-to-Signal Bridge

```typescript
import { toSignal, toObservable } from '@angular/core/rxjs-interop';

// Observable → Signal
readonly routeId = toSignal(
  this.route.params.pipe(map(p => p['id'])),
  { initialValue: '' }
);

// Signal → Observable
readonly items$ = toObservable(this.items);
```

## Migration 6: Async Data Loading with resource()

### Before (Manual Loading Pattern)

```typescript
@Component({...})
export class FruitDetail {
  fruit?: Fruit;
  loading = false;
  error?: Error;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.loading = true;
    this.http.get<Fruit>('/api/fruit/1').subscribe({
      next: (f) => { this.fruit = f; this.loading = false; },
      error: (e) => { this.error = e; this.loading = false; }
    });
  }
}
```

### After (resource API — v20+)

```typescript
@Component({...})
export class FruitDetail {
  fruitId = input.required<string>();

  fruitDetail = resource({
    request: this.fruitId,
    loader: async ({ request: id }) => {
      const response = await fetch(`/api/fruit/${id}`);
      return response.json() as Promise<Fruit>;
    }
  });

  // Access: fruitDetail.value(), fruitDetail.isLoading(), fruitDetail.error()
}
```

### rxResource (RxJS Variant)

```typescript
fruitDetail = rxResource({
  request: this.fruitId,
  loader: ({ request: id }) =>
    this.http.get<Fruit>(`/api/fruit/${id}`)
});
```

## Incremental Adoption Strategy

Adopt signals incrementally — do not rewrite everything at once.

### Phase 1: New Code Only
Write all new components with signal inputs/outputs/queries.
Existing code stays as-is.

### Phase 2: Run Automated Schematics
```bash
ng generate @angular/core:signal-input-migration
ng generate @angular/core:output-migration
ng generate @angular/core:signal-queries-migration
ng generate @angular/core:inject
```

### Phase 3: Convert Services
Migrate `BehaviorSubject` patterns in services to signals.
Start with leaf services (no downstream consumers).

### Phase 4: Adopt resource() for Data Loading
Replace manual loading patterns with `resource()` or `rxResource()`.

### Phase 5: Remove Unnecessary RxJS
After signals are widespread, audit for RxJS usage that can be
simplified. Keep RxJS for genuine async orchestration.
