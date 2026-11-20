#!/bin/bash

if [ "$#" -eq 0 ]; then
    echo "Error: A plan title is required"
    exit 1
fi

TITLE="$@"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Read the file names in the plan directory to find the next prefix
MAX_ID=0

while IFS= read -r file; do
    NUM=$(basename "$file" | cut -c1-3)

    if [ "$NUM" -gt "$MAX_ID" ]; then
        MAX_ID=$NUM
    fi
done < <(find "$SCRIPT_DIR" -type f -name '[0-9][0-9][0-9]_*')

NEXT_ID=$(printf "%03d" "$((MAX_ID + 1))")
FILE_NAME=$(printf "%s_%s.md" "$NEXT_ID" "$TITLE" | tr "[:upper:] " "[:lower:]-")

cat << EOF > ${SCRIPT_DIR}/draft/${FILE_NAME}
---
id: $NEXT_ID
title: $TITLE
status: draft
---
EOF