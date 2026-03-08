"""Anthology Backend - FastAPI Application"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scrape, projects

load_dotenv()

app = FastAPI(
    title="Anthology API",
    description="Scrape documentation websites and convert to Markdown for LLM context",
    version="1.0.0",
)

# Parse allowed origins from env or use defaults
origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
allowed_origins = [orig.strip() for orig in origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape.router, prefix="/api")
app.include_router(projects.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
