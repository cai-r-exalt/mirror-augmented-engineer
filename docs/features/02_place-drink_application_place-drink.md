# Place an order for a drink

**Contexte**
Festival goer orders a drink (alcoholic or non-alcoholic) using drink tokens.

**Critères d'acceptation**
Feature: Place drink order

Scenario: Order a non-alcoholic drink (free)
Given a non-alcoholic drink item in stock
When a festival goer places an order for it
Then the order is accepted and no drink tokens are deducted

Scenario: Order a premium alcoholic drink
Given a premium alcoholic drink in stock and user has 2 drink tokens
When the user orders the premium drink
Then 2 drink tokens are deducted and stock is decremented

**Notes**
- Endpoint: POST /orders with item ids and quantities. Validate stock and token costs before creating the order.