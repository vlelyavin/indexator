#!/usr/bin/env python3
"""Find mismatched translation keys between analyzer code and translation files."""

import json
import re
from pathlib import Path
from collections import defaultdict

def load_translation_keys(lang_file):
    """Load all translation keys from a language file."""
    with open(lang_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    keys = set()

    def extract_keys(obj, prefix=''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_prefix = f'{prefix}.{key}' if prefix else key
                if isinstance(value, dict):
                    extract_keys(value, new_prefix)
                else:
                    keys.add(new_prefix)
        return keys

    return extract_keys(data)

def find_t_calls(file_path):
    """Find all self.t() calls in a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to match self.t("key") or self.t("key", ...)
    pattern = r'self\.t\(["\']([^"\']+)["\']'
    matches = re.findall(pattern, content)

    return matches

def main():
    print('=' * 80)
    print('Translation Key Mismatch Finder')
    print('=' * 80)
    print()

    # Load translation keys from English file (source of truth)
    en_file = Path('app/locales/en.json')
    print(f'Loading translation keys from {en_file}...')
    valid_keys = load_translation_keys(en_file)
    print(f'  Found {len(valid_keys)} valid translation keys')
    print()

    # Find all analyzer files
    analyzers_dir = Path('app/analyzers')
    analyzer_files = [f for f in analyzers_dir.glob('*.py')
                      if f.name not in ['__init__.py', 'base.py']]

    print(f'Scanning {len(analyzer_files)} analyzer files...')
    print()

    # Track mismatches
    mismatches = defaultdict(list)
    total_keys_used = 0
    missing_keys = set()

    for analyzer_file in sorted(analyzer_files):
        keys_used = find_t_calls(analyzer_file)
        total_keys_used += len(keys_used)

        file_mismatches = []
        for key in keys_used:
            if key not in valid_keys:
                file_mismatches.append(key)
                missing_keys.add(key)

        if file_mismatches:
            mismatches[analyzer_file.name] = file_mismatches

    # Print results
    if mismatches:
        print(f'[ERROR] Found {len(missing_keys)} missing/mismatched keys in {len(mismatches)} files:')
        print()

        for filename in sorted(mismatches.keys()):
            print(f'  {filename}:')
            for key in mismatches[filename]:
                print(f'    - {key}')
                # Try to find similar keys
                analyzer_name = filename.replace('.py', '')
                potential_matches = [k for k in valid_keys if analyzer_name in k and 'summary' in k]
                if potential_matches:
                    print(f'      Maybe: {", ".join(list(potential_matches)[:3])}')
            print()
    else:
        print('[OK] All translation keys match!')

    # Summary
    print('=' * 80)
    print('Summary:')
    print(f'  Total analyzer files scanned: {len(analyzer_files)}')
    print(f'  Total self.t() calls found: {total_keys_used}')
    print(f'  Missing/mismatched keys: {len(missing_keys)}')
    print(f'  Files with mismatches: {len(mismatches)}')
    print('=' * 80)

if __name__ == '__main__':
    main()
