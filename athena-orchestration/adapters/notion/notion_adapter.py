"""Notion Adapter - Notion workspace integration."""

import os
from typing import Any, Optional

from notion_client import AsyncClient

from adapters.base import BaseAdapter, AdapterResult
from contracts.tool_contract import ToolContract, ToolType, ToolCapabilities


class NotionAdapter(BaseAdapter):
    """Notion adapter for page CRUD, database queries, and block updates."""

    def __init__(self):
        super().__init__()
        self._client: Optional[AsyncClient] = None

    @property
    def tool_contract(self) -> ToolContract:
        return ToolContract(
            name="notion",
            type=ToolType.NOTION,
            vendor="Notion",
            version="1.0.0",
            description="Notion integration for page and database operations",
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
                    "database_id": {"type": "string"},
                    "parent_page_id": {"type": "string"},
                },
                "required": [],
            },
            env_vars=["NOTION_API_KEY"],
            api_endpoint="https://api.notion.com/v1",
            documentation_url="https://developers.notion.com",
        )

    async def initialize(self, config: dict[str, Any]) -> None:
        api_key = config.get("api_key") or os.getenv("NOTION_API_KEY")
        if not api_key:
            raise ValueError("NOTION_API_KEY is required")

        self._client = AsyncClient(auth=api_key)
        self._config["database_id"] = config.get("database_id")
        self._config["parent_page_id"] = config.get("parent_page_id")
        await super().initialize(config)

    async def execute(self, input_data: dict[str, Any]) -> AdapterResult:
        if not self._initialized or not self._client:
            return AdapterResult(
                success=False,
                error="Adapter not initialized. Call initialize() first.",
            )

        try:
            operation = input_data.get("operation", "query")

            if operation == "create_page":
                return await self._create_page(input_data)
            elif operation == "update_page":
                return await self._update_page(input_data)
            elif operation == "get_page":
                return await self._get_page(input_data)
            elif operation == "delete_page":
                return await self._delete_page(input_data)
            elif operation == "query_database":
                return await self._query_database(input_data)
            elif operation == "create_database":
                return await self._create_database(input_data)
            elif operation == "append_block_children":
                return await self._append_block_children(input_data)
            else:
                return AdapterResult(success=False, error=f"Unknown operation: {operation}")
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    async def _create_page(self, input_data: dict[str, Any]) -> AdapterResult:
        """Create a new page in Notion."""
        properties = input_data.get("properties", {})
        content = input_data.get("content")
        parent_id = input_data.get("parent_id") or self._config.get("database_id")

        if not parent_id:
            return AdapterResult(success=False, error="No parent_id or database_id provided")

        page_params: dict[str, Any] = {"parent": {"database_id": parent_id}, "properties": properties}

        if content:
            page_params["children"] = self._parse_content(content)

        response = await self._client.pages.create(**page_params)

        return AdapterResult(
            success=True,
            data={"page_id": response.id, "url": response.url},
            metadata={"operation": "create_page"},
        )

    async def _update_page(self, input_data: dict[str, Any]) -> AdapterResult:
        """Update an existing page."""
        page_id = input_data.get("page_id")
        if not page_id:
            return AdapterResult(success=False, error="page_id is required")

        properties = input_data.get("properties", {})
        response = await self._client.pages.update(page_id=page_id, properties=properties)

        return AdapterResult(
            success=True,
            data={"page_id": response.id, "url": response.url},
            metadata={"operation": "update_page"},
        )

    async def _get_page(self, input_data: dict[str, Any]) -> AdapterResult:
        """Get a page by ID."""
        page_id = input_data.get("page_id")
        if not page_id:
            return AdapterResult(success=False, error="page_id is required")

        response = await self._client.pages.retrieve(page_id=page_id)

        return AdapterResult(
            success=True,
            data={"page": response},
            metadata={"operation": "get_page"},
        )

    async def _delete_page(self, input_data: dict[str, Any]) -> AdapterResult:
        """Archive a page (Notion doesn't support hard delete)."""
        page_id = input_data.get("page_id")
        if not page_id:
            return AdapterResult(success=False, error="page_id is required")

        # Archive the page instead of deleting
        response = await self._client.pages.update(page_id=page_id, archived=True)

        return AdapterResult(
            success=True,
            data={"page_id": response.id, "archived": True},
            metadata={"operation": "delete_page"},
        )

    async def _query_database(self, input_data: dict[str, Any]) -> AdapterResult:
        """Query a database with filters."""
        database_id = input_data.get("database_id") or self._config.get("database_id")
        if not database_id:
            return AdapterResult(success=False, error="database_id is required")

        filter_obj = input_data.get("filter")
        sorts = input_data.get("sorts")
        page_size = input_data.get("page_size", 100)

        response = await self._client.databases.query(
            database_id=database_id, filter=filter_obj, sorts=sorts, page_size=page_size
        )

        return AdapterResult(
            success=True,
            data={
                "results": [r.model_dump() for r in response.results],
                "has_more": response.has_more,
                "next_cursor": response.next_cursor,
            },
            metadata={"operation": "query_database"},
        )

    async def _create_database(self, input_data: dict[str, Any]) -> AdapterResult:
        """Create a new database."""
        parent_page_id = input_data.get("parent_page_id") or self._config.get("parent_page_id")
        if not parent_page_id:
            return AdapterResult(success=False, error="parent_page_id is required")

        title = input_data.get("title", "New Database")
        properties = input_data.get("properties", {})

        response = await self._client.databases.create(
            parent={"page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": title}}],
            properties=properties,
        )

        return AdapterResult(
            success=True,
            data={"database_id": response.id, "url": response.url},
            metadata={"operation": "create_database"},
        )

    async def _append_block_children(self, input_data: dict[str, Any]) -> AdapterResult:
        """Append block children to a page."""
        block_id = input_data.get("block_id") or input_data.get("page_id")
        if not block_id:
            return AdapterResult(success=False, error="block_id or page_id is required")

        children = input_data.get("children", [])
        if not children:
            return AdapterResult(success=False, error="children is required")

        response = await self._client.blocks.children.append(block_id=block_id, children=children)

        return AdapterResult(
            success=True,
            data={"results": [r.model_dump() for r in response.results]},
            metadata={"operation": "append_block_children"},
        )

    def _parse_content(self, content: str | list[dict]) -> list[dict]:
        """Parse content into Notion blocks."""
        if isinstance(content, list):
            return content

        # Convert string content to paragraphs
        paragraphs = content.split("\n\n")
        return [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": p}}]}} for p in paragraphs if p]

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            # Try to get user info as health check
            await self._client.users.me()
            return True
        except Exception:
            return False
