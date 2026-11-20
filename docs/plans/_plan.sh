#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAX_TITLE_LENGTH=128
MAX_FILE_NAME_LENGTH=30

usage() {
    echo "Usage: _plan.sh <command> [args]"
    echo
    echo "Commands:"
    echo "  new <title>   Create a new draft plan"
    echo "  start <draft> Promote a draft (id or filename) to an in-progress plan"
    echo "  help          Show this message"
}

# Print the next 3 digit id for the plans directly inside $1 (not recursive)
next_id() {
    local dir="$1" max_id=0 file num

    while IFS= read -r file; do
        num=$(basename "$file" | cut -c1-3)

        if [ "$((10#$num))" -gt "$max_id" ]; then
            max_id=$((10#$num))
        fi
    done < <(find "$dir" -maxdepth 1 -type f -name '[0-9][0-9][0-9]_*')

    printf "%03d" "$((max_id + 1))"
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

    # The file name uses a shorter version of the title
    local SLUG_SOURCE="${TITLE:0:MAX_FILE_NAME_LENGTH}"
    SLUG_SOURCE="${SLUG_SOURCE%"${SLUG_SOURCE##*[![:space:]]}"}"

    local NEXT_ID FILE_NAME
    NEXT_ID=$(next_id "$SCRIPT_DIR/draft")
    FILE_NAME=$(printf "%s_%s.md" "$NEXT_ID" "$SLUG_SOURCE" | tr "[:upper:] " "[:lower:]-")

    cat << EOT > "${SCRIPT_DIR}/draft/${FILE_NAME}"
---
id: "$NEXT_ID"
title: $TITLE
status: draft
---
EOT
}

cmd_start() {
    if [ "$#" -eq 0 ]; then
        echo "Error: A draft id or file name is required" >&2
        exit 1
    fi

    local name matches
    name="$(basename "$1")"
    name="${name%.md}"

    # A bare 3 digit id matches on prefix, anything else is a file name
    if [[ "$name" =~ ^[0-9]{3}$ ]]; then
        matches=("$SCRIPT_DIR/draft/${name}_"*.md)
    else
        matches=("$SCRIPT_DIR/draft/${name}.md")
    fi

    if [ ! -f "${matches[0]}" ]; then
        echo "Error: no draft found for '$1'" >&2
        exit 1
    fi

    if [ "${#matches[@]}" -gt 1 ]; then
        echo "Error: '$1' matches more than one draft:" >&2
        printf "  %s\n" "${matches[@]##*/}" >&2
        exit 1
    fi

    local old_path="${matches[0]}" old_name new_id new_name new_path
    old_name="$(basename "$old_path")"
    new_id=$(next_id "$SCRIPT_DIR")
    new_name="${new_id}${old_name:3}"
    new_path="$SCRIPT_DIR/$new_name"

    if [ -e "$new_path" ]; then
        echo "Error: $new_name already exists" >&2
        exit 1
    fi

    # Only touch the first id and status lines inside the front matter block
    awk -v id="$new_id" '
        /^---[[:space:]]*$/ { fence++ }
        fence == 1 && !id_done && /^id:/ { print "id: \"" id "\""; id_done = 1; next }
        fence == 1 && !status_done && /^status:/ { print "status: in-progress"; status_done = 1; next }
        { print }
    ' "$old_path" > "$new_path" && rm "$old_path"

    echo "draft/$old_name -> $new_name"
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
    new) cmd_new "$@" ;;
    start) cmd_start "$@" ;;
    -h|--help|help) usage ;;
    "") usage >&2; exit 1 ;;
    *)
        echo "Error: unknown command '$COMMAND' (did you mean: _plan.sh new \"<title>\"?)" >&2
        usage >&2
        exit 1
        ;;
esac
