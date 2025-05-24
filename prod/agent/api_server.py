#!/usr/bin/env python3
"""
API Server for Voice Agent

This script provides a Flask API server to process audio from the frontend,
generate responses, and convert them to speech.
"""

import os
import io
import tempfile
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openai
import dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio using OpenAI Whisper.
    
    Expects audio file in the request.
    Returns the transcribed text.
    """
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        
        # Save audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            audio_file.save(temp_audio.name)
            temp_audio_path = temp_audio.name
        
        # Transcribe audio using OpenAI Whisper
        with open(temp_audio_path, 'rb') as audio:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        
        # Clean up temporary file
        os.unlink(temp_audio_path)
        
        return jsonify({
            "text": transcript.text
        })
    
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-response', methods=['POST'])
def generate_response():
    """
    Generate a response using OpenAI GPT.
    
    Expects JSON with 'text' field containing the user's message.
    Returns the generated response.
    """
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
        
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
        
        return jsonify({
            "text": response_text
        })
    
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    """
    Convert text to speech using OpenAI TTS.
    
    Expects JSON with 'text' field containing the text to convert.
    Returns the audio file.
    """
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
        
        text = data['text']
        
        # Convert text to speech using OpenAI TTS
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        # Save audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
            for chunk in response.iter_bytes(chunk_size=4096):
                temp_audio.write(chunk)
            temp_audio_path = temp_audio.name
        
        # Send the audio file
        return send_file(
            temp_audio_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='response.mp3'
        )
    
    except Exception as e:
        logger.error(f"Error converting text to speech: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """
    Process audio end-to-end:
    1. Transcribe audio
    2. Generate response
    3. Convert response to speech
    
    Expects audio file in the request.
    Returns JSON with transcribed text, response text, and audio URL.
    """
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        
        # Save audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            audio_file.save(temp_audio.name)
            temp_audio_path = temp_audio.name
        
        # Transcribe audio using OpenAI Whisper
        with open(temp_audio_path, 'rb') as audio:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        
        # Clean up temporary file
        os.unlink(temp_audio_path)
        
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
        
        # Save audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
            for chunk in tts_response.iter_bytes(chunk_size=4096):
                temp_audio.write(chunk)
            temp_audio_path = temp_audio.name
        
        # Prepare response
        response_data = {
            "user_text": user_text,
            "response_text": response_text,
            "audio_path": f"/api/audio/{os.path.basename(temp_audio_path)}"
        }
        
        # Store the audio path for later retrieval
        app.config[os.path.basename(temp_audio_path)] = temp_audio_path
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    """
    Retrieve audio file by filename.
    """
    try:
        if filename not in app.config:
            return jsonify({"error": "Audio file not found"}), 404
        
        audio_path = app.config[filename]
        
        return send_file(
            audio_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='response.mp3'
        )
    
    except Exception as e:
        logger.error(f"Error retrieving audio: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
