# Bartender reviews requests to change an acknowledged order

**Contexte**
When a festival goer requests changes to an acknowledged order, bartender reviews and accepts/rejects based on prepared item reuse.

**Critères d'acceptation**
Feature: Review acknowledged-order changes

Scenario: Accept change when transfer possible
Given some items prepared can be transferred to the modified order
When bartender accepts the change
Then the user is notified and estimated time is updated

Scenario: Reject change when no prepared items reusable
Given no prepared items can be reused
When bartender rejects the change
Then the user is notified of rejection

**Notes**
- Manual bartender decision with UI support required.