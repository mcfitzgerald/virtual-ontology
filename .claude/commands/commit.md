---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(npm:*), Bash(grep:*), Bash(cat:*), Bash(echo:*), Edit, Write, Read
description: Commit changes and update changelog automatically
---

# Smart Git Commit with Changelog Integration

## Context
- Current git status: !`git status --porcelain`
- Staged changes: !`git diff --cached --stat`
- Unstaged changes: !`git diff --stat`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -5`
- Changelog exists: !`test -f CHANGELOG.md && echo "YES" || echo "NO"`

## Instructions

### CRITICAL: ALWAYS UPDATE CHANGELOG.MD
**If CHANGELOG.md exists in the project, you MUST update it with every commit.**

### 1. **Analyze Changes**
1. Review all changes (staged and unstaged)
2. Determine commit type using conventional commits:
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `style`: Code style/formatting
   - `refactor`: Code refactoring
   - `perf`: Performance improvements
   - `test`: Test additions/changes
   - `chore`: Build process or auxiliary tool changes
   - `build`: Build system or dependency changes

### 2. **Update CHANGELOG.md (MANDATORY if it exists)**
If CHANGELOG.md exists:
1. Read the existing CHANGELOG.md
2. Add new entry at the top under "## [Unreleased]" section
3. Format entries as:
   ```markdown
   ## [Unreleased]
   
   ### Added
   - Description of new features
   
   ### Changed
   - Description of changes
   
   ### Fixed
   - Description of fixes
   ```
4. If no [Unreleased] section exists, create it

### 3. **Stage and Commit**
1. Stage all relevant files: `git add <files>`
2. **ALWAYS stage CHANGELOG.md if updated**: `git add CHANGELOG.md`
3. Create commit with conventional commit message format
4. Include the standard footer:
   ```
   🤖 Generated with [Claude Code](https://claude.ai/code)
   
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

### 4. **Verify**
After committing:
1. Run `git status` to confirm commit succeeded
2. Confirm CHANGELOG.md was included if it was updated

## Example Workflow
```bash
# 1. Check what needs to be committed
git status
git diff

# 2. Update CHANGELOG.md (if it exists)
# Edit CHANGELOG.md to add entry

# 3. Stage files including CHANGELOG.md
git add <changed-files>
git add CHANGELOG.md  # IMPORTANT: Don't forget this!

# 4. Commit with message
git commit -m "feat: add Poetry dependency management

- Reduced dependencies from 298 to 96 packages
- Added pyproject.toml configuration
- Created documentation

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 5. Verify
git status
```

## Changelog Entry Categories
Use these categories in CHANGELOG.md:
- **Added** - for new features
- **Changed** - for changes in existing functionality
- **Deprecated** - for soon-to-be removed features
- **Removed** - for removed features
- **Fixed** - for bug fixes
- **Security** - for vulnerability fixes

## IMPORTANT REMINDERS
- **ALWAYS check if CHANGELOG.md exists**
- **ALWAYS update it if it exists**
- **ALWAYS stage CHANGELOG.md with other changes**
- **NEVER skip the changelog update when the file exists**