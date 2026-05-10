

import sys
print("Python path:", sys.path[:3])

print("\n1. Importing contents module...")
try:
    from github_mcp.tools import contents
    print("✓ contents module imported")
except Exception as e:
    print(f"✗ Failed to import contents: {e}")
    sys.exit(1)

print("\n2. Checking get_tool_handlers before registration...")
handlers_before = contents.get_tool_handlers()
print(f"Handlers before registration: {list(handlers_before.keys())}")

print("\n3. Registering tools...")
class MockServer:
    pass

contents.register_tools(MockServer())
print("✓ Tools registered")

print("\n4. Checking get_tool_handlers after registration...")
handlers_after = contents.get_tool_handlers()
print(f"Handlers after registration: {list(handlers_after.keys())}")

print("\n5. Checking tool definitions...")
definitions = contents.get_tool_definitions()
print(f"Tool definitions: {[tool.name for tool in definitions]}")

print("\n✓ All checks passed!")