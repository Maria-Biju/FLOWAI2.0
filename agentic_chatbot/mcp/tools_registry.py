# mcp/tools_registry.py
import os
import importlib

TOOLS = {}
TOOLS_METADATA = []


def load_tools():
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")

    for filename in sorted(os.listdir(tools_dir)):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue

        module_name = f"mcp.tools.{filename[:-3]}"

        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            print(f"[TOOLS REGISTRY] Skipping {module_name}: {e}")
            continue

        if hasattr(module, "TOOL"):
            tool_def = module.TOOL

            TOOLS[tool_def["name"]] = tool_def["handler"]
            TOOLS_METADATA.append({
                "name": tool_def["name"],
                "description": tool_def["description"],
                "schema": tool_def["schema"]
            })


load_tools()