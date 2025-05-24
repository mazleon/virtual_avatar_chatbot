import React, { useState, useEffect, useRef } from 'react';
import './index.css';

// Import LiveKit components
import { LiveKitRoom, AudioRenderer, useRoom, useParticipant } from '@livekit/components-react';
import '@livekit/components-styles';

// API endpoint configuration
const API_BASE_URL = 'http://localhost:7880';
const TOKEN_ENDPOINT = 'http://localhost:5000/api/token';

// LiveKit configuration
const LIVEKIT_URL = 'ws://localhost:7880';
const ROOM_NAME = 'voice-agent-room';
const PARTICIPANT_NAME = 'user';

// Bank-specific configuration
const BANK_NAME = 'Modhumoti Bank PLC';
const ASSISTANT_NAME = 'Virtual Banking Assistant';

function SimpleApp() {
  // State variables
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState([
    { sender: 'System', text: 'Welcome to the Voice Agent demo. Click "Start Recording" to begin.' }
  ]);
  const [audioStream, setAudioStream] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [apiStatus, setApiStatus] = useState('unknown');
  const [recordingTime, setRecordingTime] = useState(0);
  const [volume, setVolume] = useState(0);
  const [textInput, setTextInput] = useState('');
  
  // Refs
  const timerRef = useRef(null);
  const animationRef = useRef(null);
  const audioAnalyserRef = useRef(null);
  const audioDataRef = useRef(null);
  const messagesEndRef = useRef(null);
  
  // Check API connection on mount
  useEffect(() => {
    checkApiConnection();
    
    // Clean up on unmount
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);
  
  // Auto-scroll to the bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Format recording time as MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = (seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };
  
  // Handle sending text messages
  const handleSendText = async () => {
    if (!textInput.trim() || isProcessing) return;
    
    setIsProcessing(true);
    addMessage('You', textInput);
    
    try {
      // Simulate sending text to the API
      // In a real implementation, you would send this to a text endpoint
      // For now, we'll simulate a response
      setTimeout(() => {
        const simulatedResponse = "Thank you for your message. As a virtual banking assistant for Modhumoti Bank, I'm here to help with your banking needs. How else can I assist you today?";
        addMessage('Agent', simulatedResponse);
        
        // Play the response using text-to-speech
        const utterance = new SpeechSynthesisUtterance(simulatedResponse);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
        
        setIsProcessing(false);
      }, 1500);
      
      // Clear the text input
      setTextInput('');
    } catch (error) {
      console.error('Error sending text message:', error);
      addMessage('System', 'Error processing your message. Please try again.');
      setIsProcessing(false);
    }
  };
  
  // Check if the API server is running
  const checkApiConnection = async () => {
    try {
      // Use AbortController to set a timeout for the fetch request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        signal: controller.signal,
        mode: 'cors',
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        setApiStatus('connected');
        addMessage('System', 'Connected to API server successfully.');
      } else {
        setApiStatus('error');
        addMessage('System', `Error connecting to API server: ${response.status} ${response.statusText}`);
      }
    } catch (err) {
      console.error('API connection error:', err);
      setApiStatus('error');
      
      // More user-friendly error message
      if (err.name === 'AbortError') {
        addMessage('System', 'Connection to API server timed out. Please check if the server is running.');
      } else if (err.message.includes('Failed to fetch')) {
        addMessage('System', 'Cannot reach API server. Please make sure the FastAPI server is running at port 5000.');
      } else {
        addMessage('System', `Error connecting to API server: ${err.message}`);
      }
    }
  };
  
  // Start recording from microphone
  const startRecording = async () => {
    try {
      // Clear previous audio chunks
      setAudioChunks([]);
      
      // Request access to the microphone
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setAudioStream(stream);
      
      // Set up audio analysis for visualization
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      const audioSource = audioContext.createMediaStreamSource(stream);
      audioSource.connect(analyser);
      
      // Store the analyser for later use
      audioAnalyserRef.current = analyser;
      audioDataRef.current = new Uint8Array(analyser.frequencyBinCount);
      
      // Start visualization
      visualizeAudio();
      
      // Create a new MediaRecorder instance
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      setMediaRecorder(recorder);
      
      // Event handler for when data is available
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          setAudioChunks(chunks => [...chunks, e.data]);
        }
      };
      
      // Start recording
      recorder.start(200); // Collect data every 200ms
      setIsRecording(true);
      addMessage('System', 'Recording started. Speak now...');
      
      // Start timer
      setRecordingTime(0);
      timerRef.current = setInterval(() => {
        setRecordingTime(prevTime => prevTime + 1);
      }, 1000);
      
    } catch (err) {
      console.error('Error starting recording:', err);
      addMessage('System', `Error starting recording: ${err.message}`);
    }
  };
  
  // Visualize audio input
  const visualizeAudio = () => {
    if (!audioAnalyserRef.current) return;
    
    const analyser = audioAnalyserRef.current;
    const dataArray = audioDataRef.current;
    
    // Get volume data
    analyser.getByteFrequencyData(dataArray);
    
    // Calculate volume level (average of frequency data)
    const average = dataArray.reduce((acc, val) => acc + val, 0) / dataArray.length;
    setVolume(average);
    
    // Continue animation
    animationRef.current = requestAnimationFrame(visualizeAudio);
  };
  
  // Stop recording
  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      // Stop the recording
      mediaRecorder.stop();
      setIsRecording(false);
      addMessage('System', 'Recording stopped. Processing audio...');
      
      // Stop the timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      
      // Stop the visualization
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
      
      // Stop all tracks in the stream
      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        setAudioStream(null);
      }
      
      // Process the recorded audio after a short delay to ensure all chunks are collected
      setTimeout(() => {
        if (audioChunks.length > 0) {
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          processAudio(audioBlob);
        } else {
          addMessage('System', 'No audio recorded. Please try again.');
        }
      }, 300);
    }
  };
  
  // Process audio with the API
  const processAudio = async (audioBlob) => {
    try {
      setIsProcessing(true);
      addMessage('System', 'Processing audio...');
      
      // Create a FormData object to send the audio file
      const formData = new FormData();
      formData.append('audio', audioBlob);
      
      // Send the audio to the backend for processing
      const response = await fetch(`${API_BASE_URL}/api/process-audio`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = 'Failed to process audio';
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // If parsing fails, use the raw text
          errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      
      // Add user message with transcribed text
      addMessage('User', data.user_text);
      
      // Add agent response
      addMessage('Agent', data.response_text);
      
      // Play the audio response
      if (data.audio_id) {
        const audioUrl = `${API_BASE_URL}/audio/${data.audio_id}.mp3`;
        playAudioFromUrl(audioUrl);
      }
      
    } catch (err) {
      console.error('Error processing audio:', err);
      addMessage('System', `Error processing audio: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Play audio from URL
  const playAudioFromUrl = (url) => {
    // Create an audio element to play the response
    const audio = new Audio(url);
    
    // Add event listeners
    audio.addEventListener('play', () => {
      addMessage('System', 'Playing audio response...');
    });
    
    audio.addEventListener('ended', () => {
      addMessage('System', 'Audio response finished.');
    });
    
    audio.addEventListener('error', (e) => {
      console.error('Error playing audio:', e);
      addMessage('System', 'Error playing audio response.');
    });
    
    // Play the audio
    audio.play().catch(err => {
      console.error('Error playing audio:', err);
      addMessage('System', `Error playing audio: ${err.message}`);
    });
  };
  
  // Add a message to the conversation with typing animation effect
  const addMessage = (sender, text) => {
    // For agent messages, show typing animation
    if (sender === 'Agent') {
      // First add a typing indicator
      setMessages(prevMessages => [...prevMessages, { sender, text: '...', isTyping: true }]);
      
      // Then gradually reveal the text
      let visibleLength = 0;
      const textLength = text.length;
      const typingInterval = setInterval(() => {
        visibleLength += 1;
        
        if (visibleLength <= textLength) {
          setMessages(prevMessages => {
            // Find and update the typing message
            const updatedMessages = [...prevMessages];
            const typingIndex = updatedMessages.findIndex(msg => msg.isTyping);
            
            if (typingIndex !== -1) {
              updatedMessages[typingIndex] = {
                sender,
                text: text.substring(0, visibleLength),
                isTyping: visibleLength < textLength
              };
            }
            
            return updatedMessages;
          });
        } else {
          clearInterval(typingInterval);
        }
      }, 30); // Adjust typing speed here
    } else {
      // For non-agent messages, add immediately
      setMessages(prevMessages => [...prevMessages, { sender, text }]);
    }
  };
  
  // Render the UI
  return (
    <div className="app-container">
      <div className="main-layout">
        <div className="avatar-section">
          <div className="title-bar">
            <h1>{BANK_NAME}</h1>
          </div>
          
          <div className="avatar-container">
            <div className="virtual-avatar">
              <div className="avatar-image">
                <div className={`avatar-circle ${isRecording ? 'pulse' : ''}`}>
                  <div className="avatar-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.98C6.03 13.99 10 12.9 12 12.9C13.99 12.9 17.97 13.99 18 15.98C16.71 17.92 14.5 19.2 12 19.2Z" fill="#2c3e50"/>
                    </svg>
                  </div>
                </div>
              </div>
              <h2>{ASSISTANT_NAME}</h2>
              {isRecording && (
                <div className="recording-indicator">
                  <div className="pulse-indicator">🔴 Recording</div>
                  <div className="recording-time">{formatTime(recordingTime)}</div>
                  <div className="volume-meter">
                    <div 
                      className="volume-level" 
                      style={{ width: `${Math.min(100, volume)}%` }}
                    />
                  </div>
                </div>
              )}
              
              {isProcessing && (
                <div className="processing-indicator">
                  <div className="spinner"></div>
                  <span>Processing...</span>
                </div>
              )}
            </div>
          </div>
          
          <div className="avatar-controls">
            <button 
              onClick={isRecording ? stopRecording : startRecording}
              className={isRecording ? 'stop' : 'start'}
              disabled={isProcessing || apiStatus !== 'connected'}
            >
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
            <button className="action-button">
              Help
            </button>
          </div>
        </div>
        
        <div className="chat-section">
          <div className="connection-status">
            <div className={`status-indicator ${apiStatus}`}>
              Connection Status: {apiStatus === 'connected' ? 'Connected' : 'Disconnected'}
              {apiStatus === 'error' && (
                <button onClick={checkApiConnection} className="retry-button">
                  Connect
                </button>
              )}
            </div>
          </div>
          
          <div className="conversation">
            <div className="messages">
              {messages.map((msg, index) => (
                <div key={index} className={`message ${msg.sender.toLowerCase()} ${msg.isTyping ? 'typing' : ''}`}>
                  <div className="sender">{msg.sender}</div>
                  <div className="text">
                    {msg.text}
                    {msg.isTyping && <span className="typing-cursor">|</span>}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>
          
          <div className="message-input">
            <input 
              type="text" 
              placeholder="Type your message here..."
              disabled={isRecording || isProcessing}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendText()}
            />
            <button 
              className="send-button"
              onClick={handleSendText}
              disabled={isRecording || isProcessing || !textInput.trim()}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SimpleApp;
