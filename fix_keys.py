#!/usr/bin/env python3
"""Fix remaining translation keys in analyzer files."""

import os
import re

ANALYZERS_DIR = "app/analyzers"

def fix_file(filepath):
    """Fix translation keys in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Replace remaining message keys (but not in @property methods)
    # Pattern: self.t("analyzers.X.Y" where Y is not "name" or "description"
    def replace_message(match):
        full_match = match.group(0)
        analyzer = match.group(1)
        key = match.group(2)
        params = match.group(3)

        # Skip if in @property method context (name or description)
        if key in ['name', 'description']:
            return full_match

        # Replace with issues prefix
        return f'self.t("analyzer_content.{analyzer}.issues.{key}"{params}'

    # Match self.t("analyzers.X.Y"...) but not name/description
    content = re.sub(
        r'self\.t\("analyzers\.([^.]+)\.([^"]+)"([^)]*)\)',
        replace_message,
        content
    )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Process all analyzer files
for filename in os.listdir(ANALYZERS_DIR):
    if filename.endswith('.py') and filename not in ['__init__.py', 'base.py']:
        filepath = os.path.join(ANALYZERS_DIR, filename)
        if fix_file(filepath):
            print(f"Fixed: {filename}")
        else:
            print(f"No changes: {filename}")

print("\nAll analyzer files processed!")
