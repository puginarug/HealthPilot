"""MCP Server Registry.

Central registry for all MCP servers and their tools.
Provides unified access to tools across all servers.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp_servers.health_data_server import health_data_server
from mcp_servers.nutrition_server import nutrition_server
from mcp_servers.wellness_server import wellness_server

logger = logging.getLogger(__name__)


class MCPRegistry:
    """Registry of all MCP servers and their tools.

    Provides:
    - Tool discovery across servers
    - Server metadata access
    - Unified tool list for agent binding
    """

    def __init__(self) -> None:
        self.servers = [
            nutrition_server,
            health_data_server,
            wellness_server,
        ]
        logger.info("Initialized MCP registry with %d servers", len(self.servers))

    def get_all_tools(self) -> list:
        """Get all tools from all registered servers.

        Returns:
            Combined list of all tools.
        """
        tools = []
        for server in self.servers:
            tools.extend(server.get_tools())
        logger.debug("Collected %d total tools from MCP servers", len(tools))
        return tools

    def get_tools_by_server(self, server_name: str) -> list:
        """Get tools from a specific server.

        Args:
            server_name: Name of the server (e.g., "nutrition", "health-data").

        Returns:
            List of tools from that server.
        """
        for server in self.servers:
            if server.name == server_name:
                return server.get_tools()
        return []

    def get_server_info(self) -> list[dict[str, Any]]:
        """Get metadata about all registered servers.

        Returns:
            List of server info dicts with name, description, tool count.
        """
        return [
            {
                "name": server.name,
                "description": server.description,
                "tool_count": len(server.get_tools()),
                "tools": server.get_tool_names(),
            }
            for server in self.servers
        ]

    def list_servers(self) -> list[str]:
        """Get names of all registered servers.

        Returns:
            List of server names.
        """
        return [server.name for server in self.servers]


# Global registry instance
mcp_registry = MCPRegistry()


def get_all_tools() -> list:
    """Convenience function to get all tools from the registry.

    Returns:
        Combined list of all MCP tools.
    """
    return mcp_registry.get_all_tools()
