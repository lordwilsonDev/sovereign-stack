"""
🌉 SOVEREIGN BRIDGE - MoIE-OS ↔ Python Brain
=============================================

Connects the Rust/Swift MoIE-OS kernel to the
Python Sovereign Stack for unified operation.

Architecture:
  MoIE-OS (Rust) → HTTP/Unix Socket → This Bridge → Python Brain
"""

import json
import asyncio
import hashlib
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional
import threading
import sys

# Add Sovereign Stack imports
sys.path.insert(0, str(Path(__file__).parent.parent / "sovereign"))
sys.path.insert(0, str(Path(__file__).parent.parent / "dragon"))


class SovereignBrain:
    """
    The Python brain that processes requests from MoIE-OS.
    """
    
    def __init__(self):
        self._cbf = None
        self._filter = None
        self._merkle = None
        self._swarm = None
        self._initialized = False
    
    def initialize(self):
        """Load all components."""
        if self._initialized:
            return
        
        print("🧠 Initializing Sovereign Brain...")
        
        # Load CBF
        try:
            from nagumo_cbf import NagumoSafetyController
            self._cbf = NagumoSafetyController()
            print("   ✅ Nagumo CBF")
        except Exception as e:
            print(f"   ⚠️ CBF: {e}")
        
        # Load Axiomatic Filter
        try:
            from axiomatic_filter import AxiomaticFilter
            self._filter = AxiomaticFilter()
            print("   ✅ Axiomatic Filter")
        except Exception as e:
            print(f"   ⚠️ Filter: {e}")
        
        # Load Merkle
        try:
            from merkle_trace import SovereignEvidence
            self._merkle = SovereignEvidence()
            print("   ✅ Merkle Trace")
        except Exception as e:
            print(f"   ⚠️ Merkle: {e}")
        
        self._initialized = True
        print("🧠 Sovereign Brain READY")
    
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request from MoIE-OS.
        
        Request types:
        - think: Generate response with safety checks
        - verify: Dual-scout verification
        - safety: Check safety barriers
        - log: Log to Merkle chain
        """
        if not self._initialized:
            self.initialize()
        
        req_type = request.get("type", "think")
        payload = request.get("payload", {})
        
        start = time.perf_counter()
        
        if req_type == "think":
            result = self._think(payload.get("query", ""))
        elif req_type == "verify":
            result = self._verify(payload.get("claim", ""))
        elif req_type == "safety":
            result = self._check_safety(payload)
        elif req_type == "log":
            result = self._log_event(payload)
        else:
            result = {"error": f"Unknown request type: {req_type}"}
        
        result["latency_ms"] = (time.perf_counter() - start) * 1000
        result["brain_version"] = "1.0.0"
        
        return result
    
    def _think(self, query: str) -> Dict[str, Any]:
        """Process a query with full safety pipeline."""
        # 1. Axiomatic filter
        if self._filter:
            analysis = self._filter.invert_request(query)
            if not analysis.is_safe:
                return {
                    "answer": None,
                    "refused": True,
                    "violations": analysis.violates_axioms,
                    "reason": "Axiom violation"
                }
        
        # 2. CBF check
        barrier_h = 1.0
        if self._cbf:
            barrier_h = self._cbf.cbf.evaluate(self._cbf.current_state)
            if barrier_h < 0:
                return {
                    "answer": None,
                    "refused": True,
                    "barrier_h": barrier_h,
                    "reason": "Safety barrier violated"
                }
        
        # 3. Generate (placeholder - would call LLM)
        answer = f"Processed: {query}"
        
        # 4. Log to Merkle
        if self._merkle:
            self._merkle.log_query(query, "processed", True)
        
        return {
            "answer": answer,
            "refused": False,
            "barrier_h": barrier_h,
            "safe": True
        }
    
    def _verify(self, claim: str) -> Dict[str, Any]:
        """Dual-scout verification."""
        try:
            from sovereign_swarm import SovereignSwarm
            swarm = SovereignSwarm()
            swarm.initialize()
            result = swarm.scout(claim)
            return {
                "consensus": result.is_consensus,
                "alpha": result.alpha_result.response[:100],
                "omega": result.omega_result.response[:100],
                "merkle": result.merkle_hash,
                "safe": result.is_safe
            }
        except Exception as e:
            return {"error": str(e), "consensus": False}
    
    def _check_safety(self, state: Dict) -> Dict[str, Any]:
        """Check safety barriers."""
        if self._cbf:
            self._cbf.update_state(
                thermal=state.get("temperature", 50),
                memory=state.get("memory", 0.5)
            )
            h = self._cbf.cbf.evaluate(self._cbf.current_state)
            return {
                "barrier_h": h,
                "safe": h > 0,
                "margin": h / 1.0  # Headroom
            }
        return {"barrier_h": 1.0, "safe": True}
    
    def _log_event(self, event: Dict) -> Dict[str, Any]:
        """Log event to Merkle chain."""
        if self._merkle:
            self._merkle.log_heartbeat(
                event.get("temperature", 50),
                event.get("memory", 4),
                event.get("status", "ok")
            )
            return {
                "logged": True,
                "root": self._merkle.trace.root[:16]
            }
        return {"logged": False}


# Global brain instance
BRAIN = SovereignBrain()


class BridgeHandler(BaseHTTPRequestHandler):
    """HTTP handler for MoIE-OS → Python bridge."""
    
    def log_message(self, format, *args):
        pass  # Suppress logs
    
    def do_POST(self):
        """Handle POST requests from MoIE-OS."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            request = json.loads(body)
            result = BRAIN.process(request)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_GET(self):
        """Health check and status."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "healthy",
                "brain": "sovereign",
                "version": "1.0.0"
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()


def run_bridge(port: int = 9999):
    """Run the Sovereign Bridge server."""
    BRAIN.initialize()
    
    print(f"\n🌉 SOVEREIGN BRIDGE")
    print(f"   http://localhost:{port}")
    print(f"   POST /         - Process request")
    print(f"   GET  /health   - Health check")
    print("-" * 40)
    
    server = HTTPServer(('127.0.0.1', port), BridgeHandler)
    server.serve_forever()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, default=9999)
    args = parser.parse_args()
    
    run_bridge(args.port)
