#!/usr/bin/env python3
"""
Process the raw PDF-extracted index and create a structured JSON file.
"""

import json
import re
from typing import List, Dict, Optional

def is_page_number(line: str) -> bool:
    """Check if a line is just a standalone page number."""
    return line.strip().isdigit()

def is_section_header(line: str) -> bool:
    """Check if a line is a section header like '## B', 'C', 'D', etc."""
    return re.match(r'^##?\s*[A-Z]$', line.strip()) is not None

def fix_spacing(text: str) -> str:
    """Fix missing spaces in common patterns."""
    # Fix "classinib_insync" -> "class in ib_insync"
    text = re.sub(r'classin(ib_insync)', r'class in \1', text)

    # Fix "inmoduleib_insync" -> "in module ib_insync"
    text = re.sub(r'inmodule(ib_insync[.\w]*)', r'in module \1', text)

    # Fix missing space before "attribute", "property", "method"
    text = re.sub(r'(\w)(attribute|property|method)\b', r'\1 \2', text)

    # Fix missing space after commas (but not in paths)
    text = re.sub(r',(\w)', r', \1', text)

    return text

def clean_entry(entry: str) -> str:
    """Clean up an individual entry."""
    entry = entry.strip()

    # Remove trailing commas and punctuation
    entry = re.sub(r'[,;]+$', '', entry)

    # Fix spacing issues
    entry = fix_spacing(entry)

    return entry

def parse_entry(entry: str) -> Optional[Dict[str, str]]:
    """
    Parse an index entry into structured data.

    Expected formats:
    - name (ib_insync.module.Class attribute)
    - name (ib_insync.module.Class property)
    - name() (ib_insync.module.Class method)
    - name() (in module ib_insync.module)
    - Class (class in ib_insync.module)
    """
    entry = entry.strip()
    if not entry:
        return None

    # Remove any leading arrow or list markers
    entry = re.sub(r'^[→\-\*•]\s*', '', entry)

    # Pattern for: name() (ib_insync.module.Class method)
    # or: name (ib_insync.module.Class attribute/property)
    match = re.match(r'^(\w+)\(\)\s*\(([^)]+)\s+(method)\)', entry)
    if match:
        name, path, entry_type = match.groups()
        path = path.strip()

        # Parse the path
        if ' in ' in path:
            path = path.split(' in ')[-1]

        parts = path.rsplit('.', 1)
        if len(parts) == 2:
            module_class = parts[0]
            # Check if it's a class method
            if '.' in module_class:
                module_parts = module_class.rsplit('.', 1)
                return {
                    'name': name,
                    'full_path': f"{path}.{name}",
                    'type': 'method',
                    'module': module_parts[0],
                    'class': module_parts[1]
                }

        return {
            'name': name,
            'full_path': f"{path}.{name}",
            'type': 'method',
            'module': path,
            'class': None
        }

    # Pattern for: name (ib_insync.module.Class attribute/property)
    match = re.match(r'^(\w+)\s*\(([^)]+)\s+(attribute|property)\)', entry)
    if match:
        name, path, entry_type = match.groups()
        path = path.strip()

        if ' in ' in path:
            path = path.split(' in ')[-1]

        parts = path.rsplit('.', 1)
        if len(parts) == 2:
            module_class = parts[0]
            if '.' in module_class:
                module_parts = module_class.rsplit('.', 1)
                return {
                    'name': name,
                    'full_path': f"{path}.{name}",
                    'type': entry_type,
                    'module': module_parts[0],
                    'class': module_parts[1]
                }

        return {
            'name': name,
            'full_path': f"{path}.{name}",
            'type': entry_type,
            'module': path,
            'class': None
        }

    # Pattern for: name() (in module ib_insync.module)
    match = re.match(r'^(\w+)\(\)\s*\(in module ([^)]+)\)', entry)
    if match:
        name, module = match.groups()
        return {
            'name': name,
            'full_path': f"{module}.{name}",
            'type': 'function',
            'module': module.strip(),
            'class': None
        }

    # Pattern for: Class (class in ib_insync.module)
    match = re.match(r'^(\w+)\s*\(class in ([^)]+)\)', entry)
    if match:
        name, module = match.groups()
        return {
            'name': name,
            'full_path': f"{module}.{name}",
            'type': 'class',
            'module': module.strip(),
            'class': None
        }

    # Pattern for static method: name() (ib_insync.module.Class static method)
    match = re.match(r'^(\w+)\(\)\s*\(([^)]+)\s+static method\)', entry)
    if match:
        name, path = match.groups()
        path = path.strip()

        parts = path.rsplit('.', 1)
        if len(parts) == 2:
            module_class = parts[0]
            if '.' in module_class:
                module_parts = module_class.rsplit('.', 1)
                return {
                    'name': name,
                    'full_path': f"{path}.{name}",
                    'type': 'static_method',
                    'module': module_parts[0],
                    'class': module_parts[1]
                }

    # If we can't parse it, return None
    return None

def split_merged_entries(line: str) -> List[str]:
    """
    Split entries that got merged on the same line.
    Look for patterns where multiple entries are on one line.
    """
    entries = []

    # Pattern: entry1) entry2(
    # This catches cases where one entry ends with ) and another starts with name(
    parts = re.split(r'\)\s+([A-Z][a-z]\w+)\(', line)

    if len(parts) > 1:
        # First part is the first entry
        entries.append(parts[0] + ')')
        # Remaining parts alternate between name and rest of entry
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                entries.append(parts[i] + '(' + parts[i + 1])
            else:
                entries.append(parts[i])
    else:
        # Try another pattern: entry1 attribute) entry2 (
        parts = re.split(r'\)\s+([A-Z][a-z]\w+)\s*\(', line)
        if len(parts) > 1:
            entries.append(parts[0] + ')')
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    entries.append(parts[i] + ' (' + parts[i + 1])
                else:
                    entries.append(parts[i])
        else:
            # No split needed
            entries.append(line)

    return entries

def process_index_file(input_path: str) -> List[Dict[str, str]]:
    """Process the raw index file and return structured data."""
    entries = []
    pending_line = None
    issues = {
        'page_numbers_removed': 0,
        'section_headers_removed': 0,
        'unparseable_lines': []
    }

    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Remove line number prefix (from cat -n format)
            line = re.sub(r'^\s*\d+→', '', line)
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip page numbers
            if is_page_number(line):
                issues['page_numbers_removed'] += 1
                continue

            # Skip section headers
            if is_section_header(line):
                issues['section_headers_removed'] += 1
                continue

            # Skip the word "Index" by itself
            if line.strip() == 'Index':
                continue

            # Skip module section markers
            if line.strip().startswith('module') and len(line.strip().split()) <= 2:
                continue

            # Handle lines that are continuations (don't start with a name pattern)
            # If pending_line exists, try to merge
            if pending_line and not re.match(r'^[A-Z_][a-zA-Z0-9_]*[\(\s]', line):
                pending_line = pending_line + ' ' + line
                continue

            # If we have a pending line, process it now
            if pending_line:
                # Try to split merged entries
                split_entries = split_merged_entries(pending_line)
                for entry_text in split_entries:
                    entry_text = clean_entry(entry_text)
                    if entry_text:
                        parsed = parse_entry(entry_text)
                        if parsed:
                            entries.append(parsed)
                        else:
                            issues['unparseable_lines'].append({
                                'line_num': line_num - 1,
                                'text': entry_text
                            })
                pending_line = None

            # Start new pending line
            pending_line = line

        # Process the last pending line
        if pending_line:
            split_entries = split_merged_entries(pending_line)
            for entry_text in split_entries:
                entry_text = clean_entry(entry_text)
                if entry_text:
                    parsed = parse_entry(entry_text)
                    if parsed:
                        entries.append(parsed)
                    else:
                        issues['unparseable_lines'].append({
                            'line_num': line_num,
                            'text': entry_text
                        })

    return entries, issues

def main():
    input_file = '/home/user/in_insync_docs/index_raw.md'
    output_file = '/home/user/in_insync_docs/index_cleaned.json'

    print("Processing index file...")
    entries, issues = process_index_file(input_file)

    # Sort entries by name
    entries.sort(key=lambda x: (x['name'].lower(), x['full_path']))

    # Remove duplicates
    seen = set()
    unique_entries = []
    for entry in entries:
        key = (entry['name'], entry['full_path'], entry['type'])
        if key not in seen:
            seen.add(key)
            unique_entries.append(entry)

    # Create output structure
    output = {
        'index': unique_entries,
        'metadata': {
            'total_entries': len(unique_entries),
            'duplicates_removed': len(entries) - len(unique_entries),
            'page_numbers_removed': issues['page_numbers_removed'],
            'section_headers_removed': issues['section_headers_removed']
        }
    }

    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Processed {len(unique_entries)} unique entries")
    print(f"✓ Removed {len(entries) - len(unique_entries)} duplicates")
    print(f"✓ Removed {issues['page_numbers_removed']} page numbers")
    print(f"✓ Removed {issues['section_headers_removed']} section headers")
    print(f"✓ Output saved to: {output_file}")

    if issues['unparseable_lines']:
        print(f"\n⚠ Warning: {len(issues['unparseable_lines'])} lines could not be parsed")
        print("First 10 unparseable lines:")
        for issue in issues['unparseable_lines'][:10]:
            print(f"  Line {issue['line_num']}: {issue['text']}")

if __name__ == '__main__':
    main()
