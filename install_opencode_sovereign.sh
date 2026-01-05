#!/bin/bash
# Sovereign Stack + OpenCode Installation Script
# =============================================

set -e  # Exit on error

echo "🔧 Installing Sovereign Stack OpenCode Integration"
echo "=================================================="
echo

# Check if Ollama is running
echo "1. Checking Ollama status..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ⚠️  Warning: Ollama doesn't appear to be running"
    echo "   Please start Ollama: 'ollama serve' in another terminal"
    echo "   Or install: https://ollama.ai/download"
else
    echo "   ✅ Ollama is running"
fi
echo

# Install Python dependencies
echo "2. Installing Python dependencies..."
pip install -q fastapi uvicorn httpx 2>/dev/null || {
    echo "   ❌ Failed to install dependencies"
    exit 1
}
echo "   ✅ FastAPI, uvicorn, httpx installed"
echo

# Install OpenCode
echo "3. Installing OpenCode..."
if command -v opencode &> /dev/null; then
    echo "   ✅ OpenCode already installed ($(opencode --version 2>/dev/null || echo 'version unknown'))"
else
    if command -v npm &> /dev/null; then
        echo "   Installing via npm..."
        npm install -g opencode-ai@latest
        echo "   ✅ OpenCode installed"
    elif command -v brew &> /dev/null; then
        echo "   Installing via Homebrew..."
        brew install opencode
        echo "   ✅ OpenCode installed"
    else
        echo "   ⚠️  npm or brew not found. Please install OpenCode manually:"
        echo "   curl -fsSL https://opencode.ai/install | bash"
    fi
fi
echo

# Pull recommended model
echo "4. Pulling recommended model (qwen2.5-coder:1.5b)..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    ollama pull qwen2.5-coder:1.5b 2>&1 | grep -v "pulling" || true
    echo "   ✅ Model ready"
else
    echo "   ⚠️  Skipping (Ollama not running)"
fi
echo

# Create OpenCode config
echo "5. Configuring OpenCode to use Sovereign Proxy..."
OPENCODE_CONFIG_DIR="$HOME/.opencode"
mkdir -p "$OPENCODE_CONFIG_DIR"

cat > "$OPENCODE_CONFIG_DIR/config.json" << 'EOF'
{
  "model": {
    "provider": "openai",
    "name": "qwen2.5-coder:1.5b",
    "baseURL": "http://localhost:8765/v1",
    "apiKey": "sovereign-stack"
  },
  "temperature": 0.7
}
EOF

echo "   ✅ Config created at $OPENCODE_CONFIG_DIR/config.json"
echo

# Create launcher script
echo "6. Creating launcher scripts..."

# Proxy starter
cat > "$HOME/.opencode/start-sovereign-proxy.sh" << 'EOF'
#!/bin/bash
cd ~/sparse_axion_rag
source .venv/bin/activate 2>/dev/null || true
python3 scripts/opencode_integration/sovereign_proxy.py \
    --backend ollama \
    --model qwen2.5-coder:1.5b \
    --port 8765
EOF
chmod +x "$HOME/.opencode/start-sovereign-proxy.sh"

echo "   ✅ Proxy launcher created"
echo

# Final instructions
echo "✅ Installation Complete!"
echo
echo "📋 Next Steps:"
echo "   1. Start the Sovereign Proxy:"
echo "      ~/.opencode/start-sovereign-proxy.sh"
echo
echo "   2. In another terminal, use OpenCode:"
echo "      opencode \"explain how thermal_loop.py works\""
echo
echo "   3. Monitor the dashboard:"
echo "      http://localhost:8888"
echo
echo "🔒 Safety Features Active:"
echo "   ✓ Thermal monitoring"
echo "   ✓ Merkle attestation"
echo "   ✓ Request logging"
echo
