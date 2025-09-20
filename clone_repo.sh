#!/bin/bash

# GitHub Repository Cloner
# Usage: ./clone_repo.sh <repo_name> [target_directory]

REPO_NAME=$1
TARGET_DIR=${2:-"/workspace/github_repos"}
TOKEN="ghs_MCVvsz23GICmF3tE3OpGJpfu73MRtL4878k5"
USERNAME="marvinmckinneyii0"

if [ -z "$REPO_NAME" ]; then
    echo "Usage: ./clone_repo.sh <repo_name> [target_directory]"
    echo ""
    echo "Available repositories:"
    echo "  - ai_engineering_hub"
    echo "  - excel_automation1"
    echo "  - Marvin-Python-Projects"
    echo "  - marvinmckinneyii0"
    echo "  - mutual-fund-analysis"
    echo "  - RTX-Docs"
    echo ""
    echo "Example: ./clone_repo.sh excel_automation1"
    exit 1
fi

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Clone the repository
echo "Cloning $REPO_NAME to $TARGET_DIR/$REPO_NAME..."
git clone "https://x-access-token:${TOKEN}@github.com/${USERNAME}/${REPO_NAME}.git" "$TARGET_DIR/$REPO_NAME"

if [ $? -eq 0 ]; then
    echo "Successfully cloned $REPO_NAME!"
    echo "Repository location: $TARGET_DIR/$REPO_NAME"
else
    echo "Failed to clone $REPO_NAME"
fi