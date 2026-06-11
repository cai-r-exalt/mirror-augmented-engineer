# Regular hydration notifications

**Contexte**
System sends periodic reminders to festival goers to drink water; frequency adapts to recent alcohol consumption and time of day.

**Critères d'acceptation**
Feature: Hydration reminders

Scenario: Hourly reminders during window
Given current time is 12:00 and user present
When schedule runs
Then user receives a hydration reminder every hour between 11:00 and 19:00

Scenario: Increased frequency after heavy drinking
Given a user drank more than 3 alcoholic drinks in past hour
When schedule runs
Then reminders are sent every 30 minutes for that user

**Notes**
- Implementation: background scheduler (cron/job queue) and opt-out considerations.