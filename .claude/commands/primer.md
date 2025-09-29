---
allowed-tools: Bash(git:*), Bash(grep:*), Bash(ls:*), Bash(head:*), Bash(tail:*), Bash(date:*), Bash(wc:*), Read, Write, TodoWrite
description: Generate or update PRIMER.md with current project context for fresh Claude sessions
---

# Generate Project Context Primer

## Purpose
Generate or update PRIMER.md with current project state for quick context when starting new Claude sessions. This replaces the transient PROJECT_STATUS_HANDOVER.md with a maintained, comprehensive context file.

## Pre-flight Checks
- Current branch: !`git branch --show-current`
- Last commit: !`git log -1 --oneline`
- Uncommitted changes: !`git status --porcelain | wc -l` files
- Today's date: !`date +%Y-%m-%d`

## Instructions

### Phase 1: Gather Dynamic Information

1. **Recent Git Activity**:
   ```bash
   # Last 5 commits
   git log -5 --oneline --no-decorate
   
   # Current branch and status
   git status -sb
   ```

2. **Check for Active Work**:
   - Read CHANGELOG.md [Unreleased] section for recent changes
   - Check if TODO.md exists and read current tasks
   - Look for any validation results in recent commits

3. **Extract Key Metrics**:
   ```bash
   # Check latest validation results if available
   ls -t validation/*.log 2>/dev/null | head -1
   
   # Count Python files
   find twin_model -name "*.py" | wc -l
   ```

### Phase 2: Extract Static/Semi-Static Information

1. **Read Core Documentation**:
   - `reference/theory_notes.md` - Extract key domain knowledge
   - `docs/optimization-guide.md` - Extract OEE progression stages
   - `CLAUDE.md` - Extract code patterns and practices
   - `config/calibrated_parameters.yaml` - Check current batch_size and key parameters

2. **Project Structure**:
   ```bash
   # Get main directories
   ls -d */ | grep -E "^(twin_model|config|manifests|ontology|reference|docs)/" | head -10
   ```

### Phase 3: Generate PRIMER.md

Create or update PRIMER.md with the following structure:

```markdown
# Virtual Ontology - Project Context Primer

*Last Updated: [timestamp]*
*Branch: [current-branch]*
*Last Commit: [commit-hash and message]*

## Project Essence

**One-Line**: Discrete event simulation of manufacturing production lines using SimPy containers with ontology-driven architecture.

**Architecture**: Three-file system
- **Ontology** (structure) → Defines equipment types and relationships
- **Manifest** (instances) → Declares actual equipment and connections  
- **Config** (parameters) → Contains tunable simulation parameters

**Key Formula**: 
```
Actual throughput = (batch_size / processing_interval) × performance_factor × quality_rate
```

## Current Sprint

### Active Work
[Extract from CHANGELOG [Unreleased] and recent commits]

### Known Issues
[Extract from TODO.md if exists, or note critical issues]

### Recent Fixes
[Last 2-3 significant fixes from CHANGELOG]

## Quick Orientation

Essential files to review (in order):
1. `reference/theory_notes.md` - Production line theory and empirical data
2. `config/calibrated_parameters.yaml` - Current tunable parameters (check batch_size!)
3. `docs/optimization-guide.md` - Progressive OEE improvement guide
4. `CHANGELOG.md` - Recent changes and fixes

## Domain Knowledge

### Production Line Speeds (Reality Check)
- **Standard lines**: 100-200 units/min (not 440-500!)
- **High-speed**: Up to 800 units/min (specialized)
- **Current config**: [extract from parameters]

### Theory of Constraints (TOC)
Goldratt's Five Focusing Steps:
1. Identify the constraint (usually the filler)
2. Exploit the constraint (never let it starve/block)
3. Subordinate everything (V-curve speeds)
4. Elevate if needed (increase capacity)
5. Repeat the process

### V-Curve Design
- Constraint: 100% (bottleneck, usually filler)
- Upstream: +20% (push material to constraint)
- Downstream: +10-30% (pull from constraint)

### OEE Progression Path
- Baseline: 45-50% (poor performance, no optimization)
- + Accumulation: 55-60%
- + Maintenance: 65-70%  
- + Performance: 70-75%
- World-Class: 75-80%

## Roadmap

### Immediate (Next Session)
- [ ] Fix batch_size from 10 to 100 in calibrated_parameters.yaml
- [ ] Verify production reaches 3-4M units/14 days (vs current 326K)
- [ ] Implement V-curve speed differentials

### Short-term (Next Week)
- [ ] Create accumulation buffer primitive
- [ ] Add V-curve controller
- [ ] Implement constraint tracker (TOC)
- [ ] Test with accumulation for 60% OEE

### Medium-term (Next Month)
- [ ] Add changeover matrix and timing
- [ ] Implement campaign optimization
- [ ] Create production order management
- [ ] Document optimization strategies

### Long-term (Future)
- [ ] ML-based parameter optimization
- [ ] Real-time adaptation
- [ ] Multi-site simulation
- [ ] Digital twin integration

## Code Patterns

### Critical Rules
- **Always**: Use `poetry run python` (never bare python)
- **Parameters**: Resolution hierarchy: equipment-specific → type-specific → defaults
- **No hardcodes**: Everything in config files
- **Testing**: Run `validate_phase3.py` after changes
- **Commits**: Use `/commit` command to update CHANGELOG

### Common Commands
```bash
# Validate current configuration
poetry run python validation/validate_phase3.py

# Run tests
poetry run pytest

# Type checking
poetry run mypy twin_model

# Linting
poetry run ruff check
```

## Recent Decisions

[Extract last 5 important decisions from git log and CHANGELOG]

## Testing & Validation

### Quick Validation
```bash
poetry run python validation/validate_phase3.py
```
Expected output: [current vs target]

### Key Metrics to Track
- Total production over 14 days (target: 8.4M eventually, realistic: 3-4M)
- OEE components (Availability, Performance, Quality)
- Constraint utilization (should be >90%)
- Buffer levels (accumulation points)

## Project Structure

```
twin_model/          # Core simulation package
├── primitives/      # Flow primitives (Source, Equipment, Sink)  
├── monitoring/      # Real-time metrics and OEE
├── scheduling/      # MES and production scheduling
└── tests/          # Unit and integration tests

config/             # Tunable parameters (YAML)
manifests/          # Equipment instances (YAML)
ontology/           # Type definitions (YAML)
reference/          # Theory and research docs
docs/              # Documentation
└── llm-ready/     # LLM-optimized docs
```

## Next Actions

[Based on roadmap and current state]

---

*Note: This primer is auto-generated. Run `/primer` command to update.*
```

### Phase 4: Report Generation Summary

After generating PRIMER.md, provide a summary:
- What changed since last update
- Any critical issues found
- Suggested next actions
- Files that may need attention

### Phase 5: Cleanup Suggestion

If this is the first run and PRIMER.md is successfully created:
- Suggest archiving PROJECT_STATUS_HANDOVER.md
- Suggest archiving IMPLEMENTATION_PLAN.md (after extracting roadmap)
- Note that PRIMER.md is now the maintained context file

## Usage

Run this command:
1. At the start of new Claude sessions
2. After completing major work
3. Before handoff to another session
4. When project direction changes significantly

The generated PRIMER.md should be:
- Under 300 lines for quick scanning  
- Focused on actionable context
- Updated with current state
- Clear about next steps