import React, { useState } from 'react';
import { Room, RoomEvent } from 'livekit-client';
import '@livekit/components-styles';

function App() {
  const [roomName, setRoomName] = useState('agent-room');
  const [token, setToken] = useState('');
  const [room, setRoom] = useState(null);
  const [connectionState, setConnectionState] = useState('disconnected');
  const [messages, setMessages] = useState([]);
  const [isMicrophoneActive, setIsMicrophoneActive] = useState(false);

  // Fetch token from server
  const fetchToken = async () => {
    try {
      const response = await fetch(`http://localhost:8000/get-token?room=${roomName}&identity=user`);
      const data = await response.json();
      if (data.token) {
        setToken(data.token);
        return data.token;
      } else {
        throw new Error('No token received');
      }
    } catch (e) {
      console.error('Error fetching token:', e);
      // Fallback to hardcoded token for testing - this token is generated with the new secret
      const fallbackToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTY2NzY4MDAsImlzcyI6ImRldmtleSIsIm5hbWUiOiJVc2VyIiwibmJmIjoxNzE2NTkwNDAwLCJzdWIiOiJ1c2VyIiwidmlkZW8iOnsicm9vbSI6ImFnZW50LXJvb20iLCJyb29tSm9pbiI6dHJ1ZX19.mNrTj8NqIJj_hSQ9MQgxoOJm8rlF_EfYR78xo7K4Ym0';
      setToken(fallbackToken);
      return fallbackToken;
    }
  };

  const addMessage = (sender, text) => {
    setMessages(prev => [...prev, { sender, text, timestamp: new Date() }]);
  };

  const handleConnect = async () => {
    setConnectionState('connecting');
    try {
      // Get token if not already available
      const currentToken = token || await fetchToken();
      
      // Create a new room
      const newRoom = new Room({
        adaptiveStream: true,
        dynacast: true,
        publishDefaults: {
          simulcast: true,
          audioEnabled: isMicrophoneActive,
        },
      });
      
      // Set up event listeners
      newRoom.on(RoomEvent.ParticipantConnected, (participant) => {
        addMessage('System', `${participant.identity} joined the room`);
      });
      
      newRoom.on(RoomEvent.ParticipantDisconnected, (participant) => {
        addMessage('System', `${participant.identity} left the room`);
      });
      
      newRoom.on(RoomEvent.Disconnected, () => {
        setConnectionState('disconnected');
        addMessage('System', 'Disconnected from room');
      });
      
      newRoom.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        addMessage('System', `Subscribed to ${track.kind} track from ${participant.identity}`);
        
        // Attach audio track to audio element
        if (track.kind === 'audio') {
          const audioElement = document.createElement('audio');
          audioElement.id = `audio-${participant.identity}-${track.sid}`;
          audioElement.autoplay = true;
          document.getElementById('audio-container').appendChild(audioElement);
          track.attach(audioElement);
        }
      });
      
      // Connect to the room
      await newRoom.connect('wss://robiassistant-f38d9mhx.livekit.cloud', currentToken);
      setRoom(newRoom);
      setConnectionState('connected');
      addMessage('System', 'Connected to room. You can now speak with the agent.');
      
      // Enable microphone if needed
      if (isMicrophoneActive) {
        await newRoom.localParticipant.setMicrophoneEnabled(true);
      }
      
    } catch (e) {
      console.error('Connection error:', e);
      setConnectionState('disconnected');
      addMessage('System', `Connection error: ${e.message}`);
    }
  };

  const handleDisconnect = () => {
    if (room) {
      room.disconnect();
      setRoom(null);
    }
    setConnectionState('disconnected');
  };

  const toggleMicrophone = async () => {
    const newState = !isMicrophoneActive;
    setIsMicrophoneActive(newState);
    
    if (room && room.localParticipant) {
      try {
        await room.localParticipant.setMicrophoneEnabled(newState);
        addMessage('System', newState ? 'Microphone enabled' : 'Microphone disabled');
      } catch (e) {
        console.error('Error toggling microphone:', e);
        addMessage('System', `Error toggling microphone: ${e.message}`);
      }
    }
  };

  return (
    <div className="container">
      <div className="header">
        <h1 className="title">LiveKit Voice Agent</h1>
        <h2 className="subtitle">Talk with an AI voice assistant</h2>
      </div>

      <div className="card">
        <div className="room-controls">
          <div>
            <label htmlFor="room-name">Room Name: </label>
            <input
              id="room-name"
              type="text"
              value={roomName}
              onChange={(e) => setRoomName(e.target.value)}
              disabled={connectionState === 'connected'}
            />
          </div>
          
          <div className="controls">
            {connectionState !== 'connected' ? (
              <button 
                className="button" 
                onClick={handleConnect}
                disabled={connectionState === 'connecting'}
              >
                {connectionState === 'connecting' ? 'Connecting...' : 'Connect'}
              </button>
            ) : (
              <>
                <button 
                  className="button" 
                  onClick={toggleMicrophone}
                >
                  {isMicrophoneActive ? 'Mute Microphone' : 'Unmute Microphone'}
                </button>
                <button 
                  className="button" 
                  onClick={handleDisconnect}
                >
                  Disconnect
                </button>
              </>
            )}
          </div>
          
          <div className={`status ${connectionState}`}>
            Status: {connectionState.charAt(0).toUpperCase() + connectionState.slice(1)}
          </div>
        </div>
      </div>

      <div id="audio-container" style={{ display: 'none' }}></div>

      <div className="card">
        <h3>Conversation</h3>
        <div className="transcript">
          {messages.length === 0 ? (
            <p>No messages yet. Connect to the room and start speaking.</p>
          ) : (
            messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`message ${msg.sender.toLowerCase() === 'user' ? 'user' : 
                             msg.sender.toLowerCase() === 'agent' ? 'agent' : ''}`}
              >
                <div className="message-sender">{msg.sender}</div>
                <p className="message-text">{msg.text}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
