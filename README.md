# Destino — Autonomous Multi-Agent Travel System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-StateGraph-FF6F61)](https://langchain-ai.github.io/langgraph/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Model_Context_Protocol-6B21A8)](https://modelcontextprotocol.io)
[![Groq](https://img.shields.io/badge/Inference-Llama_3.3_70B_via_Groq-f50057)](https://groq.com)

Created & Maintained by **Param Pandya** ([parampandya.dev](https://parampandya.dev))

---

## 🌟 Overview

**Destino** is a production-grade, stateful autonomous multi-agent travel orchestration system. Built using **LangGraph**, the **Model Context Protocol (MCP)**, and **FastAPI**, Destino converts natural language travel requests into personalized, budget-conscious, and weather-aware itineraries.

Unlike single-prompt chatbot wrappers, Destino uses a central **Supervisor Agent** to decompose queries, validate inputs via **Domain Guardrails**, dynamically select domain specialist agents (flights, hotels, weather, budget), and pause execution for **Human-in-the-Loop (HITL)** approval before generating final itineraries.


---

## 🖼️ Application Screenshot

![Destino Dashboard](static/destino_dashboard_screenshot.png)

*Destino Dark Glassmorphism Interface featuring real-time Supervisor execution tracking, currency selection, quick-start prompts, and interactive Human-in-the-Loop review.*

---

## 🚀 Key Features

- 🧠 **Supervisor Agent & Input Guardrails**: Automatically filters out non-travel or unsafe queries, extracts key travel constraints (origin, destination, budget, duration), and routes work dynamically to relevant sub-agents.
- 🔌 **Model Context Protocol (MCP)**: Standardized, decoupled tool access connecting agents to live APIs:
  - **Tavily MCP**: Web search engine for curated stay suggestions, neighborhood safety, and local attractions.
  - **AviationStack MCP**: Aviation metadata for airline routes, leg options, and peak season airfare warnings.
  - **Custom OpenWeather FastMCP Server**: Built-in microservice for real-time temperatures, humidity, and 5-period weather forecasts.
- 👤 **Human-in-the-Loop (HITL) Checkpoint**: Uses LangGraph's `interrupt()` state mechanism to present draft itineraries to the user for approval or revision before generating final outputs.
- 💰 **Multi-Currency Budget Analyst**: Computes estimates and normalizes monetary amounts across **INR (₹)**, **USD ($)**, **EUR (€)**, and **GBP (£)**.
- 📄 **Export Capabilities**: Built-in Markdown renderer, clipboard copy, and formatted PDF export engine (`html2pdf`).
- 📚 **Dedicated System Documentation**: Built-in `/docs` route offering an in-depth system architecture breakdown, agent roles, and engineering design rationale.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([👤 User Request]) --> Guardrail{🧠 Input Guardrail}
    Guardrail -- Off-Topic / Unsafe --> Blocked[❌ Request Blocked]
    Guardrail -- Valid Travel Query --> Supervisor[👔 Supervisor Agent]
    
    Supervisor -->|Dynamic Routing| Flight[✈️ Flight Agent / AviationStack MCP]
    Supervisor -->|Dynamic Routing| Hotel[🏨 Hotel Agent / Tavily MCP]
    Supervisor -->|Dynamic Routing| Weather[🌤️ Weather Agent / OpenWeather FastMCP]
    Supervisor -->|Dynamic Routing| Budget[💰 Budget Analyst Agent]
    
    Flight --> Itinerary[🗺️ Itinerary Aggregator Agent]
    Hotel --> Itinerary
    Weather --> Itinerary
    Budget --> Itinerary
    
    Itinerary --> HITL[👤 Human-in-the-Loop Interrupt]
    
    HITL -- Reject + Feedback --> Final[✨ Final Response Agent]
    HITL -- Approve --> Final
    
    Final --> PDF[📄 Final Plan & PDF Download]
```

---

## 🤖 Specialist Agents & Tools

| Agent | Icon | MCP / Tool Integration | Primary Responsibility |
| :--- | :---: | :--- | :--- |
| **Supervisor & Guardrail** | 🧠 | `Llama-3.3-70B` | Validates query relevance, extracts constraints, plans execution, and routes to sub-agents. |
| **Flight Agent** | ✈️ | AviationStack MCP (`uvx`) | Retrieves airport metadata, airline routes, connecting flight options, and airfare guidance. |
| **Hotel Discovery** | 🏨 | Tavily Search MCP (`stdio`/`http`) | Performs web searches for luxury/budget accommodations, guest reviews, and safe neighborhoods. |
| **Weather Specialist** | 🌤️ | Custom OpenWeather FastMCP | Fetches current weather metrics, 5-day forecasts, and seasonal packing suggestions. |
| **Budget Analyst** | 💰 | LLM Financial Feasibility Engine | Analyzes cost breakdowns, surge pricing risks, and formats all figures in the selected currency. |
| **Itinerary Aggregator** | 🗺️ | Multi-source Synthesis Engine | Combines flight, hotel, weather, and budget outputs into a structured draft itinerary. |
| **Human-in-the-Loop** | 👤 | LangGraph `interrupt()` | Pauses execution state for user review, supporting approval or feedback-driven revision. |

---

## 📁 Project Structure

```
.
├── app.py                         # FastAPI Web Application & REST Endpoints (/api/travel, /docs, /health)
├── backend.py                     # LangGraph StateGraph, Supervisor routing, agents & checkpointer setup
├── mcp_client.py                  # MultiServerMCPClient adapter (Tavily, AviationStack, OpenWeather)
├── custom_weather_mcp_server.py   # FastMCP Weather microservice querying OpenWeather API
├── templates/
│   ├── index.html                 # Application-first homepage UI with hero, planner & HITL card
│   └── docs.html                  # Technical documentation & system architecture overview page
├── static/
│   ├── style.css                  # Modern glassmorphism CSS design system & micro-animations
│   ├── script.js                 # Client-side state handler, API calls & PDF export engine
│   └── destino_dashboard_screenshot.png # Application dashboard screenshot asset
├── .env.example                   # Template for environment variables and API keys
├── requirements.txt               # Python package dependencies
├── Dockerfile                     # Containerization build setup
└── README.md                      # Comprehensive project documentation
```

---

## 🛠️ Quick Start Guide

### Prerequisites

- **Python 3.10+** installed on your system.
- **uv / uvx** package manager (required for running `aviationstack-mcp`). Install via `pip install uv`.
- API Keys for **Groq**, **Tavily**, **OpenWeather** *(optional)*, and **AviationStack** *(optional)*.

### 1. Clone the Repository

```bash
git clone https://github.com/Param-Pandya/destino.git
cd destino
```

### 2. Set Up Virtual Environment

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
TAVILY_API_KEY=tvly_your_tavily_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here   # Optional
AVIATION_STACK_API_KEY=your_aviationstack_key_here   # Optional
DATABASE_URL=postgresql://user:pass@localhost:5432/destino # Optional (defaults to MemorySaver)
```

### 5. Launch the Server

```powershell
python app.py
```

Navigating to **http://127.0.0.1:8000**:
- **Application Interface**: `http://127.0.0.1:8000/`
- **Technical Documentation**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/health`

---

## 📡 REST API Reference

### 1. Generate Travel Plan Draft
`POST /api/travel`

**Request Body:**
```json
{
  "message": "Plan a 7-day trip to Japan with flights, hotels, and sightseeing under 2 lakhs INR",
  "currency": "INR (₹ / Rupees)"
}
```

**Response:**
```json
{
  "success": true,
  "thread_id": "user_a1b2c3d4",
  "answer": "Draft itinerary markdown...",
  "requires_approval": true,
  "approval_request": "Please review the generated draft itinerary...",
  "selected_agents": ["flight_agent", "hotel_agent", "weather_agent", "budget_agent", "itinerary_agent"],
  "trip_constraints": {
    "destination": "Japan",
    "duration": "7 days",
    "budget": "200,000 INR"
  }
}
```

### 2. Submit Human-in-the-Loop Review
`POST /api/travel/approve`

**Request Body (Approve):**
```json
{
  "thread_id": "user_a1b2c3d4",
  "approved": true,
  "feedback": "",
  "currency": "INR (₹ / Rupees)"
}
```

**Request Body (Request Revision):**
```json
{
  "thread_id": "user_a1b2c3d4",
  "approved": false,
  "feedback": "Reduce hotel budget and add one day for Kyoto traditional tea ceremony.",
  "currency": "INR (₹ / Rupees)"
}
```

---

## 👨‍💻 Author & License

Designed and Engineered by **Param Pandya**  
- Website: [parampandya.dev](https://parampandya.dev)  
- GitHub: [@param-pandya](https://github.com/param-pandya)
- Linkedin: [parampandya](https://www.linkedin.com/in/parampandya/)
 
Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
