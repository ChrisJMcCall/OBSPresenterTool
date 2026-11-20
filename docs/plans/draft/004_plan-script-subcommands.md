---
id: 004
title: Plan Script Subcommands
status: draft
---

## Context

`_plan.sh` currently takes a bare title (`_plan.sh "UI Improvements"`) and only creates draft plans.
Make it subcommand-based (`_plan.sh new "UI Improvements"`) so more commands, such as promote, can
be added later.

## Changes

**docs/plans/\_plan.sh**

- Wrap the existing creation logic in a `cmd_new()` function. Its logic will change: next-ID scan
  will be constrained to the draft folder, but still use filename slug, heredoc into `draft/`.
- Add a `usage()` function that prints `Usage: _plan.sh <command> [args]` and lists `new <title>`.
- Add a dispatcher at the bottom:
  ```bash
  COMMAND="${1:-}"
  shift || true
  case "$COMMAND" in
      new) cmd_new "$@" ;;
      -h|--help|help) usage ;;
      "") usage >&2; exit 1 ;;
      *) echo "Error: unknown command '$COMMAND' (did you mean: _plan.sh new \"<title>\"?)" >&2
         usage >&2; exit 1 ;;
  esac
  ```
  A bare `_plan.sh` prints usage to stderr and exits 1. Only `help`, `-h` and `--help` print usage and
  exit 0. Unknown commands exit 1.
- `cmd_new` keeps the "A plan title is required" error when no title is given. It joins multiple
  words with `TITLE="$*"`.
- `cmd_new` truncates the title to 30 characters (the README schema limit) and strips trailing
  whitespace left by the cut. Truncation happens before the filename is built, so the front matter
  title and the filename agree.
- Quote `${SCRIPT_DIR}/draft/${FILE_NAME}` in the redirect.

**docs/plans/README.md**

- Update the example to `$ \_plan.sh new "Input Form Improvements"`.

## Out of scope

- No `promote` subcommand, even though the README describes promotion. It is a natural follow-up.
- Existing draft files keep their current ids. After the scan is limited to `draft/`, the next draft
  id is computed from `draft/` only, so this draft (004) may need renumbering by hand.

## Verification

- `_plan.sh` with no args prints usage to stderr and exits 1.
- `_plan.sh help` prints usage and exits 0.
- `_plan.sh bogus` and `_plan.sh "Old Style"` print an error with a hint and exit 1.
- A title over 30 characters is truncated in both the front matter and the filename, with no trailing
  space or hyphen.
- `_plan.sh new UI Improvements` (unquoted) creates a single plan.
- The new id is based on `draft/` only.
- `_plan.sh new` with no title prints an error and exits 1.
- `_plan.sh new "Test Plan"` creates `draft/NNN_test-plan.md` with correct front matter. Delete it
  afterward.
- `bash -n docs/plans/_plan.sh`, plus `shellcheck` if installed.
- Review `git diff`.
