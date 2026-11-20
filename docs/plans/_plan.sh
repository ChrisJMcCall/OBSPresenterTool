#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAX_TITLE_LENGTH=30

usage() {
    echo "Usage: _plan.sh <command> [args]"
    echo
    echo "Commands:"
    echo "  new <title>   Create a new draft plan"
    echo "  help          Show this message"
}

cmd_new() {
    if [ "$#" -eq 0 ]; then
        echo "Error: A plan title is required" >&2
        exit 1
    fi

    local TITLE="$*"
    TITLE="${TITLE:0:MAX_TITLE_LENGTH}"
    # Strip trailing whitespace left by the truncation
    TITLE="${TITLE%"${TITLE##*[![:space:]]}"}"

    # Read the file names in the draft directory to find the next prefix
    local MAX_ID=0
    local file NUM

    while IFS= read -r file; do
        NUM=$(basename "$file" | cut -c1-3)

        if [ "$((10#$NUM))" -gt "$MAX_ID" ]; then
            MAX_ID=$((10#$NUM))
        fi
    done < <(find "$SCRIPT_DIR/draft" -type f -name '[0-9][0-9][0-9]_*')

    local NEXT_ID FILE_NAME
    NEXT_ID=$(printf "%03d" "$((MAX_ID + 1))")
    FILE_NAME=$(printf "%s_%s.md" "$NEXT_ID" "$TITLE" | tr "[:upper:] " "[:lower:]-")

    cat << EOT > "${SCRIPT_DIR}/draft/${FILE_NAME}"
---
id: $NEXT_ID
title: $TITLE
status: draft
---
EOT
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
    new) cmd_new "$@" ;;
    -h|--help|help) usage ;;
    "") usage >&2; exit 1 ;;
    *)
        echo "Error: unknown command '$COMMAND' (did you mean: _plan.sh new \"<title>\"?)" >&2
        usage >&2
        exit 1
        ;;
esac
