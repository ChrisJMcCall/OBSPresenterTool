# Planning

Planning is documented in this folder with markdown files that have a 3 digit prefix. The \_plan.sh
script is used to create a new plan ex: $ \_plan.sh new "Input Form Improvements"

- new plans are created with a "draft" status
- docs/plans/draft should contain ALL plans with a "draft" status
- docs/plans/draft should ONLY contain plans with a "draft" status
- a plan outside docs/plans/draft must never have a "draft" status
- Plans in the draft folder should not be executed. Promote them with `start` first

Draft plans have their own ordering, separate from all other plans. A draft is promoted with
`$ \_plan.sh start <draft>`, where `<draft>` is the draft's 3 digit id or its file name. This:

- gets the next sequential number from the non-draft plan list
- moves the plan from docs/plans/draft to docs/plans, replacing the 3 digit prefix in the file name
  with the new id
- updates the id in the front matter to the new id
- sets the status to "in-progress"

Do not move plans out of the draft folder by hand.

# Plan schema

The front matter of each plan should match this schema (JSON Schema, written in YAML):

```yaml
$schema: https://json-schema.org/draft/2020-12/schema
type: object
required: [id, title, status]
additionalProperties: false
properties:
  id:
    description: Sequential number, padded with zeros to 3 digits
    type: string
    pattern: "^[0-9]{3}$"
  title:
    description: A descriptive string
    type: string
    minLength: 1
    maxLength: 128
  status:
    type: string
    enum: [draft, ready, in-progress, implemented, cancelled]
```

Example front matter

```yaml
---
id: "004"
title: Plan Script Subcommands
status: draft
---
```
