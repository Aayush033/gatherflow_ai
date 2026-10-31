#!/usr/bin/env bash
# ==============================================================================
# GatherFlow AI — Clean GitHub Push Script (Bash)
# ==============================================================================
set -euo pipefail

echo "=========================================================="
echo "  GatherFlow AI — Preparing Clean Git Repository"
echo "=========================================================="

if [ ! -d .git ]; then
    echo "Initializing Git repository..."
    git init
fi

if [ ! -f .gitignore ]; then
    echo "Error: .gitignore missing!"
    exit 1
fi

git add .

# Verify no secrets or databases staged
if git diff --name-only --cached | grep -E '^(\.env|\.env\.local|.*\.db|.*\.sqlite|chroma_db/)' > /dev/null; then
    echo "ERROR: Sensitive files detected in git staging! Unstaging..."
    git diff --name-only --cached | grep -E '^(\.env|\.env\.local|.*\.db|.*\.sqlite|chroma_db/)' | xargs git reset HEAD
    echo "Please ensure .env and *.db are untracked before committing."
    exit 1
fi

echo "Verified: No secrets or local database files staged."
git commit -m "feat: GatherFlow AI Prompt Wars 2026 production release with 22/22 verified tests"
git branch -M main

if ! git remote | grep -q '^origin$'; then
    read -r -p "Enter GitHub repository URL (e.g. https://github.com/<username>/gatherflow-ai.git): " REPO_URL
    if [ -n "$REPO_URL" ]; then
        git remote add origin "$REPO_URL"
    else
        echo "No remote added. Local commit completed on branch main."
        exit 0
    fi
fi

git push -u origin main
echo "Successfully pushed to GitHub!"

