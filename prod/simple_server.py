#!/usr/bin/env python3
"""
Simple HTTP Server for Voice Agent

This script provides a basic HTTP server to handle API requests from the frontend.
It uses only Python standard library modules to avoid dependency issues.
"""

import os
import json
import uuid
import http.server
import socketserver
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Create directories for temporary files
TEMP_DIR = Path("./temp")
AUDIO_DIR = TEMP_DIR / "audio"
TEMP_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

# Set port (using 8080 to avoid conflicts)
PORT = int(os.environ.get("API_PORT", 8080))

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler with CORS support"""
    
    def send_cors_headers(self):
        """Send CORS headers"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        # Health check endpoint
        if parsed_path.path == "/health":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return
        
        # Serve static files
        if parsed_path.path.startswith("/audio/"):
            file_name = parsed_path.path.split("/")[-1]
            file_path = AUDIO_DIR / file_name
            
            if file_path.exists():
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_cors_headers()
                self.end_headers()
                
                # Send empty audio file for now
                self.wfile.write(b"")
                return
        
        # Default to 404 for unknown paths
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Type", "application/json")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        # Process audio endpoint
        if parsed_path.path == "/api/process-audio":
            content_length = int(self.headers.get("Content-Length", 0))
            
            # Generate a unique ID for the audio file
            audio_id = str(uuid.uuid4())
            
            # Create a mock audio file
            audio_path = AUDIO_DIR / f"{audio_id}.mp3"
            with open(audio_path, "wb") as f:
                # In a real implementation, this would be the TTS audio
                f.write(b"")
            
            # Prepare the response
            response = {
                "user_text": "This is a simulated user message. In a real implementation, this would be transcribed from the audio.",
                "response_text": "This is a simulated response from the virtual assistant. The server is now working correctly!",
                "audio_id": audio_id
            }
            
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Default to 404 for unknown paths
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Type", "application/json")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())

def run_server():
    """Run the HTTP server"""
    handler = CORSHTTPRequestHandler
    
    # Allow the server to reuse the address
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
