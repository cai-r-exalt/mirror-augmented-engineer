# Cancel an order

**Contexte**
Festival goers can cancel orders before acknowledgment and should receive token refunds.

**Critères d'acceptation**
Feature: Cancel order

Scenario: Cancel unacknowledged order
Given an unacknowledged order that consumed tokens
When the user cancels it
Then tokens are refunded and user receives confirmation

Scenario: Cannot cancel acknowledged order
Given an acknowledged order
When the user attempts cancellation
Then cancellation is rejected

**Notes**
- Ensure token refund is atomic and idempotent.