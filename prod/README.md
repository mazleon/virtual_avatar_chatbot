# LiveKit Voice Agent

A voice agent system using LiveKit for real-time communication between a Python backend agent and a React frontend.

## Project Structure

```
voice_agent/
├── agent/                # Python voice agent
│   ├── main.py           # Main agent code
│   ├── token_server.py   # Token generation server
│   ├── generate_token.py # Token generation script
│   └── requirements.txt  # Python dependencies
├── docker/               # Docker configuration
│   ├── docker-compose.yml # LiveKit server configuration
│   └── livekit.yaml      # LiveKit server config
├── frontend/             # React frontend
│   ├── package.json      # Frontend dependencies
│   ├── public/           # Static assets
│   └── src/              # React source code
├── .env                  # Environment variables
├── start.sh             # Startup script
├── README.md            # This file
└── PROJECT_PLAN.md      # Detailed project plan
```

## Prerequisites

- Docker Desktop
- Python 3.8+ with uv package manager
- Node.js 16+ and npm

## Quick Start

The easiest way to run the entire system is using the provided startup script:

```bash
# Make the script executable if needed
chmod +x start.sh

# Run the startup script
./start.sh
```

This will start the LiveKit server, Python agent, token server, and React frontend all at once.

## Manual Setup Instructions

### 1. LiveKit Server (Docker)

1. Start the LiveKit server using Docker:

```bash
cd docker
docker-compose up -d
```

2. Verify the server is running:

```bash
docker ps
```

### 2. Python Voice Agent

1. Set up the Python environment using uv:

```bash
cd agent

# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies using uv
uv pip install -r requirements.txt --system
```

2. Start the token server:

```bash
python token_server.py
```

3. In a new terminal, activate the environment and run the agent:

```bash
cd agent
source .venv/bin/activate
python main.py
```

### 3. React Frontend

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Start the development server:

```bash
npm start
```

3. Open your browser and navigate to http://localhost:3000

## Configuration

The system uses the following default configuration:

- LiveKit Server URL: ws://localhost:7880
- Room name: agent-room
- Agent identity: agent
- Frontend identity: user

You can modify these settings in the `.env` file.

## Testing the Connection

You can generate a test token using the provided script:

```bash
cd agent
source .venv/bin/activate
python generate_token.py --json
```

This will output a token you can use to test the connection.

## Development

- Python Agent: Modify `agent/main.py` to customize agent behavior
- Frontend: Edit files in `frontend/src/` to customize the UI

## Troubleshooting

- If components can't connect, ensure they're all using the same LiveKit server URL and room name
- Check Docker logs for LiveKit server issues: `docker logs livekit-server`
- Verify the token server is running: `curl http://localhost:8000/health`
- Make sure your OpenAI API key is correctly set in the `.env` file
- If audio processing isn't working, check the audio device settings in the `.env` file
