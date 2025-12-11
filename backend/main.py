from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app.api.endpoints.candidates import router as candidates_router
from app.api.endpoints.webhooks import router as webhooks_router
from app.api.endpoints.merge import router as merge_router

app = FastAPI(
    title="Automated Candidate Screening API",
    description="AI-powered candidate screening with ElevenLabs voice agents and Twilio telephony",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(candidates_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(merge_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Serve static frontend files if /static folder exists (production deployment)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    # Serve static assets
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")
    
    # SPA fallback - serve index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If it's an API route, let it 404 naturally
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}
        
        # Serve static file if exists
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Fallback to index.html for SPA routing
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    # Development mode - just show API info
    @app.get("/")
    def read_root():
        return {
            "message": "Welcome to the Automated Candidate Screening API",
            "docs": "/docs",
            "version": "1.0.0"
        }

