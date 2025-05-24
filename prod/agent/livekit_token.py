#!/usr/bin/env python3
"""
Generate a LiveKit token for testing purposes.
"""

import os
import sys
import argparse
from livekit import rtc

def generate_token(api_key, api_secret, room_name, identity):
    token = rtc.AccessToken(api_key, api_secret)
    grant = rtc.RoomJoinOptions(
        room=room_name,
        identity=identity,
        name=identity
    )
    token.add_grant(grant)
    return token.to_jwt()

def main():
    parser = argparse.ArgumentParser(description="Generate a LiveKit token")
    parser.add_argument("--api-key", required=True, help="LiveKit API key")
    parser.add_argument("--api-secret", required=True, help="LiveKit API secret")
    parser.add_argument("--room", default="agent-room", help="Room name")
    parser.add_argument("--identity", default="user", help="Identity")
    
    args = parser.parse_args()
    
    token = generate_token(args.api_key, args.api_secret, args.room, args.identity)
    print(f"Token: {token}")

if __name__ == "__main__":
    main()
