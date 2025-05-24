#!/usr/bin/env python3
"""
Standalone FastAPI Server Runner for Voice Agent
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("API_PORT", 5000))
    
    # Run the FastAPI server
    print(f"Starting FastAPI server on port {port}...")
    uvicorn.run(
        "fastapi_server_new:app", 
        host="0.0.0.0", 
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
