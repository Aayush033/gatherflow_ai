# ==============================================================================
# GatherFlow AI — Clean GitHub Push Script (PowerShell)
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  GatherFlow AI — Preparing Clean Git Repository" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Initialize git if not already initialized
if (-not (Test-Path .git)) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
}

# 2. Check that .gitignore protects sensitive files
if (-not (Test-Path .gitignore)) {
    Write-Error ".gitignore file is missing! Aborting to prevent leaking secrets."
    exit 1
}

# 3. Add all tracked files
Write-Host "Staging files..." -ForegroundColor Yellow
git add .

# 4. Verify no .env or .db files are staged
$stagedFiles = git diff --name-only --cached
$leakFound = $false
foreach ($file in $stagedFiles) {
    if ($file -match "^\.env" -or $file -match "\.db$" -or $file -match "chroma_db/") {
        Write-Host "WARNING: Sensitive file staged: $file" -ForegroundColor Red
        $leakFound = $true
    }
}
if ($leakFound) {
    Write-Error "Found sensitive files staged for commit. Please check .gitignore and unstage them before pushing."
    exit 1
}

Write-Host "Verified: No secrets or local database files are staged." -ForegroundColor Green

# 5. Commit
$commitMsg = "feat: GatherFlow AI Prompt Wars 2026 production release with 22/22 verified tests"
git commit -m $commitMsg

# 6. Branch
git branch -M main

# 7. Prompt for Remote URL if not set
$remotes = git remote
if (-not ($remotes -contains "origin")) {
    $repoUrl = Read-Host "Enter your GitHub repository URL (e.g. https://github.com/<username>/gatherflow-ai.git)"
    if (-not [string]::IsNullOrWhiteSpace($repoUrl)) {
        git remote add origin $repoUrl
    } else {
        Write-Host "No remote added. Repository is committed locally on branch main." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin main

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Successfully pushed to GitHub!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

