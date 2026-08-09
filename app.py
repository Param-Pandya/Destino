from pathlib import Path
import traceback

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from backend import run_travel_agent_async, resume_travel_agent_async

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Destino",
    description=(
        "Destino — Autonomous Multi-Agent Travel System with Supervisor Routing, "
        "Input Guardrails, and Human-in-the-Loop Approval. Created by Param Pandya."
    ),
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
)

static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(static_dir)),
        name="static",
    )

templates_dir = BASE_DIR / "templates"
if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))
else:
    templates = None


class TravelRequest(BaseModel):
    message: str
    thread_id: str | None = None
    currency: str = "USD ($)"


class ApprovalRequest(BaseModel):
    thread_id: str = Field(min_length=1)
    approved: bool
    feedback: str = ""
    currency: str = "USD ($)"


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    if templates and (BASE_DIR / "templates" / "index.html").exists():
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={},
        )
    return HTMLResponse("<html><body><h1>Destino — Multi-Agent Travel System</h1><p>API is active. Visit <a href='/health'>/health</a>.</p></body></html>")


@app.get("/docs", response_class=HTMLResponse)
async def documentation(request: Request):
    if templates and (BASE_DIR / "templates" / "docs.html").exists():
        return templates.TemplateResponse(
            request=request,
            name="docs.html",
            context={},
        )
    return HTMLResponse("<html><body><h1>Destino Documentation</h1><p>Visit <a href='/health'>/health</a> for status.</p></body></html>")


@app.post("/api/travel")
async def travel_planner(request_data: TravelRequest):
    try:
        user_message = request_data.message.strip()

        if not user_message:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Message cannot be empty.",
                },
            )

        result = await run_travel_agent_async(
            user_input=user_message,
            thread_id=request_data.thread_id,
            currency=request_data.currency,
        )

        return JSONResponse(
            content={
                "success": True,
                **result,
            }
        )

    except Exception as exc:
        print("ERROR:", exc, flush=True)
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
            },
        )


@app.post("/api/travel/approve")
async def approve_travel_plan(request_data: ApprovalRequest):
    try:
        if not request_data.approved and not request_data.feedback.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Please provide revision feedback when rejecting the draft.",
                },
            )

        result = await resume_travel_agent_async(
            thread_id=request_data.thread_id,
            approved=request_data.approved,
            feedback=request_data.feedback,
        )

        return JSONResponse(
            content={
                "success": True,
                **result,
            }
        )

    except Exception as exc:
        print("APPROVAL ERROR:", exc, flush=True)
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
            },
        )


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    return "User-agent: *\nAllow: /\nSitemap: https://destino.parampandya.dev/sitemap.xml\n"


@app.get("/sitemap.xml")
async def sitemap_xml():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://destino.parampandya.dev/</loc>
    <lastmod>2026-08-08</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://destino.parampandya.dev/docs</loc>
    <lastmod>2026-08-08</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://parampandya.dev/</loc>
    <lastmod>2026-08-08</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>"""
    return Response(content=xml_content, media_type="application/xml")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "Destino API is running",
        "author": "Param Pandya (parampandya.dev)",
        "features": [
            "supervisor_agent",
            "input_guardrail",
            "human_in_the_loop",
        ],
    }


@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
