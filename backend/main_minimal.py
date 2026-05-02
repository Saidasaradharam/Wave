from fastapi import FastAPI
import logging
import os

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Wave API")

@app.get("/")
def root():
    return {
        "status": "ok", 
        "message": "Wave - Team Coordination Platform",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/info")
def info():
    return {
        "app": "Wave",
        "description": "Enterprise team coordination platform",
        "features": [
            "Project management",
            "Task tracking", 
            "Team collaboration",
            "Google Cloud integration"
        ]
    }