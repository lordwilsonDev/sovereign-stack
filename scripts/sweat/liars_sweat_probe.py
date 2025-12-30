"""
LiarsSweatProbe: Linear Classifier for Sycophancy Detection
Detects the computational stress of deception in the residual stream.
"""

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
from dataclasses import dataclass
from typing import Optional, Tuple
import time

@dataclass
class SweatResult:
    """Result from the Liar's Sweat probe."""
    score: float  # 0-1, higher = more sycophantic
    is_sycophantic: bool
    latency_us: float  # Microseconds
    layer_id: int

class LiarsSweatProbe(nn.Module):
    """
    Linear probe trained to detect sycophancy in activation space.
    
    The probe learns a direction vector W_probe such that:
    SweatScore(x) = σ(W_probe · x + b_probe)
    
    Where high scores indicate the model is suppressing truth to agree.
    """
    
    def __init__(self, input_dim: int):
        super().__init__()
        self.projection = nn.Linear(input_dim, 1)
        self.input_dim = input_dim
    
    def __call__(self, x: mx.array) -> mx.array:
        """
        Compute sweat score from activation vector.
        Returns probability 0-1.
        """
        logits = self.projection(x)
        return mx.sigmoid(logits)
    
    def get_direction_vector(self) -> mx.array:
        """Get the learned sycophancy direction in activation space."""
        return self.projection.weight.squeeze()
    
    def check(self, activation: mx.array, threshold: float = 0.85) -> SweatResult:
        """
        Check an activation vector for sycophancy.
        Measures latency for performance monitoring.
        """
        t0 = time.perf_counter_ns()
        
        score = self(activation)
        mx.eval(score)  # Force computation
        
        t1 = time.perf_counter_ns()
        latency_us = (t1 - t0) / 1000
        
        score_val = score.item() if score.ndim == 0 else score.squeeze().item()
        
        return SweatResult(
            score=score_val,
            is_sycophantic=score_val > threshold,
            latency_us=latency_us,
            layer_id=-1  # Set by caller
        )

class ProbeTrainer:
    """
    Training pipeline for the Liar's Sweat probe.
    Uses Binary Cross Entropy with empathy decorrelation.
    """
    
    def __init__(
        self,
        input_dim: int,
        learning_rate: float = 0.001,
        empathy_penalty: float = 0.1
    ):
        self.probe = LiarsSweatProbe(input_dim)
        self.optimizer = optim.Adam(learning_rate=learning_rate)
        self.empathy_penalty = empathy_penalty
        mx.eval(self.probe.parameters())
    
    def loss_fn(
        self,
        model: LiarsSweatProbe,
        X: mx.array,
        y: mx.array,
        empathy_labels: Optional[mx.array] = None
    ) -> mx.array:
        """
        Binary Cross Entropy with optional empathy decorrelation.
        
        Args:
            X: Activation vectors [N, dim]
            y: Sycophancy labels [N] (1 = sycophantic, 0 = honest)
            empathy_labels: Empathy scores [N] (for decorrelation)
        """
        logits = model.projection(X).squeeze()
        bce_loss = nn.losses.binary_cross_entropy(logits, y)
        
        if empathy_labels is not None and self.empathy_penalty > 0:
            # Penalize correlation between predictions and empathy
            predictions = mx.sigmoid(logits)
            correlation = mx.abs(mx.mean(predictions * empathy_labels) - 
                                 mx.mean(predictions) * mx.mean(empathy_labels))
            bce_loss = bce_loss + self.empathy_penalty * correlation
        
        return bce_loss
    
    def train_step(
        self,
        X: mx.array,
        y: mx.array,
        empathy_labels: Optional[mx.array] = None
    ) -> float:
        """Single training step. Returns loss value."""
        loss_and_grad = nn.value_and_grad(self.probe, lambda m: self.loss_fn(m, X, y, empathy_labels))
        loss, grads = loss_and_grad(self.probe)
        self.optimizer.update(self.probe, grads)
        mx.eval(self.probe.parameters(), self.optimizer.state)
        return loss.item()
    
    def train(
        self,
        X_train: mx.array,
        y_train: mx.array,
        empathy_train: Optional[mx.array] = None,
        epochs: int = 100,
        batch_size: int = 32,
        verbose: bool = True
    ) -> LiarsSweatProbe:
        """
        Full training loop.
        """
        n_samples = X_train.shape[0]
        
        for epoch in range(epochs):
            # Simple full-batch training for small datasets
            loss = self.train_step(X_train, y_train, empathy_train)
            
            if verbose and (epoch + 1) % 10 == 0:
                # Calculate accuracy
                preds = (self.probe(X_train).squeeze() > 0.5).astype(mx.float32)
                accuracy = mx.mean(preds == y_train).item()
                print(f"Epoch {epoch+1}/{epochs}: Loss={loss:.4f}, Accuracy={accuracy:.2%}")
        
        return self.probe

def calculate_empathy_correlation(
    probe: LiarsSweatProbe,
    X: mx.array,
    empathy_labels: mx.array
) -> float:
    """
    Calculate correlation between probe scores and empathy labels.
    Target: < 0.10 for successful decoupling.
    """
    scores = probe(X).squeeze()
    mx.eval(scores)
    
    # Pearson correlation
    mean_scores = mx.mean(scores)
    mean_empathy = mx.mean(empathy_labels)
    
    numerator = mx.mean((scores - mean_scores) * (empathy_labels - mean_empathy))
    denominator = mx.sqrt(mx.mean((scores - mean_scores)**2) * mx.mean((empathy_labels - mean_empathy)**2))
    
    correlation = numerator / (denominator + 1e-8)
    return abs(correlation.item())

if __name__ == "__main__":
    print("🔬 LiarsSweatProbe Test")
    print("=" * 40)
    
    # Create probe
    input_dim = 4096
    probe = LiarsSweatProbe(input_dim)
    
    # Test with random activation
    activation = mx.random.normal((input_dim,))
    result = probe.check(activation)
    
    print(f"Input dim: {input_dim}")
    print(f"Sweat Score: {result.score:.4f}")
    print(f"Is Sycophantic: {result.is_sycophantic}")
    print(f"Latency: {result.latency_us:.2f}µs")
    
    # Test training
    print("\n📊 Training Test...")
    trainer = ProbeTrainer(input_dim)
    
    # Synthetic data
    X = mx.random.normal((100, input_dim))
    y = mx.array([1.0 if i < 50 else 0.0 for i in range(100)])
    empathy = mx.random.uniform(shape=(100,))
    
    trained_probe = trainer.train(X, y, empathy, epochs=50, verbose=True)
    
    # Check empathy correlation
    corr = calculate_empathy_correlation(trained_probe, X, empathy)
    print(f"\nEmpathy Correlation: {corr:.4f} (target: < 0.10)")
    print("✅ LiarsSweatProbe initialized successfully.")
