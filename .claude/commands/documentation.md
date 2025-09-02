---
allowed-tools: Bash(find:*), Bash(grep:*), Bash(~/.local/bin/poetry run sphinx-build:*), Bash(pandoc:*), Bash(git:*), Bash(ls:*), Bash(tree:*), Read, Write, Edit, TodoWrite, WebFetch, Task
description: Ensure all required docs exist and are synchronized with codebase
---

# Documentation Management & Synchronization

## Pre-flight Check
- Last commit: !`git log -1 --oneline`
- Uncommitted changes: !`git status --porcelain | wc -l` files
- CHANGELOG updated: !`head -20 CHANGELOG.md | grep -E "^## \[Unreleased\]" -A 5 | head -10`
- Current date: !`date +%Y-%m-%d`

## Workflow Integration Check

If uncommitted changes exist, suggest:
```
Please run `/commit` first to capture recent changes in CHANGELOG.md
This will provide context for documentation updates.
```

## Required Documentation Checklist

### Core Documents Status
1. **README.md**: !`test -f README.md && echo "✅ EXISTS" || echo "❌ MISSING"`
2. **CHANGELOG.md**: !`test -f CHANGELOG.md && echo "✅ EXISTS" || echo "❌ MISSING"`
3. **LICENSE**: !`test -f LICENSE && echo "✅ EXISTS" || echo "❌ MISSING"`
4. **docs/DOCS_TOC.md**: !`test -f docs/DOCS_TOC.md && echo "✅ EXISTS" || echo "❌ MISSING"`
5. **Architecture doc**: !`find docs -name "*architecture*" -o -name "*ARCHITECTURE*" | head -1 | xargs -I {} test -f {} && echo "✅ EXISTS" || echo "❌ MISSING"`

### LLM-Ready Documentation
- Directory exists: !`test -d docs/llm-ready && echo "✅ EXISTS" || echo "❌ MISSING"`
- Files present: !`ls docs/llm-ready/*.md 2>/dev/null | wc -l` markdown files

### API Documentation
- Sphinx source: !`test -d docs/sphinx-source && echo "✅ EXISTS" || echo "❌ MISSING"`
- AutoAPI configured: !`grep -q "autoapi.extension" docs/sphinx-source/conf.py 2>/dev/null && echo "✅ CONFIGURED" || echo "❌ NOT CONFIGURED"`
- Build directory: !`test -d docs/build && echo "✅ EXISTS" || echo "❌ MISSING"`

## Instructions

### Phase 1: Analyze Recent Changes
1. **Read CHANGELOG.md for recent updates**:
   - Identify new features, changes, fixes
   - Note any architectural changes
   - Check for API modifications

2. **Analyze code changes since last doc update**:
   ```bash
   # Find Python files modified in last 7 days
   find . -name "*.py" -mtime -7 -not -path "./archive/*" -not -path "./.venv/*" | head -20
   
   # Check for new modules/classes
   git diff HEAD~5 --name-only | grep "\.py$" | head -20
   ```

### Phase 2: Verify Documentation Requirements

#### A. README.md Validation
1. **Check Quick Start section**:
   - Verify installation instructions match pyproject.toml
   - Test code examples actually work
   - Ensure import statements are correct
   - Validate SimPy environment setup

2. **Check API examples**:
   - Match current class/function signatures
   - Use correct parameter names
   - Include proper error handling

3. **Verify links**:
   - Documentation links point to existing files
   - External links are valid
   - Relative paths are correct

#### B. DOCS_TOC.md Maintenance
1. **Update file tree**:
   ```bash
   tree docs -I "__pycache__|*.pyc|build" -L 3
   ```

2. **Verify all listed files exist**:
   ```bash
   # Extract file paths from TOC and verify
   grep -E "^\s*[├└│].*\.(md|yaml|yml|rst)$" docs/DOCS_TOC.md | while read line; do
     # Check file existence
   done
   ```

#### C. Architecture Documentation
1. **Verify architecture matches code**:
   - Check class hierarchies
   - Validate module dependencies
   - Ensure design patterns are current

2. **Update diagrams** (if present):
   - Component relationships
   - Data flow
   - System boundaries

### Phase 3: Regenerate API Documentation

1. **Clean previous build**:
   ```bash
   rm -rf docs/build/
   rm -rf docs/sphinx-source/autoapi/
   ```

2. **Run Sphinx with AutoAPI**:
   ```bash
   cd docs/sphinx-source
   ~/.local/bin/poetry run sphinx-build -b html . ../build/html
   ```

3. **Generate LLM-ready version**:
   ```bash
   # Convert RST to Markdown
   find docs/build -name "*.rst" -exec pandoc -f rst -t markdown {} -o {}.md \;
   
   # Or use sphinx-llms-txt if configured
   ~/.local/bin/poetry run sphinx-build -b llms-txt docs/sphinx-source docs/build/llm-text
   ```

4. **Create consolidated API reference**:
   - Combine module docs into single file
   - Add navigation anchors
   - Format for LLM consumption

### Phase 4: Synchronize Documentation

1. **Update code examples in docs**:
   - Extract code blocks from documentation
   - Validate against current API
   - Fix any discrepancies

2. **Cross-reference with CHANGELOG**:
   - Ensure all changes are reflected in docs
   - Add version notes where applicable
   - Update "What's New" sections

3. **Update configuration examples**:
   ```bash
   # Check YAML examples match schema
   for yaml in docs/llm-ready/yaml-examples/*.yaml; do
     echo "Validating: $yaml"
     # Verify structure matches code expectations
   done
   ```

### Phase 5: Documentation Coverage Analysis

1. **Find undocumented modules**:
   ```bash
   # Find Python files without corresponding docs
   for py in $(find twin_model -name "*.py" -not -name "__*"); do
     module=$(echo $py | sed 's/.py$//' | tr '/' '.')
     if ! grep -q "$module" docs/llm-ready/*.md 2>/dev/null; then
       echo "Undocumented: $module"
     fi
   done
   ```

2. **Check docstring coverage**:
   ```bash
   # Use interrogate or similar tool
   ~/.local/bin/poetry run interrogate -v twin_model/
   ```

### Phase 6: Generate Documentation Proposal

Create a structured proposal:

```markdown
# Documentation Update Proposal - [DATE]

## Recent Changes (from CHANGELOG)
- [List relevant changes]

## Documentation Status
### ✅ Complete
- [List up-to-date docs]

### ⚠️ Needs Update
- [File]: [What needs updating]

### ❌ Missing
- [Required doc]: [What it should contain]

## Code Coverage
- Modules documented: X/Y (Z%)
- Docstring coverage: X%
- Examples tested: X/Y

## Proposed Actions
1. **Immediate Updates**:
   - [File]: [Specific changes needed]

2. **New Documentation**:
   - [File to create]: [Purpose]

3. **API Regeneration**:
   - [ ] Rebuild Sphinx docs
   - [ ] Update LLM-ready docs
   - [ ] Verify examples

4. **Link Fixes**:
   - [Broken link]: [Correct target]

## Estimated Time: X minutes

## Proceed? [Yes/No/Revise]
```

### Phase 7: Execute Updates (After Confirmation)

1. **Create backup**:
   ```bash
   cp -r docs/ docs.backup.$(date +%Y%m%d)/
   ```

2. **Apply updates**:
   - Edit files as proposed
   - Regenerate API docs
   - Update TOC and indexes

3. **Validate changes**:
   - Test all code examples
   - Verify internal links
   - Check formatting

4. **Clean up**:
   ```bash
   rm -rf docs.backup.*/  # After verification
   ```

5. **Update CHANGELOG.md**:
   - Add documentation updates entry

## Special Considerations

### For LLM-Ready Documentation
- Use numbered files (01-, 02-, etc.) for clear learning path
- Include complete examples, not fragments
- Add context and prerequisites
- Explain "why" not just "how"

### For API Reference
- Include type hints in signatures
- Show return types clearly
- Provide usage examples for each class/function
- Document exceptions raised

### For Architecture Documentation
- Keep diagrams simple and text-based when possible
- Explain design decisions
- Document trade-offs
- Include extension points

## Output Standards
- All markdown should follow CommonMark spec
- YAML examples should be valid and parse correctly
- Code examples should be executable
- File paths should be absolute from project root

## Important Notes
- Always backup before major changes
- Test code examples in actual environment
- Preserve historical documentation in archive if needed
- Keep documentation version-synchronized with code
- Update DOCS_TOC.md after any structural changes