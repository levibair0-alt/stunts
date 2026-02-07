"""
Main Loop - Continuous task runner with per-project frequency
Checks Notion for tasks, plans, executes, commits, and logs
"""

import json
import yaml
import os
import time
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.planner_agent import PlannerAgent
from agents.executor_agent import ExecutorAgent
from agents.commit_agent import CommitAgent
from cto.connector import CTOConnector
from notion.notion_client import NotionClient

class MainLoop:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.projects = self._load_projects()
        self.settings = self._load_settings()
        
        # Initialize agents
        self.planner = PlannerAgent(config_path)
        self.executor = ExecutorAgent(config_path)
        self.commit_agent = CommitAgent(config_path)
        self.cto_connector = CTOConnector()
        self.notion_client = NotionClient()
        
        print("[MainLoop] Orchestrator initialized")
        print(f"[MainLoop] Managing {len(self.projects)} projects")
    
    def _load_projects(self):
        """Load projects configuration"""
        projects_path = os.path.join(self.config_path, "projects.json")
        with open(projects_path, 'r') as f:
            return json.load(f)
    
    def _load_settings(self):
        """Load system settings"""
        settings_path = os.path.join(self.config_path, "settings.yaml")
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def check_for_tasks(self, project: dict) -> list:
        """
        Poll Notion for new tasks for a project
        Placeholder: Returns dummy tasks for now
        """
        tasks_db = project.get('notion_db_tasks')
        
        if not tasks_db:
            return []
        
        # Placeholder: Query Notion for tasks
        # tasks = self.notion_client.query_tasks(tasks_db, {"status": "To Do"})
        
        print(f"[MainLoop] Checking tasks for {project['name']}")
        return []  # Return new tasks
    
    def process_project(self, project: dict):
        """
        Process a single project:
        1. Check for tasks
        2. Plan each task
        3. Execute
        4. Commit (if allowed)
        5. Log to Notion
        """
        project_name = project['name']
        repo_path = project['repo']
        
        print(f"\n[MainLoop] === Processing {project_name} ===")
        
        # Check for tasks
        tasks = self.check_for_tasks(project)
        
        if not tasks:
            print(f"[MainLoop] No new tasks for {project_name}")
            return
        
        for task in tasks:
            print(f"\n[MainLoop] Processing task: {task}")
            
            try:
                # Plan the task
                plan = self.planner.plan_task(task, project_name)
                
                # Execute the task
                result = self.executor.execute_task(plan)
                
                # Commit if allowed
                if result.get('success') and project.get('auto_commit'):
                    commit_result = self.commit_agent.commit_changes(
                        plan,
                        os.path.join(self.config_path, '..', repo_path)
                    )
                    print(f"[MainLoop] Commit result: {commit_result}")
                
                # Log to Notion (both master and project DBs)
                run_data = {
                    "run_id": f"run-{datetime.now().timestamp()}",
                    "project": project_name,
                    "timestamp": datetime.now().isoformat(),
                    "status": result.get('status'),
                    "actions": json.dumps(plan, indent=2),
                    "errors": result.get('error', '')
                }
                
                # Log to master runs DB (placeholder)
                # self.notion_client.log_run(master_runs_db_id, run_data)
                
                # Log to project runs DB (placeholder)
                if project.get('notion_db_runs'):
                    # self.notion_client.log_run(project['notion_db_runs'], run_data)
                    pass
                
            except Exception as e:
                print(f"[MainLoop] ERROR processing task: {e}")
        
        print(f"[MainLoop] === Finished {project_name} ===\n")
    
    def run_once(self):
        """Run one iteration through all projects"""
        print(f"\n[MainLoop] Starting run at {datetime.now()}")
        
        for project in self.projects:
            if not project['repo']:  # Skip unconfigured projects
                continue
            
            try:
                self.process_project(project)
            except Exception as e:
                print(f"[MainLoop] ERROR in {project['name']}: {e}")
        
        print(f"[MainLoop] Run completed at {datetime.now()}\n")
    
    def run_continuous(self):
        """
        Continuous loop with per-project frequency checking
        """
        print("[MainLoop] Starting continuous mode")
        print("[MainLoop] Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.run_once()
                
                # Sleep until next check (use shortest frequency)
                shortest_freq = min([
                    p.get('run_frequency', self.settings.get('default_run_frequency', 300))
                    for p in self.projects if p['repo']
                ])
                
                print(f"[MainLoop] Sleeping for {shortest_freq}s...")
                time.sleep(shortest_freq)
        
        except KeyboardInterrupt:
            print("\n[MainLoop] Stopped by user")

if __name__ == "__main__":
    # Use relative path to config from runner directory
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config')
    
    loop = MainLoop(config_path)
    
    # Run once for testing
    loop.run_once()
    
    # Or run continuous:
    # loop.run_continuous()
