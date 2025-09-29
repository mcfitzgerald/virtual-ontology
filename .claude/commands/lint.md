---
allowed-tools: Bash(poetry run mypy:*), Bash(poetry run ruff:*), Bash(wc:*), Bash(grep:*), Read, Edit, TodoWrite
description: Run mypy and ruff with auto-fix capabilities for code quality
---

# Code Quality Check with Auto-Fix

## Current Status
- Python files: !`find . -name "*.py" -not -path "./.venv/*" -not -path "./archive/*" | wc -l`
- Last lint check: !`git log --grep="lint\|style\|type" --oneline -1 | head -1 || echo "Unknown"`
- Poetry environment: !`poetry check 2>&1`

## Instructions

### Phase 1: Type Checking with mypy

1. **Run initial mypy check**:
   ```bash
   poetry run mypy . --show-error-codes --pretty --show-error-context
   ```

2. **Get detailed statistics**:
   ```bash
   poetry run mypy . --html-report mypy-report --linecount-report mypy-linecount 2>/dev/null
   
   # Show type coverage
   poetry run mypy . --any-exprs-report mypy-coverage 2>/dev/null
   if [ -f mypy-coverage/any-exprs.txt ]; then
     echo "Type coverage by module:"
     cat mypy-coverage/any-exprs.txt | head -20
   fi
   ```

3. **Common mypy issues to fix**:
   - Missing type annotations
   - Optional without explicit import
   - Incompatible return types
   - Untyped function definitions
   - Import errors

4. **Categorize mypy errors**:
   ```bash
   # Group errors by type
   poetry run mypy . 2>&1 | grep "error:" | sed 's/.*error: //' | cut -d'[' -f1 | sort | uniq -c | sort -rn
   ```

### Phase 2: Style & Linting with ruff

1. **Run ruff check with auto-fix** (safe fixes only):
   ```bash
   # First, see what will be fixed
   poetry run ruff check . --fix --show-fixes
   
   # Actually apply the fixes
   poetry run ruff check . --fix
   ```

2. **Run ruff format** (code formatting):
   ```bash
   # Check what will be formatted
   poetry run ruff format . --check --diff
   
   # Apply formatting
   poetry run ruff format .
   ```

3. **Check for unsafe fixes** (require manual review):
   ```bash
   # Show unsafe fixes that ruff could apply
   poetry run ruff check . --unsafe-fixes --show-fixes
   ```

4. **Get detailed statistics**:
   ```bash
   # Count issues by rule
   poetry run ruff check . --statistics
   ```

### Phase 3: Advanced Checks

1. **Check for common anti-patterns**:
   ```bash
   # Unused imports (if not caught by ruff)
   poetry run ruff check . --select F401
   
   # Undefined names
   poetry run ruff check . --select F821
   
   # Unused variables
   poetry run ruff check . --select F841
   ```

2. **Security checks**:
   ```bash
   # Hardcoded passwords, SQL injection risks, etc.
   poetry run ruff check . --select S
   ```

3. **Complexity checks**:
   ```bash
   # Cyclomatic complexity
   poetry run ruff check . --select C901
   ```

4. **Documentation checks**:
   ```bash
   # Missing docstrings
   poetry run ruff check . --select D
   ```

### Phase 4: Generate Fix Proposal

Create a structured report:

```markdown
# Lint Report - [DATE]

## Summary
- Files checked: X
- Total issues found: Y
- Auto-fixed: Z
- Manual review needed: W

## Type Checking (mypy)
### Coverage
- Files with type hints: X/Y (Z%)
- Functions typed: X/Y (Z%)
- Line coverage: X%

### Issues by Category
- [Error Type]: X occurrences
  - Example: [file:line] - [error message]

### Critical Issues
[List any import errors or major type conflicts]

## Style & Linting (ruff)
### Auto-Fixed (Already Applied)
- Removed unused imports: X
- Fixed formatting: Y files
- Resolved style issues: Z

### Remaining Issues (Need Manual Review)
#### High Priority
- [Issue]: [File:Line] - [Description]

#### Medium Priority
- [Issue]: [File:Line] - [Description]

#### Low Priority (Style)
- [Issue]: [File:Line] - [Description]

## Code Quality Metrics
### Before
- mypy errors: X
- ruff violations: Y
- Type coverage: Z%

### After Auto-Fix
- mypy errors: X
- ruff violations: Y
- Type coverage: Z%

## Recommended Actions
1. **Immediate fixes** (blocking):
   - [Specific fix needed]

2. **Type annotations to add**:
   - [Function/Class]: [Suggested type]

3. **Refactoring suggestions**:
   - [Complex function]: Reduce complexity
   - [Long file]: Split into modules

## Next Steps
[ ] Review and approve auto-fixes
[ ] Address remaining mypy errors
[ ] Add missing type hints
[ ] Fix complexity issues
[ ] Update docstrings

## Proceed with fixes? [Yes/No/Selective]
```

### Phase 5: Apply Fixes (After Confirmation)

1. **For approved auto-fixes**:
   - Already applied by ruff --fix
   - Verify changes with git diff

2. **For type annotations**:
   ```python
   # Add type hints to functions
   # Example transformations:
   # Before: def process(data):
   # After:  def process(data: List[Dict[str, Any]]) -> bool:
   ```

3. **For manual fixes**:
   - Edit files to resolve issues
   - Re-run checks to verify

4. **Update configuration** (if needed):
   - Add to pyproject.toml:
     ```toml
     [tool.mypy]
     ignore_missing_imports = true
     strict_optional = true
     
     [tool.ruff]
     line-length = 100
     select = ["E", "F", "I", "N", "W"]
     ```

### Phase 6: Verification

1. **Re-run all checks**:
   ```bash
   poetry run mypy .
   poetry run ruff check .
   ```

2. **Verify no regressions**:
   ```bash
   # Run tests to ensure fixes didn't break anything
   poetry run pytest
   ```

3. **Update CHANGELOG.md**:
   - Add entry about code quality improvements
   - Note type coverage increase
   - Document any significant refactoring

## Configuration Files

### Recommended pyproject.toml settings:
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Set to true for strict
ignore_missing_imports = true
follow_imports = "normal"
show_error_codes = true
pretty = true

[tool.ruff]
target-version = "py311"
line-length = 100
indent-width = 4

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "W",   # pycodestyle warnings
    "B",   # flake8-bugbear
    "C90", # mccabe complexity
    "D",   # pydocstyle (optional)
    "S",   # flake8-bandit security
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "D100",  # Missing docstring in public module
    "D104",  # Missing docstring in public package
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

## Important Notes
- Auto-fixes are generally safe but review with `git diff`
- Some type errors may require design changes
- Don't suppress errors without understanding them
- Keep type coverage above 80% for maintainability
- Run lint checks before commits (consider pre-commit hooks)
- Document any intentional type ignores with comments