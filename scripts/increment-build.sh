#!/bin/bash
# Increment build number before QA deployment

set -e

BUILD_INFO_FILE="BUILD_INFO"
BUILD_LOG="build_history.log"

# Get current build number
current_build=$(grep "^BUILD_NUMBER=" $BUILD_INFO_FILE | cut -d'=' -f2)

# Generate new build number (date-based with increment)
date_part=$(date +%Y%m%d)
current_date=$(echo $current_build | cut -d'.' -f1)

if [ "$date_part" == "$current_date" ]; then
    # Same day, increment counter
    counter=$(echo $current_build | cut -d'.' -f2)
    new_counter=$((counter + 1))
    new_build="${date_part}.${new_counter}"
else
    # New day, reset counter
    new_build="${date_part}.1"
fi

# Get git commit (if available)
if git rev-parse --git-dir > /dev/null 2>&1; then
    git_commit=$(git rev-parse --short HEAD 2>/dev/null || echo "dev")
else
    git_commit="dev"
fi

# Update BUILD_INFO file
build_date=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "🔧 Updating build information..."
echo "   Previous: $current_build"
echo "   New: $new_build"
echo "   Commit: $git_commit"
echo ""

# Backup current BUILD_INFO
cp $BUILD_INFO_FILE ${BUILD_INFO_FILE}.bak

# Update BUILD_INFO
sed -i "s/^BUILD_NUMBER=.*/BUILD_NUMBER=$new_build/" $BUILD_INFO_FILE
sed -i "s/^BUILD_DATE=.*/BUILD_DATE=$build_date/" $BUILD_INFO_FILE
sed -i "s/^GIT_COMMIT=.*/GIT_COMMIT=$git_commit/" $BUILD_INFO_FILE

# Log the build
echo "[$build_date] Build $new_build (commit: $git_commit)" >> $BUILD_LOG

echo "✅ Build number updated: $new_build"
echo "📝 Logged to $BUILD_LOG"
echo ""
echo "🚀 Ready for QA deployment!"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff $BUILD_INFO_FILE"
echo "  2. Rebuild services: docker compose build"
echo "  3. Run tests: ./scripts/run-tests.sh"
echo "  4. Deploy to QA: docker compose up -d"

