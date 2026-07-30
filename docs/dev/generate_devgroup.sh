#!/bin/bash

# File Name
OUTPUT_FILE="dev_group.md"

echo "File Generation $OUTPUT_FILE..."

cat << 'EOF' > "$OUTPUT_FILE"
\page dev_docs Developer Documentation

Welcome to the Developer Documentation. Below is the table of contents for all available guides and resources:

EOF

find . -type f -name "*.md" | sort | while read -r file; do
    if [ "$(basename "$file")" == "$OUTPUT_FILE" ]; then
        continue
    fi

    BASENAME=$(basename "$file" .md)

    file_clean="${file#./}"
    PAGE_ID="md_$(echo "$file_clean" | sed 's/\.md$//' | sed 's/\//_/g')"

    PAGE_TITLE=$(grep -m 1 '^#[ \t]' "$file" | sed 's/^#[ \t]*//')

    if [ -z "$PAGE_TITLE" ]; then
        PAGE_TITLE="$BASENAME"
    fi

    if ! head -n 1 "$file" | grep -q "^\\\\page"; then
        temp_file=$(mktemp)
        echo "\page $PAGE_ID $PAGE_TITLE" > "$temp_file"
        echo "" >> "$temp_file" # Ajoute une ligne vide pour la lisibilité
        cat "$file" >> "$temp_file"
        mv "$temp_file" "$file"
    fi

    echo "* \subpage $PAGE_ID \"$PAGE_TITLE\"" >> "$OUTPUT_FILE"
done

echo "Finished !"
