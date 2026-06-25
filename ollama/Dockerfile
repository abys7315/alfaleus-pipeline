FROM ollama/ollama:latest

# Start the ollama server in the background and pull the model during the image build phase.
# This ensures the 600MB model is baked into the Docker image, so Railway
# doesn't have to download it from scratch every time the container restarts.
RUN nohup bash -c "ollama serve &" && sleep 5 && ollama pull tinyllama

# Expose the standard Ollama port
EXPOSE 11434
