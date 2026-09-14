from operator import mod
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
from langchain_groq import ChatGroq

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATION_STACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


client = MultiServerMCPClient(
    {
        "tavily":{
            "transport": "streamable_http",

            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}",

        },
        "Aviationstack MCP": {
            "transport": "stdio",
      "command": "uvx",
      "args": [
        "--with",
        "mcp<2",
        "aviationstack-mcp"
      ],
      "env": {
        "AVIATION_STACK_API_KEY": AVIATION_STACK_API_KEY
      }, 
      
    },
    'weather_mcp': {
        "transport": "stdio",
        "command": "python",
        "args": [
            "custom_weather_mcp_server.py"
        ],
        "env": {
            "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY or ""
        }
    }
    }
)

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key= os.getenv("GROQ_API_KEY")
)

async def get_all_tools():
    tools = await client.get_tools()
    print("\n Available Tools \n")
    for tool in tools:
        print(tool.name)



### tavily and avaition functions
search_tool = None
aviation_tools = {

}

async def initilize_mcp():
    global search_tool
    global aviation_tools

    if search_tool is not None and aviation_tools:
        return

    tools = await client.get_tools()
    print("\n\n Available tools")

    for tool in tools:
        print(tool.name)
        
    search_tool = next(
        tool
        for tool in tools
        if tool.name == "tavily_search"
    )

    aviation_tools = {
        tool.name: tool
        for toll in tools
        if tool.name != "tavily_search"
    }


async def tavily_mcp_search(query:str):
    await initilize_mcp()
    result = await search_tool.ainvoke({"query":query})
    return result


async def aviation_mcp_call(
    tool_name: str,
    tool_agrs: dict = None
):
    tools = await client.get_tools()
    tool = next(
        t for t in tools
        if t.name == tool_name
    )

    result = await tool.ainvoke(
        tool_agrs or {}
    )

    return result


async def weather_mcp_call(
    tool_name: str,
    tool_args: dict = None
):
    tools = await client.get_tools()
    tool = next(
        t for t in tools
        if t.name == tool_name
    )

    result = await tool.ainvoke(
        tool_args or {}
    )

    return result


### Wether tools

weather_tool = None
forecast_tool = None

async def initilize_weather_tools():
    global weather_tool, forecast_tool

    if weather_tool is not None:
        return
    
    tools = await client.get_tools()

    weather_tool = next(
        t for t in tools
        if t.name == "get_current_weather"
    )

    forecast_tool = next(
        t for t in tools
        if t.name == "get_forecast"
    )


async def weather_mcp_search(query:str):
    await initilize_weather_tools()
    return await weather_tool.ainvoke({
        'city': query
    })


async def forecast_mcp_search(query:str):
    await initilize_weather_tools()
    return await forecast_tool.ainvoke({
        'city': query
    }
)


# Destination Extractor

def extract_destination(query:str):
    prompt = f"""
    Extract only the destination city or country.
    
    Query:
    {query}

    Return only the destinaton name

    """

    response = llm.invoke(prompt).content
    return response.strip()