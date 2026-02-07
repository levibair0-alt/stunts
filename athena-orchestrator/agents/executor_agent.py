"""
Executor Agent - Executes tasks with safety checks
Validates plan against permissions.yaml
"""

import json
import yaml
import os

class ExecutorAgent:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.permissions = self._load_permissions()
        self.settings = self._load_settings()
    
    def _load_permissions(self):
        """Load per-project permissions"""
        perms_path = os.path.join(self.config_path, "permissions.yaml")
        with open(perms_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_settings(self):
        """Load system settings"""
        settings_path = os.path.join(self.config_path, "settings.yaml")
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def check_permissions(self, project: str, plan: dict) -> bool:
        """
        Validate plan against project permissions
        """
        if project not in self.permissions:
            print(f"[Executor] ERROR: Unknown project: {project}")
            return False
        
        perms = self.permissions[project]
        
        # Check auto_commit permission
        if not perms.get('auto_commit_allowed', False):
            print(f"[Executor] Auto-commit not allowed for {project}")
        
        # Check file types
        allowed_types = perms.get('allowed_file_types', ['*'])
        blocked_files = perms.get('blocked_files', [])
        
        for file in plan.get('files_to_create', []) + plan.get('files_to_modify', []):
            # Check blocked files
            for pattern in blocked_files:
                if file.endswith(pattern.replace('*', '')):
                    print(f"[Executor] ERROR: Blocked file type: {file}")
                    return False
        
        print(f"[Executor] Permissions validated for {project}")
        return True
    
    def execute_task(self, plan: dict) -> dict:
        """
        Execute a task plan
        """
        project = plan['project']
        
        # Check permissions first
        if not self.check_permissions(project, plan):
            return {
                "success": False,
                "error": "Permission check failed",
                "status": "blocked"
            }
        
        # Placeholder for actual execution logic
        # This would be wired to CTO connector later
        
        print(f"[Executor] Executing task: {plan['task']}")
        print(f"[Executor] Project: {project}")
        print(f"[Executor] Files to create: {len(plan.get('files_to_create', []))}")
        print(f"[Executor] Files to modify: {len(plan.get('files_to_modify', []))}")
        
        result = {
            "success": True,
            "status": "completed",
            "message": "Task executed successfully",
            "output": "Placeholder execution output"
        }
        
        return result
    
    def validate_files(self, files: list, project: str) -> bool:
        """Validate files against project permissions"""
        if project not in self.permissions:
            return False
        
        perms = self.permissions[project]
        blocked = perms.get('blocked_files', [])
        
        for file in files:
            for pattern in blocked:
                if file.endswith(pattern.replace('*', '')):
                    print(f"[Executor] Blocked: {file}")
                    return False
        
        return True

if __name__ == "__main__":
    executor = ExecutorAgent("config")
    test_plan = {
        "project": "stunts",
        "task": "test execution",
        "branch": "task/test",
        "files_to_create": ["test.py"],
        "files_to_modify": []
    }
    result = executor.execute_task(test_plan)
    print(json.dumps(result, indent=2))
