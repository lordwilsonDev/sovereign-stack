#!/bin/bash
# Quick Start: OpenCode + Sovereign Stack
# ========================================

echo "🚀 Starting Sovereign Stack + OpenCode"
echo

# Check if proxy is already running
if lsof -i :8766 > /dev/null 2>&1; then
    echo "✅ Proxy already running on port 8766"
else
    echo "Starting Sovereign Proxy..."
    cd ~/sparse_axion_rag
    source .venv/bin/activate
    python3 scripts/opencode_integration/sovereign_proxy.py \
        --backend ollama \
        --model qwen2.5-coder:1.5b \
        --port 8766 &
    
    PROXY_PID=$!
    echo "   Proxy PID: $PROXY_PID"
    sleep 2
fi

echo
echo "✅ Ready!"
echo
echo "Usage:"
echo "  opencode \"your request here\""
echo
echo "Example:"
echo "  opencode \"add a fibonacci function to my code\""
echo
echo "Dashboard: http://localhost:8888"
echo "Proxy health: http://localhost:8766/health"
echo
