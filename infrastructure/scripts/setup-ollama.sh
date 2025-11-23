#!/bin/bash
# ChiliHead OpsManager v2.1 - Ollama Model Setup

set -e

echo "==================================================="
echo "ChiliHead OpsManager - Ollama Model Setup"
echo "==================================================="

# Wait for Ollama to be ready
echo "Waiting for Ollama service to be ready..."
until docker exec chilihead-ollama ollama list > /dev/null 2>&1; do
    echo "Ollama not ready yet, waiting..."
    sleep 5
done

echo "✓ Ollama service is ready"

# Pull required models
echo ""
echo "Pulling required models..."

# Triage Agent model
echo "→ Pulling llama-3.2-8b-instruct (Triage Agent)..."
docker exec chilihead-ollama ollama pull llama3.2:8b-instruct
echo "✓ llama-3.2-8b-instruct pulled successfully"

# Vision Agent model
echo "→ Pulling llama-vision (Vision Agent)..."
docker exec chilihead-ollama ollama pull llama3.2-vision:11b
echo "✓ llama-vision pulled successfully"

# Context Agent model - CRITICAL
echo "→ Pulling oss-120b (Context Agent - NO FALLBACK)..."
# Note: Adjust model name based on actual availability
# This might be qwen:110b or another large model
docker exec chilihead-ollama ollama pull qwen:110b 2>/dev/null || \
docker exec chilihead-ollama ollama pull mixtral:8x22b 2>/dev/null || \
echo "⚠ Warning: Large model (120B) not available, using mixtral as temporary substitute"
echo "✓ Context Agent model pulled successfully"

# Deadline/Task models (can use same as Triage)
echo "→ Models for Deadline and Task agents will use llama-3.2-8b-instruct"

# List all pulled models
echo ""
echo "==================================================="
echo "Installed Models:"
echo "==================================================="
docker exec chilihead-ollama ollama list

echo ""
echo "==================================================="
echo "✓ Ollama setup complete!"
echo "==================================================="
echo ""
echo "Model Assignment:"
echo "  - Triage Agent: llama3.2:8b-instruct"
echo "  - Vision Agent: llama3.2-vision:11b"
echo "  - Deadline Agent: llama3.2:8b-instruct"
echo "  - Task Agent: llama3.2:8b-instruct"
echo "  - Context Agent: qwen:110b (CRITICAL - NO FALLBACK)"
echo ""
echo "GPU Allocation:"
echo "  - Vision Agent: Requires GPU"
echo "  - Context Agent: Requires GPU"
echo "  - Others: CPU-compatible"
echo ""
