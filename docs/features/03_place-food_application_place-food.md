# Place an order for food

**Contexte**
Festival goer orders snacks or meals which cost food tokens.

**Critères d'acceptation**
Feature: Place food order

Scenario: Order a snack
Given a snack item in stock and user has at least 1 food token
When the user orders the snack
Then 1 food token is deducted and stock is decremented

Scenario: Order a meal
Given a meal item in stock and user has at least 3 food tokens
When the user orders the meal
Then 3 food tokens are deducted and stock is decremented

**Notes**
- Ensure distinction between snack and meal pricing in order validation.