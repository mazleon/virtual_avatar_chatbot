#!/usr/bin/env python3
"""
Token Generator for LiveKit Voice Agent

This script generates access tokens for the LiveKit server.
"""

import argparse
import sys
from livekit import rtc
import json

def generate_token(api_key, api_secret, room_name, identity, ttl=86400):
    """Generate a LiveKit access token."""
    token = rtc.AccessToken(api_key, api_secret, ttl=ttl)
    grant = rtc.RoomJoinOptions(
        room=room_name,
        identity=identity,
        name=f"{identity.capitalize()}"
    )
    token.add_grant(grant)
    return token.to_jwt()

def main():
    parser = argparse.ArgumentParser(description="Generate LiveKit access tokens")
    parser.add_argument("--api-key", default="devkey", help="LiveKit API key")
    parser.add_argument("--api-secret", default="secretkeythatshouldbeatleast32chars", help="LiveKit API secret")
    parser.add_argument("--room", default="agent-room", help="Room name")
    parser.add_argument("--identity", default="user", help="Participant identity")
    parser.add_argument("--ttl", type=int, default=86400, help="Token TTL in seconds")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    try:
        token = generate_token(
            args.api_key,
            args.api_secret,
            args.room,
            args.identity,
            args.ttl
        )
        
        if args.json:
            result = {
                "token": token,
                "room": args.room,
                "identity": args.identity,
                "ttl": args.ttl
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"Token for {args.identity} in room {args.room}:")
            print(token)
    except Exception as e:
        print(f"Error generating token: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
