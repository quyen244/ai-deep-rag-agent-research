import asyncio
from fastmcp import Client


client = Client("http://localhost:8000/mcp")


async def call_tool(name : str):
    async with client:
        result = await client.call_tool("greet" , {"name" : name})
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()


        print(result) 
        print(result.content[0].text)

        print(tools)

asyncio.run(
    call_tool(
        'Quyen'
    )
)




