---
allowed-tools: Bash(find:*), Bash(ls:*), Bash(grep:*), Bash(rg:*), Bash(tree:*), Bash(git:*), Bash(~/.local/bin/poetry:*), Bash(stat:*), Bash(wc:*), Bash(du:*), Read, Write, Edit, TodoWrite
description: Aggressively clean project by analyzing timestamps, finding unused code, and managing Poetry environment
---

# Aggressive Project Housekeeping

## Context Analysis
- Current date: !`date +%Y-%m-%d`
- Project size: !`find . -type f -name "*.py" | wc -l` Python files
- Disk usage: !`du -sh . 2>/dev/null | cut -f1`
- Git status: !`git status --porcelain | wc -l` uncommitted changes
- Poetry status: !`~/.local/bin/poetry check 2>&1`
- Last cleanup: Check archive/ directory manually

## Instructions

### IMPORTANT: Generate Proposal First
**Never execute deletions or major changes without user confirmation.**

### Phase 1: Timestamp Analysis
1. **Find stale files** (not modified in 30+ days):
   ```bash
   find . -type f -name "*.py" -mtime +30 -not -path "./archive/*" -not -path "./.venv/*" | head -20
   ```

2. **Find files never committed to git**:
   ```bash
   git ls-files --others --exclude-standard | grep -E "\.(py|yaml|yml|md)$" | head -20
   ```

3. **Find files not accessed recently** (60+ days):
   ```bash
   find . -type f -name "*.py" -atime +60 -not -path "./archive/*" -not -path "./.venv/*" | head -20
   ```

4. **Check for old backup files**:
   ```bash
   find . -type f \( -name "*~" -o -name "*.bak" -o -name "*.backup" -o -name "*.old" -o -name "*_old.*" -o -name "*_backup.*" \) -not -path "./archive/*"
   ```

### Phase 2: Unused Code Detection
1. **Find orphaned test files**:
   ```bash
   # Find test files outside of tests directory
   find . -name "test_*.py" -not -path "./*/tests/*" -not -path "./archive/*"
   
   # Find test files for non-existent modules
   for test in $(find . -path "./*/tests/*" -name "test_*.py"); do
     module=$(basename "$test" | sed 's/test_//;s/.py$//')
     if ! find . -name "${module}.py" -not -path "./*/tests/*" | grep -q .; then
       echo "Orphaned test: $test"
     fi
   done
   ```

2. **Find duplicate or versioned files**:
   ```bash
   # Find V2, V3, FIXED, etc. suffixes
   find . -type f -name "*_v[0-9].*" -o -name "*V[0-9].*" -o -name "*_fixed.*" -o -name "*_FIXED.*" -o -name "*_new.*" -o -name "*_NEW.*" | grep -v archive
   
   # Find potential duplicates by similar names
   find . -name "*.py" -not -path "./archive/*" -not -path "./.venv/*" | sed 's/.*\///' | sort | uniq -d
   ```

3. **Find commented-out code blocks** (>5 lines):
   ```bash
   # Find files with large commented sections
   for file in $(find . -name "*.py" -not -path "./archive/*" -not -path "./.venv/*"); do
     commented=$(grep -c "^[[:space:]]*#" "$file" 2>/dev/null || echo 0)
     total=$(wc -l < "$file" 2>/dev/null || echo 1)
     if [ "$commented" -gt 5 ] && [ "$total" -gt 0 ]; then
       ratio=$((commented * 100 / total))
       if [ "$ratio" -gt 20 ]; then
         echo "$file: ${ratio}% commented (${commented}/${total} lines)"
       fi
     fi
   done | head -10
   ```

4. **Find TODO/FIXME comments older than 14 days**:
   ```bash
   # Check git blame for old TODOs
   grep -r "TODO\|FIXME\|HACK\|XXX" --include="*.py" . 2>/dev/null | head -20
   ```

### Phase 3: Poetry Environment Cleanup
1. **Check dependency usage**:
   ```bash
   # List all installed packages
   ~/.local/bin/poetry show --no-ansi
   
   # Find potentially unused dependencies
   ~/.local/bin/poetry show --tree --no-ansi | grep "^\w" | cut -d' ' -f1 > /tmp/deps.txt
   for dep in $(cat /tmp/deps.txt); do
     # Convert package name to import name (handle common cases)
     import_name=$(echo $dep | tr '-' '_' | tr '[:upper:]' '[:lower:]')
     if ! grep -r "import $import_name\|from $import_name" --include="*.py" . >/dev/null 2>&1; then
       echo "Potentially unused: $dep"
     fi
   done
   ```

2. **Check for outdated packages**:
   ```bash
   ~/.local/bin/poetry show --outdated --no-ansi
   ```

3. **Check poetry.lock consistency**:
   ```bash
   ~/.local/bin/poetry lock --check
   ```

### Phase 4: File System Cleanup
1. **Find and count cache files**:
   ```bash
   find . -type d -name "__pycache__" | wc -l
   find . -type f -name "*.pyc" -o -name "*.pyo" | wc -l
   ```

2. **Find empty directories**:
   ```bash
   find . -type d -empty -not -path "./.git/*" -not -path "./archive/*"
   ```

3. **Find build artifacts**:
   ```bash
   find . -type d \( -name "dist" -o -name "build" -o -name "*.egg-info" \) -not -path "./archive/*"
   ```

4. **Find OS-specific junk files**:
   ```bash
   find . -type f \( -name ".DS_Store" -o -name "Thumbs.db" -o -name "desktop.ini" \) 
   ```

### Phase 5: Generate Proposal

Create a comprehensive proposal with:

1. **IMMEDIATE DELETIONS** (safe to remove):
   - __pycache__ directories
   - *.pyc, *.pyo files
   - .DS_Store, Thumbs.db
   - Empty directories
   - *~ backup files

2. **ARCHIVE CANDIDATES** (move to archive/YYYYMMDD_housekeeping/):
   - Files not modified in 30+ days
   - Versioned files (V2, FIXED, etc.)
   - Old test files
   - Files with >50% commented code

3. **MANUAL REVIEW NEEDED**:
   - Potentially unused dependencies
   - Orphaned test files
   - Files never committed to git
   - Old TODO/FIXME comments

4. **METRICS**:
   - Files to delete: X files, Y MB
   - Files to archive: X files, Y MB
   - Dependencies to remove: X packages
   - Estimated space saved: Y MB

### Phase 6: Execute (After Confirmation)

1. **Create archive directory**:
   ```bash
   archive_dir="archive/$(date +%Y%m%d)_housekeeping"
   mkdir -p "$archive_dir"
   ```

2. **Archive files** (based on user confirmation)

3. **Clean caches**:
   ```bash
   find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
   find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
   ```

4. **Update Poetry**:
   ```bash
   ~/.local/bin/poetry lock --no-update
   ~/.local/bin/poetry install --sync
   ```

5. **Update .gitignore** if new patterns found

6. **Update CHANGELOG.md** with housekeeping summary

## Output Format

Present findings as a structured proposal:

```markdown
# Housekeeping Proposal - [DATE]

## Summary
- Current project size: X files, Y MB
- Proposed deletions: X files, Y MB
- Proposed archives: X files, Y MB
- Estimated final size: X files, Y MB

## Immediate Deletions (Safe)
[List files with reasons]

## Archive Candidates
[List files with last modified date and reason]

## Dependency Cleanup
[List unused/outdated packages]

## Manual Review Required
[List items needing user decision]

## Proceed? [Yes/No/Revise]
```

## Important Notes
- Always create archive before deletion
- Never delete without user confirmation
- Keep audit trail in CHANGELOG.md
- Preserve anything that might be referenced in documentation
- Be extra careful with configuration files