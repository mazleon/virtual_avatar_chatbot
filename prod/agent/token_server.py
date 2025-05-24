#!/usr/bin/env python3
"""
Token Server for LiveKit Voice Agent

This script provides a simple HTTP server to generate LiveKit tokens for the frontend.
"""

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from livekit import rtc

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get LiveKit configuration from environment variables
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secretkeythatshouldbeatleast32chars")
DEFAULT_ROOM = os.getenv("LIVEKIT_ROOM", "agent-room")
DEFAULT_IDENTITY = os.getenv("FRONTEND_IDENTITY", "user")

@app.route('/get-token', methods=['GET'])
def get_token():
    """Generate a LiveKit token for the frontend."""
    room_name = request.args.get('room', DEFAULT_ROOM)
    identity = request.args.get('identity', DEFAULT_IDENTITY)
    
    try:
        # Create a token for the user
        token = rtc.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.add_grant(
            rtc.RoomJoinOptions(
                room=room_name,
                identity=identity,
                name=f"{identity.capitalize()}"
            )
        )
        
        # Return the token as JSON
        return jsonify({
            "token": token.to_jwt(),
            "room": room_name,
            "identity": identity
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
