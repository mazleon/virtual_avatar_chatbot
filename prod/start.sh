#!/bin/bash
# Startup script for LiveKit Voice Agent

# Function to check if the LiveKit server is accessible
check_livekit() {
  echo "Checking connection to LiveKit server..."
  LIVEKIT_URL=$(grep LIVEKIT_URL .env | cut -d '=' -f2)
  
  if [[ $LIVEKIT_URL == wss://* ]]; then
    echo "Using external LiveKit server: $LIVEKIT_URL"
  else
    echo "Warning: Not using a secure WebSocket connection for LiveKit."
  fi
}

# Function to start the Python agent
start_agent() {
  echo "Setting up Python environment for agent..."
  cd agent
  
  # Create virtual environment using uv if it doesn't exist
  if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with uv..."
    uv venv
  fi
  
  # Activate virtual environment
  source .venv/bin/activate
  
  # Install dependencies
  echo "Installing dependencies with uv..."
  uv pip install -r agent/requirements.txt --system
  
  # Install FastAPI and its dependencies
  echo "Installing FastAPI and its dependencies with uv..."
  uv pip install fastapi uvicorn python-multipart --system
  
  # Start the FastAPI server in the background
  echo "Starting FastAPI server on port 5000..."
  cd agent && python fastapi_server_new.py &
  API_SERVER_PID=$!
  
  # Start the agent in the background
  echo "Starting voice agent..."
  python main.py &
  AGENT_PID=$!
  
  cd ..
  
  echo "Token server started with PID: $TOKEN_SERVER_PID"
  echo "Agent started with PID: $AGENT_PID"
}

# Function to start the React frontend
start_frontend() {
  echo "Setting up React frontend..."
  cd frontend
  
  # Install dependencies if node_modules doesn't exist
  if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
  fi
  
  # Try ports 3000, 3001, 3002, 3003, 3004, 3005 in sequence
  for PORT in 3000 3001 3002 3003 3004 3005; do
    if ! lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
      echo "Starting frontend development server on port $PORT..."
      PORT=$PORT npm start &
      break
    else
      echo "Port $PORT is already in use. Trying next port..."
      # If we've tried all ports and none are available
      if [ $PORT -eq 3005 ]; then
        echo "All ports (3000-3005) are in use. Please free up a port and try again."
        return 1
      fi
    fi
  done
  
  FRONTEND_PID=$!
  cd ..
  
  echo "Frontend started with PID: $FRONTEND_PID"
}

# Function to clean up on exit
cleanup() {
  echo "Shutting down components..."
  
  # Kill background processes
  if [ ! -z "$API_SERVER_PID" ]; then
    kill $API_SERVER_PID 2>/dev/null
  fi
  
  if [ ! -z "$AGENT_PID" ]; then
    kill $AGENT_PID 2>/dev/null
  fi
  
  if [ ! -z "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID 2>/dev/null
  fi
  
  # Nothing to clean up for Docker since we're using an external LiveKit server
  
  echo "All components have been shut down."
}

# Set up trap to clean up on exit
trap cleanup EXIT

# Main execution
echo "Starting LiveKit Voice Agent..."

# Check LiveKit server connection
check_livekit

# Start all components
start_agent
start_frontend

echo "All components started. Press Ctrl+C to stop."

# Keep script running
wait
