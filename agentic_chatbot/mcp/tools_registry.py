# mcp/tools_registry.py

import os
import importlib

TOOLS = {}

TOOLS_METADATA = []


def load_tools():
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"mcp.tools.{filename[:-3]}"
            module = importlib.import_module(module_name)

            if hasattr(module, "TOOL"):
                tool_def = module.TOOL
                TOOLS[tool_def["name"]] = tool_def["handler"]

                TOOLS_METADATA.append({
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "schema": tool_def["schema"]
                })


load_tools()