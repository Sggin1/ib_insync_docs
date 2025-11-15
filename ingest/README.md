# Ingest Folder Design

**Purpose:** Organize all source documentation for processing
**Date:** 2025-11-15

---

## Folder Structure

```
ingest/
├── README.md                  # This file
├── metadata.yaml              # Describes each source file
│
├── markdown/                  # All markdown documentation
│   ├── ib.md                  # Main API reference + examples
│   ├── ib_insync_complete_guide.md
│   ├── ib_insync_futures_update.md
│   └── index.md               # API index (pointers only)
│
├── json/                      # Structured data files
│   └── index_cleaned.json     # Pre-processed index
│
├── pdf/                       # Original PDF documentation
│   └── ib-insync.pdf
│
└── versions/                  # Version control for updates
    └── v0.9.86/               # Original version
        └── (copy of all files)
```

---

## File Type Classification

### Content Files (Process Fully)
Files with actual documentation content to extract:
- `ib.md` - Mixed API reference + code examples
- `ib_insync_complete_guide.md` - Tutorial with examples
- `ib_insync_futures_update.md` - Futures-specific guide

### Index/Pointer Files (Handle Specially)
Files that are just indexes or pointers to other content:
- `index.md` - Alphabetical API index (likely pointers)
- May not have code examples, just references

### Structured Data (Parse Differently)
- `index_cleaned.json` - Pre-parsed structured data
- May already be processed, use for validation

### Source Material (Reference Only)
- `ib-insync.pdf` - Original PDF (don't process, keep for reference)

---

## metadata.yaml

```yaml
version: "0.9.86"
last_updated: "2024-03-01"

files:
  markdown:
    ib.md:
      type: content
      contains:
        - api_reference
        - code_examples
        - documentation
      size_kb: 144
      lines: 4071
      priority: high

    ib_insync_complete_guide.md:
      type: content
      contains:
        - tutorial
        - code_examples
        - best_practices
      size_kb: 52
      lines: 1578
      priority: high

    ib_insync_futures_update.md:
      type: content
      contains:
        - futures_specific
        - code_examples
      size_kb: 18
      lines: 522
      priority: medium

    index.md:
      type: index
      contains:
        - api_references
        - pointers
      size_kb: 66
      lines: 892
      priority: low
      note: "Index file - mostly pointers, fewer examples"

  json:
    index_cleaned.json:
      type: structured_data
      contains:
        - api_index
      priority: validation
      note: "Pre-processed, use for validation"

  pdf:
    ib-insync.pdf:
      type: source
      priority: reference_only
      note: "Original PDF, keep for reference but don't process"
```

---

## Handling Different File Types

### 1. Content Files (Full Processing)

```python
# Extract everything
content_files = [
    'ingest/markdown/ib.md',
    'ingest/markdown/ib_insync_complete_guide.md',
    'ingest/markdown/ib_insync_futures_update.md'
]

for file in content_files:
    extract_code_examples(file)
    extract_api_methods(file)
    extract_explanations(file)
    extract_gotchas(file)
```

### 2. Index Files (Selective Processing)

```python
# Handle index.md specially
def process_index_file(file):
    """
    Index files have pointers, not full content.
    Extract API method names but skip example extraction.
    """
    # Extract API method references
    api_methods = extract_api_references(file)

    # Don't extract code examples (likely minimal/none)
    # Don't extract explanations (just pointers)

    # Use for validation - ensure all APIs documented
    validate_api_coverage(api_methods)
```

### 3. JSON Files (Direct Parse)

```python
# Use structured data for validation
def process_json_index(file):
    """
    JSON already structured, use for validation.
    """
    with open(file) as f:
        index_data = json.load(f)

    # Cross-reference with extracted data
    validate_against_index(index_data)
```

---

## Adding New Documentation

### Process for Updates

```bash
# 1. Add new files to ingest/
ingest/
└── markdown/
    └── new_feature_guide.md  # NEW

# 2. Update metadata.yaml
files:
  markdown:
    new_feature_guide.md:
      type: content
      contains: [code_examples]
      priority: high

# 3. Update config.yaml to include new file
extraction:
  source_files:
    - ingest/markdown/ib.md
    - ingest/markdown/ib_insync_complete_guide.md
    - ingest/markdown/ib_insync_futures_update.md
    - ingest/markdown/new_feature_guide.md  # ADD

# 4. Re-run pipeline
python scripts/run_all.py
```

### Version Management

```bash
# Before major updates, snapshot current version
cp -r ingest/ ingest/versions/v0.9.86/

# Process new version
# Update ingest/ with new files

# Compare results
diff outputs/5_final/ outputs/5_final_v0.9.86/
```

---

## Configuration Updates

### Old (Bad)
```yaml
extraction:
  source_files:
    - ../ib.md              # Files scattered in parent dir
    - ../guide.md
    - ../index.md
```

### New (Good)
```yaml
extraction:
  source_root: ../ingest   # Base directory

  # Content files (full processing)
  content_files:
    - markdown/ib.md
    - markdown/ib_insync_complete_guide.md
    - markdown/ib_insync_futures_update.md

  # Index files (API references only)
  index_files:
    - markdown/index.md

  # Structured data (validation)
  validation_files:
    - json/index_cleaned.json

  # Reference only (skip)
  reference_files:
    - pdf/ib-insync.pdf
```

---

## Detection Logic

### Auto-detect File Types

```python
def detect_file_type(file_path: Path) -> str:
    """
    Automatically detect if file is content vs index.
    """
    content = file_path.read_text()

    # Count code blocks
    code_blocks = len(re.findall(r'```', content))

    # Count API references (e.g., "ib_insync.ib.IB.method")
    api_refs = len(re.findall(r'ib_insync\.\w+\.\w+', content))

    # Heuristics
    if code_blocks > 20:
        return 'content'  # Has lots of examples
    elif 'index' in file_path.name.lower():
        return 'index'    # Filename suggests index
    elif api_refs > 100 and code_blocks < 10:
        return 'index'    # Many refs, few examples = index
    else:
        return 'content'  # Default to content
```

---

## Benefits

### Organization
✅ All source files in one place (`ingest/`)
✅ Clear separation: source → processing → outputs
✅ Easy to add new documentation
✅ Version management for updates

### Processing
✅ Different handling for content vs index files
✅ Prevent duplicate extraction from pointers
✅ Use structured data for validation
✅ Skip reference-only files (PDF)

### Maintenance
✅ Easy to update documentation
✅ Track which files are processed
✅ Metadata describes each file's purpose
✅ Clean git history (source changes separate from code)

---

## Migration Plan

### Step 1: Create Ingest Structure
```bash
mkdir -p ingest/{markdown,json,pdf,versions}
```

### Step 2: Move Files
```bash
mv ib.md ingest/markdown/
mv ib_insync_complete_guide.md ingest/markdown/
mv ib_insync_futures_update.md ingest/markdown/
mv index.md ingest/markdown/
mv index_cleaned.json ingest/json/
mv ib-insync.pdf ingest/pdf/
```

### Step 3: Create Metadata
```bash
# Create ingest/metadata.yaml (see above)
```

### Step 4: Update Config
```bash
# Update dedup/config.yaml with new paths
source_root: ../ingest
```

### Step 5: Update Extraction Logic
```python
# Add file type detection
# Handle index files differently
# Use JSON for validation
```

---

## Example: Handling index.md

```python
# index.md likely looks like:
"""
## API Reference

- ib_insync.ib.IB.connect() - line 45
- ib_insync.ib.IB.disconnect() - line 67
- ib_insync.order.Order - line 234
...
"""

# Don't extract code examples from this!
# Just extract API method names for coverage check

def process_index_file(path):
    content = path.read_text()

    # Extract API references
    pattern = r'(ib_insync\.\w+\.\w+)'
    api_methods = re.findall(pattern, content)

    # Store for validation
    return {
        'type': 'index',
        'api_methods': api_methods,
        'use_for': 'validation'
    }
```

---

## Next Steps

1. ✅ Review this design
2. ⏳ Create ingest/ folder structure
3. ⏳ Move files from root to ingest/
4. ⏳ Create metadata.yaml
5. ⏳ Update config.yaml paths
6. ⏳ Add file type detection logic
7. ⏳ Update extraction to handle different types

This keeps everything organized and ready for future updates! 📁
