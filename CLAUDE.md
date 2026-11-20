# Project

Python application to automate presenting difficulties in OBS.

## OBS and Python

- OBS requires a specific version of python. The current one in use on this machine is 3.11 inside
  of /opt/homebrew/Frameworks/
- uv is used to manage the python project

# Development

Run with:

```bash
uv run window-selector
```

## Planning

Read: docs/plans/README.md

- Work done towards specifications outlined in a plan should be done in a branch that is not "main"

## Rules

- Don't introduce dependencies without asking.
- Prefer existing patterns over introducing new abstractions.

## Before finishing

- Run tests
- Run lint/type checking
- Review git diff
- Summarize changes and remaining concerns
