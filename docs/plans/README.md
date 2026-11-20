# Planning

Planning is documented in this folder with markdown files that have a 3 digit prefix. The \_plan.sh
script is used to create a new plan ex: $ \_plan.sh new "Input Form Improvements"

- new plans are created with a "draft" status
- docs/plans/draft is the location for plans with a "draft" status

Draft plans have their own ordering, separate from all other plans. When a plan is promoted out of
draft status, it will get the next sequential number from the non-draft plan list, update its id,
and then move to docs/plans with a new file name that replaces the 3 digit prefix with the new id.

# Plan schema

```yaml
---
id: 3 digit, sequential, number padded with zeros
title: A descriptive string. Limit to 30 characters
status: draft/ready/in-progress/implemented/cancelled
---
```
