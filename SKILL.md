--- 
name: create-issue
description: Create an issue in the form of a markdown file with title, description, implementation plan, and Gherkin test scenarios from a functional request. Use when needing structured, testable issues.
---

# Instructions
1. Extract context and success criteria from the request
2. Ask 2-3 questions to clarify the request if necessary
3. Identify impacted layers. If more than one layer is impacted, you MUST generate one issue per layer. For each layer:
    1. Summarize the context specific to the layer
    2. Identify specific success criteria for the layer
    3. Generate a concise title and structured description.
    4. Produce 1..N Gherkin scenarios covering happy path and edge cases.
    5. Create the issue in the `docs/features/{feature_name}/{layer_name}_{issue_title}.md` file using the `templates/issue.md` template.
    6. Validate the issue using `scripts/validate_issue.py`.

# Note
- This skill is intended to create manageable issues. Typically, it should not span more than one layer.
- If the request is too broad, propose the user to break it down per layer (domain, application, infrastructure).
