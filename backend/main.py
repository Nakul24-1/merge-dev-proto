from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.api.endpoints.candidates import router as candidates_router
from app.api.endpoints.webhooks import router as webhooks_router

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

# Include routers
app.include_router(candidates_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Automated Candidate Screening API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
