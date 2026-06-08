# Place Order with Stock Validation (Infrastructure Layer)

**Contexte**
The Infrastructure layer must implement the persistence layer for orders and inventory, including:
- Creating SQLAlchemy models for Inventory (tracking stock quantities for each item)
- Creating or updating Order persistence models to reference inventory items
- Implementing repository/adapter methods to query inventory availability
- Implementing transaction-safe stock validation and deduction logic
- Creating database migrations with Alembic for schema changes
- Ensuring thread-safety and consistency for concurrent order placements

**Critères d'acceptation**

Feature: Order and Inventory Persistence with Stock Validation

Scenario: Create inventory record for a drink item
Given an infrastructure persistence layer with SQLAlchemy setup
When creating an inventory record for beer (drink type, quantity 10)
Then the inventory record should be persisted in the database
And the record should be retrievable by item_id

Scenario: Query available inventory for multiple items
Given inventory records exist for beer (5 units), wine (0 units), snack (8 units)
When querying inventory availability for all items
Then the repository should return all three items with their correct quantities

Scenario: Validate stock availability before order placement
Given inventory has beer (3 units)
When validating stock for an order requesting 2 beers
Then validation should succeed and return True

Scenario: Reject validation when stock is insufficient
Given inventory has beer (1 unit)
When validating stock for an order requesting 2 beers
Then validation should fail and return False with insufficient stock reason

Scenario: Atomically decrement inventory on order acknowledgement
Given inventory has beer (10 units) and snack (5 units)
And an order is acknowledged requesting 3 beers and 2 snacks
When decrementing inventory for the order
Then inventory should be updated to beer (7 units) and snack (3 units)

Scenario: Prevent race condition with concurrent orders
Given inventory has beer (2 units)
When two concurrent requests try to order 1 beer each
Then both orders should be accepted for processing
And the orders should be processed one at a time in sequence
And final inventory should be exactly 0 units

Scenario: Create order record with inventory item references
Given valid inventory items exist
When creating an order record with items (2 beers, 1 snack)
Then the order should be persisted with order_id
And order_items relationship should contain both items with correct quantities

Scenario: Query orders by festival goer ID
Given multiple orders exist for different festival goers
When querying orders for a specific festival_goer_id
Then the repository should return only that festival goer's orders

Scenario: Handle inventory quantity cannot go negative
Given inventory has beer (2 units)
When attempting to decrement inventory by 5 units
Then the operation should fail or raise validation error
And inventory quantity should remain at 2

Scenario: Create and run Alembic migration for inventory schema
Given the Alembic migration system is set up
When running migrations
Then a new inventory table should be created with required columns and constraints

**Notes**
- Use SQLAlchemy ORM for model definitions
- Implement inventory repository pattern for queries
- Use database transactions/locks to prevent race conditions (consider pessimistic locking)
- Concurrent orders should be serialized so they are processed one at a time
- Stock validation and deduction should be atomic operations
- Migrations should be reversible (down migration required)
- Inventory quantity must never go negative (database constraint recommended)
- Consider adding updated_at timestamp for audit trail
- This layer focuses solely on persistence and transaction safety, not business logic
