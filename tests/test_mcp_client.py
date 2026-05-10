import asyncio
import json
import subprocess
import sys


async def test_mcp_server():
    """Launch the server and send test MCP messages."""
    
    print("=== Testing GitHub MCP Server ===\n")
    
    # Start the server process
    server_process = subprocess.Popen(
        [sys.executable, "-m", "github_mcp.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # Give server time to start
        await asyncio.sleep(2)
        
        # Test 1: Initialize handshake
        print("Test 1: Sending initialize request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        server_process.stdin.write(json.dumps(init_request) + "\n")
        server_process.stdin.flush()
        
        # Read response with timeout
        try:
            response_line = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, server_process.stdout.readline),
                timeout=5.0
            )
            if response_line:
                response = json.loads(response_line)
                print(f"Initialize response: {json.dumps(response, indent=2)}\n")
        except asyncio.TimeoutError:
            print("Timeout waiting for initialize response\n")
        
        # Test 2: Send initialized notification
        print("Test 2: Sending initialized notification...")
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized"
        }
        
        server_process.stdin.write(json.dumps(initialized_notification) + "\n")
        server_process.stdin.flush()
        await asyncio.sleep(1)
        
        # Test 3: List tools
        print("Test 3: Listing tools...")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        server_process.stdin.write(json.dumps(list_tools_request) + "\n")
        server_process.stdin.flush()
        
        try:
            response_line = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, server_process.stdout.readline),
                timeout=5.0
            )
            if response_line:
                response = json.loads(response_line)
                print(f"List tools response: {json.dumps(response, indent=2)}\n")
                
                if "result" in response and "tools" in response["result"]:
                    tools = response["result"]["tools"]
                    print(f"Found {len(tools)} tools:")
                    for tool in tools:
                        print(f"  - {tool['name']}: {tool['description']}")
        except asyncio.TimeoutError:
            print("Timeout waiting for tools/list response\n")
        
        # Test 4: Call hello_world tool
        print("\nTest 4: Calling hello_world tool...")
        call_tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "hello_world",
                "arguments": {"name": "MCP Developer"}
            }
        }
        
        server_process.stdin.write(json.dumps(call_tool_request) + "\n")
        server_process.stdin.flush()
        
        try:
            response_line = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, server_process.stdout.readline),
                timeout=5.0
            )
            if response_line:
                response = json.loads(response_line)
                print(f"Call tool response: {json.dumps(response, indent=2)}\n")
                
                if "result" in response and "content" in response["result"]:
                    content = response["result"]["content"][0]["text"]
                    print(f"Tool returned: {content}")
        except asyncio.TimeoutError:
            print("Timeout waiting for tools/call response\n")
        
        # Test 5: Call echo tool
        print("\nTest 5: Calling echo tool...")
        call_tool_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "echo",
                "arguments": {
                    "message": "Hello from test client!",
                    "uppercase": True
                }
            }
        }
        
        server_process.stdin.write(json.dumps(call_tool_request) + "\n")
        server_process.stdin.flush()
        
        try:
            response_line = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, server_process.stdout.readline),
                timeout=5.0
            )
            if response_line:
                response = json.loads(response_line)
                print(f"Call tool response: {json.dumps(response, indent=2)}\n")
                
                if "result" in response and "content" in response["result"]:
                    content = response["result"]["content"][0]["text"]
                    print(f"Tool returned: {content}")
        except asyncio.TimeoutError:
            print("Timeout waiting for tools/call response\n")
        
        # Test 6: Shutdown
        print("\nTest 6: Shutting down...")
        shutdown_request = {
            "jsonrpc": "2.0",
            "method": "shutdown"
        }
        
        server_process.stdin.write(json.dumps(shutdown_request) + "\n")
        server_process.stdin.flush()
        await asyncio.sleep(1)
        
    except Exception as e:
        print(f"Error during test: {e}")
        # Read stderr for debugging
        stderr_data = server_process.stderr.read()
        if stderr_data:
            print(f"Server stderr: {stderr_data}")
    finally:
        # Terminate server
        server_process.terminate()
        try:
            await asyncio.wait_for(asyncio.get_event_loop().run_in_executor(None, server_process.wait), timeout=2.0)
        except:
            server_process.kill()
        print("\n=== Tests complete ===")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
