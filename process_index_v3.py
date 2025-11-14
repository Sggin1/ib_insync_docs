#!/usr/bin/env python3
"""
Final version with comprehensive parsing to handle all entry types.
"""

import json
import re
from typing import List, Dict, Optional, Tuple

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Fix common spacing issues
    text = re.sub(r'classin(ib_insync)', r'class in \1', text)
    text = re.sub(r'inmodule(ib_insync[.\w]*)', r'in module \1', text)
    text = re.sub(r'([a-zA-Z0-9])(attribute|property|method)', r'\1 \2', text)
    return text.strip()

def is_skip_line(text: str) -> bool:
    """Check if this line should be skipped."""
    text = text.strip()
    if not text:
        return True
    # Page numbers
    if text.isdigit() and len(text) <= 3:
        return True
    # Section headers
    if re.match(r'^##?\s*[A-Z]$', text):
        return True
    # Index markers
    if re.match(r'^Index\s*\d*$', text):
        return True
    # Module markers
    if text == 'module':
        return True
    # Single letters or short garbage
    if len(text) <= 2 and text.isalpha():
        return True
    return False

def extract_all_entries_from_text(text: str) -> List[str]:
    """
    Extract all entries from text, handling merged entries on same line.
    """
    entries = []

    # Clean the text first
    text = clean_text(text)

    # Pattern 1: Class definitions - Class(class in module)
    # More permissive: match anything in parentheses
    pattern1 = r'\b([A-Z][a-zA-Z0-9_]*)\s*\(\s*class\s+in\s+(ib_insync\.[a-zA-Z0-9_.]+)\s*\)'
    for match in re.finditer(pattern1, text):
        entries.append(f"{match.group(1)} (class in {match.group(2)})")
        # Remove this match from text to avoid reprocessing
        text = text[:match.start()] + ' ' * (match.end() - match.start()) + text[match.end():]

    # Pattern 2: Functions - name() (in module module.path)
    pattern2 = r'\b([a-zA-Z_]\w*)\(\)\s*\(\s*in\s+module\s+(ib_insync\.[a-zA-Z0-9_.]+)\s*\)'
    for match in re.finditer(pattern2, text):
        entries.append(f"{match.group(1)}() (in module {match.group(2)})")
        text = text[:match.start()] + ' ' * (match.end() - match.start()) + text[match.end():]

    # Pattern 3: Methods - name() (path method) or name() (path static method)
    pattern3 = r'\b([a-zA-Z_]\w*)\(\)\s*\(\s*(ib_insync\.[a-zA-Z0-9_.]+)\s+(static\s+)?method\s*\)'
    for match in re.finditer(pattern3, text):
        method_type = 'static method' if match.group(3) else 'method'
        entries.append(f"{match.group(1)}() ({match.group(2)} {method_type})")
        text = text[:match.start()] + ' ' * (match.end() - match.start()) + text[match.end():]

    # Pattern 4: Attributes/Properties - name (path attribute/property)
    pattern4 = r'\b([a-zA-Z_]\w*)\s+\(\s*(ib_insync\.[a-zA-Z0-9_.]+)\s+(attribute|property)\s*\)'
    for match in re.finditer(pattern4, text):
        entries.append(f"{match.group(1)} ({match.group(2)} {match.group(3)})")

    return entries

def parse_entry(entry: str) -> Optional[Dict[str, str]]:
    """Parse a single cleaned entry into structured data."""
    entry = entry.strip()
    if not entry:
        return None

    # Remove trailing commas
    entry = re.sub(r'[,;]+$', '', entry).strip()

    # Class: Name (class in module.path)
    match = re.match(r'^([A-Z][a-zA-Z0-9_]*)\s+\(class\s+in\s+(ib_insync\.[a-zA-Z0-9_.]+)\)$', entry)
    if match:
        name, module = match.groups()
        return {
            'name': name,
            'full_path': f"{module}.{name}",
            'type': 'class',
            'module': module,
            'class': None
        }

    # Function: name() (in module module.path)
    match = re.match(r'^([a-zA-Z_]\w*)\(\)\s+\(in\s+module\s+(ib_insync\.[a-zA-Z0-9_.]+)\)$', entry)
    if match:
        name, module = match.groups()
        return {
            'name': name,
            'full_path': f"{module}.{name}",
            'type': 'function',
            'module': module,
            'class': None
        }

    # Static method: name() (module.Class static method)
    match = re.match(r'^([a-zA-Z_]\w*)\(\)\s+\((ib_insync\.[a-zA-Z0-9_.]+)\s+static\s+method\)$', entry)
    if match:
        name, path = match.groups()
        parts = path.rsplit('.', 1)
        if len(parts) == 2:
            module_class, _ = parts
            module_parts = module_class.rsplit('.', 1) if '.' in module_class else (module_class, None)
            return {
                'name': name,
                'full_path': f"{path}.{name}",
                'type': 'static_method',
                'module': module_parts[0] if len(module_parts) == 2 else module_class,
                'class': module_parts[1] if len(module_parts) == 2 else None
            }

    # Method: name() (module.Class method)
    match = re.match(r'^([a-zA-Z_]\w*)\(\)\s+\((ib_insync\.[a-zA-Z0-9_.]+)\s+method\)$', entry)
    if match:
        name, path = match.groups()
        parts = path.rsplit('.', 1)
        if len(parts) == 2:
            module_class, _ = parts
            module_parts = module_class.rsplit('.', 1) if '.' in module_class else (module_class, None)
            return {
                'name': name,
                'full_path': f"{path}.{name}",
                'type': 'method',
                'module': module_parts[0] if len(module_parts) == 2 else module_class,
                'class': module_parts[1] if len(module_parts) == 2 else None
            }

    # Attribute/Property: name (module.Class attribute/property)
    match = re.match(r'^([a-zA-Z_]\w*)\s+\((ib_insync\.[a-zA-Z0-9_.]+)\s+(attribute|property)\)$', entry)
    if match:
        name, path, entry_type = match.groups()
        parts = path.rsplit('.', 1)
        if len(parts) == 2:
            module_class, _ = parts
            module_parts = module_class.rsplit('.', 1) if '.' in module_class else (module_class, None)
            return {
                'name': name,
                'full_path': f"{path}.{name}",
                'type': entry_type,
                'module': module_parts[0] if len(module_parts) == 2 else module_class,
                'class': module_parts[1] if len(module_parts) == 2 else None
            }

    return None

def process_file(input_path: str) -> Tuple[List[Dict[str, str]], Dict]:
    """Process the entire file."""
    all_entries = []
    stats = {
        'lines_processed': 0,
        'lines_skipped': 0,
        'raw_entries_found': 0,
        'unparseable': []
    }

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove line number prefixes
    content = re.sub(r'^\s*\d+→', '', content, flags=re.MULTILINE)

    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        if is_skip_line(line):
            stats['lines_skipped'] += 1
            continue

        stats['lines_processed'] += 1

        # Extract all entries from this line
        extracted = extract_all_entries_from_text(line)
        stats['raw_entries_found'] += len(extracted)

        for entry_text in extracted:
            parsed = parse_entry(entry_text)
            if parsed:
                all_entries.append(parsed)
            else:
                stats['unparseable'].append({
                    'line': line_num,
                    'text': entry_text[:80]
                })

    return all_entries, stats

def main():
    input_file = '/home/user/in_insync_docs/index_raw.md'
    output_file = '/home/user/in_insync_docs/index_cleaned.json'

    print("Processing PDF-extracted index...")
    print("=" * 60)

    entries, stats = process_file(input_file)

    # Sort and deduplicate
    entries.sort(key=lambda x: (x['name'].lower(), x['full_path']))

    seen = set()
    unique_entries = []
    for entry in entries:
        key = (entry['name'], entry['full_path'], entry['type'])
        if key not in seen:
            seen.add(key)
            unique_entries.append(entry)

    # Categorize by type
    type_counts = {}
    for entry in unique_entries:
        t = entry['type']
        type_counts[t] = type_counts.get(t, 0) + 1

    # Create output
    output = {
        'index': unique_entries,
        'metadata': {
            'total_entries': len(unique_entries),
            'duplicates_removed': len(entries) - len(unique_entries),
            'breakdown_by_type': type_counts
        }
    }

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n✓ Extracted {len(unique_entries)} unique index entries")
    print(f"✓ Removed {len(entries) - len(unique_entries)} duplicate entries")
    print(f"✓ Processed {stats['lines_processed']} lines")
    print(f"✓ Skipped {stats['lines_skipped']} non-content lines")
    print(f"\nBreakdown by type:")
    for entry_type, count in sorted(type_counts.items()):
        print(f"  - {entry_type}: {count}")

    print(f"\n✓ Output saved to: {output_file}")

    if stats['unparseable']:
        print(f"\n⚠ Warning: {len(stats['unparseable'])} entries could not be parsed")
        print("Sample unparseable entries:")
        for item in stats['unparseable'][:5]:
            print(f"  Line {item['line']}: {item['text']}")

if __name__ == '__main__':
    main()
