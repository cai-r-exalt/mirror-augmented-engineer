# Change an order

**Contexte**
Festival goers can modify their order before the bartender acknowledges it; modifications must revalidate balances and stock.

**Critères d'acceptation**
Feature: Modify order before acknowledgment

Scenario: Add item before acknowledgment
Given an unacknowledged order and sufficient tokens and stock
When the user adds an item
Then the modified order is accepted and tokens/stock updated

Scenario: Reject change if already acknowledged
Given an acknowledged order
When the user requests changes
Then the system rejects the change and notifies the bartender

**Notes**
- Endpoint: PATCH /orders/{order_id} with validation and state checks.