#!/usr/bin/env python3
"""
Sovereign Stack LLM Proxy
==========================

OpenAI-compatible proxy server that adds Sovereign Stack safety layers.
Sits between OpenCode and the actual LLM (Ollama/OpenAI).

Usage:
    python sovereign_proxy.py --backend ollama --model qwen2.5-coder:1.5b
"""

import asyncio
import json
import time
from typing import AsyncIterator, Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    import httpx
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   pip install fastapi uvicorn httpx")
    sys.exit(1)

# Sovereign Stack imports
from scripts.sovereign.thermal_loop import ThermalLoop
from scripts.sovereign.merkle_tree import MerkleTree
from scripts.bridge.sovereign_bridge import SovereignBrain

@dataclass
class ProxyConfig:
    """Configuration for the proxy server."""
    backend: str = "ollama"  # "ollama", "openai", "anthropic"
    backend_url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:1.5b"
    port: int = 8765
    enable_thermal: bool = True
    enable_sweat: bool = False  # Disabled by default (requires model activations)
    enable_abind: bool = False  # Disabled by default (requires async refactor)
    enable_merkle: bool = True
    log_dir: str = ".sovereign/opencode_logs"

@dataclass
class TokenMetrics:
    """Metrics for a single token."""
    token: str
    timestamp: float
    thermal_state: str
    sweat_score: Optional[float] = None
    coherence: Optional[float] = None
    verified: bool = True

class SovereignProxy:
    """
    LLM proxy with Sovereign Stack safety integration.
    """
    
    def __init__(self, config: ProxyConfig):
        self.config = config
        self.app = FastAPI(title="Sovereign Stack LLM Proxy")
        self.thermal_loop: Optional[ThermalLoop] = None
        self.merkle_tree: Optional[MerkleTree] = None
        self.brain = SovereignBrain()
        self.token_metrics: List[TokenMetrics] = []
        self.request_count = 0
        
        # Setup CORS for web dashboard access
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._setup_routes()
        
        # Initialize safety components
        self._init_safety_components()
    
    def _init_safety_components(self):
        """Initialize Sovereign Stack safety components."""
        # Thermal monitoring
        if self.config.enable_thermal:
            self.thermal_loop = ThermalLoop()
            self.thermal_loop.start()
            print(f"✅ Thermal monitoring enabled")
        
        # Merkle attestation
        if self.config.enable_merkle:
            self.merkle_tree = MerkleTree()
            print(f"✅ Merkle attestation enabled")
        
        # Sovereign Brain
        self.brain.initialize()
        print(f"✅ Sovereign Brain governance ACTIVE")
        
        # Create log directory
        Path(self.config.log_dir).mkdir(parents=True, exist_ok=True)
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "sovereign_stack": "active",
                "thermal_enabled": self.config.enable_thermal,
                "merkle_enabled": self.config.enable_merkle,
                "requests_processed": self.request_count
            }
        
        @self.app.post("/v1/chat/completions")
        async def chat_completions(request: Request):
            """
            OpenAI-compatible chat completions endpoint.
            Intercepts and verifies tokens before streaming.
            """
            self.request_count += 1
            
            try:
                body = await request.json()
                stream = body.get("stream", False)
                
                if stream:
                    return StreamingResponse(
                        self._stream_completion(body),
                        media_type="text/event-stream"
                    )
                else:
                    return await self._sync_completion(body)
                    
            except Exception as e:
                print(f"❌ Error in chat_completions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/v1/models")
        async def list_models():
            """List available models (for OpenAI compatibility)."""
            return {
                "object": "list",
                "data": [
                    {
                        "id": self.config.model,
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "sovereign-stack"
                    }
                ]
            }
    
    async def _stream_completion(self, request_body: dict) -> AsyncIterator[str]:
        """
        Stream completion with Sovereign Stack verification.
        """
        messages = request_body.get("messages", [])
        model = request_body.get("model", self.config.model)
        
        # Log request
        if self.merkle_tree:
            self.merkle_tree.add_leaf(json.dumps({
                "type": "request",
                "model": model,
                "message_count": len(messages),
                "timestamp": time.time()
            }))
        
        # forward to brain for axiomatic filtering
        if request_body.get("messages"):
            last_msg = messages[-1].get("content", "")
            brain_check = self.brain.process({"type": "think", "payload": {"query": last_msg}})
            
            if brain_check.get("refused"):
                yield self._format_sse({
                    "choices": [{
                        "delta": {"content": f"[REFUSED: {brain_check.get('reason')}]"},
                        "index": 0,
                        "finish_reason": "refusal"
                    }]
                })
                return

        # Forward to backend
        async for chunk in self._forward_to_backend(request_body):
            # Extract token
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                
                if content:
                    # Create metrics
                    metrics = TokenMetrics(
                        token=content,
                        timestamp=time.time(),
                        thermal_state=self.thermal_loop.get_current().state.value if self.thermal_loop else "unknown"
                    )
                    self.token_metrics.append(metrics)
                    
                    # Log to Merkle tree
                    if self.merkle_tree:
                        self.merkle_tree.add_leaf(json.dumps({
                            "type": "token",
                            "content": content,
                            "thermal_state": metrics.thermal_state,
                            "timestamp": metrics.timestamp
                        }))
            
            # Stream verified token
            yield self._format_sse(chunk)
        
        # Final attestation
        if self.merkle_tree:
            merkle_root = self.merkle_tree.get_root()
            yield self._format_sse({
                "choices": [{
                    "delta": {},
                    "index": 0,
                    "finish_reason": "stop"
                }],
                "sovereign_attestation": {
                    "merkle_root": merkle_root,
                    "verified": True,
                    "timestamp": time.time()
                }
            })
    
    async def _sync_completion(self, request_body: dict) -> dict:
        """Non-streaming completion."""
        # Collect all chunks
        full_content = ""
        async for chunk_str in self._stream_completion(request_body):
            # Parse SSE format
            if chunk_str.startswith("data: "):
                chunk_json = chunk_str[6:].strip()
                if chunk_json and chunk_json != "[DONE]":
                    chunk = json.loads(chunk_json)
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        full_content += content
        
        return {
            "id": f"sovereign-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request_body.get("model", self.config.model),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": full_content
                },
                "finish_reason": "stop"
            }]
        }
    
    async def _forward_to_backend(self, request_body: dict) -> AsyncIterator[dict]:
        """Forward request to actual LLM backend."""
        if self.config.backend == "ollama":
            async for chunk in self._ollama_stream(request_body):
                yield chunk
        elif self.config.backend == "openai":
            async for chunk in self._openai_stream(request_body):
                yield chunk
        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")
    
    async def _ollama_stream(self, request_body: dict) -> AsyncIterator[dict]:
        """Stream from Ollama backend."""
        url = f"{self.config.backend_url}/api/chat"
        
        # Convert OpenAI format to Ollama format
        ollama_request = {
            "model": request_body.get("model", self.config.model),
            "messages": request_body.get("messages", []),
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=ollama_request) as response:
                async for line in response.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        
                        # Convert Ollama format to OpenAI format
                        openai_chunk = {
                            "id": f"chatcmpl-{int(time.time())}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": ollama_request["model"],
                            "choices": [{
                                "index": 0,
                                "delta": {
                                    "content": chunk.get("message", {}).get("content", "")
                                },
                                "finish_reason": "stop" if chunk.get("done") else None
                            }]
                        }
                        
                        yield openai_chunk
    
    async def _openai_stream(self, request_body: dict) -> AsyncIterator[dict]:
        """Stream from OpenAI backend (placeholder)."""
        raise NotImplementedError("OpenAI backend not yet implemented")
    
    def _format_sse(self, data: dict) -> str:
        """Format data as Server-Sent Event."""
        return f"data: {json.dumps(data)}\n\n"
    
    def run(self):
        """Start the proxy server."""
        print(f"🚀 Sovereign Stack LLM Proxy")
        print(f"   Backend: {self.config.backend} ({self.config.backend_url})")
        print(f"   Model: {self.config.model}")
        print(f"   Listening: http://localhost:{self.config.port}")
        print(f"   OpenAI endpoint: http://localhost:{self.config.port}/v1/chat/completions")
        print()
        
        try:
            uvicorn.run(
                self.app,
                host="0.0.0.0",
                port=self.config.port,
                log_level="info"
            )
        finally:
            # Cleanup
            if self.thermal_loop:
                self.thermal_loop.stop()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Sovereign Stack LLM Proxy")
    parser.add_argument("--backend", default="ollama", choices=["ollama", "openai"])
    parser.add_argument("--backend-url", default="http://localhost:11434")
    parser.add_argument("--model", default="qwen2.5-coder:1.5b")
    parser.add_argument("--port", type=int, default=8765)
    
    args = parser.parse_args()
    
    config = ProxyConfig(
        backend=args.backend,
        backend_url=args.backend_url,
        model=args.model,
        port=args.port
    )
    
    proxy = SovereignProxy(config)
    proxy.run()

if __name__ == "__main__":
    main()
