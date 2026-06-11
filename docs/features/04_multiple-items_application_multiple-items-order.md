# Order multiple items in a single order

**Contexte**
Festival goers should be able to order multiple items in one request; totals must respect token balances and stock availability.

**Critères d'acceptation**
Feature: Multi-item order

Scenario: Successful multi-item order within balance
Given a user with 5 drink tokens and 6 food tokens and all items in stock
When they place an order containing multiple drinks and snacks whose total costs are within balances
Then the order is accepted, tokens deducted, and stock decremented for each item

Scenario: Rejected when any item out of stock
Given one requested item is out of stock
When the user places the multi-item order
Then the order is rejected and no tokens are deducted

**Notes**
- Atomicity: order placement must be transactional.