# Manage inventory of drinks and food items

**Contexte**
Bartenders manage stock levels for drinks, snacks, and meals; stock updates and checks are required during orders.

**Critères d'acceptation**
Feature: Inventory management

Scenario: Update stock quantity
Given a bartender updates an item stock to 10
When the update is saved
Then the system stores stock=10 and it cannot be negative

Scenario: Order checks stock before deduction
Given an order request for items
When the system validates the order
Then it rejects the order if any item stock is insufficient and does not deduct tokens

**Notes**
- Admin endpoints for stock: PATCH /inventory/{item_id}.