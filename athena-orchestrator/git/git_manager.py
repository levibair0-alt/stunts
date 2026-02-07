"""
Git Manager with branch prefix support
Handles all Git operations with proper error handling
"""

import subprocess
import os
from typing import List, Optional

def run_cmd(cmd: str, cwd: Optional[str] = None, check: bool = True):
    """Run a shell command with optional directory context"""
    full_cmd = f"cd {cwd} && {cmd}" if cwd else cmd
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nError: {result.stderr}")
    
    return result

def clone_repo(repo_url: str, path: str) -> None:
    """Clone a Git repository"""
    run_cmd(f"git clone {repo_url} {path}")

def checkout_branch(path: str, branch: str) -> None:
    """Checkout or create a branch"""
    run_cmd(f"git checkout {branch}", cwd=path)

def create_branch(path: str, branch_name: str, from_branch: str = None) -> None:
    """Create a new branch from current or specified branch"""
    if from_branch:
        run_cmd(f"git checkout {from_branch}", cwd=path)
    run_cmd(f"git checkout -b {branch_name}", cwd=path)

def commit_all(path: str, message: str) -> None:
    """Stage and commit all changes"""
    run_cmd("git add .", cwd=path)
    run_cmd(f'git commit -m "{message}"', cwd=path)

def push(path: str, remote: str = "origin", branch: str = None) -> None:
    """Push changes to remote repository"""
    if not branch:
        branch = get_current_branch(path)
    run_cmd(f"git push {remote} {branch}", cwd=path)

def get_current_branch(path: str) -> str:
    """Get the name of the current branch"""
    result = run_cmd("git branch --show-current", cwd=path)
    return result.stdout.strip()

def get_commit_history(path: str, limit: int = 10) -> List[str]:
    """Get recent commit history"""
    result = run_cmd(f"git log -{limit} --oneline", cwd=path)
    return result.stdout.strip().split('\n')

def pull(path: str, remote: str = "origin", branch: str = None) -> None:
    """Pull latest changes from remote"""
    if not branch:
        branch = get_current_branch(path)
    run_cmd(f"git pull {remote} {branch}", cwd=path)

def get_repo_status(path: str) -> str:
    """Get repository status"""
    result = run_cmd("git status --short", cwd=path)
    return result.stdout.strip()

def add_file(path: str, file_path: str) -> None:
    """Stage a specific file"""
    run_cmd(f"git add {file_path}", cwd=path)

if __name__ == "__main__":
    # Simple test
    print("Git Manager loaded successfully")
