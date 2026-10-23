"""Quick check that the MCP server works. Start server.py first, then run this."""
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "http://localhost:8000/mcp"


async def main():
    async with streamablehttp_client(URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            print("Tools:", [t.name for t in tools])

            calls = [
                ("list_datasets", {}),
                ("describe_dataset", {"dataset": "sales"}),
                ("top_n", {"dataset": "sales", "metric": "revenue", "group_by": "region", "n": 3}),
                ("trend", {"dataset": "sales", "metric": "revenue"}),
                ("compare", {"dataset": "sales", "metric": "revenue", "group_by": "region",
                             "first": "South", "second": "North"}),
            ]
            for name, args in calls:
                result = await session.call_tool(name, args)
                print(f"\n{name}:\n{result.content[0].text}")


asyncio.run(main())
