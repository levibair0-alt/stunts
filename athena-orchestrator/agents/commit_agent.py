"""
Commit Agent - Handles Git commits with rate limiting
Enforces max_commits_per_hour from settings.yaml
"""

import json
import yaml
import os
from datetime import datetime, timedelta
from typing import Dict, List

class CommitAgent:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.settings = self._load_settings()
        self.commit_history: Dict[str, List[datetime]] = {}
        
        # Load existing commit history if any
        self._load_commit_history()
    
    def _load_settings(self):
        """Load system settings"""
        settings_path = os.path.join(self.config_path, "settings.yaml")
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_commit_history(self):
        """Load commit history from file if exists"""
        history_path = os.path.join(self.config_path, "commit_history.json")
        if os.path.exists(history_path):
            with open(history_path, 'r') as f:
                data = json.load(f)
                # Convert strings back to datetime
                for project, commits in data.items():
                    self.commit_history[project] = [
                        datetime.fromisoformat(c) for c in commits
                    ]
    
    def _save_commit_history(self):
        """Save commit history to file"""
        history_path = os.path.join(self.config_path, "commit_history.json")
        # Convert datetime to strings for JSON
        data = {}
        for project, commits in self.commit_history.items():
            data[project] = [c.isoformat() for c in commits]
        
        with open(history_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _cleanup_old_commits(self, project: str):
        """Remove commits older than 1 hour from tracking"""
        if project not in self.commit_history:
            return
        
        one_hour_ago = datetime.now() - timedelta(hours=1)
        self.commit_history[project] = [
            c for c in self.commit_history[project]
            if c > one_hour_ago
        ]
    
    def check_commit_limit(self, project: str) -> bool:
        """
        Check if project can make another commit
        Enforces max_commits_per_hour limit
        """
        max_commits = self.settings.get('max_commits_per_hour', 20)
        
        # Cleanup old commits first
        self._cleanup_old_commits(project)
        
        if project not in self.commit_history:
            self.commit_history[project] = []
        
        current_count = len(self.commit_history[project])
        
        if current_count >= max_commits:
            print(f"[Commit] ERROR: Max commits per hour reached for {project}")
            print(f"[Commit] Current: {current_count}, Max: {max_commits}")
            return False
        
        print(f"[Commit] Commit allowed: {current_count}/{max_commits} for {project}")
        return True
    
    def record_commit(self, project: str):
        """Record a commit for rate limiting"""
        if project not in self.commit_history:
            self.commit_history[project] = []
        
        self.commit_history[project].append(datetime.now())
        self._save_commit_history()
    
    def commit_changes(self, plan: dict, repo_path: str) -> dict:
        """
        Commit changes with guardrails checking
        """
        project = plan['project']
        
        # Check commit limit first
        if not self.check_commit_limit(project):
            return {
                "success": False,
                "error": f"Max commits per hour limit reached for {project}",
                "status": "blocked"
            }
        
        # Import git manager here to avoid circular imports
        from git.git_manager import commit_all, push
        
        try:
            # Commit all changes
            commit_all(repo_path, plan['commit_message'])
            
            # Record commit for rate limiting
            self.record_commit(project)
            
            print(f"[Commit] Successfully committed: {plan['commit_message']}")
            
            return {
                "success": True,
                "status": "committed",
                "message": "Changes committed successfully"
            }
        
        except Exception as e:
            print(f"[Commit] ERROR: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "failed"
            }
    
    def push_changes(self, plan: dict, repo_path: str) -> dict:
        """Push changes to remote"""
        from git.git_manager import push, get_current_branch
        
        try:
            branch = plan.get('branch', get_current_branch(repo_path))
            push(repo_path, "origin", branch)
            
            print(f"[Commit] Pushed to remote: {branch}")
            
            return {
                "success": True,
                "status": "pushed",
                "branch": branch
            }
        
        except Exception as e:
            print(f"[Commit] Push ERROR: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "push_failed"
            }

if __name__ == "__main__":
    agent = CommitAgent("config")
    test_plan = {
        "project": "stunts",
        "task": "test",
        "branch": "task/test",
        "commit_message": "Test commit"
    }
    result = agent.check_commit_limit("stunts")
    print(f"Can commit: {result}")
