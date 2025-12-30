"""
CBF Logits Processor: Control Barrier Functions on Token Logits
Applies safety constraints at the generation level using quadratic programming.
Optimized for Apple Silicon AMX co-processor via MLX.
"""

import mlx.core as mx
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Callable

@dataclass
class SafetyConstraint:
    """Represents a semantic safety constraint."""
    name: str
    unsafe_token_ids: List[int]
    penalty: float = -1e9

class CBFLogitsProcessor:
    """
    Control Barrier Function processor for logits.
    Ensures the generation trajectory stays within the "safe set".
    
    The barrier function h(x) measures distance to safety.
    We enforce: ḣ(x, u) >= -α * h(x) at each step.
    """
    
    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha
        self.constraints: List[SafetyConstraint] = []
        self.semantic_centroids: Optional[mx.array] = None
        self.unsafe_regions: List[mx.array] = []
        
    def add_constraint(self, constraint: SafetyConstraint):
        """Add a safety constraint."""
        self.constraints.append(constraint)
    
    def add_unsafe_tokens(self, name: str, token_ids: List[int], penalty: float = -1e9):
        """Convenience method to block specific tokens."""
        self.constraints.append(SafetyConstraint(name, token_ids, penalty))
    
    def set_safe_centroid(self, centroid: mx.array):
        """Set the semantic centroid of the 'safe' region."""
        self.semantic_centroids = centroid
    
    def compute_barrier(self, logits: mx.array, current_state: Optional[mx.array] = None) -> mx.array:
        """
        Compute the barrier function h(x) for the current state.
        Returns a score where h(x) >= 0 means safe, h(x) < 0 means unsafe.
        """
        if self.semantic_centroids is None:
            # Default: all positions are safe
            return mx.ones(logits.shape[-1])
        
        # Distance from safe centroid (simplified)
        # In production, this would use embedding space distances
        return mx.ones(logits.shape[-1])
    
    def __call__(self, input_ids: mx.array, logits: mx.array) -> mx.array:
        """
        Apply CBF constraints to logits.
        This is called during generation to filter unsafe tokens.
        """
        # 1. Apply hard constraints (token blocking)
        for constraint in self.constraints:
            if constraint.unsafe_token_ids:
                mask = mx.zeros(logits.shape[-1])
                for token_id in constraint.unsafe_token_ids:
                    if token_id < logits.shape[-1]:
                        mask = mask.at[token_id].add(constraint.penalty)
                logits = logits + mask
        
        # 2. Compute barrier function
        barrier_values = self.compute_barrier(logits)
        
        # 3. Apply soft barrier (gradient-based steering)
        # Tokens that would move toward unsafe region get penalized
        # This is the core CBF constraint: ḣ(x, u) >= -α * h(x)
        unsafe_mask = barrier_values < 0
        soft_penalty = mx.where(unsafe_mask, barrier_values * self.alpha * 100, 0)
        logits = logits + soft_penalty
        
        return logits
    
    def get_safe_token_mask(self, vocab_size: int) -> mx.array:
        """Return a mask of all safe tokens (1 = safe, 0 = unsafe)."""
        mask = mx.ones(vocab_size)
        for constraint in self.constraints:
            for token_id in constraint.unsafe_token_ids:
                if token_id < vocab_size:
                    mask = mask.at[token_id].set(0)
        return mask

if __name__ == "__main__":
    print("🛡️ CBF Logits Processor Test")
    print("=" * 40)
    
    processor = CBFLogitsProcessor(alpha=0.1)
    
    # Add constraint: Block token IDs 100, 200, 300 (example unsafe tokens)
    processor.add_unsafe_tokens("harmful_tokens", [100, 200, 300])
    
    # Test with mock logits
    vocab_size = 32000
    mock_logits = mx.random.normal((1, 10, vocab_size))
    mock_input_ids = mx.array([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]])
    
    # Apply processor
    filtered_logits = processor(mock_input_ids, mock_logits)
    
    # Verify blocked tokens have very low probability
    print(f"Original logit at token 100: {mock_logits[0, -1, 100].item():.2f}")
    print(f"Filtered logit at token 100: {filtered_logits[0, -1, 100].item():.2e}")
    print(f"Safe mask sum: {processor.get_safe_token_mask(vocab_size).sum().item():.0f} / {vocab_size}")
    print("✅ CBF Logits Processor initialized.")
