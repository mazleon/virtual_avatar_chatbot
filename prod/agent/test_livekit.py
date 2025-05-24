#!/usr/bin/env python3
"""
Test connectivity to the LiveKit server.
"""

import asyncio
import os
import dotenv
from livekit import rtc

# Load environment variables
dotenv.load_dotenv()

# Get LiveKit configuration from environment variables
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://robiassistant-f38d9mhx.livekit.cloud")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secretkeythatshouldbeatleast32chars")
ROOM_NAME = os.getenv("LIVEKIT_ROOM", "agent-room")
IDENTITY = "test-user"

async def main():
    # Create a token
    token = rtc.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.add_grant(
        rtc.RoomJoinOptions(
            room=ROOM_NAME,
            identity=IDENTITY,
            name=IDENTITY
        )
    )
    jwt = token.to_jwt()
    print(f"Generated token: {jwt}")
    
    # Create a room
    room = rtc.Room()
    
    # Set up event handlers
    @room.on("connected")
    def on_connected():
        print(f"Connected to room: {room.name}")
    
    @room.on("disconnected")
    def on_disconnected():
        print("Disconnected from room")
    
    @room.on("connection_state_changed")
    def on_connection_state_changed(state):
        print(f"Connection state changed: {state}")
    
    # Try to connect
    try:
        print(f"Connecting to {LIVEKIT_URL}...")
        await room.connect(LIVEKIT_URL, jwt)
        print("Connected successfully!")
        
        # Wait a bit
        await asyncio.sleep(5)
        
        # Disconnect
        await room.disconnect()
        print("Disconnected successfully!")
    except Exception as e:
        print(f"Error connecting to LiveKit: {e}")

if __name__ == "__main__":
    asyncio.run(main())
