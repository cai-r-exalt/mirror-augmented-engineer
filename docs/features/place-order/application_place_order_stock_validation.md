# Place Order with Stock Validation (Application Layer)

**Contexte**
The Application layer must implement the REST API endpoints and request/response handling for placing orders with inventory stock validation. This includes:
- Creating or updating the POST /orders endpoint to accept multiple items
- Validating request payloads (item IDs, quantities, types)
- Delegating to the domain use case for stock validation and business logic
- Returning appropriate success (201) or failure (400/409) responses
- Ensuring proper error messages guide the user when items are out of stock

**Critères d'acceptation**

Feature: Place Order API with Stock Validation

Scenario: Successfully place an order via API with all items in stock
Given a valid authenticated festival goer
And inventory has beer (5 units) and snack (10 units)
When the festival goer calls POST /orders with 2 beers and 3 snacks
Then the API should return 201 Created
And the response should contain order details with status "pending_acknowledgement"

Scenario: Return 400 Bad Request when item_id is missing
Given a valid authenticated festival goer
When the festival goer calls POST /orders with incomplete request body
Then the API should return 400 Bad Request
And the response should include validation error about missing item_id

Scenario: Return 400 Bad Request when quantity is invalid
Given a valid authenticated festival goer
When the festival goer calls POST /orders with quantity 0
Then the API should return 400 Bad Request
And the response should include error about invalid quantity

Scenario: Return 409 Conflict when an item is out of stock
Given a valid authenticated festival goer
And inventory has beer (0 units)
When the festival goer calls POST /orders with 1 beer
Then the API should return 409 Conflict
And the response should indicate ITEM_OUT_OF_STOCK error

Scenario: Return 409 Conflict when stock is insufficient
Given a valid authenticated festival goer
And inventory has beer (2 units)
When the festival goer calls POST /orders with 5 beers
Then the API should return 409 Conflict
And the response should indicate INSUFFICIENT_STOCK error with available quantity

Scenario: Return 404 Not Found when item does not exist
Given a valid authenticated festival goer
When the festival goer calls POST /orders with a non-existent item_id
Then the API should return 404 Not Found
And the response should include error about item not found

Scenario: Return 401 Unauthorized when not authenticated
Given an unauthenticated user
When the user calls POST /orders
Then the API should return 401 Unauthorized

**Notes**
- Request schema: OrderCreateRequest with items array (each item has item_id and quantity)
- Response schema: OrderResponse with order_id, status, items, created_at, total_cost
- Use 409 Conflict for stock-related issues (business rule violation)
- Use 400 Bad Request for validation/input issues
- Use 404 Not Found for missing items
- The Application layer delegates stock checking logic to domain use case
- This is focused on REST API contract and request/response handling only
