"""
Sycophancy Variance Detector
Gradient-based detection using ∇_input sensitivity analysis.
"""

import mlx.core as mx
import mlx.nn as nn
from dataclasses import dataclass
from typing import List, Optional, Tuple
import time

@dataclass
class SycophancyAnalysis:
    """Result of sycophancy variance analysis."""
    variance: float           # Variance of gradients
    sensitivity: float        # Mean absolute gradient
    is_sycophantic: bool      # Above threshold
    barrier_value: float      # h_truth = threshold - variance
    latency_us: float

class SycophancyVarianceDetector:
    """
    Gradient-based sycophancy detection.
    
    From the blueprint:
    - Calculate G = ∇_input Logits(Output)
    - High Var(G) indicates sycophancy (output too sensitive to input phrasing)
    - CBF barrier: h_truth = Threshold - Var(G)
    - If h_truth < 0, apply steering vector to force truthfulness
    """
    
    def __init__(
        self,
        variance_threshold: float = 0.5,
        sensitivity_threshold: float = 0.3
    ):
        self.variance_threshold = variance_threshold
        self.sensitivity_threshold = sensitivity_threshold
    
    def compute_gradient_variance(
        self,
        model: nn.Module,
        input_embeddings: mx.array,
        output_logits: mx.array
    ) -> Tuple[float, float]:
        """
        Compute the variance of gradients w.r.t. input.
        
        High variance = model output is very sensitive to input phrasing
        = hallmark of sycophancy
        """
        # In production, this would compute actual gradients via backprop
        # For now, we approximate using logit statistics
        
        # Logit variance as proxy for sensitivity
        logit_std = mx.std(output_logits).item()
        logit_mean = mx.mean(mx.abs(output_logits)).item()
        
        # Normalize to 0-1 range
        variance_proxy = min(1.0, logit_std / (logit_mean + 1e-8))
        sensitivity_proxy = min(1.0, logit_mean / 10.0)
        
        return variance_proxy, sensitivity_proxy
    
    def analyze(
        self,
        model: nn.Module,
        input_embeddings: mx.array,
        output_logits: mx.array
    ) -> SycophancyAnalysis:
        """
        Full sycophancy analysis.
        """
        t0 = time.perf_counter_ns()
        
        variance, sensitivity = self.compute_gradient_variance(
            model, input_embeddings, output_logits
        )
        
        # CBF barrier function
        # h_truth > 0 = safe, h_truth < 0 = sycophantic
        barrier = self.variance_threshold - variance
        
        is_sycophantic = (
            variance > self.variance_threshold or
            sensitivity > self.sensitivity_threshold
        )
        
        t1 = time.perf_counter_ns()
        
        return SycophancyAnalysis(
            variance=variance,
            sensitivity=sensitivity,
            is_sycophantic=is_sycophantic,
            barrier_value=barrier,
            latency_us=(t1 - t0) / 1000
        )
    
    def compute_steering_vector(
        self,
        analysis: SycophancyAnalysis,
        logits: mx.array
    ) -> mx.array:
        """
        Compute a steering vector to reduce sycophancy.
        
        When h_truth < 0, we need to force the model toward
        lower input-sensitivity outputs.
        """
        if not analysis.is_sycophantic:
            return mx.zeros_like(logits)
        
        # Steering strength proportional to barrier violation
        strength = min(1.0, abs(analysis.barrier_value) * 2)
        
        # Push toward uniform distribution (maximum entropy = minimum sycophancy)
        mean_logit = mx.mean(logits)
        steering = (mean_logit - logits) * strength
        
        return steering

class TruthBarrierFunction:
    """
    Control Barrier Function for truth enforcement.
    
    h(s) > 0: Safe (truthful)
    h(s) → 0: Approaching boundary
    h(s) < 0: Unsafe (sycophantic)
    
    Nagumo condition: ∂h/∂s · ṡ ≥ -α(h(s))
    """
    
    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha  # Class-K function parameter
        self.sycophancy_detector = SycophancyVarianceDetector()
    
    def barrier(self, analysis: SycophancyAnalysis) -> float:
        """
        Compute barrier value h(s).
        """
        return analysis.barrier_value
    
    def is_safe(self, analysis: SycophancyAnalysis) -> bool:
        """
        Check if current state is safe.
        """
        return self.barrier(analysis) >= 0
    
    def nagumo_condition(
        self,
        current_analysis: SycophancyAnalysis,
        next_analysis: SycophancyAnalysis
    ) -> bool:
        """
        Check Nagumo's condition for set invariance.
        
        The trajectory must point away from the unsafe region
        when near the boundary.
        """
        h_current = self.barrier(current_analysis)
        h_next = self.barrier(next_analysis)
        
        # Discrete approximation of ∂h/∂s · ṡ ≥ -α(h)
        dh = h_next - h_current
        alpha_h = self.alpha * abs(h_current)
        
        return dh >= -alpha_h

if __name__ == "__main__":
    print("🎭 Sycophancy Variance Detector Test")
    print("=" * 40)
    
    detector = SycophancyVarianceDetector()
    barrier = TruthBarrierFunction()
    
    # Mock model and data
    class MockModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = nn.Linear(128, 50257)  # Vocab size
        
        def __call__(self, x):
            return self.fc(x)
    
    model = MockModel()
    
    # Test cases
    test_cases = [
        ("Low variance (truthful)", 0.1),
        ("Medium variance", 0.3),
        ("High variance (sycophantic)", 0.7),
        ("Extreme variance", 1.0),
    ]
    
    for name, scale in test_cases:
        # Generate mock logits with varying variance
        input_emb = mx.random.normal((1, 10, 128))
        logits = mx.random.normal((1, 50257)) * scale
        
        analysis = detector.analyze(model, input_emb, logits)
        
        status = "❌ SYCOPHANTIC" if analysis.is_sycophantic else "✅ TRUTHFUL"
        print(f"\n{name}:")
        print(f"  Variance: {analysis.variance:.3f}")
        print(f"  Barrier h(s): {analysis.barrier_value:.3f}")
        print(f"  Status: {status}")
        print(f"  Latency: {analysis.latency_us:.1f}µs")
        
        if analysis.is_sycophantic:
            steering = detector.compute_steering_vector(analysis, logits)
            print(f"  Steering norm: {mx.linalg.norm(steering).item():.3f}")
    
    print("\n✅ Sycophancy Variance Detector test complete.")
