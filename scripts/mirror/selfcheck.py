"""
SelfCheckGPT: Stochastic Sampling for Hallucination Detection
Spawns parallel generation threads to detect confabulation.
If samples contradict each other, the model is hallucinating.
"""

import trio
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SelfCheckResult:
    is_consistent: bool
    consistency_score: float
    samples: List[str]
    detected_hallucination: bool

class SelfCheckGPT:
    """
    Implements the SelfCheckGPT protocol for hallucination detection.
    
    Mechanism:
    1. Generate N parallel samples with high temperature
    2. Compare samples for consistency
    3. If samples contradict, the model is confabulating
    """
    
    def __init__(self, num_samples: int = 3, consistency_threshold: float = 0.7):
        self.num_samples = num_samples
        self.consistency_threshold = consistency_threshold
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def generate_sample(self, prompt: str, generator_fn) -> str:
        """Generate a single sample (stub - replace with actual generation)."""
        await trio.sleep(0.01)  # Simulated generation time
        # In production, this calls the LLM with high temperature
        return f"Sample response to: {prompt}"
    
    async def check_claim(
        self, 
        claim: str, 
        context: str,
        generator_fn = None
    ) -> SelfCheckResult:
        """
        Check if a factual claim is hallucinated.
        
        Args:
            claim: The statement to verify
            context: The original prompt/context
            generator_fn: Function to generate alternative samples
        """
        # Generate parallel samples
        samples = []
        async with trio.open_nursery() as nursery:
            async def collect_sample():
                sample = await self.generate_sample(context, generator_fn)
                samples.append(sample)
            
            for _ in range(self.num_samples):
                nursery.start_soon(collect_sample)
        
        # Encode all samples including the claim
        all_texts = [claim] + samples
        embeddings = self.encoder.encode(all_texts)
        
        # Compute pairwise similarities
        claim_embedding = embeddings[0:1]
        sample_embeddings = embeddings[1:]
        
        similarities = cosine_similarity(claim_embedding, sample_embeddings)[0]
        avg_similarity = np.mean(similarities)
        
        # Also check inter-sample consistency
        if len(sample_embeddings) > 1:
            inter_sample_sim = cosine_similarity(sample_embeddings)
            inter_consistency = np.mean(inter_sample_sim[np.triu_indices(len(sample_embeddings), k=1)])
        else:
            inter_consistency = 1.0
        
        # Determine if hallucinating
        overall_consistency = (avg_similarity + inter_consistency) / 2
        is_hallucinating = overall_consistency < self.consistency_threshold
        
        return SelfCheckResult(
            is_consistent=not is_hallucinating,
            consistency_score=overall_consistency,
            samples=samples,
            detected_hallucination=is_hallucinating
        )
    
    def sync_check(self, claim: str, samples: List[str]) -> SelfCheckResult:
        """
        Synchronous version for when we already have samples.
        """
        all_texts = [claim] + samples
        embeddings = self.encoder.encode(all_texts)
        
        claim_embedding = embeddings[0:1]
        sample_embeddings = embeddings[1:]
        
        similarities = cosine_similarity(claim_embedding, sample_embeddings)[0]
        avg_similarity = np.mean(similarities)
        
        inter_sample_sim = cosine_similarity(sample_embeddings)
        inter_consistency = np.mean(inter_sample_sim[np.triu_indices(len(sample_embeddings), k=1)])
        
        overall_consistency = (avg_similarity + inter_consistency) / 2
        is_hallucinating = overall_consistency < self.consistency_threshold
        
        return SelfCheckResult(
            is_consistent=not is_hallucinating,
            consistency_score=overall_consistency,
            samples=samples,
            detected_hallucination=is_hallucinating
        )

if __name__ == "__main__":
    print("🔬 SelfCheckGPT Test")
    print("=" * 40)
    
    checker = SelfCheckGPT(num_samples=3, consistency_threshold=0.6)
    
    # Test with consistent samples
    claim = "Apple Silicon uses Unified Memory Architecture."
    samples = [
        "M1 chips feature a unified memory system shared by CPU and GPU.",
        "Apple's M-series processors have a unified memory pool.",
        "The UMA in Apple Silicon allows efficient data sharing."
    ]
    
    result = checker.sync_check(claim, samples)
    print(f"Claim: {claim}")
    print(f"Consistency Score: {result.consistency_score:.2f}")
    print(f"Detected Hallucination: {result.detected_hallucination}")
    print("✅ SelfCheckGPT initialized.")
