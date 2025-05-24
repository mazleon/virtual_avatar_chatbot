#!/usr/bin/env python3
"""
LiveKit Voice Agent - Python Backend

This script implements a voice agent that connects to a LiveKit server,
processes audio from participants, and responds with synthesized speech.
"""

import os
import sys
import asyncio
import logging
import argparse
from dotenv import load_dotenv
import numpy as np
import openai
from livekit import rtc, api
from pydub import AudioSegment
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default configuration
DEFAULT_LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
DEFAULT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
DEFAULT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secret")
DEFAULT_ROOM_NAME = os.getenv("LIVEKIT_ROOM", "agent-room")
DEFAULT_IDENTITY = os.getenv("LIVEKIT_IDENTITY", "agent")

class VoiceAgent:
    def __init__(self, livekit_url, api_key, api_secret, room_name, identity):
        self.livekit_url = livekit_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.room_name = room_name
        self.identity = identity
        self.room = rtc.Room()
        self.audio_buffer = []
        self.is_processing = False
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Set up event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Set up event handlers for LiveKit room events."""
        
        @self.room.on("participant_connected")
        def on_participant_connected(participant):
            logger.info(f"Participant connected: {participant.identity}")
        
        @self.room.on("participant_disconnected")
        def on_participant_disconnected(participant):
            logger.info(f"Participant disconnected: {participant.identity}")
        
        @self.room.on("track_subscribed")
        def on_track_subscribed(track, publication, participant):
            logger.info(f"Track subscribed: {track.kind} from {participant.identity}")
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                audio_stream = rtc.AudioStream(track)
                asyncio.ensure_future(self._process_audio(audio_stream, participant))
    
    async def _process_audio(self, audio_stream, participant):
        """Process incoming audio from a participant."""
        async for frame in audio_stream:
            # Add audio frame to buffer
            self.audio_buffer.append(frame.data)
            
            # Process audio if we have enough data and not already processing
            if len(self.audio_buffer) >= 50 and not self.is_processing:  # ~1 second of audio
                self.is_processing = True
                audio_data = self._combine_audio_frames(self.audio_buffer)
                self.audio_buffer = []
                
                # Process in a separate task to not block audio reception
                asyncio.create_task(self._handle_speech(audio_data, participant))
    
    def _combine_audio_frames(self, frames):
        """Combine multiple audio frames into a single numpy array."""
        return np.concatenate(frames)
    
    async def _handle_speech(self, audio_data, participant):
        """Process speech and generate a response."""
        try:
            # Convert numpy array to wav file in memory
            audio_segment = self._numpy_to_audio_segment(audio_data)
            
            # Save audio to a temporary file-like object
            audio_file = io.BytesIO()
            audio_segment.export(audio_file, format="wav")
            audio_file.seek(0)
            
            # Use OpenAI Whisper for speech-to-text
            transcript = await asyncio.to_thread(
                self._transcribe_audio, 
                audio_file
            )
            
            if transcript:
                logger.info(f"Transcribed from {participant.identity}: {transcript}")
                
                # Generate response using OpenAI
                response_text = await asyncio.to_thread(
                    self._generate_response,
                    transcript
                )
                
                logger.info(f"Response to {participant.identity}: {response_text}")
                
                # Convert text to speech
                speech_audio = await asyncio.to_thread(
                    self._text_to_speech,
                    response_text
                )
                
                # Publish the audio response
                await self._publish_audio_response(speech_audio)
        except Exception as e:
            logger.error(f"Error processing speech: {e}")
        finally:
            self.is_processing = False
    
    def _numpy_to_audio_segment(self, audio_data):
        """Convert numpy array to AudioSegment."""
        # Assuming 16-bit PCM audio at 48kHz (LiveKit default)
        return AudioSegment(
            audio_data.tobytes(),
            frame_rate=48000,
            sample_width=2,
            channels=1
        )
    
    def _transcribe_audio(self, audio_file):
        """Transcribe audio using OpenAI Whisper."""
        try:
            result = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return result.text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def _generate_response(self, text):
        """Generate a response using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant. Keep responses concise and natural."},
                    {"role": "user", "content": text}
                ],
                max_tokens=os.getenv("MAX_TOKENS", 150)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return "I'm sorry, I couldn't process that request."
    
    def _text_to_speech(self, text):
        """Convert text to speech using OpenAI TTS."""
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            # Get the audio content as bytes
            audio_data = io.BytesIO()
            for chunk in response.iter_bytes(chunk_size=4096):
                audio_data.write(chunk)
            audio_data.seek(0)
            
            # Convert to the format needed for LiveKit
            audio_segment = AudioSegment.from_file(audio_data, format="mp3")
            return audio_segment
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            return None
    
    async def _publish_audio_response(self, audio_segment):
        """Publish audio response to the room."""
        if not audio_segment:
            return
        
        try:
            # Convert audio to the format needed by LiveKit
            # This is a simplified version - actual implementation would need to match
            # LiveKit's audio format requirements
            audio_data = np.array(audio_segment.get_array_of_samples())
            
            # Create a local audio track
            source = rtc.AudioSource()
            track = source.create_track()
            
            # Publish the track
            await self.room.local_participant.publish_track(track)
            
            # Send the audio data
            source.capture_frame(audio_data)
            
            # Wait a bit for the audio to be sent
            await asyncio.sleep(audio_segment.duration_seconds)
            
            # Unpublish the track
            await self.room.local_participant.unpublish_track(track)
        except Exception as e:
            logger.error(f"Error publishing audio: {e}")
    
    async def connect(self):
        """Connect to the LiveKit room."""
        try:
            # Create a token for the agent
            token = rtc.AccessToken(self.api_key, self.api_secret)
            token.add_grant(
                rtc.RoomJoinOptions(
                    room=self.room_name,
                    identity=self.identity,
                    name=f"Voice Agent ({self.identity})"
                )
            )
            
            # Connect to the room
            await self.room.connect(self.livekit_url, token.to_jwt())
            logger.info(f"Connected to room: {self.room_name}")
            
            # Stay connected indefinitely
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise

async def main():
    parser = argparse.ArgumentParser(description="LiveKit Voice Agent")
    parser.add_argument("--url", default=os.getenv("LIVEKIT_URL", DEFAULT_LIVEKIT_URL),
                        help="LiveKit server URL")
    parser.add_argument("--api-key", default=os.getenv("LIVEKIT_API_KEY", DEFAULT_API_KEY),
                        help="LiveKit API key")
    parser.add_argument("--api-secret", default=os.getenv("LIVEKIT_API_SECRET", DEFAULT_API_SECRET),
                        help="LiveKit API secret")
    parser.add_argument("--room", default=os.getenv("LIVEKIT_ROOM", DEFAULT_ROOM_NAME),
                        help="LiveKit room name")
    parser.add_argument("--identity", default=os.getenv("LIVEKIT_IDENTITY", DEFAULT_IDENTITY),
                        help="Agent identity")
    
    args = parser.parse_args()
    
    # Create and connect the agent
    agent = VoiceAgent(
        args.url,
        args.api_key,
        args.api_secret,
        args.room,
        args.identity
    )
    
    await agent.connect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent error: {e}")
        sys.exit(1)
