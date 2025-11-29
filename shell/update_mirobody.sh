#!/bin/bash

# Script to check latest mirobody version and update requirements.txt
# Usage: ./update_mirobody.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

printf "${BLUE}========================================${NC}\n"
printf "${BLUE}  Update Mirobody Version${NC}\n"
printf "${BLUE}========================================${NC}\n\n"

# Get current version from requirements.txt
CURRENT_VERSION=""
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    CURRENT_VERSION=$(grep "^mirobody==" "$PROJECT_ROOT/requirements.txt" | sed 's/mirobody==//')
    printf "Current version in requirements.txt: ${YELLOW}${CURRENT_VERSION:-Not found}${NC}\n"
fi

# Query latest version
printf "Querying latest version...\n"
LATEST_VERSION=$(pip index versions mirobody --extra-index-url https://repo.thetahealth.ai/repository/pypi-ai-snapshots/simple/ 2>/dev/null | grep "LATEST:" | awk '{print $2}')

if [ -z "$LATEST_VERSION" ]; then
    printf "${YELLOW}Could not fetch latest version${NC}\n"
    exit 1
fi

printf "Latest available version: ${GREEN}${LATEST_VERSION}${NC}\n\n"

# Update requirements.txt
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    if grep -q "^mirobody==" "$PROJECT_ROOT/requirements.txt"; then
        sed -i.bak "s/^mirobody==.*/mirobody==${LATEST_VERSION}/" "$PROJECT_ROOT/requirements.txt"
    else
        echo "mirobody==${LATEST_VERSION}" >> "$PROJECT_ROOT/requirements.txt"
    fi
    rm -f "$PROJECT_ROOT/requirements.txt.bak"
    printf "${GREEN}✓ Updated requirements.txt to mirobody==${LATEST_VERSION}${NC}\n"
else
    printf "${YELLOW}requirements.txt not found${NC}\n"
    exit 1
fi

printf "\n${BLUE}========================================${NC}\n"
printf "${GREEN}✓ Version Updated${NC}\n"
printf "${BLUE}========================================${NC}\n\n"
printf "  ${YELLOW}${CURRENT_VERSION:-N/A}${NC} → ${GREEN}${LATEST_VERSION}${NC}\n\n"
printf "${YELLOW}Next: Run ./deploy.sh to apply changes${NC}\n\n"
