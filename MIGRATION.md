# Migration Guide: Organize Source Files into Ingest Folder

**Date:** 2025-11-15
**Purpose:** Move source documentation from root to organized ingest/ structure

---

## Current State (Before Migration)

```
ib_insync_docs/
├── ib.md                              ← Scattered in root
├── ib_insync_complete_guide.md
├── ib_insync_futures_update.md
├── index.md
├── ib-insync.pdf
├── index_cleaned.json
├── dedup/
└── agent/
```

## Target State (After Migration)

```
ib_insync_docs/
├── ingest/                            ← All source files organized
│   ├── README.md
│   ├── metadata.yaml
│   ├── markdown/
│   │   ├── ib.md
│   │   ├── ib_insync_complete_guide.md
│   │   ├── ib_insync_futures_update.md
│   │   └── index.md
│   ├── json/
│   │   └── index_cleaned.json
│   └── pdf/
│       └── ib-insync.pdf
├── dedup/
└── agent/
```

---

## Migration Steps

### Step 1: Move Files (DO NOT RUN YET - For Future)

```bash
# Navigate to repo root
cd /home/user/ib_insync_docs

# Move markdown files
mv ib.md ingest/markdown/
mv ib_insync_complete_guide.md ingest/markdown/
mv ib_insync_futures_update.md ingest/markdown/
mv index.md ingest/markdown/

# Move JSON files
mv index_cleaned.json ingest/json/ 2>/dev/null || echo "File not found, skipping"

# Move PDF files
mv ib-insync.pdf ingest/pdf/
```

### Step 2: Verify Files Moved

```bash
# Check ingest structure
ls -la ingest/markdown/
ls -la ingest/json/
ls -la ingest/pdf/

# Should see:
# ingest/markdown/: 4 .md files
# ingest/json/: 1 .json file (if exists)
# ingest/pdf/: 1 .pdf file
```

### Step 3: Verify Config Points to Ingest

```bash
# dedup/config.yaml should already be updated:
grep "source_root" dedup/config.yaml
# Should show: source_root: ../ingest
```

### Step 4: Test Extraction (After Implementation)

```bash
cd dedup
python scripts/01_extract.py

# Should read from ingest/ folder
# Check outputs/1_extracted/ for results
```

---

## Why Not Migrate Now?

**Wait to migrate files until extraction logic is implemented because:**

1. **Current state works** - Files in root, config points to ../file.md
2. **Haven't implemented extractor yet** - Can't test if migration works
3. **Git history cleaner** - One commit: migrate files + update extractor together
4. **Avoid breaking changes** - Keep working state until ready to switch

---

## When to Migrate

**Migrate during Phase 1 (Extraction) implementation:**

```
Phase 1 Steps:
1. Implement extractor with ingest/ support ← Implement first
2. Test extractor with files in root          ← Test current state
3. Migrate files to ingest/                   ← Then migrate
4. Test extractor with new structure          ← Verify works
5. Commit: "feat: Migrate source files to ingest folder"
```

---

## Alternative: Symbolic Links (If Needed)

If you want to keep files in root for compatibility:

```bash
# Create symlinks from root to ingest
ln -s ingest/markdown/ib.md ib.md
ln -s ingest/markdown/ib_insync_complete_guide.md ib_insync_complete_guide.md
# etc.
```

**Not recommended** - Better to have single source of truth in ingest/

---

## Handling File Type Detection

### Content Files (Extract Everything)

Files that will be processed fully:
- `ingest/markdown/ib.md`
- `ingest/markdown/ib_insync_complete_guide.md`
- `ingest/markdown/ib_insync_futures_update.md`

### Index Files (API Names Only)

Files that are just indexes/pointers:
- `ingest/markdown/index.md`

**Extraction logic will:**
- Detect file type from metadata.yaml
- Skip code extraction for index files
- Extract only API method names for validation

### Example Code

```python
# dedup/src/extractors.py (to be implemented)

def load_file_metadata(file_path):
    """Load metadata to determine file type."""
    metadata = yaml.load('ingest/metadata.yaml')
    file_name = file_path.name

    file_info = metadata['files']['markdown'].get(file_name)
    return file_info.get('type', 'content')  # Default to content

def extract_from_file(file_path):
    """Extract content based on file type."""
    file_type = load_file_metadata(file_path)

    if file_type == 'content':
        return extract_full_content(file_path)
    elif file_type == 'index':
        return extract_api_references_only(file_path)
    elif file_type == 'structured_data':
        return parse_and_validate(file_path)
    else:  # reference
        return None  # Skip
```

---

## Validation After Migration

```bash
# Verify all files accounted for
python -c "
import yaml
from pathlib import Path

metadata = yaml.safe_load(Path('ingest/metadata.yaml').read_text())

for category in ['markdown', 'json', 'pdf']:
    for filename in metadata['files'][category].keys():
        filepath = Path(f'ingest/{category}/{filename}')
        exists = '✓' if filepath.exists() else '✗'
        print(f'{exists} {filepath}')
"

# Should show all ✓
```

---

## Git Workflow

### Current Commit (Now)

```bash
git add ingest/ dedup/config.yaml MIGRATION.md
git commit -m "feat: Add ingest folder structure for organized source data"
```

### Future Commit (During Phase 1)

```bash
# After implementing extractor and testing
mv ib.md ingest/markdown/
# ... move all files

git add ingest/ ib.md ib_insync*.md index.md ib-insync.pdf
git commit -m "feat: Migrate source files to ingest folder

- Move all markdown files to ingest/markdown/
- Move PDF to ingest/pdf/
- Move JSON to ingest/json/
- Extractor now reads from organized structure
- All tests passing with new structure
"
```

---

## Rollback Plan

If migration causes issues:

```bash
# Rollback git commit
git revert HEAD

# Or manually move files back
mv ingest/markdown/*.md .
mv ingest/pdf/*.pdf .
mv ingest/json/*.json .
```

---

## Summary

**Now:**
- ✅ ingest/ structure created
- ✅ metadata.yaml configured
- ✅ config.yaml updated to use ingest/
- ✅ Files still in root (working state)

**Later (Phase 1):**
- ⏳ Implement extractor with file type handling
- ⏳ Test with current file locations
- ⏳ Migrate files to ingest/
- ⏳ Test with new structure
- ⏳ Commit migration

**Benefits When Done:**
- 📁 Organized source data
- 🔍 Different handling for content vs index files
- ➕ Easy to add new documentation
- 📦 Version management ready
- 🎯 Clean separation: source → processing → outputs

---

**Do not migrate files yet - wait until Phase 1 implementation is ready to test!**
