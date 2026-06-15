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

The application layer is the outermost ring of the Hexagonal Architecture. It handles HTTP requests, orchestrates use cases, and maps domain exceptions to HTTP responses. It is the **primary adapter** for incoming requests.

### FastAPI Router Organization

Organize routes by domain concept (e.g., user routes, order routes). Each domain concept gets its own router file:

```python
# File: app/application/routers/users.py
from fastapi import APIRouter, HTTPException, status, Depends
from app.application.schemas import CreateUserRequest, UserResponse
from app.application.dependencies import get_create_user_use_case
from app.domain.exceptions import InvalidUserError, UserAlreadyExistsError

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
) -> UserResponse:
    """Create a new user."""
    try:
        response = await use_case.execute(request)
        return response
    except InvalidUserError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
) -> UserResponse:
    """Fetch user by ID."""
    try:
        response = await use_case.execute(GetUserRequest(user_id=user_id))
        return response
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

**Key Principles**:
- One router file per domain concept
- Organize routers in `app/application/routers/`
- Include prefix and tags for OpenAPI documentation
- All route handlers are `async`
- Use dependency injection for use cases and services

### Dependency Injection

Create a centralized dependency injection module to provide use cases and infrastructure components:

```python
# File: app/application/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.persistence.database import get_db_session
from app.domain.ports import UserRepository
from app.infrastructure.persistence.repositories import SQLAlchemyUserRepository
from app.application.use_cases import CreateUserUseCase, GetUserUseCase

async def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """Provide UserRepository instance."""
    return SQLAlchemyUserRepository(session)

async def get_create_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
) -> CreateUserUseCase:
    """Provide CreateUserUseCase with injected dependencies."""
    return CreateUserUseCase(user_repository=user_repo)

async def get_get_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
) -> GetUserUseCase:
    """Provide GetUserUseCase with injected dependencies."""
    return GetUserUseCase(user_repository=user_repo)
```

**Key Principles**:
- Centralize all dependency creation
- Use FastAPI `Depends()` for dependency resolution
- Chain dependencies (use cases depend on repositories)
- Repositories depend on database sessions
- One dependency function per use case or service

### Request/Response DTOs (Pydantic Models)

Request and response schemas are Pydantic models. They validate incoming data and serialize outgoing data automatically.

```python
# File: app/application/schemas.py
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    """Request schema for creating a user."""
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=100, description="User full name")

class UserResponse(BaseModel):
    """Response schema for user data."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    is_active: bool = Field(..., description="Whether user is active")

    model_config = ConfigDict(
        from_attributes=True,  # Allow construction from ORM models
        json_schema_extra={
            "example": {
                "id": "user-123",
                "email": "user@example.com",
                "name": "John Doe",
                "is_active": True,
            }
        }
    )
```

**Key Principles**:
- Pydantic validates incoming JSON automatically
- Use `EmailStr` for email fields (requires pydantic[email])
- Include `Field()` with descriptions for OpenAPI documentation
- Set `from_attributes=True` for ORM model compatibility
- Include `json_schema_extra` with examples
- Never expose domain entities directly; map to response DTOs

### Error Handling & HTTP Mapping

Map domain exceptions to appropriate HTTP status codes. Create an exception handler or catch at route level:

```python
# File: app/application/exception_handlers.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.domain.exceptions import (
    DomainException,
    InvalidUserError,
    UserAlreadyExistsError,
    UserNotFoundError,
    InsufficientBalanceError,
)

def setup_exception_handlers(app: FastAPI) -> None:
    """Configure exception handlers for the FastAPI app."""

    @app.exception_handler(InvalidUserError)
    async def handle_invalid_user_error(request: Request, exc: InvalidUserError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "error_code": "INVALID_USER"},
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def handle_user_already_exists(request: Request, exc: UserAlreadyExistsError):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "error_code": "USER_EXISTS"},
        )

    @app.exception_handler(UserNotFoundError)
    async def handle_user_not_found(request: Request, exc: UserNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "error_code": "USER_NOT_FOUND"},
        )

    @app.exception_handler(InsufficientBalanceError)
    async def handle_insufficient_balance(request: Request, exc: InsufficientBalanceError):
        return JSONResponse(
            status_code=402,
            content={"detail": str(exc), "error_code": "INSUFFICIENT_BALANCE"},
        )

    @app.exception_handler(DomainException)
    async def handle_domain_exception(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "error_code": "DOMAIN_ERROR"},
        )
```

**HTTP Status Codes Mapping**:
- **400 Bad Request**: `InvalidUserError`, `OrderValidationError` — validation failed
- **402 Payment Required**: `InsufficientBalanceError` — insufficient funds
- **404 Not Found**: `UserNotFoundError`, `OrderNotFoundError` — resource doesn't exist
- **409 Conflict**: `UserAlreadyExistsError` — duplicate/constraint violation
- **500 Internal Server Error**: Unexpected exceptions (framework errors, unexpected infrastructure issues)

### Main Application Setup

Create a factory function to initialize FastAPI with all routers and exception handlers:

```python
# File: app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.application.routers import users, orders
from app.application.exception_handlers import setup_exception_handlers
from app.infrastructure.persistence.database import init_db

def create_app() -> FastAPI:
    """Factory function to create and configure FastAPI application."""
    app = FastAPI(
        title="Bel'Air's Buvette API",
        description="Backend API for Bel'Air's Buvette",
        version="1.0.0",
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Startup/shutdown events
    @app.on_event("startup")
    async def startup():
        await init_db()

    # Exception handlers
    setup_exception_handlers(app)

    # Routers
    app.include_router(users.router)
    app.include_router(orders.router)

    return app

app = create_app()

# For development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Key Principles**:
- Use factory pattern for app creation (easier to test)
- Configure CORS, middleware early
- Register startup/shutdown events
- Include exception handlers before routers
- Include routers last

### Validation at Application Layer

Validate user input and authorize requests at the application layer. Never trust the network.

```python
# File: app/application/validators.py
from app.application.schemas import CreateUserRequest

def validate_create_user_request(request: CreateUserRequest) -> None:
    """Validate create user request; raise ValueError if invalid."""
    if not request.email:
        raise ValueError("Email is required")

    if not request.name or len(request.name.strip()) == 0:
        raise ValueError("Name is required and cannot be whitespace only")

# File: app/application/routers/users.py
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
) -> UserResponse:
    """Create a new user."""
    try:
        validate_create_user_request(request)  # Additional validation if needed
        response = await use_case.execute(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidUserError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
```

**Key Principles**:
- Pydantic handles basic validation (type, format, length constraints)
- Use validators for complex business logic validation
- Always validate before calling use cases
- Raise appropriate HTTPException on validation failure

## Section 7: Infrastructure Layer Specifics

The infrastructure layer implements the ports defined in the domain layer and integrates external frameworks/services. It contains repositories, ORM models, external service clients, and configuration. **The domain layer must never depend on infrastructure; only infrastructure depends on domain.**

### SQLAlchemy ORM Models

ORM models represent database tables. They are **separate from domain entities**—never use domain entities directly as ORM models.

```python
# File: app/infrastructure/persistence/models.py
from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class UserORM(Base):
    """ORM model for users table."""
    __tablename__ = "users"

    id: str = Column(String(36), primary_key=True)
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    orders = relationship("OrderORM", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<UserORM(id={self.id}, email={self.email})>"

class OrderORM(Base):
    """ORM model for orders table."""
    __tablename__ = "orders"

    id: str = Column(String(36), primary_key=True)
    customer_id: str = Column(String(36), ForeignKey("users.id"), nullable=False)
    total_price: float = Column(Float, nullable=False)
    status: str = Column(String(50), default="pending", nullable=False, index=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    customer = relationship("UserORM", back_populates="orders")
    items = relationship("OrderItemORM", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<OrderORM(id={self.id}, customer_id={self.customer_id}, status={self.status})>"

class OrderItemORM(Base):
    """ORM model for order items (join table)."""
    __tablename__ = "order_items"

    id: str = Column(String(36), primary_key=True)
    order_id: str = Column(String(36), ForeignKey("orders.id"), nullable=False)
    sku: str = Column(String(100), nullable=False)
    quantity: int = Column(Integer, nullable=False)
    price: float = Column(Float, nullable=False)

    # Relationships
    order = relationship("OrderORM", back_populates="items")

    def __repr__(self) -> str:
        return f"<OrderItemORM(order_id={self.order_id}, sku={self.sku}, qty={self.quantity})>"
```

**Key Principles**:
- Column names use `snake_case`
- Primary key always `id` (uuid4 string)
- Use `DateTime` with `utcnow` for consistency
- Add `index=True` for frequently queried fields (email, status)
- Use `ForeignKey` and `relationship()` for associations
- Use `cascade="all, delete-orphan"` for cleanup
- Keep ORM models **simple data holders** — no business logic

### Repository Implementation Pattern

Repositories bridge domain entities and ORM models. They implement abstract ports from the domain layer.

```python
# File: app/infrastructure/persistence/repositories.py
from typing import list
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.domain.entities import User, Order
from app.domain.ports import UserRepository, OrderRepository
from app.infrastructure.persistence.models import UserORM, OrderORM, OrderItemORM

class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository port."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: str) -> User | None:
        """Fetch user by ID; returns domain entity or None."""
        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self._session.execute(stmt)
        orm_user = result.scalar_one_or_none()
        return self._orm_to_entity(orm_user) if orm_user else None

    async def get_by_email(self, email: str) -> User | None:
        """Fetch user by email; returns domain entity or None."""
        stmt = select(UserORM).where(UserORM.email == email)
        result = await self._session.execute(stmt)
        orm_user = result.scalar_one_or_none()
        return self._orm_to_entity(orm_user) if orm_user else None

    async def list_active(self) -> list[User]:
        """Fetch all active users; returns list of domain entities."""
        stmt = select(UserORM).where(UserORM.is_active == True).order_by(UserORM.created_at.desc())
        result = await self._session.execute(stmt)
        orm_users = result.scalars().all()
        return [self._orm_to_entity(u) for u in orm_users]

    async def save(self, user: User) -> None:
        """Persist domain entity as ORM model; creates or updates."""
        orm_user = self._entity_to_orm(user)
        self._session.add(orm_user)
        await self._session.flush()

    async def delete(self, user_id: str) -> None:
        """Delete user by ID."""
        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self._session.execute(stmt)
        orm_user = result.scalar_one_or_none()
        if orm_user:
            await self._session.delete(orm_user)
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

class SQLAlchemyOrderRepository(OrderRepository):
    """SQLAlchemy implementation of OrderRepository port."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, order_id: str) -> Order | None:
        """Fetch order with all items; returns domain aggregate root or None."""
        stmt = select(OrderORM).where(OrderORM.id == order_id)
        result = await self._session.execute(stmt)
        orm_order = result.scalar_one_or_none()
        return self._orm_to_entity(orm_order) if orm_order else None

    async def get_by_customer(self, customer_id: str) -> list[Order]:
        """Fetch all orders for customer; returns list of aggregates."""
        stmt = (
            select(OrderORM)
            .where(OrderORM.customer_id == customer_id)
            .order_by(OrderORM.created_at.desc())
        )
        result = await self._session.execute(stmt)
        orm_orders = result.scalars().all()
        return [self._orm_to_entity(o) for o in orm_orders]

    async def save(self, order: Order) -> None:
        """Persist entire aggregate (order + items) as ORM models."""
        orm_order = self._entity_to_orm(order)
        self._session.add(orm_order)
        await self._session.flush()

    def _orm_to_entity(self, orm_order: OrderORM) -> Order:
        """Convert ORM aggregate to domain aggregate root."""
        from app.domain.entities import OrderItem, Money

        items = [
            OrderItem(
                sku=item.sku,
                quantity=item.quantity,
                price=Money(item.price, "USD"),
            )
            for item in orm_order.items
        ]

        return Order(
            id=orm_order.id,
            customer_id=orm_order.customer_id,
            items=items,
            total_price=Money(orm_order.total_price, "USD"),
            status=orm_order.status,
        )

    def _entity_to_orm(self, order: Order) -> OrderORM:
        """Convert domain aggregate to ORM aggregate."""
        orm_order = OrderORM(
            id=order.id,
            customer_id=order.customer_id,
            total_price=order.total_price.amount,
            status=order.status,
        )

        orm_order.items = [
            OrderItemORM(
                id=str(uuid4()),
                order_id=order.id,
                sku=item.sku,
                quantity=item.quantity,
                price=item.price.amount,
            )
            for item in order.items
        ]

        return orm_order
```

**Key Principles**:
- Repository methods always return **domain entities**, never ORM models
- Mapping methods (`_orm_to_entity`, `_entity_to_orm`) keep conversion isolated
- All methods are `async`; use `await` for I/O
- Use `flush()` not `commit()` — session manages transactions
- For aggregates, save **entire aggregate** as one unit
- Query methods include filters (e.g., `list_active()`) to avoid fetching unnecessary data

### Database Configuration & Sessions

Create a database module to configure SQLAlchemy and provide async sessions:

```python
# File: app/infrastructure/persistence/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.infrastructure.persistence.models import Base
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.sql_echo,
    poolclass=NullPool,  # Disable connection pooling for simplicity; enable for production
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db_session() -> AsyncSession:
    """Dependency injection: provide async session for each request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    """Initialize database: create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db() -> None:
    """Drop all tables (for testing)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def close_db() -> None:
    """Close database connection."""
    await engine.dispose()
```

**Key Principles**:
- Use `create_async_engine()` with `AsyncSession` for async support
- Use `NullPool` for serverless/testing; enable pooling for production
- `expire_on_commit=False` prevents lazy-loading issues after commit
- `get_db_session()` is a FastAPI dependency that yields sessions
- `init_db()` creates all tables on startup
- Always `await session.close()` in finally block

### External Service Clients

Implement ports for external services (email, payment, etc.) as infrastructure adapters:

```python
# File: app/infrastructure/external/email_service.py
import aiohttp

from app.domain.ports import EmailService

class SmtpEmailService(EmailService):
    """SMTP email service implementation."""

    def __init__(self, smtp_host: str, smtp_port: int, from_email: str):
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._from_email = from_email

    async def send_welcome_email(self, email: str, name: str) -> None:
        """Send welcome email using SMTP."""
        subject = "Welcome to Bel'Air's Buvette"
        body = f"Hello {name}, welcome to our service!"

        # Use aiosmtplib or similar async email library
        # Pseudocode:
        # async with aiosmtplib.SMTP(hostname=self._smtp_host) as smtp:
        #     await smtp.send_message(Message(subject=subject, body=body, to=email))

        print(f"Email sent to {email}: {subject}")

class SendgridEmailService(EmailService):
    """SendGrid email service implementation."""

    def __init__(self, api_key: str, from_email: str):
        self._api_key = api_key
        self._from_email = from_email

    async def send_welcome_email(self, email: str, name: str) -> None:
        """Send welcome email using SendGrid API."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "personalizations": [{"to": [{"email": email}]}],
                "from": {"email": self._from_email},
                "subject": "Welcome to Bel'Air's Buvette",
                "content": [{"type": "text/html", "value": f"<p>Hello {name}</p>"}],
            }
            headers = {"Authorization": f"Bearer {self._api_key}"}

            async with session.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers=headers,
            ) as response:
                if response.status != 202:
                    raise Exception(f"SendGrid error: {response.status}")
```

**Key Principles**:
- Implement abstract ports from domain layer
- Use async HTTP clients (`aiohttp`, `httpx`) for external APIs
- **Never raise framework exceptions** — convert to domain exceptions
- Support multiple implementations (SMTP, SendGrid, etc.)
- Use dependency injection to switch implementations without code changes

### Configuration Management

Centralize configuration to avoid hardcoding values:

```python
# File: app/core/config.py
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # App
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost/belvette"
    sql_echo: bool = False

    # Email
    email_service: Literal["smtp", "sendgrid"] = "smtp"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    sendgrid_api_key: str = ""
    from_email: str = "noreply@belvette.local"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # JWT (if using)
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
```

**Usage:**

```python
# File: app/main.py
from app.core.config import settings

if settings.environment == "production":
    # Use production database
    pass
else:
    # Use development database
    pass

# Inject email service based on config
if settings.email_service == "sendgrid":
    email_service = SendgridEmailService(
        api_key=settings.sendgrid_api_key,
        from_email=settings.from_email,
    )
else:
    email_service = SmtpEmailService(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        from_email=settings.from_email,
    )
```

**Key Principles**:
- Use `pydantic-settings` for environment variable loading
- All secrets come from `.env` file (never commit `.env`)
- Provide sensible defaults for development
- Support multiple configurations per environment
- Inject configured services at app startup

## Section 8: Testing Patterns

Testing follows the Hexagonal Architecture: domain tests (fast, no dependencies), application tests (mocked infrastructure), and integration tests (real infrastructure).

### Domain Layer Tests

Domain tests are **fast and isolated**. They test business logic with no external dependencies:

```python
# File: tests/domain/test_order.py
import pytest
from app.domain.entities import Order, OrderItem, Money
from app.domain.exceptions import OrderValidationError

class TestOrder:
    """Test Order aggregate root."""

    def test_create_order_with_items(self):
        """Test creating an order with items."""
        item = OrderItem(sku="SKU001", quantity=2, price=Money(50.0, "USD"))
        order = Order(
            id="order-1",
            customer_id="customer-1",
            items=[item],
        )

        assert order.id == "order-1"
        assert len(order.items) == 1
        assert order.total_price.amount == 100.0

    def test_cannot_create_order_without_items(self):
        """Test that order creation fails without items."""
        with pytest.raises(ValueError, match="at least one item"):
            Order(id="order-1", customer_id="customer-1", items=[])

    def test_add_item_to_order(self):
        """Test adding item to pending order."""
        item1 = OrderItem(sku="SKU001", quantity=1, price=Money(50.0, "USD"))
        order = Order(id="order-1", customer_id="customer-1", items=[item1])

        item2 = OrderItem(sku="SKU002", quantity=2, price=Money(30.0, "USD"))
        order.add_item(item2)

        assert len(order.items) == 2
        assert order.total_price.amount == 110.0

    def test_cannot_add_duplicate_sku(self):
        """Test that duplicate SKUs are rejected."""
        item1 = OrderItem(sku="SKU001", quantity=1, price=Money(50.0, "USD"))
        order = Order(id="order-1", customer_id="customer-1", items=[item1])

        item2 = OrderItem(sku="SKU001", quantity=2, price=Money(50.0, "USD"))
        with pytest.raises(ValueError, match="already in order"):
            order.add_item(item2)

    def test_cannot_add_item_to_finalized_order(self):
        """Test that finalized orders cannot be modified."""
        item = OrderItem(sku="SKU001", quantity=1, price=Money(50.0, "USD"))
        order = Order(id="order-1", customer_id="customer-1", items=[item])
        order.finalize()

        new_item = OrderItem(sku="SKU002", quantity=1, price=Money(50.0, "USD"))
        with pytest.raises(ValueError, match="non-pending"):
            order.add_item(new_item)
```

**Key Principles**:
- Test only domain entities and value objects
- No mocking, no async, no I/O
- Test happy paths and error cases
- Use descriptive test names (test_*_when_*)
- Keep tests focused (one assertion per test, or related assertions only)

### Application Layer Tests (with Mocks)

Application tests use mocked infrastructure to test use cases:

```python
# File: tests/application/test_create_user_use_case.py
import pytest
from unittest.mock import AsyncMock, patch
from app.application.use_cases import CreateUserUseCase
from app.application.schemas import CreateUserRequest, CreateUserResponse
from app.domain.entities import User
from app.domain.ports import UserRepository
from app.domain.exceptions import UserAlreadyExistsError

@pytest.fixture
def mock_user_repository() -> AsyncMock:
    """Provide mock UserRepository."""
    return AsyncMock(spec=UserRepository)

@pytest.mark.asyncio
async def test_create_user_success(mock_user_repository):
    """Test successful user creation."""
    mock_user_repository.get_by_email.return_value = None

    use_case = CreateUserUseCase(user_repository=mock_user_repository)
    request = CreateUserRequest(email="john@example.com", name="John Doe")

    response = await use_case.execute(request)

    assert response.email == "john@example.com"
    assert response.user_id is not None
    mock_user_repository.save.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_already_exists(mock_user_repository):
    """Test creation fails when user already exists."""
    existing_user = User(id="user-1", email="john@example.com", name="John Doe")
    mock_user_repository.get_by_email.return_value = existing_user

    use_case = CreateUserUseCase(user_repository=mock_user_repository)
    request = CreateUserRequest(email="john@example.com", name="John Doe")

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(request)

    mock_user_repository.save.assert_not_called()
```

**Key Principles**:
- Mock all external dependencies (repositories, services, ports)
- Use `AsyncMock` for async dependencies
- Use `@pytest.mark.asyncio` for async tests
- Test both success and error paths
- Verify mocks were called with expected arguments
- Keep tests small and focused

### Integration Tests (Real Infrastructure)

Integration tests use real infrastructure (test database, test containers):

```python
# File: tests/integration/test_user_repository.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.infrastructure.persistence.models import Base, UserORM
from app.infrastructure.persistence.repositories import SQLAlchemyUserRepository
from app.domain.entities import User

@pytest.fixture
async def db_session():
    """Provide test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_save_and_retrieve_user(db_session):
    """Test saving and retrieving user from database."""
    repository = SQLAlchemyUserRepository(db_session)
    user = User(id="user-1", email="john@example.com", name="John Doe")

    await repository.save(user)
    retrieved = await repository.get_by_id("user-1")

    assert retrieved is not None
    assert retrieved.email == "john@example.com"
    assert retrieved.name == "John Doe"

@pytest.mark.asyncio
async def test_get_by_email(db_session):
    """Test fetching user by email."""
    repository = SQLAlchemyUserRepository(db_session)
    user = User(id="user-1", email="john@example.com", name="John Doe")
    await repository.save(user)

    retrieved = await repository.get_by_email("john@example.com")

    assert retrieved is not None
    assert retrieved.id == "user-1"
```

**Key Principles**:
- Use in-memory SQLite for fast tests, or Testcontainers for production databases
- Create tables in setup; drop in teardown
- Test full flows (save → retrieve → verify)
- Use real repository implementations
- Keep tests focused on data persistence behavior

### Test Organization

```
tests/
├── conftest.py                 # Shared fixtures
├── domain/
│   ├── test_user.py
│   ├── test_order.py
│   └── test_money.py
├── application/
│   ├── test_create_user_use_case.py
│   ├── test_get_user_use_case.py
│   └── test_create_order_use_case.py
├── infrastructure/
│   ├── test_sqlalchemy_user_repository.py
│   └── test_email_service.py
├── integration/
│   ├── test_full_user_creation_flow.py
│   └── test_full_order_flow.py
└── fixtures/
    ├── users.py               # Fixture data
    └── orders.py
```

---

## Section 9: Error Handling & Exceptions

### Exception Hierarchy

Create a clear exception hierarchy for the domain:

```python
# File: app/domain/exceptions.py

class DomainException(Exception):
    """Base exception for all domain errors."""
    pass

class ValidationError(DomainException):
    """Raised when entity validation fails."""
    pass

class InvalidUserError(ValidationError):
    """User data violates business rules."""
    pass

class InvalidOrderError(ValidationError):
    """Order data violates business rules."""
    pass

class StateError(DomainException):
    """Raised when operation is invalid for current state."""
    pass

class UserAlreadyExistsError(StateError):
    """User already exists (duplicate)."""
    pass

class OrderNotPendingError(StateError):
    """Operation requires pending order."""
    pass

class NotFoundError(DomainException):
    """Resource not found."""
    pass

class UserNotFoundError(NotFoundError):
    """User does not exist."""
    pass

class OrderNotFoundError(NotFoundError):
    """Order does not exist."""
    pass

class ConflictError(DomainException):
    """Operation violates constraints."""
    pass

class InsufficientBalanceError(ConflictError):
    """User has insufficient balance."""
    pass
```

### Raising Exceptions in Domain

Always raise domain exceptions. Never propagate framework exceptions:

```python
# File: app/domain/entities.py
from app.domain.exceptions import InvalidUserError, UserAlreadyExistsError

class User:
    def __post_init__(self):
        if not self.email or "@" not in self.email:
            raise InvalidUserError(f"Invalid email: {self.email}")

        if not self.name or len(self.name.strip()) == 0:
            raise InvalidUserError("Name cannot be empty")

# File: app/domain/use_cases.py
class CreateUserUseCase:
    async def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        existing = await self._repository.get_by_email(request.email)
        if existing:
            raise UserAlreadyExistsError(f"User {request.email} already exists")

        user = User(id=str(uuid4()), email=request.email, name=request.name)
        await self._repository.save(user)
        return CreateUserResponse(user_id=user.id, email=user.email)
```

### Converting Infrastructure Exceptions

Infrastructure layer catches framework exceptions and converts to domain exceptions:

```python
# File: app/infrastructure/persistence/repositories.py
from sqlalchemy.exc import IntegrityError
from app.domain.exceptions import InvalidUserError

class SQLAlchemyUserRepository(UserRepository):
    async def save(self, user: User) -> None:
        try:
            orm_user = self._entity_to_orm(user)
            self._session.add(orm_user)
            await self._session.flush()
        except IntegrityError as e:
            if "unique constraint" in str(e):
                raise InvalidUserError(f"User {user.email} already exists") from e
            raise Exception(f"Database constraint error: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Failed to save user: {str(e)}") from e
```

### Mapping to HTTP Responses

Application layer maps domain exceptions to HTTP responses:

```python
# File: app/application/routers/users.py
from fastapi import APIRouter, HTTPException, status

@router.post("/")
async def create_user(request: CreateUserRequest, use_case: CreateUserUseCase):
    try:
        response = await use_case.execute(request)
        return response
    except InvalidUserError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error")
```

---

## Section 10: Comments & Documentation

### When to Comment

**Good comments** explain **why**, not **what**. The code shows what; comments explain reasoning:

```python
# Bad: Restates what code does
def calculate_total(items):
    total = 0  # Initialize total to 0
    for item in items:
        total += item.price  # Add item price to total
    return total

# Good: Explains why
def calculate_total(items):
    # Avoid using sum() with generator; we need to exclude cancelled items
    total = 0
    for item in items:
        if item.status != "cancelled":
            total += item.price
    return total
```

### Docstrings

Use **Google-style docstrings** for all public functions, classes, and modules:

```python
"""Module docstring: brief description.

This module handles user-related domain logic including validation,
creation, and state transitions.

Example:
    Basic usage of User entity:

        user = User(id="user-1", email="john@example.com", name="John Doe")
        user.activate()
"""

class User:
    """Domain entity representing a user in the system.

    Users have identity, lifecycle (created → active → inactive),
    and enforce invariants (unique email, non-empty name).

    Attributes:
        id: Unique user identifier (UUID).
        email: User email address (must be valid).
        name: User full name (non-empty).
        is_active: Whether user account is active.
    """

    def activate(self) -> None:
        """Activate user account.

        Raises:
            ValueError: If user is already active.
        """
        if self.is_active:
            raise ValueError("User is already active")
        self.is_active = True
```

### Module-Level Documentation

Document modules to explain purpose and key concepts:

```python
"""app.domain.ports

Abstract port definitions (interfaces) for domain dependencies.

Ports define contracts for secondary adapters (repositories, external services).
They live in the domain layer and are implemented in the infrastructure layer.

Implementations should be in app.infrastructure:
- UserRepository → SQLAlchemyUserRepository
- EmailService → SmtpEmailService, SendgridEmailService

See Also:
    - app.infrastructure.persistence for repository implementations
    - app.infrastructure.external for external service implementations
"""
```

### API Documentation

Use `description` fields in FastAPI route decorators:

```python
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Creates a new user account. Email must be unique. Returns 400 if validation fails.",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Validation error (invalid email, duplicate)"},
        409: {"description": "User already exists"},
    },
)
async def create_user(request: CreateUserRequest) -> UserResponse:
    """Create a new user."""
```

---

## Section 11: Common Anti-Patterns to Avoid

### Anti-Pattern 1: Anemic Domain Models

❌ **Bad**: Domain entity with no behavior, just data holders:

```python
@dataclass
class Order:
    id: str
    customer_id: str
    items: list[OrderItem]
    total_price: float

# Validation and logic live in use case, not entity!
async def create_order(items):
    if not items:
        raise ValueError("Order must have items")
    total = sum(i.price for i in items)
    return Order(id=uuid4(), customer_id="...", items=items, total_price=total)
```

✅ **Good**: Domain entity enforces its own invariants:

```python
@dataclass
class Order:
    id: str
    customer_id: str
    items: list[OrderItem] = field(default_factory=list)
    total_price: Money | None = None

    def __post_init__(self):
        if not self.items:
            raise ValueError("Order must have items")
        self._recalculate_total()

    def add_item(self, item: OrderItem) -> None:
        if not self.items:
            raise ValueError("Order must have items")
        self.items.append(item)
        self._recalculate_total()

    def _recalculate_total(self) -> None:
        total = sum(i.price.amount * i.quantity for i in self.items)
        self.total_price = Money(total, "USD")
```

### Anti-Pattern 2: Mixing Layers

❌ **Bad**: Importing domain from infrastructure; mixing concerns:

```python
# app/infrastructure/user_service.py
from app.application.schemas import UserResponse  # Wrong layer!
from app.infrastructure.models import UserORM

class UserService:
    def get_user(self, user_id: str) -> UserResponse:
        orm_user = self._session.query(UserORM).get(user_id)
        return UserResponse.from_orm(orm_user)  # DTO logic in infrastructure!
```

✅ **Good**: Clean boundaries; infrastructure only touches domain:

```python
# app/infrastructure/persistence/repositories.py
from app.domain.entities import User  # Domain layer only
from app.domain.ports import UserRepository

class SQLAlchemyUserRepository(UserRepository):
    def get_by_id(self, user_id: str) -> User | None:
        orm_user = self._session.query(UserORM).get(user_id)
        return self._orm_to_entity(orm_user)

# app/application/routers/users.py
from app.domain.entities import User  # Domain
from app.application.schemas import UserResponse  # Application

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, use_case: GetUserUseCase):
    user: User = await use_case.execute(...)
    return UserResponse.from_orm(user)  # Mapping in application layer
```

### Anti-Pattern 3: God Objects

❌ **Bad**: One class doing too much:

```python
class UserService:  # 500+ lines!
    # Creating users
    async def create_user(self, ...): ...
    # Validating emails
    async def validate_email(self, ...): ...
    # Sending emails
    async def send_welcome_email(self, ...): ...
    # Managing passwords
    async def reset_password(self, ...): ...
    # Handling subscriptions
    async def subscribe_user(self, ...): ...
```

✅ **Good**: Separate concerns into focused use cases:

```python
# Each use case handles one business scenario
class CreateUserUseCase:
    async def execute(self, request: CreateUserRequest) -> CreateUserResponse: ...

class ResetPasswordUseCase:
    async def execute(self, request: ResetPasswordRequest) -> None: ...

class SubscribeUserUseCase:
    async def execute(self, user_id: str) -> None: ...
```

### Anti-Pattern 4: Over-Abstraction

❌ **Bad**: Too many layers for simple operations:

```python
class UserFactory(Factory):
    def create_user(self, ...): ...

class UserBuilder(Builder):
    def with_email(self, ...): ...

class UserValidator(Validator):
    def validate(self, ...): ...

class UserDTO(DTO):
    # Just a wrapper

# Overkill for domain entity creation!
```

✅ **Good**: Simple domain entities, minimal abstraction:

```python
# Domain entity constructor enforces invariants
user = User(id=str(uuid4()), email=email, name=name)  # Done!
```

### Anti-Pattern 5: Blocking Calls in Async Code

❌ **Bad**: Using synchronous I/O in async context:

```python
async def fetch_user(user_id: str):
    # Blocks entire event loop!
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()
```

✅ **Good**: Use async HTTP clients:

```python
import httpx

async def fetch_user(user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        return response.json()
```

### Anti-Pattern 6: Leaking Infrastructure to Domain

❌ **Bad**: Domain exceptions depend on infrastructure:

```python
# app/domain/exceptions.py
from sqlalchemy.exc import IntegrityError  # Domain should not know SQLAlchemy!

class UserAlreadyExistsError(IntegrityError):
    pass
```

✅ **Good**: Domain exceptions are infrastructure-agnostic:

```python
# app/domain/exceptions.py
class UserAlreadyExistsError(DomainException):  # Independent!
    pass

# app/infrastructure/repositories.py
from sqlalchemy.exc import IntegrityError

class SQLAlchemyUserRepository:
    def save(self, user: User):
        try:
            # ...
        except IntegrityError:
            raise UserAlreadyExistsError(...)  # Convert at boundary
```

### Anti-Pattern 7: Circular Dependencies

❌ **Bad**: Domain imports application; application imports domain:

```python
# app/domain/entities.py
from app.application.schemas import UserRequest  # Circular!

# app/application/use_cases.py
from app.domain.entities import User
```

✅ **Good**: Dependency points inward (application → domain, never domain → application):

```python
# app/domain/entities.py - No imports from application!

# app/application/use_cases.py
from app.domain.entities import User  # One-way dependency
```

---

## Final Checklist

Before committing code, verify:

- ✅ Type hints on all functions and class attributes
- ✅ Google-style docstrings on public functions/classes
- ✅ Import organization: stdlib → third-party → local
- ✅ **CRITICAL** Ruff compliance: `uv run ruff check .`
- ✅ No circular dependencies between layers
- ✅ Domain entities enforce invariants; no anemic models
- ✅ Repositories return domain entities, never ORM models
- ✅ All I/O is async; use `await` throughout call chain
- ✅ Domain exceptions only; no framework exceptions in domain
- ✅ Tests cover domain, application (with mocks), integration
