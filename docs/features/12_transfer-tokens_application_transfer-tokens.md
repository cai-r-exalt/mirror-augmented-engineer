# Transfer tokens to another festival goer

**Contexte**
Festival goers can transfer up to three tokens of each type to another, with recipient confirmation.

**Critères d'acceptation**
Feature: Token transfer between users

Scenario: Successful transfer with confirmation
Given user A has at least 3 drink tokens and user B accepts transfer
When A transfers 3 drink tokens to B
Then A's balance decreases and B's increases accordingly

Scenario: Prevent over-transfer
Given A has only 1 snack token and attempts to transfer 3
When transfer is requested
Then the system rejects the transfer

**Notes**
- Flow: POST /transfers, recipient confirmation endpoint required.