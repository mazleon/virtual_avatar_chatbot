#!/usr/bin/env python3
"""
Standalone script to run the FastAPI server
"""

import os
import uvicorn

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("API_PORT", 5000))
    
    print(f"Starting FastAPI server on port {port}...")
    
    # Run the FastAPI server with uvicorn
    uvicorn.run(
        "agent.fastapi_server_new:app", 
        host="0.0.0.0", 
        port=port,
        reload=True
    )
