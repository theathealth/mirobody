#!/bin/bash

# Script to update mirobody to the latest version
# Usage: ./update_mirobody.sh

set -e

# Activate virtual environment if it exists
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
elif [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

printf "${BLUE}========================================${NC}\n"
printf "${BLUE}  Update Mirobody to Latest Version${NC}\n"
printf "${BLUE}========================================${NC}\n\n"

# Step 1: Show current version
printf "${BLUE}[Step 1/3] Check current version...${NC}\n"
CURRENT_VERSION=$(python3 -c "
try:
    from importlib.metadata import version
    print(version('mirobody'))
except:
    try:
        import mirobody
        print(getattr(mirobody, '__version__', 'unknown'))
    except:
        print('Not installed')
" 2>/dev/null)

printf "  Current version: ${YELLOW}${CURRENT_VERSION}${NC}\n\n"

# Step 2: Update pip package with error handling
printf "${BLUE}[Step 2/3] Update mirobody pip package...${NC}\n"

# Get latest available version
LATEST_VERSION=$(pip index versions mirobody --extra-index-url https://repo.thetahealth.ai/repository/pypi-ai-snapshots/simple/ 2>/dev/null | grep "LATEST:" | awk '{print $2}')
printf "  Latest available version: ${YELLOW}${LATEST_VERSION}${NC}\n"

# Get list of recent available versions (top 10)
RECENT_VERSIONS=$(pip index versions mirobody --extra-index-url https://repo.thetahealth.ai/repository/pypi-ai-snapshots/simple/ 2>/dev/null | grep "Available versions:" | head -1 | sed 's/Available versions: //' | tr ',' '\n' | head -10 | xargs)

# Try to install latest version
if pip install --upgrade mirobody \
    --extra-index-url https://repo.thetahealth.ai/repository/pypi-ai-snapshots/simple/ >/dev/null 2>&1; then
    printf "${GREEN}  ✓ Upgraded to ${LATEST_VERSION}${NC}\n"
else
    printf "${YELLOW}  Trying alternative versions...${NC}\n"
    SUCCESS=false
    for version in $RECENT_VERSIONS; do
        if [ "$version" = "$LATEST_VERSION" ]; then
            continue
        fi
        if pip install mirobody==$version --extra-index-url https://repo.thetahealth.ai/repository/pypi-ai-snapshots/simple/ >/dev/null 2>&1; then
            printf "${GREEN}  ✓ Installed ${version}${NC}\n"
            SUCCESS=true
            break
        fi
    done
    if [ "$SUCCESS" = false ]; then
        printf "${RED}  ✗ Update failed, keeping ${CURRENT_VERSION}${NC}\n"
    fi
fi

# Check new version
NEW_VERSION=$(python3 -c "
try:
    from importlib.metadata import version
    print(version('mirobody'))
except:
    import mirobody
    print(getattr(mirobody, '__version__', 'unknown'))
" 2>/dev/null)

if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
    printf "\n${GREEN}✓ Updated: ${CURRENT_VERSION} → ${NEW_VERSION}${NC}\n\n"
else
    printf "\n${YELLOW}Already at version ${NEW_VERSION}${NC}\n\n"
fi

# Step 3: Update requirements.txt automatically
printf "${BLUE}[Step 3/3] Update requirements.txt...${NC}\n"
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
        # Update mirobody version in requirements.txt
        sed -i.bak "s/^mirobody==.*/mirobody==${NEW_VERSION}/" "$PROJECT_ROOT/requirements.txt"
        rm -f "$PROJECT_ROOT/requirements.txt.bak"
        printf "${GREEN}  ✓ Updated requirements.txt to mirobody==${NEW_VERSION}${NC}\n"
    else
        printf "${YELLOW}  requirements.txt already at version ${NEW_VERSION}${NC}\n"
    fi
else
    printf "${YELLOW}  requirements.txt not found, skipping${NC}\n"
fi
printf "\n"

# Summary
printf "${BLUE}========================================${NC}\n"
printf "${GREEN}✓ Update Completed${NC}\n"
printf "${BLUE}========================================${NC}\n\n"

printf "  ${YELLOW}${CURRENT_VERSION}${NC} → ${GREEN}${NEW_VERSION}${NC}\n\n"

if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
    printf "${YELLOW}Next: Run ./deploy.sh to apply changes${NC}\n\n"
fi

exit 0
