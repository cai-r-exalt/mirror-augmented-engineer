# Python Coding Guidelines for Bel'Air's Buvette

This document outlines Python coding standards for the Bel'Air's Buvette backend, following the Hexagonal Architecture (Ports and Adapters) pattern. All code must adhere to these guidelines to maintain consistency, readability, and adherence to the architecture principles.

---

## Section 1: Overview & Tech Stack

### Python Version and Tools

- **Python Version**: 3.13+ (as specified in pyproject.toml)
- **Code Formatter**: Ruff (automatic formatting enforced via `ruff format`)
- **Linter**: Ruff (static analysis with rules E, F, I)
- **Type Checking**: Built-in type hints required for all functions and methods
- **Package Management**: `uv` for dependency management
- **Testing Framework**: pytest with pytest-asyncio for async tests

### Ruff Configuration

The project enforces strict code quality standards via Ruff. Key configuration in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I"]
```

**Key Rules:**
- **Line Length**: 120 characters (soft limit for readability, hard limit enforced by formatter)
- **E**: pycodestyle (PEP 8 violations) — catches indentation, whitespace, naming issues
- **F**: Pyflakes (logical errors) — catches undefined names, unused imports, duplicate definitions
- **I**: isort (import organization) — enforces consistent import ordering

### Import Organization

Imports must be organized in three groups, separated by blank lines:

1. **Standard Library** (e.g., `dataclasses`, `asyncio`, `json`)
2. **Third-Party** (e.g., `pydantic`, `sqlalchemy`, `fastapi`)
3. **Local** (e.g., `from app.domain.entities import User`, `from app.infrastructure.persistence import UserRepository`)

Ruff will automatically organize imports alphabetically within each group. Use `ruff check --fix` to auto-correct import order.

### Python Idioms

- **No wildcards**: Never use `from module import *` — be explicit about imports
- **No `eval()` or `exec()`**: These are security risks and violate Hexagonal Architecture
- **Type hints everywhere**: All function signatures, method signatures, and class attributes must have type hints
- **f-strings only**: Use f-strings for formatting; no `.format()` or `%` formatting

---

## Section 2: Naming Conventions & Code Organization

### Class Naming

- **PascalCase** for all classes (e.g., `User`, `CreateOrderUseCase`, `SQLAlchemyUserRepository`)
- **No underscores** within class names unless it's a private/internal class (e.g., `_InternalHelper`)
- **Descriptive names**: Class names should reflect their purpose or domain concept

### Function and Method Naming

- **snake_case** for all functions and methods (e.g., `create_user()`, `validate_email()`, `fetch_order_by_id()`)
- **Verb-first**: Prefer action verbs for methods (e.g., `get_user()`, `set_price()`, `validate_input()`, `execute()`)
- **Query methods**: Use `is_*` or `has_*` for boolean-returning methods (e.g., `is_active()`, `has_items()`)

### Constants

- **UPPER_SNAKE_CASE** for module-level constants (e.g., `MAX_ORDER_SIZE = 100`, `DEFAULT_CURRENCY = "USD"`)
- **Constants in classes**: Use `UPPER_SNAKE_CASE` with class scope if needed (e.g., `class Order: MAX_ITEMS = 50`)

### Port Naming (Abstract Interfaces)

**Critical**: Unlike Java/C#, Python ports do NOT use "I" prefix.

- **Abstract ports**: Use the concept name directly (e.g., `UserRepository`, `PaymentGateway`, `EmailService`)
  - Store in `app/domain/ports/`
  - Define as abstract base classes with `@abstractmethod` decorators
  - Example:
    ```python
    from abc import ABC, abstractmethod
    from app.domain.entities import User
    
    class UserRepository(ABC):  # No "I" prefix!
        @abstractmethod
        async def get_by_id(self, user_id: str) -> User | None:
            pass
        
        @abstractmethod
        async def save(self, user: User) -> None:
            pass
    ```

- **Concrete implementations**: Prefix with the technology/adapter name (e.g., `SQLAlchemyUserRepository`, `StripePaymentGateway`, `SmtpEmailService`)
  - Store in `app/infrastructure/` (persistence, external, etc.)
  - Example:
    ```python
    from app.domain.ports import UserRepository
    from app.infrastructure.persistence.models import UserORM
    
    class SQLAlchemyUserRepository(UserRepository):
        def __init__(self, session: AsyncSession):
            self._session = session
        
        async def get_by_id(self, user_id: str) -> User | None:
            # Implementation
            pass
    ```

### Use Cases

- **Class naming**: Suffix with `UseCase` (e.g., `CreateUserUseCase`, `ProcessPaymentUseCase`)
- **Method naming**: Use `execute()` as the primary entry point
  - Accept a request DTO (e.g., `CreateUserRequest`)
  - Return a response DTO (e.g., `CreateUserResponse`)
  - Inject dependencies via constructor
  - Example:
    ```python
    from dataclasses import dataclass
    
    @dataclass
    class CreateUserRequest:
        email: str
        name: str
    
    @dataclass
    class CreateUserResponse:
        user_id: str
        email: str
    
    class CreateUserUseCase:
        def __init__(self, user_repository: UserRepository):
            self._repository = user_repository
        
        async def execute(self, request: CreateUserRequest) -> CreateUserResponse:
            # Implementation
            pass
    ```

### Module Organization

**Keep related code together**:
- One entity per file (e.g., `user.py` contains just the `User` entity)
- One use case per file (e.g., `create_user_use_case.py` contains just `CreateUserUseCase`)
- Group related ports in a single file if they're tightly coupled (e.g., `repositories.py` for `UserRepository`, `OrderRepository`)
- Separate implementations by technology (e.g., `persistence/sqlalchemy/user_repository.py` vs `persistence/mongodb/user_repository.py`)

### Dataclasses vs Pydantic

**Dataclasses** (Domain Layer):
- Used for **domain entities, value objects, and aggregate roots**
- No validation (validation lives in domain logic, not annotations)
- Lightweight, fast, no external dependencies
- Example:
  ```python
  from dataclasses import dataclass
  
  @dataclass
  class User:
      id: str
      email: str
      name: str
      is_active: bool
  ```

**Pydantic** (Application Layer):
- Used for **request/response DTOs** (schemas in FastAPI routers)
- Automatic validation and serialization
- Generates OpenAPI documentation automatically
- Example:
  ```python
  from pydantic import BaseModel, EmailStr
  
  class CreateUserRequest(BaseModel):
      email: EmailStr
      name: str
  
  class UserResponse(BaseModel):
      id: str
      email: str
      name: str
  ```

**Key Distinction**: Domain entities are **never Pydantic models**. Domain entities do not validate input — they enforce business rules through methods and maintain invariants. Pydantic is for API contracts only.

---

## Section 3: Classes & Type Hints

### Type Hints

All function and method signatures must include type hints. Use union types with `|` (Python 3.10+) instead of `Union[A, B]`.

```python
# Good
def get_user_by_id(user_id: str) -> User | None:
    pass

# Bad (no return type)
def get_user_by_id(user_id: str):
    pass

# Bad (using Union instead of |)
from typing import Union
def get_user_by_id(user_id: str) -> Union[User, None]:
    pass
```

### Generic Types

Use generic type parameters for collections and container classes:

```python
from typing import Generic, TypeVar

T = TypeVar('T')

# Good: Generic repository
class Repository(Generic[T]):
    async def get_by_id(self, id: str) -> T | None:
        pass

# Usage
class UserRepository(Repository[User]):
    async def get_by_id(self, id: str) -> User | None:
        pass

# Good: Lists and dicts with type parameters
def process_users(users: list[User]) -> dict[str, User]:
    return {user.id: user for user in users}
```

### Dataclasses

Use `@dataclass` for domain entities, value objects, and aggregate roots. Include `frozen=True` for immutability.

```python
from dataclasses import dataclass, field

# Mutable entity (allowed for aggregates with controlled mutations)
@dataclass
class Order:
    id: str
    customer_id: str
    items: list[OrderItem] = field(default_factory=list)
    total_price: float = 0.0

# Immutable value object (frozen)
@dataclass(frozen=True)
class Money:
    amount: float
    currency: str
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

# Immutable entity (frozen)
@dataclass(frozen=True)
class User:
    id: str
    email: str
    name: str
    is_active: bool = True
```

**Frozen Dataclasses**: Use `@dataclass(frozen=True)` for Value Objects and immutable entities. Operations on frozen objects return new instances:

```python
@dataclass(frozen=True)
class Point:
    x: float
    y: float
    
    def move(self, dx: float, dy: float) -> 'Point':
        return Point(self.x + dx, self.y + dy)

# Usage
p1 = Point(1.0, 2.0)
p2 = p1.move(3.0, 4.0)  # Returns new Point; p1 unchanged
```

### Pydantic Models (Application Layer)

Pydantic models for request/response validation:

```python
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)  # For ORM mapping
```

### Repository Pattern Example: SQLAlchemyUserRepository

Here's a concrete implementation showing how repositories bridge domain entities and ORM models:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domain.entities import User
from app.domain.ports import UserRepository
from app.infrastructure.persistence.models import UserORM


class SQLAlchemyUserRepository(UserRepository):
    """Maps between domain User entities and SQLAlchemy ORM UserORM models."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, user_id: str) -> User | None:
        """Fetch user by ID; return domain User entity."""
        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self._session.execute(stmt)
        orm_user = result.scalar_one_or_none()
        
        if orm_user is None:
            return None
        
        return self._orm_to_entity(orm_user)
    
    async def save(self, user: User) -> None:
        """Persist domain User entity as ORM model."""
        orm_user = self._entity_to_orm(user)
        self._session.add(orm_user)
        await self._session.flush()
    
    def _orm_to_entity(self, orm_user: UserORM) -> User:
        """Convert ORM model to domain entity."""
        return User(
            id=orm_user.id,
            email=orm_user.email,
            name=orm_user.name,
            is_active=orm_user.is_active,
        )
    
    def _entity_to_orm(self, user: User) -> UserORM:
        """Convert domain entity to ORM model."""
        return UserORM(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active,
        )
```

**Key Points**:
- Repository accepts async session in constructor (dependency injection)
- Methods return/accept domain entities (`User`), never ORM models
- Mapping methods (`_orm_to_entity`, `_entity_to_orm`) keep conversion logic isolated
- All I/O is async (`async def`, `await`)

---

## Section 4: Functions & Methods

### Function Signatures

All functions must have type hints for parameters and return values:

```python
# Good
async def create_user(email: str, name: str, repository: UserRepository) -> User:
    pass

# Bad (no return type)
async def create_user(email: str, name: str, repository: UserRepository):
    pass

# Bad (no parameter types)
def validate_email(email):
    pass
```

### Docstrings

Use Google-style docstrings for all public functions and methods:

```python
def calculate_order_total(items: list[OrderItem], discount_percent: float = 0.0) -> float:
    """Calculate the total price of an order, applying optional discount.
    
    Args:
        items: List of OrderItem objects to sum.
        discount_percent: Discount to apply as percentage (0-100). Default is 0.
    
    Returns:
        Total price after discount as float.
    
    Raises:
        ValueError: If discount_percent is outside 0-100 range.
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")
    
    subtotal = sum(item.price * item.quantity for item in items)
    return subtotal * (1 - discount_percent / 100)
```

### Method Length and Complexity

- **Target**: 10–20 lines per method (comfortable reading without scrolling)
- **Hard Limit**: 30 lines (if longer, extract helper methods)
- **Guideline**: One method = one responsibility

```python
# Good: Each method is short and focused
class OrderService:
    async def create_order(self, request: CreateOrderRequest) -> Order:
        items = await self._validate_items(request.item_ids)
        customer = await self._verify_customer(request.customer_id)
        order = Order(customer_id=customer.id, items=items)
        await self._repository.save(order)
        return order
    
    async def _validate_items(self, item_ids: list[str]) -> list[OrderItem]:
        # 5 lines max
        pass
    
    async def _verify_customer(self, customer_id: str) -> Customer:
        # 5 lines max
        pass

# Bad: Method is 50 lines doing too much
class OrderService:
    async def create_order(self, request: CreateOrderRequest) -> Order:
        # Validates items
        # Verifies customer
        # Calculates pricing
        # Checks inventory
        # Applies discounts
        # ... 50 lines of mixed logic
        pass
```

### Composition Over Nesting

Avoid deeply nested if/else chains. Use early returns and guard clauses:

```python
# Bad: Deeply nested
def process_payment(amount: float, user: User) -> bool:
    if user is not None:
        if user.is_active:
            if amount > 0:
                if user.balance >= amount:
                    user.balance -= amount
                    return True
    return False

# Good: Guard clauses with early returns
def process_payment(amount: float, user: User) -> bool:
    if user is None or not user.is_active:
        return False
    
    if amount <= 0:
        return False
    
    if user.balance < amount:
        return False
    
    user.balance -= amount
    return True
```

### Error Handling & Exceptions

**Domain Layer**: Raise domain-specific exceptions. Never raise framework exceptions.

```python
# Domain exceptions (defined in app/domain/exceptions.py or entity module)
class InvalidUserError(Exception):
    """Raised when user data is invalid."""
    pass

class InsufficientBalanceError(Exception):
    """Raised when user balance is too low."""
    pass

class User:
    def __post_init__(self):
        if not self.email:
            raise InvalidUserError("Email cannot be empty")
    
    def transfer_balance(self, amount: float) -> None:
        if self.balance < amount:
            raise InsufficientBalanceError(
                f"Balance {self.balance} < required {amount}"
            )
        self.balance -= amount
```

**Infrastructure Layer**: Catch infrastructure exceptions and convert to domain exceptions.

```python
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

class SQLAlchemyUserRepository(UserRepository):
    async def save(self, user: User) -> None:
        try:
            orm_user = self._entity_to_orm(user)
            self._session.add(orm_user)
            await self._session.flush()
        except IntegrityError as e:
            raise InvalidUserError(f"User already exists: {user.email}") from e
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}") from e
```

**Application Layer**: Catch domain exceptions and map to HTTP responses.

```python
from fastapi import HTTPException, status

@app.post("/users")
async def create_user(req: CreateUserRequest, use_case: CreateUserUseCase):
    try:
        response = await use_case.execute(CreateUserRequest(email=req.email, name=req.name))
        return response
    except InvalidUserError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
```

### Async/Await Guidelines

**When to use async**:
- All I/O operations: database queries, HTTP requests, file operations
- All methods in repositories must be async
- All use cases should be async (unless CPU-only)
- All FastAPI route handlers must be async

**Mark the entire call chain as async**:
```python
# Good: async propagates upward
class CreateUserUseCase:
    async def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        user = await self._repository.get_by_email(request.email)
        if user:
            raise UserAlreadyExistsError()
        new_user = User(email=request.email, name=request.name)
        await self._repository.save(new_user)
        return CreateUserResponse(user_id=new_user.id, email=new_user.email)

@app.post("/users")
async def create_user(req: CreateUserRequest, use_case: CreateUserUseCase):
    return await use_case.execute(CreateUserRequest(email=req.email, name=req.name))

# Bad: Blocking I/O in non-async function
class CreateUserUseCase:
    def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        user = self._repository.get_by_email(request.email)  # Blocks!
        # ...
```

**Parallelism with asyncio.gather()**:

```python
import asyncio

class FetchUserDetailsUseCase:
    async def execute(self, user_id: str) -> UserDetailsResponse:
        # Fetch user, orders, and payments in parallel
        user, orders, payments = await asyncio.gather(
            self._user_repo.get_by_id(user_id),
            self._order_repo.get_by_user_id(user_id),
            self._payment_repo.get_by_user_id(user_id),
        )
        
        if not user:
            raise UserNotFoundError()
        
        return UserDetailsResponse(
            user=user,
            orders=orders,
            payments=payments,
        )
```

**Never block with `time.sleep()` or `requests.get()`**: Use `await asyncio.sleep()` and async HTTP clients (aiohttp, httpx).

```python
# Bad
import time
async def process_with_delay():
    time.sleep(1)  # Blocks entire event loop!

# Good
import asyncio
async def process_with_delay():
    await asyncio.sleep(1)  # Non-blocking
```

---

## Section 5: Domain Layer Specifics

### Entities

Domain entities represent core business concepts with identity and lifecycle:

```python
from dataclasses import dataclass, field

@dataclass
class User:
    id: str
    email: str
    name: str
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
```

**Key Characteristics**:
- Have a unique identifier (`id`)
- Are mutable (can change state over their lifecycle)
- Have lifecycle (created, modified, deleted)
- Enforce business rules through methods

### Value Objects

Value objects represent immutable concepts without identity. Two value objects are equal if their attributes match.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

@dataclass(frozen=True)
class EmailAddress:
    value: str
    
    def __post_init__(self):
        if "@" not in self.value:
            raise ValueError("Invalid email format")
```

**Key Characteristics**:
- Immutable (`frozen=True`)
- No identity (equality based on attributes)
- Enforce business rules in `__post_init__()`
- Return new instances on operations (not mutations)

### Aggregate Roots

Aggregates are consistency boundaries. An aggregate root controls access to all contained entities and value objects. Only the root can be persisted directly.

```python
from dataclasses import dataclass, field

@dataclass
class Order:
    """Aggregate root for order domain."""
    id: str
    customer_id: str
    items: list[OrderItem] = field(default_factory=list)
    total_price: Money | None = None
    status: str = "pending"
    
    def __post_init__(self):
        if not self.items:
            raise ValueError("Order must have at least one item")
    
    def add_item(self, item: OrderItem) -> None:
        """Add item to order; enforce invariants."""
        if self.status != "pending":
            raise ValueError("Cannot add items to non-pending order")
        
        # Check for duplicate SKUs
        if any(i.sku == item.sku for i in self.items):
            raise ValueError(f"Item {item.sku} already in order")
        
        self.items.append(item)
        self._recalculate_total()
    
    def remove_item(self, sku: str) -> None:
        """Remove item by SKU; maintain invariants."""
        self.items = [i for i in self.items if i.sku != sku]
        if not self.items:
            raise ValueError("Order must have at least one item")
        self._recalculate_total()
    
    def finalize(self) -> None:
        """Transition order to 'finalized' status."""
        if self.status != "pending":
            raise ValueError("Only pending orders can be finalized")
        self.status = "finalized"
    
    def _recalculate_total(self) -> None:
        """Internal method; recalculate order total."""
        total = sum(item.price.amount * item.quantity for item in self.items)
        self.total_price = Money(total, "USD")

@dataclass(frozen=True)
class OrderItem:
    """Value object; cannot be modified directly; access only through Order."""
    sku: str
    quantity: int
    price: Money
```

**Key Principles**:
- **Single Aggregate Root**: Only `Order` can be modified; `OrderItem` is immutable and accessed via `Order`
- **Enforce Invariants**: `add_item()` and `remove_item()` control mutations; `finalize()` transitions state
- **Repository Persists Whole Aggregate**: Repository saves entire `Order` and contained items, not individual items
- **Internal Entities**: Access internal entities (`OrderItem`) only through root methods, never directly

### Business Rules Enforcement

Domain entities must be self-defending. Validate in constructors (`__post_init__`) and mutation methods. Never allow invalid state.

```python
# Bad: Anemic model (no validation)
@dataclass
class User:
    id: str
    email: str
    balance: float

user = User(id="1", email="invalid", balance=-100)  # Invalid state created!

# Good: Rich model (enforces rules)
@dataclass
class User:
    id: str
    email: str
    balance: float
    
    def __post_init__(self):
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email")
        if self.balance < 0:
            raise ValueError("Balance cannot be negative")
    
    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if self.balance < amount:
            raise InsufficientBalanceError(f"Balance {self.balance} < {amount}")
        self.balance -= amount

# Now you must go through methods to ensure validity
user = User(id="1", email="test@example.com", balance=100)  # Valid
user.withdraw(50)  # Valid
user.withdraw(1000)  # Raises InsufficientBalanceError
```

### Use Cases

Use cases orchestrate domain logic and coordinate between ports. They are application-level services that execute business scenarios.

```python
from dataclasses import dataclass

@dataclass
class CreateUserRequest:
    email: str
    name: str

@dataclass
class CreateUserResponse:
    user_id: str
    email: str
    name: str

class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository, email_service: EmailService):
        self._repository = user_repository
        self._email_service = email_service
    
    async def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        # Check if user exists
        existing = await self._repository.get_by_email(request.email)
        if existing:
            raise UserAlreadyExistsError(f"User {request.email} already exists")
        
        # Create domain entity (enforces business rules)
        user = User(
            id=str(uuid4()),
            email=request.email,
            name=request.name,
        )
        
        # Persist
        await self._repository.save(user)
        
        # Send welcome email
        await self._email_service.send_welcome_email(user.email, user.name)
        
        # Return response
        return CreateUserResponse(user_id=user.id, email=user.email, name=user.name)
```

### Ports (Abstract Interfaces)

Ports define contracts for secondary dependencies. They live in the domain layer and are implemented in the infrastructure layer.

```python
from abc import ABC, abstractmethod
from app.domain.entities import User

class UserRepository(ABC):
    """Port: User persistence."""
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        pass
    
    @abstractmethod
    async def save(self, user: User) -> None:
        pass

class EmailService(ABC):
    """Port: Email delivery."""
    
    @abstractmethod
    async def send_welcome_email(self, email: str, name: str) -> None:
        pass
```

### Domain Exceptions

Define specific exceptions for business rule violations. Never let infrastructure or framework exceptions leak into domain logic.

```python
class DomainException(Exception):
    """Base class for all domain exceptions."""
    pass

class InvalidUserError(DomainException):
    """Raised when user data violates business rules."""
    pass

class UserAlreadyExistsError(DomainException):
    """Raised when attempting to create duplicate user."""
    pass

class InsufficientBalanceError(DomainException):
    """Raised when user balance is insufficient for operation."""
    pass

class OrderValidationError(DomainException):
    """Raised when order violates invariants."""
    pass
```

---

## Section 6: Application Layer Specifics

*To be completed*

## Section 7: Infrastructure Layer Specifics

*To be completed*

## Section 8: Testing Patterns

*To be completed*

## Section 9: Error Handling & Exceptions

*To be completed*

## Section 10: Comments & Documentation

*To be completed*

## Section 11: Common Anti-Patterns to Avoid

*To be completed*
