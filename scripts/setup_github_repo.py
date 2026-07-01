#!/usr/bin/env python3
"""
Setup GitHub Repository for Harness Bulletin Board
===================================================
Creates the repo on GitHub under theinversionlabs org and pushes initial content.
"""

import subprocess
import os
from pathlib import Path

REPO_DIR = Path.home() / "harness-ecosystem" / "harness-bulletin-board"
REPO_NAME = "harness-bulletin-board"
ORG = "theinversionlabs"

def run_cmd(cmd: list, cwd: Path = None) -> subprocess.CompletedProcess:
    """Run a command and return result."""
    return subprocess.run(cmd, cwd=cwd or REPO_DIR, capture_output=True, text=True)

def main():
    print(f"🚀 Setting up GitHub repo: {ORG}/{REPO_NAME}")
    
    # Check if gh is authenticated
    result = run_cmd(["gh", "auth", "status"])
    if result.returncode != 0:
        print("❌ GitHub CLI not authenticated. Run 'gh auth login' first.")
        return
    
    # Check current auth
    result = run_cmd(["gh", "auth", "status"])
    print(f"Auth status: {result.stdout.strip()}")
    
    # Create repo if it doesn't exist
    result = run_cmd(["gh", "repo", "view", f"{ORG}/{REPO_NAME}"])
    if result.returncode != 0:
        print(f"Creating repo {ORG}/{REPO_NAME}...")
        result = run_cmd(["gh", "repo", "create", f"{ORG}/{REPO_NAME}", 
                         "--public", "--description", "Harness Bulletin Board - Central coordination for 20-harness fleet"])
        if result.returncode != 0:
            print(f"❌ Failed to create repo: {result.stderr}")
            return
        print("✅ Repo created")
    else:
        print("✅ Repo already exists")
    
    # Initialize git if needed
    if not (REPO_DIR / ".git").exists():
        run_cmd(["git", "init"])
        run_cmd(["git", "checkout", "-b", "main"])
    
    # Add remote
    result = run_cmd(["git", "remote", "get-url", "origin"])
    if result.returncode != 0:
        run_cmd(["git", "remote", "add", "origin", f"https://github.com/{ORG}/{REPO_NAME}.git"])
        print("✅ Remote added")
    
    # Create initial commit
    run_cmd(["git", "add", "."])
    result = run_cmd(["git", "commit", "-m", "Initial commit: Harness Bulletin Board structure"])
    if result.returncode == 0:
        print("✅ Initial commit created")
    else:
        print("ℹ️  Nothing to commit or already committed")
    
    # Push to GitHub
    print("Pushing to GitHub...")
    result = run_cmd(["git", "push", "-u", "origin", "main"])
    if result.returncode == 0:
        print(f"✅ Pushed to https://github.com/{ORG}/{REPO_NAME}")
    else:
        print(f"❌ Push failed: {result.stderr}")
        # Try with auth
        print("Trying with gh auth...")
        result = run_cmd(["gh", "repo", "sync", f"{ORG}/{REPO_NAME}"])
        if result.returncode == 0:
            print("✅ Synced via gh")
    
    # Enable GitHub Pages for the bulletin board
    print("Enabling GitHub Pages...")
    result = run_cmd(["gh", "api", f"/repos/{ORG}/{REPO_NAME}/pages", "--method", "POST", 
                     "-f", "source[branch]=main", "-f", "source[path]=/"])
    if result.returncode == 0:
        print("✅ GitHub Pages enabled - will be at https://theinversionlabs.github.io/harness-bulletin-board/")
    else:
        print(f"ℹ️  Pages setup: {result.stderr}")

if __name__ == "__main__":
    main()
