# Pool tokens to place a group order

**Contexte**
A group of festival goers can pool tokens to place a single group order, contributing arbitrary amounts from each member.

**Critères d'acceptation**
Feature: Group order with pooled tokens

Scenario: Successful group order
Given three users contribute drink tokens summing to required total and items in stock
When they submit a group order
Then the order is accepted and tokens are deducted from contributors accordingly

Scenario: Rejected if pooled tokens insufficient
Given contributors provide less than required tokens
When they attempt to place the group order
Then the order is rejected and no tokens are deducted

**Notes**
- UI: allow specifying contributions per user; backend: validate each contributor balance before deducting.