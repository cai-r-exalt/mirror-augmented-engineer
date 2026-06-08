# Examples

Input: "The user wants to export their contacts list to CSV"

Output:
Three files, one per layer: domain, application, infrastructure.

file `docs/features/export-contacts/domain_export-contacts-issue.md`
```markdown
# Export Contacts List : Domain Layer impact
**Context**
The user wants to export their contacts list to CSV.

**Acceptance Criteria**
Feature: Export contacts list
1. Scenario: Successfully export contacts
    Given a user with 20 contacts
    When the ExportContactsUseCase is executed
    Then it returns an ExportContactsResult with all 20 contacts

2. Scenario: No contacts to export
    Given a user with no contacts
    When the ExportContactsUseCase is executed
    Then it returns an empty ExportContactsResult
```

file `docs/features/export-contacts/application_export-contacts-issue.md`
```markdown
# Export Contacts List : Application Layer impact
**Context**
The user wants to export their contacts list to CSV.
**Acceptance Criteria**
1. Scenario: Successfully export contacts
    Given an authenticated user with 20 contacts
    When calling GET /contacts/export with Accept: text/csv
    Then the router returns 200 with a valid CSV body
2. Scenario: No contacts
    Given an authenticated user with no contacts
    When calling GET /contacts/export
    Then the router returns 204 No Content
```

file `docs/features/export-contacts/infrastructure_export-contacts-issue.md`
```markdown
# Export Contacts List : Infrastructure Layer impact
**Context**
The user wants to export their contacts list to CSV.
**Acceptance Criteria**
1. Scenario: Query all contacts from the database
    Given a database with 20 contacts for a given user
    When the SQLAlchemy ContactRepository.find_all_for_user is called
    Then all 20 contacts are returned as domain entities
```
