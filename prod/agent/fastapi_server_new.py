#!/usr/bin/env python3
"""
FastAPI Server for Voice Agent

This script provides a FastAPI server to process audio from the frontend,
generate responses, and convert them to speech.
"""

import os
import uuid
import logging
from typing import Dict
from pathlib import Path

import dotenv
import openai
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()

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

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.warning("OPENAI_API_KEY not found in environment variables. Using empty string.")
    openai_api_key = ""

openai_client = openai.OpenAI(api_key=openai_api_key)

# Store audio files in memory
audio_files: Dict[str, str] = {}

class ResponseModel(BaseModel):
    user_text: str
    response_text: str
    audio_id: str

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio using OpenAI Whisper.
    
    Args:
        audio: The audio file to transcribe
        
    Returns:
        JSON with transcribed text
    """
    try:
        # Create a temporary file
        temp_file = TEMP_DIR / f"{uuid.uuid4()}.wav"
        
        # Save the uploaded file
        with open(temp_file, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Transcribe audio using OpenAI Whisper
        with open(temp_file, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # Clean up temporary file
        temp_file.unlink()
        
        return {"text": transcript.text}
    
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-response")
async def generate_response(request: Request):
    """
    Generate a response using OpenAI GPT.
    
    Args:
        request: JSON with 'text' field containing the user's message
        
    Returns:
        JSON with generated response
    """
    try:
        data = await request.json()
        if not data or 'text' not in data:
            raise HTTPException(status_code=400, detail="No text provided")
        
        user_text = data['text']
        
        # Generate response using OpenAI GPT
        response = openai_client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a helpful voice assistant. Keep responses concise and natural."},
                {"role": "user", "content": user_text}
            ],
            max_tokens=int(os.getenv("MAX_TOKENS", 150))
        )
        
        response_text = response.choices[0].message.content
        
        return {"text": response_text}
    
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/text-to-speech")
async def text_to_speech(request: Request):
    """
    Convert text to speech using OpenAI TTS.
    
    Args:
        request: JSON with 'text' field containing the text to convert
        
    Returns:
        Audio file
    """
    try:
        data = await request.json()
        if not data or 'text' not in data:
            raise HTTPException(status_code=400, detail="No text provided")
        
        text = data['text']
        
        # Convert text to speech using OpenAI TTS
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        # Generate a unique ID for the audio file
        audio_id = str(uuid.uuid4())
        
        # Save audio to a file
        audio_path = AUDIO_DIR / f"{audio_id}.mp3"
        with open(audio_path, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=4096):
                f.write(chunk)
        
        # Store the path for later retrieval
        audio_files[audio_id] = str(audio_path)
        
        return {"audio_id": audio_id}
    
    except Exception as e:
        logger.error(f"Error converting text to speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        # Create a temporary file
        temp_file = TEMP_DIR / f"{uuid.uuid4()}.wav"
        
        # Save the uploaded file
        with open(temp_file, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Transcribe audio using OpenAI Whisper
        with open(temp_file, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # Clean up temporary file
        temp_file.unlink()
        
        user_text = transcript.text
        
        # Generate response using OpenAI GPT
        response = openai_client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a helpful voice assistant. Keep responses concise and natural."},
                {"role": "user", "content": user_text}
            ],
            max_tokens=int(os.getenv("MAX_TOKENS", 150))
        )
        
        response_text = response.choices[0].message.content
        
        # Convert response to speech using OpenAI TTS
        tts_response = openai_client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=response_text
        )
        
        # Generate a unique ID for the audio file
        audio_id = str(uuid.uuid4())
        
        # Save audio to a file
        audio_path = AUDIO_DIR / f"{audio_id}.mp3"
        with open(audio_path, "wb") as f:
            for chunk in tts_response.iter_bytes(chunk_size=4096):
                f.write(chunk)
        
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
