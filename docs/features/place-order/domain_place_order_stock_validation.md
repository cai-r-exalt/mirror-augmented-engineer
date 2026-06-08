# Place Order with Stock Validation (Domain Layer)

**Contexte**
The Domain layer must implement the core business logic for placing orders with inventory stock validation. This includes:
- Creating a new Inventory entity to track stock quantities for drinks and food items
- Implementing stock validation logic in the Order domain use case
- Ensuring the order business rules are enforced before any order is confirmed

A festival goer can order multiple items in a single order, but the order must fail if any requested item is out of stock. No tokens should be deducted if the order fails due to stock issues.

**Critères d'acceptation**

Feature: Place Order with Stock Validation

Scenario: Successfully place an order when all items are in stock
Given a festival goer with 10 drink tokens and 15 food tokens
And the following inventory exists: beer (drink, 5), snack (food, 10)
When the festival goer places an order with: 2 beers and 3 snacks
Then the order should be confirmed
And the festival goer's tokens should remain 10 drink tokens and 15 food tokens

Scenario: Reject order when a drink item is out of stock
Given a festival goer with 10 drink tokens and 15 food tokens
And the following inventory exists: beer (drink, 0), snack (food, 10)
When the festival goer attempts to place an order with: 1 beer
Then the order should be rejected with reason about beer being out of stock
And the festival goer's tokens should remain unchanged

Scenario: Reject order when a food item is out of stock
Given a festival goer with 10 drink tokens and 15 food tokens
And the following inventory exists: beer (drink, 5), snack (food, 0)
When the festival goer attempts to place an order with: 1 snack
Then the order should be rejected with reason about snack being out of stock
And the festival goer's tokens should remain unchanged

Scenario: Reject order when stock quantity is insufficient for requested quantity
Given a festival goer with 10 drink tokens and 15 food tokens
And the following inventory exists: beer (drink, 2)
When the festival goer attempts to place an order with: 3 beers
Then the order should be rejected with insufficient stock message
And the festival goer's tokens should remain unchanged

**Notes**
- The Inventory entity should be a new Value Object or Entity in the domain layer
- Stock validation should happen before order confirmation
- Token deduction logic remains unchanged (happens on order acknowledgement, not on order placement)
- This is a pure business logic issue focused on domain entities and use cases
- No persistence or API concerns should be addressed in this layer
