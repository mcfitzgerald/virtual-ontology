---
allowed-tools: Bash(semgrep:*), Bash(grep:*), Bash(find:*), Bash(test:*), Read, Write, Edit, TodoWrite
description: Detect hardcodes and anti-patterns using custom semgrep rules
---

# Code Sweep - Anti-Pattern and Hardcode Detection

## Pre-flight Check
- Semgrep installed: !`which semgrep && semgrep --version | head -1 || echo "❌ NOT INSTALLED"`
- Custom rules exist: !`test -d .semgrep/rules && echo "✅ EXISTS" || echo "❌ MISSING"`
- Python files to scan: !`find . -name "*.py" -not -path "./.venv/*" -not -path "./archive/*" | wc -l`
- CLAUDE.md guidance: !`test -f CLAUDE.md && echo "✅ EXISTS" || echo "❌ MISSING"`

## Instructions

### Phase 1: Setup Semgrep Rules (First Run Only)

If `.semgrep/rules/` doesn't exist, create it with initial rules:

1. **Create directory structure**:
   ```bash
   mkdir -p .semgrep/rules
   touch .semgrep/.semgrepignore
   ```

2. **Add to .semgrepignore**:
   ```
   .venv/
   archive/
   docs/build/
   *.pyc
   __pycache__/
   ```

3. **Create initial rule files** (see Phase 7 for content)

### Phase 2: Comprehensive Hardcode Detection

1. **Run combined rules (intentionally overbroad)**:
   ```bash
   # Using combined rules that catch everything
   if [ -f .semgrep/rules/combined_rules.yaml ]; then
     echo "Running comprehensive sweep with combined_rules.yaml..."
     semgrep --config=.semgrep/rules/combined_rules.yaml . --json > /tmp/sweep_results.json 2>/dev/null
     
     # Count total findings
     total=$(jq '.results | length' /tmp/sweep_results.json 2>/dev/null || echo "0")
     echo "Total hardcode candidates found: $total"
     
     # Group by rule ID
     echo "Findings by type:"
     jq -r '.results | group_by(.check_id) | map({rule: .[0].check_id, count: length}) | .[] | "\(.rule): \(.count)"' /tmp/sweep_results.json 2>/dev/null | sort -t: -k2 -rn | head -20
   else
     echo "combined_rules.yaml not found!"
   fi
   ```

2. **Common hardcode patterns to detect**:
   - Absolute file paths: `/home/`, `/usr/`, `C:\\`
   - Hardcoded URLs: `http://`, `https://` (not in comments)
   - Magic numbers: Numeric literals > 1 (not 0, 1, -1)
   - Hardcoded credentials: `password=`, `token=`, `api_key=`
   - Fixed ports: `:8080`, `:3000`, etc.
   - Environment-specific values: `localhost`, `127.0.0.1`

3. **Quick grep-based hardcode scan** (fallback):
   ```bash
   echo "=== Potential Hardcoded Paths ==="
   grep -r "'/[a-zA-Z]" --include="*.py" . 2>/dev/null | grep -v "#" | head -10
   
   echo "=== Potential Hardcoded URLs ==="
   grep -r "http[s]*://" --include="*.py" . 2>/dev/null | grep -v "#" | head -10
   
   echo "=== Potential Magic Numbers ==="
   grep -rE "[^0-9][0-9]{3,}[^0-9]" --include="*.py" . 2>/dev/null | grep -v "#" | head -10
   ```

### Phase 3: Anti-Pattern Detection

1. **Run additional rule sets**:
   ```bash
   # Python code smells (if exists)
   if [ -f .semgrep/rules/python-smells.yaml ]; then
     echo "Running Python code smell detection..."
     semgrep --config=.semgrep/rules/python-smells.yaml . --severity=ERROR
   fi
   
   # Security patterns (if exists)
   if [ -f .semgrep/rules/security.yaml ]; then
     echo "Running security pattern detection..."
     semgrep --config=.semgrep/rules/security.yaml .
   fi
   
   # Project-specific patterns (if exists)
   if [ -f .semgrep/rules/project-specific.yaml ]; then
     echo "Running project-specific pattern detection..."
     semgrep --config=.semgrep/rules/project-specific.yaml .
   fi
   ```

2. **Common anti-patterns to detect**:
   - Mutable default arguments: `def func(param=[])`
   - Bare except clauses: `except:`
   - Using `eval()` or `exec()`
   - Comparing to None with `==` instead of `is`
   - Global variables modification
   - Deeply nested code (>4 levels)

### Phase 4: Security Pattern Detection

1. **Run security rules**:
   ```bash
   if [ -f .semgrep/rules/security.yaml ]; then
     semgrep --config=.semgrep/rules/security.yaml .
   else
     # Use semgrep registry rules as fallback
     semgrep --config=auto . --severity=ERROR --json | jq '.results[] | {file: .path, message: .extra.message}' 2>/dev/null
   fi
   ```

2. **Security issues to detect**:
   - SQL injection risks
   - Command injection
   - Path traversal
   - Unsafe deserialization
   - Hardcoded secrets

### Phase 5: TODO/FIXME Audit

1. **Find all TODO comments with context**:
   ```bash
   echo "=== TODO/FIXME/HACK Comments ==="
   grep -rn "TODO\|FIXME\|HACK\|XXX\|BUG\|REFACTOR" --include="*.py" . 2>/dev/null | while read -r line; do
     file=$(echo "$line" | cut -d: -f1)
     linenum=$(echo "$line" | cut -d: -f2)
     # Try to get git blame date for the line
     blame=$(git blame -L "$linenum,$linenum" "$file" 2>/dev/null | head -1)
     date=$(echo "$blame" | grep -oE "[0-9]{4}-[0-9]{2}-[0-9]{2}" | head -1)
     echo "[$date] $line"
   done | sort | head -20
   ```

### Phase 6: Project-Specific Patterns

1. **Check CLAUDE.md for patterns to avoid**:
   ```bash
   if [ -f CLAUDE.md ]; then
     echo "=== Checking patterns from CLAUDE.md ==="
     # Extract any "don't" or "avoid" patterns
     grep -i "don't\|avoid\|never\|no hardcode" CLAUDE.md | head -10
   fi
   ```

2. **Check for project-specific anti-patterns**:
   - Patterns violating project conventions
   - Deprecated APIs still in use
   - Old naming conventions

### Phase 7: Generate Sweep Report

Create comprehensive report:

```markdown
# Code Sweep Report - [DATE]

## Summary
- Files scanned: X
- Total hardcode candidates: Y (from intentionally overbroad scan)
- Categorized for review:
  - Critical (security/credentials): A
  - High (paths/URLs/configs): B  
  - Medium (magic numbers/timeouts): C
  - Low (string literals): D

## Hardcodes Found
### Critical (Credentials/Secrets)
- [file:line]: [Issue description]
  ```python
  [code snippet]
  ```
  **Fix**: Move to environment variable or config file

### High (Paths/URLs)
- [file:line]: Hardcoded path "/usr/local/..."
  **Fix**: Use pathlib.Path or config

### Medium (Magic Numbers)
- [file:line]: Magic number 3600
  **Fix**: Define as constant `TIMEOUT_SECONDS = 3600`

## Anti-Patterns Detected
### Python Code Smells
- [file:line]: Mutable default argument
  ```python
  def process(items=[]):  # Bad
  ```
  **Fix**: Use `items=None` with check

### Security Issues
- [file:line]: [Security issue]
  **Risk**: [Description]
  **Fix**: [Remediation]

## TODO/FIXME Audit
### Old TODOs (>30 days)
- [date] [file:line]: [TODO content]

### Critical TODOs
- [file:line]: TODO: Security fix needed

## Configuration Violations
Based on CLAUDE.md:
- [file]: Violates "[specific guideline]"

## Recommended Actions
### Immediate (Security/Critical)
1. [Specific fix with file and line]

### High Priority (Hardcodes)
1. Create config file for:
   - [List of values to externalize]

### Medium Priority (Code Quality)
1. Refactor:
   - [Pattern to fix across files]

### Low Priority (Cleanup)
1. Remove old TODOs
2. Update deprecated patterns

## Suggested Config Structure
```yaml
# config/app_config.yaml
paths:
  data_dir: "./data"
  cache_dir: "./cache"

timeouts:
  connection: 30
  processing: 3600

urls:
  api_base: "${API_BASE_URL}"
```

## Next Steps
[ ] Create/update configuration files
[ ] Replace hardcodes with config references
[ ] Fix security issues
[ ] Refactor anti-patterns
[ ] Clean up old TODOs

## Proceed with fixes? [Yes/No/Selective]
```

### Phase 8: Initialize Semgrep Rules (If Creating)

If `.semgrep/rules/` doesn't exist, create these initial rule files:

#### hardcodes.yaml:
```yaml
rules:
  - id: hardcoded-path
    pattern-either:
      - pattern: |
          "/$PATH"
      - pattern: |
          '/$PATH'
    message: Hardcoded absolute path found
    languages: [python]
    severity: WARNING

  - id: hardcoded-url
    pattern-either:
      - pattern: |
          "http://..."
      - pattern: |
          "https://..."
    message: Hardcoded URL found
    languages: [python]
    severity: WARNING

  - id: magic-number
    pattern: |
      $X = $NUM
    metavariable-regex:
      metavariable: $NUM
      regex: ^[0-9]{3,}$
    message: Magic number should be a named constant
    languages: [python]
    severity: INFO
```

#### python-smells.yaml:
```yaml
rules:
  - id: mutable-default-argument
    pattern: |
      def $FUNC(..., $ARG=[], ...):
        ...
    message: Mutable default argument
    languages: [python]
    severity: ERROR

  - id: bare-except
    pattern: |
      try:
        ...
      except:
        ...
    message: Bare except clause catches all exceptions
    languages: [python]
    severity: WARNING

  - id: eval-usage
    pattern-either:
      - pattern: eval(...)
      - pattern: exec(...)
    message: Avoid eval/exec for security
    languages: [python]
    severity: ERROR
```

#### security.yaml:
```yaml
rules:
  - id: sql-injection
    pattern: |
      $QUERY = "..." + $VAR
      $CURSOR.execute($QUERY)
    message: Potential SQL injection
    languages: [python]
    severity: ERROR

  - id: hardcoded-secret
    pattern-either:
      - pattern: password = "..."
      - pattern: api_key = "..."
      - pattern: token = "..."
    message: Hardcoded credential found
    languages: [python]
    severity: ERROR
```

### Phase 9: Apply Fixes (After Confirmation)

1. **Create configuration files** for hardcoded values
2. **Replace hardcodes** with config references
3. **Fix anti-patterns** using safe alternatives
4. **Update .semgrep/rules/** with new patterns found
5. **Add to CI/CD** pipeline for continuous checking

## Important Notes
- Semgrep rules are customizable - refine based on project needs
- Some "hardcodes" may be acceptable (test fixtures, examples)
- Focus on security issues first, then maintainability
- Document any intentional violations with `# nosemgrep` comments
- Keep semgrep rules in version control
- Run sweep before major releases