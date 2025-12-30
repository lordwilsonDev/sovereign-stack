"""
FAO Loop: The 6-Stage Functional Axiomatic Oracle
Integrates all Sovereign Stack components into a unified control loop.
"""

import mlx.core as mx
import mlx.nn as nn
import time
from dataclasses import dataclass
from typing import Optional, List, Generator
from pathlib import Path
import sys

# Import Sovereign Stack components
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "mirror"))
sys.path.insert(0, str(Path(__file__).parent.parent / "hardware"))
sys.path.insert(0, str(Path(__file__).parent.parent / "sweat"))
sys.path.insert(0, str(Path(__file__).parent.parent / "vjepa"))

from thermal_loop import ThermalLoop
from mem_governor import MemGovernor
from merkle_tree import TokenBlocker, SignedBlock
from sycophancy_variance import SycophancyVarianceDetector, TruthBarrierFunction

@dataclass
class FAOStageResult:
    """Result from a single FAO loop iteration."""
    stage: str
    success: bool
    latency_ms: float
    details: dict

@dataclass
class FAOOutput:
    """Complete FAO output with full provenance."""
    token: str
    verified: bool
    stages: List[FAOStageResult]
    signed_block: Optional[SignedBlock]
    total_latency_ms: float

class FAOLoop:
    """
    The 6-Stage Functional Axiomatic Oracle Loop.
    
    From the blueprint:
    1. PROPOSAL     - BitNet generates candidate token
    2. SIMULATION   - JEPA predicts semantic state
    3. INSPECTION   - Compute sycophancy variance
    4. ADJUDICATION - CBF checks h(s) ≥ 0
    5. EXECUTION    - Output token or apply steering
    6. ATTESTATION  - Sign Merkle root with SEP
    
    Parallel monitors:
    - ThermalLoop (temperature monitoring)
    - MemGovernor (wired memory tracking)
    - AMX Watchdog (liveness heartbeat)
    """
    
    def __init__(
        self,
        model=None,
        block_size: int = 32,
        max_latency_ms: float = 50.0
    ):
        self.model = model
        self.block_size = block_size
        self.max_latency_ms = max_latency_ms
        
        # Initialize components
        self.thermal = ThermalLoop()
        self.memory = MemGovernor()
        self.token_blocker = TokenBlocker(block_size=block_size)
        self.sycophancy_detector = SycophancyVarianceDetector()
        self.truth_barrier = TruthBarrierFunction()
        
        # Metrics
        self.total_tokens = 0
        self.rejected_tokens = 0
        self.signed_blocks = 0
    
    def start_monitors(self):
        """Start all parallel monitors."""
        self.thermal.start()
        print("🔄 FAO Loop monitors started")
    
    def stop_monitors(self):
        """Stop all parallel monitors."""
        self.thermal.stop()
        print("🔄 FAO Loop monitors stopped")
    
    def _stage_1_proposal(self, context: mx.array) -> tuple[str, mx.array, float]:
        """Stage 1: Generate candidate token via BitNet."""
        t0 = time.perf_counter()
        
        # In production, this calls the actual model
        # For now, we simulate
        candidate_token = "verified"
        logits = mx.random.normal((1, 50257))
        
        latency = (time.perf_counter() - t0) * 1000
        return candidate_token, logits, latency
    
    def _stage_2_simulation(self, token: str, logits: mx.array) -> tuple[mx.array, float]:
        """Stage 2: JEPA predicts semantic state."""
        t0 = time.perf_counter()
        
        # In production, this runs V-JEPA ensemble
        # For now, we simulate meaning vector
        meaning_vector = mx.random.normal((1, 1024))
        
        latency = (time.perf_counter() - t0) * 1000
        return meaning_vector, latency
    
    def _stage_3_inspection(self, logits: mx.array) -> tuple[dict, float]:
        """Stage 3: Compute sycophancy variance."""
        t0 = time.perf_counter()
        
        # Mock embeddings for analysis
        mock_embeddings = mx.random.normal((1, 10, 128))
        
        # Create mock model for analysis
        class MockModel(nn.Module):
            def __call__(self, x): return x
        
        analysis = self.sycophancy_detector.analyze(
            MockModel(), mock_embeddings, logits
        )
        
        latency = (time.perf_counter() - t0) * 1000
        return {
            "variance": analysis.variance,
            "sensitivity": analysis.sensitivity,
            "is_sycophantic": analysis.is_sycophantic
        }, latency
    
    def _stage_4_adjudication(self, inspection: dict) -> tuple[bool, float]:
        """Stage 4: CBF checks barrier h(s) ≥ 0."""
        t0 = time.perf_counter()
        
        # Barrier check from blueprint
        h_truth = 0.5 - inspection["variance"]
        is_safe = h_truth >= 0
        
        latency = (time.perf_counter() - t0) * 1000
        return is_safe, latency
    
    def _stage_5_execution(self, token: str, is_safe: bool) -> tuple[str, float]:
        """Stage 5: Output token or apply steering."""
        t0 = time.perf_counter()
        
        if is_safe:
            output = token
        else:
            # Apply steering - in production, resample with steering vector
            output = "[STEERED]"
            self.rejected_tokens += 1
        
        latency = (time.perf_counter() - t0) * 1000
        return output, latency
    
    def _stage_6_attestation(self, token: str) -> tuple[Optional[SignedBlock], float]:
        """Stage 6: Add to Merkle tree, sign if block complete."""
        t0 = time.perf_counter()
        
        block = self.token_blocker.add_token(token)
        if block:
            self.signed_blocks += 1
        
        latency = (time.perf_counter() - t0) * 1000
        return block, latency
    
    def process_token(self, context: mx.array) -> FAOOutput:
        """
        Process a single token through the 6-stage FAO loop.
        """
        total_start = time.perf_counter()
        stages = []
        
        # Check thermal/memory safety
        if self.thermal.should_shed_load():
            return FAOOutput(
                token="[THERMAL_SHED]",
                verified=False,
                stages=[FAOStageResult("thermal_check", False, 0, {"reason": "thermal shedding"})],
                signed_block=None,
                total_latency_ms=0
            )
        
        # Stage 1: Proposal
        token, logits, lat = self._stage_1_proposal(context)
        stages.append(FAOStageResult("1_proposal", True, lat, {"token": token}))
        
        # Stage 2: Simulation
        meaning, lat = self._stage_2_simulation(token, logits)
        stages.append(FAOStageResult("2_simulation", True, lat, {"dim": meaning.shape[-1]}))
        
        # Stage 3: Inspection
        inspection, lat = self._stage_3_inspection(logits)
        stages.append(FAOStageResult("3_inspection", True, lat, inspection))
        
        # Stage 4: Adjudication
        is_safe, lat = self._stage_4_adjudication(inspection)
        stages.append(FAOStageResult("4_adjudication", is_safe, lat, {"barrier_ok": is_safe}))
        
        # Stage 5: Execution
        output, lat = self._stage_5_execution(token, is_safe)
        stages.append(FAOStageResult("5_execution", True, lat, {"output": output}))
        
        # Stage 6: Attestation
        block, lat = self._stage_6_attestation(output)
        stages.append(FAOStageResult("6_attestation", True, lat, {"block_signed": block is not None}))
        
        total_latency = (time.perf_counter() - total_start) * 1000
        self.total_tokens += 1
        
        return FAOOutput(
            token=output,
            verified=is_safe,
            stages=stages,
            signed_block=block,
            total_latency_ms=total_latency
        )
    
    def generate(self, prompt: str, max_tokens: int = 64) -> Generator[FAOOutput, None, None]:
        """Generate tokens with full FAO verification."""
        context = mx.random.normal((1, 10, 128))  # Mock context
        
        for _ in range(max_tokens):
            output = self.process_token(context)
            yield output
            
            # Break on special tokens
            if output.token in ["[EOS]", "[THERMAL_SHED]"]:
                break
    
    def get_stats(self) -> dict:
        """Get loop statistics."""
        return {
            "total_tokens": self.total_tokens,
            "rejected_tokens": self.rejected_tokens,
            "rejection_rate": self.rejected_tokens / max(1, self.total_tokens),
            "signed_blocks": self.signed_blocks,
            "memory_safe_gb": self.memory.get_status().safe_headroom_gb
        }

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  FAO Loop: 6-Stage Functional Axiomatic Oracle               ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    loop = FAOLoop()
    
    # Check system status
    mem_status = loop.memory.get_status()
    print(f"💾 Memory: {mem_status.safe_headroom_gb:.1f}GB available")
    
    thermal = loop.thermal.get_current()
    print(f"🌡️ Thermal: {thermal.state.value}")
    
    # Run 10 tokens through the loop
    print(f"\n🔄 Running 10 tokens through FAO Loop...")
    print("-" * 50)
    
    context = mx.random.normal((1, 10, 128))
    
    for i in range(10):
        output = loop.process_token(context)
        
        status = "✅" if output.verified else "❌"
        block_icon = "📦" if output.signed_block else "  "
        
        print(f"  {status} Token {i+1}: '{output.token}' "
              f"({output.total_latency_ms:.2f}ms) {block_icon}")
    
    # Flush final block
    final_block = loop.token_blocker.flush()
    if final_block:
        print(f"  📦 Final block signed: {len(final_block.tokens)} tokens")
    
    # Stats
    stats = loop.get_stats()
    print(f"\n📊 Statistics:")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Rejected: {stats['rejected_tokens']} ({stats['rejection_rate']:.1%})")
    print(f"  Signed blocks: {stats['signed_blocks']}")
    
    print("\n✅ FAO Loop test complete.")
