"""GitHub Adapter - GitHub integration for PRs, issues, and workflows."""

import os
from typing import Any, Optional

from github import AsyncGithub, GithubIntegration

from adapters.base import BaseAdapter, AdapterResult
from contracts.tool_contract import ToolContract, ToolType, ToolCapabilities


class GitHubAdapter(BaseAdapter):
    """GitHub adapter for PR creation, issue management, and workflow triggers."""

    def __init__(self):
        super().__init__()
        self._client: Optional[AsyncGithub] = None
        self._repo_owner: Optional[str] = None
        self._repo_name: Optional[str] = None

    @property
    def tool_contract(self) -> ToolContract:
        return ToolContract(
            name="github",
            type=ToolType.GITHUB,
            vendor="GitHub",
            version="1.0.0",
            description="GitHub integration for PR, issues, and workflow management",
            capabilities=ToolCapabilities(
                streaming=False,
                function_calling=False,
                vision=False,
                tools=False,
                batch=True,
                async_execution=True,
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "repo_owner": {"type": "string"},
                    "repo_name": {"type": "string"},
                    "installation_id": {"type": "string"},
                },
                "required": [],
            },
            env_vars=["GITHUB_TOKEN"],
            api_endpoint="https://api.github.com",
            documentation_url="https://docs.github.com/en/rest",
        )

    async def initialize(self, config: dict[str, Any]) -> None:
        token = config.get("api_key") or config.get("token") or os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN is required")

        self._client = AsyncGithub(login_or_token=token)
        self._repo_owner = config.get("repo_owner")
        self._repo_name = config.get("repo_name")
        await super().initialize(config)

    async def execute(self, input_data: dict[str, Any]) -> AdapterResult:
        if not self._initialized or not self._client:
            return AdapterResult(
                success=False,
                error="Adapter not initialized. Call initialize() first.",
            )

        try:
            operation = input_data.get("operation", "get_repo")

            if operation == "create_pr":
                return await self._create_pull_request(input_data)
            elif operation == "get_pr":
                return await self._get_pull_request(input_data)
            elif operation == "list_prs":
                return await self._list_pull_requests(input_data)
            elif operation == "create_issue":
                return await self._create_issue(input_data)
            elif operation == "get_issue":
                return await self._get_issue(input_data)
            elif operation == "list_issues":
                return await self._list_issues(input_data)
            elif operation == "create_branch":
                return await self._create_branch(input_data)
            elif operation == "delete_branch":
                return await self._delete_branch(input_data)
            elif operation == "trigger_workflow":
                return await self._trigger_workflow(input_data)
            elif operation == "get_repo":
                return await self._get_repo(input_data)
            else:
                return AdapterResult(success=False, error=f"Unknown operation: {operation}")
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    async def _get_repo(self, input_data: dict[str, Any]) -> AdapterResult:
        """Get repository information."""
        owner = input_data.get("owner") or self._repo_owner
        repo = input_data.get("repo") or self._repo_name

        if not owner or not repo:
            return AdapterResult(success=False, error="owner and repo are required")

        repository = await self._client.get_repo(f"{owner}/{repo}")

        return AdapterResult(
            success=True,
            data={
                "name": repository.name,
                "full_name": repository.full_name,
                "description": repository.description,
                "default_branch": repository.default_branch,
                "private": repository.private,
                "url": repository.html_url,
            },
            metadata={"operation": "get_repo"},
        )

    async def _create_pull_request(self, input_data: dict[str, Any]) -> AdapterResult:
        """Create a new pull request."""
        owner = input_data.get("owner") or self._repo_owner
        repo = input_data.get("repo") or self._repo_name

        if not owner or not repo:
            return AdapterResult(success=False, error="owner and repo are required")

        title = input_data.get("title")
        body = input_data.get("body", "")
        head = input_data.get("head")
        base = input_data.get("base", "main")

        if not title or not head:
            return AdapterResult(success=False, error="title and head are required")

        repository = await self._client.get_repo(f"{owner}/{repo}")
        pr = await repository.create_pull_request(title=title, body=body, head=head, base=base)

        return AdapterResult(
            success=True,
            data={
                "number": pr.number,
                "title": pr.title,
                "url": pr.html_url,
                "state": pr.state,
            },
            metadata={"operation": "create_pr"},
        )

    async def _get_pull_request(self, input_data: dict[str, Any]) -> AdapterResult:
        """Get a pull request by number."""
        owner = input_data.get("owner") or self._repo_owner
        repo = input_data.get("repo") or self._repo_name
        pr_number = input_data.get("pr_number")

        if not owner or not repo or not pr_number:
            return AdapterResult(success=False, error="owner, repo, and pr_number are required")

        repository = await self._client.get_repo(f"{owner}/{repo}")
        pr = await repository.get_pull_request(pr_number)

        return AdapterResult(
            success=True,
            data={
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "url": pr.html_url,
                "head": pr.head.ref,
                "base": pr.base.ref,
                "merged": pr.merged,
            },
            metadata={"operation": "get_pr"},
        )

    async def _list_pull_requests(self, input_data: dict[str, Any]) -> AdapterResult:
        """List pull requests."""
        owner = input_data.get("owner") or self._repo_owner
        repo = input_data.get("repo") or self._repo_name
        state = input_data.get("state", "open")

        if not owner or not repo:
            return AdapterResult(success=False, error="owner and repo are required")

        repository = await self._client.get_repo(f"{owner}/{repo}")
        pulls = await repository.get_pulls(state=state)

        pr_list = []
        async for pr in pulls:
            pr_list.append(
                {
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "url": pr.html_url,
                }
            )

        return AdapterResult(
            success=True,
            data={"pull_requests": pr_list, "count": len(pr_list)},
            metadata={"operation": "list_prs"},
        )

    async def _create_issue(self, input_data: dict[str, Any]) -> AdapterResult:
        """Create a new issue."""
        owner = input_data.get("owner") or self._repo_owner
        repo = input_data.get("repo") or self._repo_name

        if not owner or not repo:
            return AdapterResult(success=False, error="owner and repo are required")

        title = input_data.get("title")
        body = input_data.get("body", "")
        labels = input_data.get("labels", [])

        if not title:
            return AdapterResult(success=False, error="title is required")

        repository = await self._client.get_repo(f"{owner}/{repo}")
        issue = await repository.create_issue(title=title, body=body, labels=labels)

        return AdapterResult(
            success=True,
            data={
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "url": issue.html_url,
                "state": issue.state,
            },
            metadata={"operation": "create_issue"},
        )

    async def _get_issue(self, input_data: dict[str, Any]) -> AdapterResult:
        """Get an issue by number."""
        owner = input_data.get("owner") or self._repo_owner
        repo = input_data.get("repo") or self._repo_name
        issue_number = input_data.get("issue_number")

        if not owner or not repo or not issue_number:
            return AdapterResult(success=False, error="owner, repo, and issue_number are required")

        repository = await self._client.get_repo(f"{owner}/{repo}")
        issue = await repository.get_issue(issue_number)

        return AdapterResult(
            success=True,
            data={
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "url": issue.html_url,
                "labels": [label.name for label in issue.labels],
            },
            metadata={"operation": "get_issue"},
        )

    async def _list_issues(self, input_data: dict[str, Any]) -> AdapterResult:
        """List issues."""
        owner = input_data.get("owner") or self._repo_owner
        repo = input_data.get("repo") or self._repo_name
        state = input_data.get("state", "open")

        if not owner or not repo:
            return AdapterResult(success=False, error="owner and repo are required")

        repository = await self._client.get_repo(f"{owner}/{repo}")
        issues = await repository.get_issues(state=state)

        issue_list = []
        async for issue in issues:
            if not issue.pull_request:  # Exclude PRs from issues
                issue_list.append(
                    {
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "url": issue.html_url,
                    }
                )

        return AdapterResult(
            success=True,
            data={"issues": issue_list, "count": len(issue_list)},
            metadata={"operation": "list_issues"},
        )

    async def _create_branch(self, input_data: dict[str, Any]) -> AdapterResult:
        """Create a new branch."""
        owner = input_data.get("owner") or self._repo_owner
        repo = input_data.get("repo") or self._repo_name
        branch_name = input_data.get("branch_name")
        from_branch = input_data.get("from_branch", "main")

        if not owner or not repo or not branch_name:
            return AdapterResult(success=False, error="owner, repo, and branch_name are required")

        repository = await self._client.get_repo(f"{owner}/{repo}")

        # Get the source branch SHA
        source_branch = await repository.get_branch(from_branch)
        sha = source_branch.commit.sha

        # Create new branch
        await repository.create_git_ref(ref=f"refs/heads/{branch_name}, sha={sha}")

        return AdapterResult(
            success=True,
            data={"branch": branch_name, "sha": sha},
            metadata={"operation": "create_branch"},
        )

    async def _delete_branch(self, input_data: dict[str, Any]) -> AdapterResult:
        """Delete a branch."""
        owner = input_data.get("owner") or self._repo_owner
        repo = input_data.get("repo") or self._repo_name
        branch_name = input_data.get("branch_name")

        if not owner or not repo or not branch_name:
            return AdapterResult(success=False, error="owner, repo, and branch_name are required")

        repository = await self._client.get_repo(f"{owner}/{repo}")
        ref = await repository.get_git_ref(f"heads/{branch_name}")
        await ref.delete()

        return AdapterResult(
            success=True,
            data={"branch": branch_name, "deleted": True},
            metadata={"operation": "delete_branch"},
        )

    async def _trigger_workflow(self, input_data: dict[str, Any]) -> AdapterResult:
        """Trigger a workflow dispatch."""
        owner = input_data.get("owner") or self._repo_owner
        repo = input_data.get("repo") or self._repo_name
        workflow_id = input_data.get("workflow_id")
        ref = input_data.get("ref", "main")
        inputs = input_data.get("inputs", {})

        if not owner or not repo or not workflow_id:
            return AdapterResult(success=False, error="owner, repo, and workflow_id are required")

        repository = await self._client.get_repo(f"{owner}/{repo}")
        workflow = await repository.get_workflow(workflow_id)

        # Trigger workflow dispatch
        await workflow.dispatch(ref=ref, inputs=inputs)

        return AdapterResult(
            success=True,
            data={"workflow_id": workflow_id, "ref": ref, "triggered": True},
            metadata={"operation": "trigger_workflow"},
        )

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            user = await self._client.get_user()
            return user.login is not None
        except Exception:
            return False
