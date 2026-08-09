import os
import shutil
import sys
from pathlib import Path
from typing import Any
import requests

import certifi
from dotenv import load_dotenv
from langchain_groq import ChatGroq

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    HAS_MCP_CLIENT = True
except Exception as exc:
    print(f"MultiServerMCPClient import warning: {exc}", flush=True)
    MultiServerMCPClient = Any
    HAS_MCP_CLIENT = False


# =========================================================
# Environment setup
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

WEATHER_SERVER_PATH = BASE_DIR / "custom_weather_mcp_server.py"


def get_env_var(name: str, fallback_name: str | None = None) -> str | None:
    val = os.getenv(name)
    if not val and fallback_name:
        val = os.getenv(fallback_name)
    return val


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if name == "AVIATION_STACK_API_KEY" and not val:
        val = os.getenv("AVIATIONSTACK_API_KEY")
    if not val:
        raise RuntimeError(
            f"{name} is missing. "
            f"Please configure {name} in your environment variables."
        )
    return val


def get_llm():
    groq_key = _require_env("GROQ_API_KEY")
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=groq_key,
    )


# =========================================================
# Lazy MCP Client Initialization
# =========================================================

_mcp_client: Any | None = None
_mcp_client_attempted: bool = False


def get_mcp_client() -> Any | None:
    global _mcp_client, _mcp_client_attempted

    if _mcp_client_attempted:
        return _mcp_client

    _mcp_client_attempted = True
    if not HAS_MCP_CLIENT:
        return None

    tavily_key = get_env_var("TAVILY_API_KEY")
    aviation_key = get_env_var("AVIATION_STACK_API_KEY", "AVIATIONSTACK_API_KEY")
    openweather_key = get_env_var("OPENWEATHER_API_KEY")
    uvx_cmd = shutil.which("uvx")

    mcp_servers: dict[str, Any] = {}

    if tavily_key:
        mcp_servers["tavily"] = {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_key}",
        }

    if aviation_key and uvx_cmd and not os.getenv("VERCEL"):
        mcp_servers["aviationstack"] = {
            "transport": "stdio",
            "command": uvx_cmd,
            "args": ["aviationstack-mcp"],
            "env": {**os.environ, "AVIATION_STACK_API_KEY": aviation_key},
        }

    if openweather_key and WEATHER_SERVER_PATH.is_file() and not os.getenv("VERCEL"):
        mcp_servers["weather"] = {
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(WEATHER_SERVER_PATH)],
            "env": {**os.environ, "OPENWEATHER_API_KEY": openweather_key},
        }

    if mcp_servers:
        try:
            _mcp_client = MultiServerMCPClient(mcp_servers)
        except Exception as exc:
            print(f"MCP Client initialization warning: {exc}", flush=True)

    return _mcp_client


async def _get_server_tool(server_name: str, tool_name: str):
    client = get_mcp_client()
    if not client:
        return None

    try:
        tools = await client.get_tools(server_name=server_name)
        return next((t for t in tools if t.name == tool_name), None)
    except Exception as exc:
        print(f"Error fetching tool '{tool_name}' from MCP server '{server_name}': {exc}", flush=True)
        return None


# =========================================================
# MCP Connection Diagnostic Test
# =========================================================

async def get_all_tools() -> None:
    client = get_mcp_client()
    if not client:
        print("MCP Client is not initialized.")
        return

    for server_name in ("tavily", "aviationstack", "weather"):
        try:
            tools = await client.get_tools(server_name=server_name)
            tool_names = ", ".join(t.name for t in tools) or "no tools"
            print(f"{server_name}: OK -> {tool_names}")
        except Exception as exc:
            print(f"{server_name}: FAILED -> {type(exc).__name__}: {exc}")


# =========================================================
# Tavily Search (MCP with HTTP REST Fallback)
# =========================================================

async def tavily_mcp_search(query: str):
    tavily_key = get_env_var("TAVILY_API_KEY")

    tool = await _get_server_tool("tavily", "tavily_search")
    if tool:
        try:
            return await tool.ainvoke({"query": query})
        except Exception as exc:
            print(f"Tavily MCP invocation failed: {exc}. Using HTTP REST fallback.", flush=True)

    if not tavily_key:
        return "Tavily web search unavailable: TAVILY_API_KEY is not configured."

    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": tavily_key, "query": query, "search_depth": "basic"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return "No hotel or accommodation results found for this query."
        return "\n\n".join(
            [f"Title: {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')}" for r in results[:5]]
        )
    except Exception as exc:
        return f"Tavily search error: {exc}"


# =========================================================
# AviationStack (MCP with HTTP REST/Data Fallback)
# =========================================================

async def aviation_mcp_call(
    tool_name: str,
    tool_args: dict[str, Any] | None = None,
):
    aviation_key = get_env_var("AVIATION_STACK_API_KEY", "AVIATIONSTACK_API_KEY")

    tool = await _get_server_tool("aviationstack", tool_name)
    if tool:
        try:
            return await tool.ainvoke(tool_args or {})
        except Exception as exc:
            print(f"AviationStack MCP invocation failed: {exc}. Using fallback.", flush=True)

    if tool_name == "list_airports":
        if aviation_key:
            try:
                r = requests.get(
                    f"http://api.aviationstack.com/v1/airports?access_key={aviation_key}&limit=20",
                    timeout=10,
                )
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
        return {
            "airports": [
                {"name": "Haneda Airport (HND)", "city": "Tokyo"},
                {"name": "Narita International Airport (NRT)", "city": "Tokyo"},
                {"name": "Dubai International Airport (DXB)", "city": "Dubai"},
                {"name": "Suvarnabhumi Airport (BKK)", "city": "Bangkok"},
                {"name": "Indira Gandhi International Airport (DEL)", "city": "Delhi"},
            ]
        }

    if tool_name == "list_airlines":
        if aviation_key:
            try:
                r = requests.get(
                    f"http://api.aviationstack.com/v1/airlines?access_key={aviation_key}&limit=20",
                    timeout=10,
                )
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
        return {
            "airlines": [
                "Japan Airlines", "ANA", "Emirates", "Qatar Airways",
                "Singapore Airlines", "Air India", "IndiGo", "British Airways"
            ]
        }

    return {"status": "available", "info": "Aviation metadata retrieved."}


# =========================================================
# OpenWeather (MCP with Direct HTTP REST Fallback)
# =========================================================

async def weather_mcp_search(city: str):
    openweather_key = get_env_var("OPENWEATHER_API_KEY")

    tool = await _get_server_tool("weather", "get_current_weather")
    if tool:
        try:
            return await tool.ainvoke({"city": city})
        except Exception as exc:
            print(f"Weather MCP invocation failed: {exc}. Using REST fallback.", flush=True)

    if not openweather_key:
        return f"Live weather data for {city} unavailable: OPENWEATHER_API_KEY is not configured. Provide general seasonal guidance."

    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": openweather_key, "units": "metric"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        return (
            f"City: {data.get('name')}, "
            f"Temp: {data['main']['temp']}°C (Feels like: {data['main']['feels_like']}°C), "
            f"Humidity: {data['main']['humidity']}%, "
            f"Condition: {data['weather'][0]['description']}"
        )
    except Exception as exc:
        return f"Weather API error for {city}: {exc}"


async def forecast_mcp_search(city: str):
    openweather_key = get_env_var("OPENWEATHER_API_KEY")

    tool = await _get_server_tool("weather", "get_forecast")
    if tool:
        try:
            return await tool.ainvoke({"city": city})
        except Exception as exc:
            print(f"Forecast MCP invocation failed: {exc}. Using REST fallback.", flush=True)

    if not openweather_key:
        return f"Weather forecast for {city} unavailable: OPENWEATHER_API_KEY is not configured."

    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"q": city, "appid": openweather_key, "units": "metric", "cnt": 5},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        forecasts = [
            f"{item.get('dt_txt', '')}: {item['main']['temp']}°C, {item['weather'][0]['description']}"
            for item in data.get("list", [])
        ]
        return "\n".join(forecasts)
    except Exception as exc:
        return f"Forecast API error for {city}: {exc}"


# =========================================================
# Destination Extractor
# =========================================================

def extract_destination(query: str) -> str:
    prompt = f"""
Extract only the destination city or country from the travel request.

Travel request:
{query}

Return only the destination name.
Do not add any explanation.
"""

    llm = get_llm()
    response = llm.invoke(prompt)

    destination = str(response.content).strip()

    if not destination:
        raise ValueError("The destination could not be extracted.")

    return destination