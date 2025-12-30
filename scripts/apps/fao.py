"""
Functional Axiom Oracle: Unified Entry Point
Integrates A-bind, Falsification Mirror, and Hardware Switchboard.
"""

import trio
import sys
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, AsyncGenerator

# Add script paths
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir / "core"))
sys.path.insert(0, str(scripts_dir / "mirror"))
sys.path.insert(0, str(scripts_dir / "hardware"))

from abind import a_bind, AxiomEffect, reality_coherence, get_coherence_status
from falsification_mirror import FalsificationMirror, VerificationLevel, falsification_mirror
from switchboard import HardwareSwitchboard, SignedPayload

@dataclass
class FAOResponse:
    output: str
    verified: bool
    coherence_score: float
    coherence_state: str
    signature: Optional[str]
    metadata: dict

class FunctionalAxiomOracle:
    """
    The Functional Axiom Oracle.
    Implements checked generation with hardware-rooted verification.
    """
    
    def __init__(
        self,
        verification_level: VerificationLevel = VerificationLevel.STANDARD,
        enable_hardware: bool = True
    ):
        self.verification_level = verification_level
        self.mirror = FalsificationMirror(verification_level=verification_level)
        self.switchboard = HardwareSwitchboard() if enable_hardware else None
        self.axioms: List[str] = []
        self._initialized = False
    
    def add_axiom(self, axiom: str):
        """Add a safety axiom."""
        self.axioms.append(axiom)
        self.mirror.add_axiom(axiom)
    
    def add_ground_truth(self, fact: str):
        """Add a ground truth for verification."""
        self.mirror.add_ground_truth(fact)
    
    async def initialize(self):
        """Initialize all subsystems."""
        if self._initialized:
            return
        
        print("🔮 Initializing Functional Axiom Oracle...")
        print(f"   Verification Level: {self.verification_level.value}")
        print(f"   Axioms Loaded: {len(self.axioms)}")
        
        if self.switchboard:
            self.switchboard.initialize()
        
        self._initialized = True
        print("✅ FAO Ready")
    
    async def shutdown(self):
        """Clean shutdown."""
        if self.switchboard:
            self.switchboard.shutdown()
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> FAOResponse:
        """
        Generate verified output using A-bind and Falsification Mirror.
        """
        if not self._initialized:
            await self.initialize()
        
        # Reset coherence for new generation
        reality_coherence.set(1.0)
        
        async def token_generator() -> AsyncGenerator[AxiomEffect, None]:
            """
            Mock generator. In production, this wraps mlx-lm generation.
            """
            # Simulate token generation
            response_tokens = [
                "The", " Functional", " Axiom", " Oracle",
                " provides", " verified", " outputs", " with",
                " cryptographic", " signing", "."
            ]
            for token in response_tokens:
                # Send heartbeat to watchdog
                if self.switchboard:
                    self.switchboard.pulse()
                
                yield AxiomEffect(token=token, logprob=-1.5)
                await trio.sleep(0.01)
        
        # Run verified generation through A-bind
        output_tokens = []
        try:
            async for verified_token in a_bind(token_generator()):
                output_tokens.append(verified_token)
        except Exception as e:
            output_tokens.append(f" [ERROR: {e}]")
        
        output = "".join(output_tokens)
        status = get_coherence_status()
        
        # Sign output if hardware is available
        signature = None
        if self.switchboard and self.switchboard.enclave.process:
            payload = self.switchboard.sign_output(output)
            if payload:
                signature = payload.signature
        
        return FAOResponse(
            output=output,
            verified=status["score"] > 0.5,
            coherence_score=status["score"],
            coherence_state=status["state"],
            signature=signature,
            metadata={
                "prompt": prompt,
                "tokens_generated": len(output_tokens),
                "verification_level": self.verification_level.value
            }
        )
    
    async def query(self, question: str) -> FAOResponse:
        """High-level query API."""
        return await self.generate(question)

async def main():
    """CLI entry point for FAO."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Functional Axiom Oracle")
    parser.add_argument("prompt", nargs="?", default=None, help="Query prompt")
    parser.add_argument("--level", choices=["quick", "standard", "paranoid"], default="standard")
    parser.add_argument("--no-hardware", action="store_true", help="Disable hardware switchboard")
    args = parser.parse_args()
    
    level_map = {
        "quick": VerificationLevel.QUICK,
        "standard": VerificationLevel.STANDARD,
        "paranoid": VerificationLevel.PARANOID
    }
    
    oracle = FunctionalAxiomOracle(
        verification_level=level_map[args.level],
        enable_hardware=not args.no_hardware
    )
    
    # Add default axioms
    oracle.add_axiom("The system must never generate harmful content.")
    oracle.add_axiom("The system must maintain factual accuracy.")
    
    await oracle.initialize()
    
    if args.prompt:
        response = await oracle.query(args.prompt)
    else:
        # Interactive mode
        print("\n🔮 FAO Interactive Mode (type 'quit' to exit)")
        print("-" * 40)
        
        while True:
            try:
                prompt = input("\n[FAO]> ").strip()
                if prompt.lower() in ["quit", "exit", "q"]:
                    break
                if not prompt:
                    continue
                
                response = await oracle.query(prompt)
                
                print(f"\n📜 Output: {response.output}")
                print(f"   Verified: {'✅' if response.verified else '❌'}")
                print(f"   Coherence: {response.coherence_score:.2f} ({response.coherence_state})")
                if response.signature:
                    print(f"   Signature: {response.signature[:40]}...")
                    
            except KeyboardInterrupt:
                break
    
    await oracle.shutdown()

if __name__ == "__main__":
    trio.run(main)
