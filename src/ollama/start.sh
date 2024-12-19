#!/bin/bash
# Start the Ollama server in the background
ollama serve &
# Wait for the server to initialize
sleep 5
# Pull the required models
ollama pull llama3
ollama pull llama3.2:1b
# Keep the server running in the foreground
wait -n