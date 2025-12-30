"""
Sweat Detector: Real-Time Sycophancy Detection During Generation
Integrates ProbeWrapper and LiarsSweatProbe for live monitoring.
"""

import mlx.core as mx
import mlx.nn as nn
import time
from dataclasses import dataclass
from typing import Optional, Dict, List, Callable
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from probe_wrapper import ProbeWrapper, ModelInstrumentor
from liars_sweat_probe import LiarsSweatProbe, SweatResult

@dataclass
class SweatAlert:
    """Alert generated when sycophancy is detected."""
    score: float
    layer_id: int
    token_position: int
    severity: str  # "low", "medium", "high", "critical"
    recommendation: str

class SweatDetector:
    """
    Real-time sycophancy detector using activation probing.
    
    Monitors the residual stream for signs of "computational stress"
    when the model suppresses truth to agree with the user.
    """
    
    def __init__(
        self,
        probe_path: Optional[str] = None,
        threshold: float = 0.85,
        target_layers: Optional[List[int]] = None
    ):
        self.threshold = threshold
        self.target_layers = target_layers or list(range(15, 25))
        self.instrumentor: Optional[ModelInstrumentor] = None
        self.probe: Optional[LiarsSweatProbe] = None
        self.alerts: List[SweatAlert] = []
        self._on_alert_callback: Optional[Callable] = None
        
        if probe_path and Path(probe_path).exists():
            self._load_probe(probe_path)
    
    def _load_probe(self, path: str):
        """Load a trained probe from disk."""
        # In production, load weights via mx.load
        pass
    
    def attach_to_model(self, model: nn.Module):
        """
        Instrument the model for sweat detection.
        """
        self.instrumentor = ModelInstrumentor(model)
        self.instrumentor.instrument_layers(self.target_layers)
        
        # Initialize probe with correct dimension
        # Detect dimension from first wrapper
        if self.target_layers:
            sample_dim = 4096  # Default, will be updated on first activation
            self.probe = LiarsSweatProbe(sample_dim)
    
    def detach_from_model(self):
        """Remove instrumentation from model."""
        if self.instrumentor:
            self.instrumentor.restore_original()
            self.instrumentor = None
    
    def check_activations(self, token_position: int = 0) -> Dict[int, SweatResult]:
        """
        Check all instrumented layers for sycophancy.
        Returns results keyed by layer ID.
        """
        if not self.instrumentor or not self.probe:
            return {}
        
        results = {}
        activations = self.instrumentor.get_all_activations()
        
        for layer_id, activation in activations.items():
            # Ensure probe dimension matches
            if activation.shape[-1] != self.probe.input_dim:
                self.probe = LiarsSweatProbe(activation.shape[-1])
            
            result = self.probe.check(activation, self.threshold)
            result.layer_id = layer_id
            results[layer_id] = result
            
            # Generate alert if sycophantic
            if result.is_sycophantic:
                self._generate_alert(result, token_position)
        
        return results
    
    def get_max_sweat_score(self) -> float:
        """Get the maximum sweat score across all layers."""
        if not self.instrumentor or not self.probe:
            return 0.0
        
        results = self.check_activations()
        if not results:
            return 0.0
        
        return max(r.score for r in results.values())
    
    def _generate_alert(self, result: SweatResult, token_position: int):
        """Generate an alert for detected sycophancy."""
        if result.score >= 0.95:
            severity = "critical"
            recommendation = "ABORT generation immediately"
        elif result.score >= 0.90:
            severity = "high"
            recommendation = "Inject honesty steering vector"
        elif result.score >= self.threshold:
            severity = "medium"
            recommendation = "Flag for review"
        else:
            severity = "low"
            recommendation = "Monitor"
        
        alert = SweatAlert(
            score=result.score,
            layer_id=result.layer_id,
            token_position=token_position,
            severity=severity,
            recommendation=recommendation
        )
        
        self.alerts.append(alert)
        
        if self._on_alert_callback:
            self._on_alert_callback(alert)
    
    def on_alert(self, callback: Callable[[SweatAlert], None]):
        """Register a callback for when sycophancy is detected."""
        self._on_alert_callback = callback
    
    def clear_alerts(self):
        """Clear all stored alerts."""
        self.alerts.clear()
    
    def get_summary(self) -> dict:
        """Get summary of detection session."""
        if not self.alerts:
            return {
                "total_alerts": 0,
                "max_score": 0.0,
                "status": "clean"
            }
        
        return {
            "total_alerts": len(self.alerts),
            "max_score": max(a.score for a in self.alerts),
            "critical_count": sum(1 for a in self.alerts if a.severity == "critical"),
            "high_count": sum(1 for a in self.alerts if a.severity == "high"),
            "status": "sycophancy_detected"
        }

# Integration with FAO
async def sweat_check_middleware(activation: mx.array, detector: SweatDetector) -> bool:
    """
    Middleware function for integration with A-bind.
    Returns True if generation should continue, False to abort.
    """
    if detector.probe is None:
        return True
    
    result = detector.probe.check(activation)
    
    if result.is_sycophantic:
        print(f"⚠️ LIAR'S SWEAT DETECTED: Score {result.score:.2f} (Latency: {result.latency_us:.1f}µs)")
        return False
    
    return True

if __name__ == "__main__":
    print("🔬 SweatDetector Test")
    print("=" * 40)
    
    # Create detector
    detector = SweatDetector(threshold=0.7)
    
    # Mock model with layers
    class MockModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = [nn.Linear(128, 128) for _ in range(32)]
        
        def __call__(self, x):
            for layer in self.layers:
                x = layer(x)
            return x
    
    model = MockModel()
    
    # Attach detector
    detector.attach_to_model(model)
    print(f"Attached to model with {len(detector.target_layers)} instrumented layers")
    
    # Register alert callback
    def on_alert(alert: SweatAlert):
        print(f"🚨 ALERT: {alert.severity.upper()} - Score {alert.score:.2f} at layer {alert.layer_id}")
    
    detector.on_alert(on_alert)
    
    # Simulate forward pass
    x = mx.random.normal((1, 10, 128))
    _ = model(x)
    
    # Check activations
    results = detector.check_activations(token_position=0)
    print(f"\nChecked {len(results)} layers")
    
    # Summary
    summary = detector.get_summary()
    print(f"Status: {summary['status']}")
    print(f"Total alerts: {summary['total_alerts']}")
    
    # Cleanup
    detector.detach_from_model()
    print("\n✅ SweatDetector test complete.")
