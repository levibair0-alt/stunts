"""
Planner Agent - AI planning with guardrails
Checks settings.yaml guardrails before planning
"""

import json
import yaml
import os

class PlannerAgent:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.settings = self._load_settings()
        
        # Verify guardrails are loaded
        self._verify_guardrails()
    
    def _load_settings(self):
        """Load system settings from config/settings.yaml"""
        settings_path = os.path.join(self.config_path, "settings.yaml")
        
        if not os.path.exists(settings_path):
            raise RuntimeError(f"Guardrails not found: {settings_path}")
        
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _verify_guardrails(self):
        """Verify critical guardrails are loaded - refuse to act if not"""
        required = [
            'max_commits_per_hour',
            'branch_prefix',
            'auto_merge',
            'require_tests'
        ]
        
        missing = [key for key in required if key not in self.settings]
        
        if missing:
            raise RuntimeError(
                f"CRITICAL: Guardrails not loaded! Missing: {missing}\n"
                "Agent will refuse to plan tasks."
            )
        
        print(f"[Planner] Guardrails verified: {list(self.settings.keys())}")
    
    def plan_task(self, task_description: str, project: str) -> dict:
        """
        Plan a task with guardrails checks
        
        Returns standardized task_output_format structure
        """
        # Placeholder for AI planning (OpenAI API to be added later)
        
        # Generate branch name with prefix
        safe_task_name = task_description.lower().replace(' ', '-')[:20]
        branch_name = f"{self.settings['branch_prefix']}{safe_task_name}"
        
        plan = {
            "project": project,
            "task": task_description,
            "branch": branch_name,
            "files_to_create": [],
            "files_to_modify": [],
            "commands_to_run": [],
            "commit_message": f"Auto: {task_description}",
            "notion_log": "Planned and ready for execution"
        }
        
        print(f"[Planner] Task planned for {project}: {task_description}")
        print(f"[Planner] Branch: {branch_name}")
        
        return plan
    
    def validate_plan(self, plan: dict) -> bool:
        """Validate plan respects guardrails"""
        if not plan['branch'].startswith(self.settings['branch_prefix']):
            print(f"[Planner] ERROR: Branch must start with {self.settings['branch_prefix']}")
            return False
        
        if not plan.get('commit_message'):
            print("[Planner] ERROR: Missing commit message")
            return False
        
        return True

if __name__ == "__main__":
    planner = PlannerAgent("config")
    plan = planner.plan_task("test task", "stunts")
    print(json.dumps(plan, indent=2))
