#!/usr/bin/env python3
"""
Direct FastAPI Server for Voice Agent

This script provides a FastAPI server to process audio from the frontend,
generate responses, and convert them to speech.
"""

import os
import uuid
import logging
from typing import Dict
from pathlib import Path

# Import for environment variables
try:
    from dotenv import load_dotenv
except ImportError:
    # Create a simple load_dotenv function if the package is not available
    def load_dotenv():
        pass
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Voice Agent API", description="API for processing audio and generating responses")

# Create directories for temporary files
TEMP_DIR = Path("./temp")
AUDIO_DIR = TEMP_DIR / "audio"
TEMP_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

# Add CORS middleware with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)

# Mount static files directory
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")

class ResponseModel(BaseModel):
    user_text: str
    response_text: str
    audio_id: str

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/api/process-audio")
async def process_audio(audio: UploadFile = File(...)):
    """
    Process audio end-to-end:
    1. Transcribe audio
    2. Generate response
    3. Convert response to speech
    
    Args:
        audio: The audio file to process
        
    Returns:
        JSON with transcribed text, response text, and audio ID
    """
    try:
        # For testing, we'll simulate the processing
        # In a real implementation, you would use OpenAI APIs
        
        # Generate a unique ID for the audio file
        audio_id = str(uuid.uuid4())
        
        # Save the uploaded file for reference
        with open(TEMP_DIR / f"input_{audio_id}.webm", "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Simulate transcription
        user_text = "This is a simulated user message. In a real implementation, this would be transcribed from the audio."
        
        # Simulate response generation
        response_text = "This is a simulated response from the virtual assistant. The server is now working correctly!"
        
        # Create a simple audio file (empty for now)
        audio_path = AUDIO_DIR / f"{audio_id}.mp3"
        with open(audio_path, "wb") as f:
            # In a real implementation, this would be the TTS audio
            f.write(b"")
        
        return ResponseModel(
            user_text=user_text,
            response_text=response_text,
            audio_id=audio_id
        )
    
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{audio_id}")
async def get_audio(audio_id: str):
    """
    Retrieve audio file by ID.
    
    Args:
        audio_id: The ID of the audio file to retrieve
        
    Returns:
        Audio file
    """
    try:
        audio_path = AUDIO_DIR / f"{audio_id}.mp3"
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename="response.mp3"
        )
    
    except Exception as e:
        logger.error(f"Error retrieving audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
