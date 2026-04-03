# Pydantic Models

Sources: Pydantic v2 official documentation (docs.pydantic.dev), FastAPI official documentation (fastapi.tiangolo.com), Samuel Colvin (Pydantic creator) blog posts, production FastAPI schema patterns

Covers: Pydantic v2 model design, field validation, custom validators, serialization aliases, discriminated unions, model_config, request/response schema separation, and common patterns for FastAPI integration.

## Model Basics

Pydantic v2 models are the foundation of FastAPI request/response handling. Define models using Python type hints:

```python
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(ge=0, le=150)

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

### Field Constraints

| Constraint | Types | Example |
|-----------|-------|---------|
| `min_length`, `max_length` | `str` | `Field(min_length=1, max_length=255)` |
| `ge`, `le`, `gt`, `lt` | `int`, `float` | `Field(ge=0, le=100)` |
| `pattern` | `str` | `Field(pattern=r"^[a-z0-9-]+$")` |
| `multiple_of` | `int`, `float` | `Field(multiple_of=5)` |
| `max_digits`, `decimal_places` | `Decimal` | `Field(max_digits=10, decimal_places=2)` |
| `default` | Any | `Field(default="pending")` |
| `default_factory` | Mutable types | `Field(default_factory=list)` |
| `alias` | Any | `Field(alias="userName")` |
| `exclude` | Any | `Field(exclude=True)` |

## Request/Response Schema Separation

Never use the same model for input and output. Separate schemas prevent leaking internal fields:

```python
# Base with shared fields
class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr

# Input: includes password, excludes id
class UserCreate(UserBase):
    password: str = Field(min_length=8)

# Update: all fields optional
class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None

# Output: includes id, excludes password
class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}

# List response with pagination
class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    per_page: int
```

### Schema Naming Conventions

| Pattern | Use For |
|---------|---------|
| `{Entity}Create` | POST request body |
| `{Entity}Update` | PUT/PATCH request body |
| `{Entity}Response` | Single item response |
| `{Entity}ListResponse` | Paginated list response |
| `{Entity}Filter` | Query parameter groups |
| `{Entity}InDB` | Internal representation (never expose) |

## model_config Options

```python
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,       # Read from ORM objects (user.name, not user["name"])
        populate_by_name=True,      # Accept both alias and field name
        str_strip_whitespace=True,  # Strip whitespace from string fields
        str_min_length=1,           # No empty strings by default
        json_schema_extra={         # Custom OpenAPI examples
            "examples": [{"name": "Alice", "email": "alice@example.com"}]
        },
    )
```

| Option | Purpose | Default |
|--------|---------|---------|
| `from_attributes` | Read ORM model attributes | `False` |
| `populate_by_name` | Accept field name alongside alias | `False` |
| `str_strip_whitespace` | Auto-strip strings | `False` |
| `strict` | Disallow type coercion (str to int) | `False` |
| `extra` | Handle extra fields: `"forbid"`, `"allow"`, `"ignore"` | `"ignore"` |
| `frozen` | Make instances immutable | `False` |
| `use_enum_values` | Store enum values, not enum members | `False` |
| `validate_default` | Validate default values | `False` |

## Custom Validators

### Field Validators

```python
from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    username: str
    password: str
    password_confirm: str

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain an uppercase letter")
        return v
```

### Model Validators

Validate across multiple fields:

```python
from pydantic import model_validator

class DateRange(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_dates(self) -> "DateRange":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

class UserCreate(BaseModel):
    password: str
    password_confirm: str

    @model_validator(mode="after")
    def passwords_match(self) -> "UserCreate":
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self
```

### Before vs After Validators

| Mode | When | Use For |
|------|------|---------|
| `mode="before"` | Before Pydantic validation | Normalizing raw input (strip, lowercase) |
| `mode="after"` | After all fields validated | Cross-field validation |
| `mode="wrap"` | Around validation | Custom coercion with fallback |

## Serialization

### Computed Fields

Add fields that are derived from other fields:

```python
from pydantic import computed_field

class UserResponse(BaseModel):
    first_name: str
    last_name: str

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

### Serialization Aliases

Use different field names in JSON output:

```python
class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(serialization_alias="userId")
    full_name: str = Field(serialization_alias="fullName")
    created_at: datetime = Field(serialization_alias="createdAt")
```

### Custom Serializers

```python
from pydantic import field_serializer

class OrderResponse(BaseModel):
    total: Decimal
    created_at: datetime

    @field_serializer("total")
    def serialize_total(self, value: Decimal) -> str:
        return f"${value:.2f}"

    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()
```

## Discriminated Unions

Handle polymorphic request/response types:

```python
from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union

class CreditCardPayment(BaseModel):
    type: Literal["credit_card"]
    card_number: str
    expiry: str

class BankTransferPayment(BaseModel):
    type: Literal["bank_transfer"]
    account_number: str
    routing_number: str

class CryptoPayment(BaseModel):
    type: Literal["crypto"]
    wallet_address: str

Payment = Annotated[
    Union[CreditCardPayment, BankTransferPayment, CryptoPayment],
    Field(discriminator="type"),
]

class OrderCreate(BaseModel):
    amount: Decimal
    payment: Payment  # FastAPI validates based on "type" field
```

The `discriminator` field tells Pydantic which union member to validate against, producing clear error messages when the type is invalid.

## FastAPI Integration Patterns

### Response Model Filtering

```python
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: AsyncSessionDep):
    user = await session.get(User, user_id)
    return user  # SQLAlchemy model auto-converted via from_attributes
```

### Multiple Response Models

```python
from fastapi import status

@router.post(
    "/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Email already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_user(data: UserCreate):
    ...
```

### Query Parameter Models (Pydantic v2 + FastAPI)

```python
class ItemFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str | None = None
    min_price: float | None = Field(None, ge=0)
    max_price: float | None = Field(None, ge=0)
    in_stock: bool = True

@router.get("/items/")
async def list_items(filters: Annotated[ItemFilter, Query()]):
    ...
```

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Same model for create and response | Leaks passwords or internal IDs | Separate Create/Response models |
| Missing `from_attributes=True` | ORM objects fail to serialize | Add to response models |
| Mutable default values | Shared state between requests | Use `Field(default_factory=list)` |
| Forgetting `@classmethod` on validators | Silent failure | Always use `@classmethod` with `@field_validator` |
| Over-nesting models | Complex schemas confuse API consumers | Flatten where possible |
| Not using `Annotated` for reusable fields | Repeated field definitions | Define annotated types |
