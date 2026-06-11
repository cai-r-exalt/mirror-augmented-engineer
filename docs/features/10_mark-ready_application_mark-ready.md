# Mark an order as ready

**Contexte**
Bartender marks orders ready when prepared items are available; festival goers are notified for pickup.

**Critères d'acceptation**
Feature: Mark order ready

Scenario: Mark ready when prepared
Given an order with enough prepared items
When bartender marks it ready
Then the order state changes to 'ready' and the user is notified

Scenario: Prevent marking when items missing
Given not enough prepared items to fulfil the order
When bartender attempts to mark ready
Then the action is rejected

**Notes**
- State transitions must be consistent and trigger notifications.