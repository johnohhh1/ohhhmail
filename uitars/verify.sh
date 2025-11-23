#!/bin/bash
# UI-TARS Build Verification Script

echo "🔍 UI-TARS Build Verification"
echo "============================="
echo ""

ERRORS=0

# Check required files
echo "📁 Checking required files..."
REQUIRED_FILES=(
    "package.json"
    "tsconfig.json"
    "Dockerfile"
    "nginx.conf"
    "src/index.tsx"
    "src/App.tsx"
    "src/UITARSPanel.tsx"
    "src/ExecutionDetail.tsx"
    "src/WorkflowGraph.tsx"
    "src/types.ts"
    "src/config.ts"
    "public/index.html"
    "public/manifest.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ Found: $file"
    fi
done

echo ""

# Check Node.js
echo "🔧 Checking environment..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo "✅ Node.js: $NODE_VERSION"
else
    echo "❌ Node.js not found"
    ERRORS=$((ERRORS + 1))
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm -v)
    echo "✅ npm: $NPM_VERSION"
else
    echo "❌ npm not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check Docker
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "✅ Docker: $DOCKER_VERSION"
else
    echo "⚠️  Docker not found (optional)"
fi

echo ""
echo "📊 Summary"
echo "=========="
echo "Required files: ${#REQUIRED_FILES[@]}"
echo "Errors found: $ERRORS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✅ All checks passed! Ready to build."
    echo ""
    echo "Next steps:"
    echo "  1. npm install"
    echo "  2. cp .env.example .env"
    echo "  3. npm start"
    exit 0
else
    echo "❌ $ERRORS errors found. Please fix before building."
    exit 1
fi
