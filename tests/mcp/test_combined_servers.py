"""
Test Combined External MCP Servers
Demonstrates using multiple external servers together
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp_client_simple import SimpleMCPClient


async def test_combined_servers():
    """Test multiple external servers working together."""
    print("=" * 60)
    print("Testing Combined External MCP Servers")
    print("=" * 60)
    print()
    print("This demonstrates how OSSARTH can use multiple external")
    print("servers together to solve complex problems.")
    print()

    # Start both servers
    print("1. Starting servers...")
    memory_client = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-memory"])
    thinking_client = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-sequential-thinking"])

    try:
        # Initialize both
        await memory_client.start()
        await thinking_client.start()
        print("   Both servers started")

        await memory_client.initialize()
        await thinking_client.initialize()
        print("   Both servers initialized")
        print()

        # Scenario: Use sequential thinking to plan, then store in memory
        print("2. Scenario: Plan project steps, then store in knowledge graph")
        print("-" * 60)
        print()

        # Use thinking server to plan
        print("Step 1: Use Sequential Thinking to plan MCP integration")
        thought_1 = await thinking_client.call_tool("sequentialthinking", {
            "thought": "To integrate MCP servers into OSSARTH, I need to: 1) Replace stdio_client with working implementation",
            "nextThoughtNeeded": True,
            "thoughtNumber": 1,
            "totalThoughts": 3
        })
        print(f"   Thought 1 recorded")

        thought_2 = await thinking_client.call_tool("sequentialthinking", {
            "thought": "2) Create ExternalServerManager to handle multiple servers and their lifecycle",
            "nextThoughtNeeded": True,
            "thoughtNumber": 2,
            "totalThoughts": 3
        })
        print(f"   Thought 2 recorded")

        thought_3 = await thinking_client.call_tool("sequentialthinking", {
            "thought": "3) Load servers from default.yaml configuration and test integration",
            "nextThoughtNeeded": False,
            "thoughtNumber": 3,
            "totalThoughts": 3
        })
        print(f"   Thought 3 recorded (plan complete)")
        print()

        # Store plan in memory server
        print("Step 2: Store plan in Memory knowledge graph")

        # Create project entity
        project_entity = await memory_client.call_tool("create_entities", {
            "entities": [{
                "name": "MCP_Integration_Plan",
                "entityType": "project",
                "observations": [
                    "Plan to integrate MCP servers into OSSARTH",
                    "Created via sequential thinking process",
                    "Date: January 7, 2026"
                ]
            }]
        })
        print(f"   Created project entity")

        # Create task entities
        tasks = await memory_client.call_tool("create_entities", {
            "entities": [
                {
                    "name": "Replace_stdio_client",
                    "entityType": "task",
                    "observations": [
                        "Replace existing stdio_client with SimpleMCPClient",
                        "Priority: High",
                        "Status: Planned"
                    ]
                },
                {
                    "name": "Create_ExternalServerManager",
                    "entityType": "task",
                    "observations": [
                        "Create manager for external server lifecycle",
                        "Priority: High",
                        "Status: Planned"
                    ]
                },
                {
                    "name": "Load_from_config",
                    "entityType": "task",
                    "observations": [
                        "Load servers from default.yaml",
                        "Priority: Medium",
                        "Status: Planned"
                    ]
                }
            ]
        })
        print(f"   Created 3 task entities")

        # Create relationships
        relations = await memory_client.call_tool("create_relations", {
            "relations": [
                {
                    "from": "MCP_Integration_Plan",
                    "to": "Replace_stdio_client",
                    "relationType": "includes"
                },
                {
                    "from": "MCP_Integration_Plan",
                    "to": "Create_ExternalServerManager",
                    "relationType": "includes"
                },
                {
                    "from": "MCP_Integration_Plan",
                    "to": "Load_from_config",
                    "relationType": "includes"
                },
                {
                    "from": "Replace_stdio_client",
                    "to": "Create_ExternalServerManager",
                    "relationType": "depends_on"
                }
            ]
        })
        print(f"   Created 4 relationships")
        print()

        # Read back the graph
        print("Step 3: Verify stored knowledge graph")
        graph = await memory_client.call_tool("read_graph")

        entities = graph['structuredContent']['entities']
        relations_list = graph['structuredContent']['relations']

        print(f"   Graph contains:")
        print(f"   - {len(entities)} entities")
        print(f"   - {len(relations_list)} relations")
        print()

        # Search for project
        print("Step 4: Search for MCP-related items")
        search_result = await memory_client.call_tool("search_nodes", {
            "query": "MCP"
        })
        print(f"   Found {len(search_result.get('structuredContent', {}).get('results', []))} matching nodes")
        print()

        print("=" * 60)
        print("SUCCESS: Combined server operation working!")
        print("=" * 60)
        print()
        print("What we demonstrated:")
        print("1. Sequential Thinking - Created 3-step plan")
        print("2. Memory - Stored plan as knowledge graph")
        print("3. Memory - Created entities and relationships")
        print("4. Memory - Searched and retrieved data")
        print()
        print("This shows how OSSARTH can:")
        print("- Use thinking server for planning/reasoning")
        print("- Store results in memory for persistence")
        print("- Query knowledge graph for information")
        print("- Combine multiple servers for complex tasks")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n\nCleaning up...")
        await memory_client.close()
        await thinking_client.close()
        print("Both servers stopped")


if __name__ == "__main__":
    asyncio.run(test_combined_servers())
