#!/bin/bash

# Twin Model Cleanup Script
# This script removes legacy code and reorganizes the twin_model directory

echo "========================================="
echo "Twin Model Cleanup Script"
echo "========================================="
echo ""

# Function to confirm action
confirm() {
    read -p "$1 (y/n)? " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 1
    fi
    return 0
}

# 1. Move test files to twin_model/tests if needed
echo "Step 1: Organizing test files..."
if [ -f "test_phase1_primitives.py" ] || [ -f "test_phase2_integration.py" ]; then
    mkdir -p twin_model/tests
    mv test_phase*.py twin_model/tests/ 2>/dev/null && echo "✓ Moved test files to twin_model/tests/"
else
    echo "✓ Test files already organized"
fi

# 2. List files to be removed
echo ""
echo "Step 2: Files to be removed (legacy code):"
echo "-------------------------------------------"
LEGACY_FILES=(
    "twin_model/equipment.py"
    "twin_model/buffer.py"
    "twin_model/production_line.py"
    "twin_model/runner.py"
    "twin_model/config.py"
    "twin_model/transduction.py"
    "twin_model/test_simulation.py"
    "twin_model/test_transduction.py"
)

for file in "${LEGACY_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  - $file ($(wc -l < "$file") lines)"
    fi
done

echo ""
if confirm "Remove legacy Python files?"; then
    for file in "${LEGACY_FILES[@]}"; do
        if [ -f "$file" ]; then
            rm "$file" && echo "✓ Removed $file"
        fi
    done
else
    echo "⊗ Skipped removing legacy files"
fi

# 3. Clean up documentation
echo ""
echo "Step 3: Documentation cleanup..."
if [ -d "twin_model/docs/_build" ]; then
    if confirm "Remove auto-generated documentation (docs/_build)?"; then
        rm -rf twin_model/docs/_build && echo "✓ Removed docs/_build"
    fi
fi

if [ -d "twin_model/docs" ]; then
    if confirm "Remove entire docs directory?"; then
        rm -rf twin_model/docs && echo "✓ Removed docs directory"
    fi
fi

# 4. Remove Python cache files
echo ""
echo "Step 4: Cleaning Python cache files..."
if confirm "Remove all __pycache__ and .pyc files?"; then
    find twin_model -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find twin_model -name "*.pyc" -delete 2>/dev/null
    find . -name "*.pyc" -delete 2>/dev/null
    echo "✓ Removed Python cache files"
else
    echo "⊗ Skipped cache cleanup"
fi

# 5. Show final structure
echo ""
echo "Step 5: Final structure:"
echo "------------------------"
echo "twin_model/"
tree -L 2 twin_model/ 2>/dev/null || ls -la twin_model/

# 6. Verification
echo ""
echo "Step 6: Verification:"
echo "---------------------"

# Check if essential files exist
ESSENTIAL_FILES=(
    "twin_model/__init__.py"
    "twin_model/model_builder.py"
    "twin_model/primitives/__init__.py"
    "twin_model/primitives/base.py"
    "twin_model/primitives/equipment.py"
    "twin_model/transduction/__init__.py"
    "twin_model/transduction/mes_transducer.py"
)

all_good=true
for file in "${ESSENTIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file MISSING!"
        all_good=false
    fi
done

echo ""
if [ "$all_good" = true ]; then
    echo "✅ Cleanup complete! All essential files preserved."
    echo ""
    echo "You can now run tests with:"
    echo "  python -m pytest twin_model/tests/"
    echo "or"
    echo "  python twin_model/tests/test_phase1_primitives.py"
else
    echo "⚠️  Warning: Some essential files are missing!"
fi

echo ""
echo "========================================="
echo "Cleanup Summary:"
echo "- Legacy files removed: ${#LEGACY_FILES[@]} files"
echo "- Test files organized in: twin_model/tests/"
echo "- Core modules preserved in: twin_model/primitives/"
echo "- Transduction layer in: twin_model/transduction/"
echo "========================================="