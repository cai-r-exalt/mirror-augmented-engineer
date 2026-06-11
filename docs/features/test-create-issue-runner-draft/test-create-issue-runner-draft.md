# Test: Create issue runner draft

**Contexte**
This is a test to verify the create_issue_runner generates and validates an issue draft.

**Critères d'acceptation**
Feature: Test issue generation

Scenario: Generate a basic issue draft
  Given a fresh workspace
  When the create_issue_runner is invoked with a valid payload
  Then it produces a markdown file under docs/features and validates successfully


**Notes**
- Add any additional notes or references here.
