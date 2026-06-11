# Bartender acknowledges an order and provides estimated readiness time

**Contexte**
Bartender acknowledges orders and supplies an estimated time based on item types and rules in FEATURES.md.

**Critères d'acceptation**
Feature: Acknowledge order and estimate time

Scenario: Acknowledge order with mixed items
Given an order with normal alcoholic drinks and snacks
When the bartender acknowledges it
Then the user is notified and an estimated readiness time is calculated per rules

Scenario: Non-alcoholic-only order estimation
Given an order with only non-alcoholic drinks
When acknowledged
Then estimate is 1 minute per different drink type

**Notes**
- Calculation must follow the documented rules including meals parallelism.