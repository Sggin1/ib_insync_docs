#!/usr/bin/env python3
"""
Enhanced version to process the PDF-extracted index with better handling of merged entries.
"""

import json
import re
from typing import List, Dict, Optional, Tuple

def is_page_number(text: str) -> bool:
    """Check if text is just a standalone page number."""
    return text.strip().isdigit() and len(text.strip()) <= 3

def is_section_header(text: str) -> bool:
    """Check if text is a section header like '## B', 'C', 'D', etc."""
    return re.match(r'^##?\s*[A-Z]$', text.strip()) is not None

def fix_spacing(text: str) -> str:
    """Fix missing spaces in common patterns."""
    # Fix "classinib_insync" -> "class in ib_insync"
    text = re.sub(r'\bclassin(ib_insync)', r'class in \1', text)

    # Fix "inmoduleib_insync" -> "in module ib_insync"
    text = re.sub(r'\binmodule(ib_insync[.\w]*)', r'in module \1', text)

    # Fix missing space before "attribute", "property", "method"
    # But only if preceded by an alphanumeric character
    text = re.sub(r'([a-zA-Z0-9])(attribute|property|method)\b', r'\1 \2', text)

    return text

def extract_entries_from_line(line: str) -> List[str]:
    """
    Extract individual entries from a line that may contain multiple entries.

    Entries typically follow patterns like:
    - name (path attribute)
    - name() (path method)
    - Name (class in path)
    """
    entries = []

    # First, fix spacing issues
    line = fix_spacing(line)

    # Pattern to identify entry boundaries:
    # An entry starts with a word (possibly with underscores) followed by optional ()
    # then a space and an opening parenthesis
    pattern = r'\b([A-Z_][a-zA-Z0-9_]*[\(\)]*)\s+\(([^)]+\s+(?:attribute|property|method|class|function))\)'

    matches = list(re.finditer(pattern, line))

    if matches:
        for match in matches:
            name = match.group(1).strip()
            rest = match.group(2).strip()
            entry = f"{name} ({rest})"
            entries.append(entry)
    else:
        # If no matches with the standard pattern, try to salvage what we can
        # Look for class definitions
        class_pattern = r'\b([A-Z][a-zA-Z0-9_]*)\s*\(class in (ib_insync\.[a-zA-Z0-9_.]+)\)'
        matches = list(re.finditer(class_pattern, line))
        for match in matches:
            entries.append(match.group(0))

    return entries

def parse_entry(entry: str) -> Optional[Dict[str, str]]:
    """
    Parse an index entry into structured data.
    """
    entry = entry.strip()
    if not entry:
        return None

    # Remove trailing commas and semicolons
    entry = re.sub(r'[,;]+$', '', entry).strip()

    # Pattern for: name() (ib_insync.module.Class method)
    match = re.match(r'^([a-zA-Z_]\w+)\(\)\s+\((ib_insync\.[a-zA-Z0-9_.]+)\s+method\)', entry)
    if match:
        name, path = match.groups()
        parts = path.rsplit('.', 1)
        if len(parts) == 2:
            module_class, _ = parts
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

    # Pattern for: name() (ib_insync.module.Class static method)
    match = re.match(r'^([a-zA-Z_]\w+)\(\)\s+\((ib_insync\.[a-zA-Z0-9_.]+)\s+static\s+method\)', entry)
    if match:
        name, path = match.groups()
        parts = path.rsplit('.', 1)
        if len(parts) == 2:
            module_class, _ = parts
            if '.' in module_class:
                module_parts = module_class.rsplit('.', 1)
                return {
                    'name': name,
                    'full_path': f"{path}.{name}",
                    'type': 'static_method',
                    'module': module_parts[0],
                    'class': module_parts[1]
                }

    # Pattern for: name (ib_insync.module.Class attribute|property)
    match = re.match(r'^([a-zA-Z_]\w+)\s+\((ib_insync\.[a-zA-Z0-9_.]+)\s+(attribute|property)\)', entry)
    if match:
        name, path, entry_type = match.groups()
        parts = path.rsplit('.', 1)
        if len(parts) == 2:
            module_class, _ = parts
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
    match = re.match(r'^([a-zA-Z_]\w+)\(\)\s+\(in\s+module\s+(ib_insync\.[a-zA-Z0-9_.]+)\)', entry)
    if match:
        name, module = match.groups()
        return {
            'name': name,
            'full_path': f"{module}.{name}",
            'type': 'function',
            'module': module,
            'class': None
        }

    # Pattern for: Class (class in ib_insync.module)
    match = re.match(r'^([A-Z][a-zA-Z0-9_]*)\s+\(class\s+in\s+(ib_insync\.[a-zA-Z0-9_.]+)\)', entry)
    if match:
        name, module = match.groups()
        return {
            'name': name,
            'full_path': f"{module}.{name}",
            'type': 'class',
            'module': module,
            'class': None
        }

    return None

def read_and_clean_file(input_path: str) -> str:
    """Read the file and do initial cleaning."""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove line number prefixes
    content = re.sub(r'^\s*\d+→', '', content, flags=re.MULTILINE)

    return content

def process_index_file(input_path: str) -> Tuple[List[Dict[str, str]], Dict]:
    """Process the raw index file and return structured data."""
    content = read_and_clean_file(input_path)

    entries = []
    issues = {
        'page_numbers_removed': 0,
        'section_headers_removed': 0,
        'unparseable_entries': []
    }

    # Split into lines and process
    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

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

        # Skip "Index" markers
        if re.match(r'^Index\s*\d*$', line):
            continue

        # Skip module markers
        if re.match(r'^module\s*$', line, re.IGNORECASE):
            continue

        # Extract entries from this line
        line_entries = extract_entries_from_line(line)

        for entry_text in line_entries:
            parsed = parse_entry(entry_text)
            if parsed:
                entries.append(parsed)
            else:
                if entry_text and not is_page_number(entry_text):
                    issues['unparseable_entries'].append({
                        'line_num': line_num,
                        'text': entry_text[:100]
                    })

    return entries, issues

def main():
    input_file = '/home/user/in_insync_docs/index_raw.md'
    output_file = '/home/user/in_insync_docs/index_cleaned.json'

    print("Processing index file with enhanced parser...")
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

    if issues['unparseable_entries']:
        print(f"\n⚠ {len(issues['unparseable_entries'])} entries could not be parsed")
        print("Sample unparseable entries (first 5):")
        for issue in issues['unparseable_entries'][:5]:
            print(f"  Line {issue['line_num']}: {issue['text']}")

if __name__ == '__main__':
    main()
