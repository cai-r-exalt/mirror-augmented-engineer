# Consult remaining token balance

**Contexte**
A festival goer needs to check their remaining drink and snack token balances for the current festival day.

**Critères d'acceptation**
Feature: Consult token balance

Scenario: Check current day's balances
Given a festival goer with 2 drink tokens and 5 snack tokens
When they request their token balance
Then the system returns drink_tokens: 2 and snack_tokens: 5

Scenario: No negative balances
Given a festival goer with zero tokens
When they request their token balance
Then the system returns zeros and does not return negative values

**Notes**
- Implementation: API endpoint GET /balances/{user_id}. Ensure per-day allocation rules are applied.