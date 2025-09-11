---
allowed-tools: Bash(find:*), Bash(grep:*), Bash(~/.local/bin/poetry run sphinx-build:*), Bash(~/.local/bin/poetry run interrogate:*), Bash(pandoc:*), Bash(git:*), Bash(ls:*), Bash(tree:*), Bash(test:*), Bash(cp:*), Bash(rm:*), Bash(cd:*), Bash(echo:*), Read, Write, Edit, TodoWrite, WebFetch, Task
description: Ensure all required docs exist and are synchronized with codebase
---

# Documentation Management & Synchronization

## Pre-flight Check
- Last commit: !`git log -1 --oneline`
- Uncommitted changes: !`git status --porcelain`
- CHANGELOG updated: Check CHANGELOG.md manually for [Unreleased] section
- Current date: Check system date

## Workflow Integration Check

If uncommitted changes exist, suggest:
```
Please run `/commit` first to capture recent changes in CHANGELOG.md
This will provide context for documentation updates.
```

## Required Documentation Checklist

### Core Documents Status
1. **README.md**: !`ls README.md`
2. **CHANGELOG.md**: !`ls CHANGELOG.md`
3. **LICENSE**: !`ls LICENSE`
4. **docs/DOCS_TOC.md**: !`ls docs/DOCS_TOC.md`
5. **Architecture doc**: !`find docs -name "*architecture*" -o -name "*ARCHITECTURE*"`

### LLM-Ready Documentation
- Directory exists: !`ls -d docs/llm-ready`
- Files present: !`ls docs/llm-ready/*.md`
- **User Guide**: !`ls docs/llm-ready/00-user-guide.md`
- **Quick Start**: !`ls docs/llm-ready/02-quickstart-api.md`
- **Config Reference**: !`ls docs/llm-ready/05-configuration-reference.md`

### API Documentation
- Sphinx source: !`ls -d docs/sphinx-source`
- AutoAPI configured: !`grep "autoapi.extension" docs/sphinx-source/conf.py`
- Build directory: !`ls -d docs/build`

## Instructions

**Note**: The sphinx-llms-txt extension listed in conf.py is experimental and may not be installed or functional. The primary approach for generating LLM-ready documentation is through pandoc conversion and cleanup scripts as detailed in Phase 3.

### Phase 1: Analyze Recent Changes
1. **Read CHANGELOG.md for recent updates**:
   - Identify new features, changes, fixes
   - Note any architectural changes
   - Check for API modifications

2. **Analyze code changes since last doc update**:
   ```bash
   # Find Python files modified in last 7 days
   find . -name "*.py" -mtime -7 -not -path "./archive/*" -not -path "./.venv/*"
   
   # Check for new modules/classes
   git diff HEAD~5 --name-only
   ```

### Phase 2: Verify and Update User Guide

#### A. User Guide Validation (00-user-guide.md)
1. **Check examples match current files**:
   ```bash
   # Verify ontology examples
   grep -A5 "ontology.yaml" docs/llm-ready/00-user-guide.md
   # Compare with actual: ontology/filling_line_ontology.yaml
   
   # Verify manifest examples
   grep -A5 "manifest.yaml" docs/llm-ready/00-user-guide.md
   # Compare with actual: manifests/equipment_manifest.yaml
   
   # Verify config examples
   grep -A5 "parameters.yaml" docs/llm-ready/00-user-guide.md
   # Compare with actual: config/tunable_parameters.yaml
   ```

2. **Update code examples**:
   - Ensure Python examples use current API
   - Verify import statements are correct
   - Test that examples actually run

3. **Check for new features**:
   - Review CHANGELOG for new capabilities
   - Add sections for new features
   - Update troubleshooting for new error types

### Phase 3: Verify Other Documentation

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
   grep -E "^\s*[├└│].*\.(md|yaml|yml|rst)$" docs/DOCS_TOC.md
   # Then manually check file existence
   ```

### Phase 4: Architecture Documentation
1. **Verify architecture matches code**:
   - Check class hierarchies
   - Validate module dependencies
   - Ensure design patterns are current

2. **Update diagrams** (if present):
   - Component relationships
   - Data flow
   - System boundaries

### Phase 5: Regenerate API Documentation

1. **Clean previous build**:
   ```bash
   rm -rf docs/build/
   rm -rf docs/sphinx-source/autoapi/
   ```

2. **Run Sphinx with AutoAPI**:
   ```bash
   cd docs/sphinx-source
   ~/.local/bin/poetry run sphinx-build -b html . ../build/html
   cd ../..
   ```

3. **Generate LLM-ready version from AutoAPI**:
   ```bash
   # Find all generated RST files from AutoAPI
   find docs/sphinx-source/autoapi -name "*.rst" -type f
   
   # Convert RST to clean Markdown with directive removal
   for rst_file in $(find docs/sphinx-source/autoapi -name "*.rst" -type f); do
       # Get relative path and create markdown filename
       rel_path=${rst_file#docs/sphinx-source/autoapi/}
       md_file="docs/llm-ready/api/${rel_path%.rst}.md"
       
       # Create directory if needed
       mkdir -p $(dirname "$md_file")
       
       # Convert with pandoc, stripping Sphinx directives
       pandoc -f rst -t gfm \
              --wrap=none \
              --no-highlight \
              "$rst_file" -o "$md_file" 2>/dev/null || echo "Failed: $rst_file"
   done
   ```

4. **Clean generated Markdown files**:
   ```bash
   # Remove common Sphinx/RST artifacts from generated files
   for md_file in $(find docs/llm-ready -name "*.md" -type f); do
       # Remove Sphinx cross-references like :class:`ClassName`
       sed -i '' -E 's/:([a-z]+):`([^`]+)`/`\2`/g' "$md_file"
       
       # Remove module paths like ~twin_model.module
       sed -i '' -E 's/~[a-zA-Z_]+\.[a-zA-Z_.]+//' "$md_file"
       
       # Remove autoclass/automodule directives
       sed -i '' '/^.. auto(class|module|function)::/d' "$md_file"
       
       # Remove :param name: and :type name: lines
       sed -i '' -E '/^[[:space:]]*:(param|type|returns|rtype|raises)[[:space:]]+/d' "$md_file"
       
       # Clean up excessive blank lines
       sed -i '' '/^$/N;/^\n$/d' "$md_file"
   done
   ```

5. **Create consolidated API reference**:
   ```bash
   # Combine cleaned API docs into single reference
   cat > docs/llm-ready/03-complete-api-reference.md << 'EOF'
   # Complete API Reference
   
   This document consolidates all API documentation for the Twin Model.
   
   EOF
   
   # Append all module docs
   for md_file in $(find docs/llm-ready/api -name "*.md" | sort); do
       echo "## $(basename $md_file .md)" >> docs/llm-ready/03-complete-api-reference.md
       echo "" >> docs/llm-ready/03-complete-api-reference.md
       cat "$md_file" >> docs/llm-ready/03-complete-api-reference.md
       echo "" >> docs/llm-ready/03-complete-api-reference.md
   done
   ```

### Phase 6: Synchronize Documentation

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
   ls docs/llm-ready/yaml-examples/*.yaml
   # Then validate each file's structure manually
   ```

### Phase 7: Validate LLM-Ready Documentation

1. **Check for RST/Sphinx artifacts**:
   ```bash
   # Detect common Sphinx directives that shouldn't be in markdown
   echo "Checking for Sphinx/RST artifacts in LLM-ready docs..."
   
   # Check for role directives
   grep -n -E ':[a-z]+:`[^`]+`' docs/llm-ready/*.md && echo "Found role directives to clean"
   
   # Check for autoapi directives
   grep -n -E '\.\. (auto|module|class|function)::' docs/llm-ready/*.md && echo "Found autoapi directives"
   
   # Check for :param: style docstring formatting
   grep -n -E '^[[:space:]]*:(param|type|returns|rtype|raises)' docs/llm-ready/*.md && echo "Found docstring directives"
   
   # Check for tilde prefixes
   grep -n '~[a-zA-Z_]' docs/llm-ready/*.md && echo "Found tilde prefixes"
   ```

2. **Validate markdown syntax**:
   ```bash
   # Check for broken code blocks
   for file in docs/llm-ready/*.md; do
       awk '/^```/ {count++} END {if (count % 2 != 0) print FILENAME ": Unclosed code block"}' "$file"
   done
   
   # Check for valid markdown structure
   # (Optional: use markdownlint if available)
   ```

3. **Test code examples**:
   ```bash
   # Extract and validate Python code blocks
   for file in docs/llm-ready/*.md; do
       echo "Checking code examples in $file"
       # Extract code blocks and check basic syntax
       awk '/^```python$/,/^```$/ {if (!/^```/) print}' "$file" > /tmp/code_check.py
       if [ -s /tmp/code_check.py ]; then
           python -m py_compile /tmp/code_check.py 2>/dev/null || echo "  Syntax issues in $file"
       fi
   done
   ```

### Phase 8: Documentation Coverage Analysis

1. **Find undocumented modules**:
   ```bash
   # Find Python files
   find twin_model -name "*.py" -not -name "__*"
   # Then check if each module is documented in docs/llm-ready/*.md
   ```

2. **Check docstring coverage**:
   ```bash
   # Use interrogate or similar tool
   ~/.local/bin/poetry run interrogate -v twin_model/
   ```

### Phase 9: Generate Documentation Proposal

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

### Phase 10: Execute Updates (After Confirmation)

1. **Create backup**:
   ```bash
   # Create backup with timestamp
   cp -r docs/ docs.backup.YYYYMMDD/
   # Replace YYYYMMDD with current date
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

## Automated Cleanup Scripts

### Clean Existing LLM-Ready Documentation
Run this script to clean any existing LLM-ready markdown files from Sphinx/RST artifacts:

```bash
#!/bin/bash
# cleanup_llm_docs.sh

echo "=== Cleaning LLM-Ready Documentation ==="

# Process all markdown files in llm-ready directory
for md_file in docs/llm-ready/*.md; do
    if [ -f "$md_file" ]; then
        echo "Cleaning: $(basename $md_file)"
        
        # Create backup
        cp "$md_file" "${md_file}.bak"
        
        # Remove Sphinx cross-references like :class:`ClassName`
        sed -i '' -E 's/:([a-z]+):`([^`]+)`/`\2`/g' "$md_file"
        
        # Remove module paths like ~twin_model.module
        sed -i '' -E 's/~[a-zA-Z_]+\.[a-zA-Z_.]+//g' "$md_file"
        
        # Remove autoclass/automodule directives
        sed -i '' '/^[[:space:]]*\.\. auto(class|module|function|method)::/d' "$md_file"
        
        # Remove :param name: and :type name: lines
        sed -i '' -E '/^[[:space:]]*:(param|type|returns|rtype|raises|note|warning|seealso)[[:space:]]+/d' "$md_file"
        
        # Remove >>> doctest lines
        sed -i '' '/^[[:space:]]*>>>/d' "$md_file"
        
        # Remove .. note:: and similar directives
        sed -i '' '/^[[:space:]]*\.\. (note|warning|danger|important|tip|hint|caution|error|attention)::/d' "$md_file"
        
        # Clean up .. code-block:: directives
        sed -i '' 's/^[[:space:]]*\.\. code-block::.*/```/g' "$md_file"
        
        # Remove :ref: references
        sed -i '' -E 's/:ref:`([^`]+)`/\1/g' "$md_file"
        
        # Clean up excessive blank lines (more than 2 consecutive)
        sed -i '' '/^$/N;/^\n$/N;/^\n\n$/d' "$md_file"
        
        # Compare with backup
        if diff -q "$md_file" "${md_file}.bak" > /dev/null; then
            echo "  No changes needed"
            rm "${md_file}.bak"
        else
            echo "  ✓ Cleaned artifacts"
            # Keep backup for review - remove later if satisfied
        fi
    fi
done

echo "=== Cleanup Complete ==="
echo "Backups created with .bak extension - review and remove when satisfied"
```

## Quality Checks for LLM-Ready Documentation

### Automated Validation Script
Create and run this validation script to ensure clean documentation:

```bash
#!/bin/bash
# validate_llm_docs.sh

echo "=== LLM Documentation Quality Check ==="
ERRORS=0

# 1. Check for Sphinx/RST artifacts
echo "Checking for documentation artifacts..."
if grep -q -E ':[a-z]+:`[^`]+`' docs/llm-ready/*.md 2>/dev/null; then
    echo "❌ Found Sphinx role directives"
    ERRORS=$((ERRORS + 1))
fi

if grep -q -E '\.\. (auto|module|class|function)::' docs/llm-ready/*.md 2>/dev/null; then
    echo "❌ Found autoapi directives"
    ERRORS=$((ERRORS + 1))
fi

if grep -q -E '^[[:space:]]*:(param|type|returns|rtype)' docs/llm-ready/*.md 2>/dev/null; then
    echo "❌ Found parameter directives"
    ERRORS=$((ERRORS + 1))
fi

# 2. Check code block formatting
echo "Validating code blocks..."
for file in docs/llm-ready/*.md; do
    if [ -f "$file" ]; then
        count=$(grep -c '^```' "$file")
        if [ $((count % 2)) -ne 0 ]; then
            echo "❌ Unclosed code block in $(basename $file)"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

# 3. Check for broken internal links
echo "Checking internal links..."
grep -o '\[.*\]([^)]*\.md[^)]*)' docs/llm-ready/*.md | while read -r link; do
    target=$(echo "$link" | sed 's/.*(\([^)]*\)).*/\1/')
    if [[ "$target" == /* ]] || [[ "$target" == ../* ]]; then
        if [ ! -f "docs/llm-ready/$target" ]; then
            echo "❌ Broken link: $target"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

if [ $ERRORS -eq 0 ]; then
    echo "✅ All quality checks passed!"
else
    echo "⚠️ Found $ERRORS issues to fix"
fi
```

### Manual Review Checklist
- [ ] No RST/Sphinx markup visible
- [ ] Code examples are executable
- [ ] Internal links work correctly
- [ ] Formatting is consistent
- [ ] No generated boilerplate text

## Special Considerations

### For User Guide (00-user-guide.md)
- Keep examples simple and self-contained
- Show complete file contents, not fragments
- Include working code that users can copy
- Provide clear step-by-step instructions
- Add troubleshooting for common errors
- Update when API changes occur

### For LLM-Ready Documentation
- Use numbered files (01-, 02-, etc.) for clear learning path
- Include complete examples, not fragments
- Add context and prerequisites
- Explain "why" not just "how"
- Ensure no Sphinx-specific markup remains
- Validate all code examples compile/run

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