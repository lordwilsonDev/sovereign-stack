"""
ProbeWrapper: MLX Layer Hooking Mechanism
Transparently intercepts activations from transformer layers for analysis.
Zero-copy access via Apple Silicon Unified Memory Architecture.
"""

import mlx.core as mx
import mlx.nn as nn
from typing import Optional, Dict, Any

class ProbeWrapper(nn.Module):
    """
    Wraps a transformer layer to capture its output activations.
    Acts as a transparent passthrough that saves the residual stream state.
    """
    
    def __init__(self, layer: nn.Module, layer_id: int):
        super().__init__()
        self.layer = layer
        self.layer_id = layer_id
        self.activations: Optional[mx.array] = None
        self._capture_enabled = True
    
    def __call__(self, x: mx.array, *args, **kwargs) -> mx.array:
        """
        Forward pass: execute original layer and capture output.
        """
        # Execute the original layer's forward pass
        output = self.layer(x, *args, **kwargs)
        
        # Capture the activation (residual stream state)
        if self._capture_enabled:
            # Store without tracking gradients for the probe
            self.activations = output
        
        return output
    
    def get_last_token_activation(self) -> Optional[mx.array]:
        """
        Get the activation for the last token position.
        This is the critical decision point before generation.
        """
        if self.activations is None:
            return None
        
        # Shape: [batch, seq_len, dim] -> [dim]
        return self.activations[0, -1, :]
    
    def enable_capture(self):
        self._capture_enabled = True
    
    def disable_capture(self):
        self._capture_enabled = False
    
    def clear(self):
        """Clear stored activations to free memory."""
        self.activations = None

class ModelInstrumentor:
    """
    Instruments a model by wrapping specific layers with ProbeWrappers.
    """
    
    def __init__(self, model: nn.Module):
        self.model = model
        self.wrappers: Dict[int, ProbeWrapper] = {}
        self._original_layers: Dict[int, nn.Module] = {}
    
    def instrument_layers(self, layer_indices: list[int]):
        """
        Replace specified layers with ProbeWrappers.
        Target middle-to-late layers where semantic conflict is highest.
        """
        # Detect model structure
        layers = self._get_layers()
        
        for i in layer_indices:
            if i >= len(layers):
                print(f"⚠️ Layer {i} out of range (model has {len(layers)} layers)")
                continue
            
            # Store original
            self._original_layers[i] = layers[i]
            
            # Create wrapper
            wrapper = ProbeWrapper(layers[i], i)
            self.wrappers[i] = wrapper
            
            # Replace in model
            self._set_layer(i, wrapper)
        
        print(f"📊 Instrumented {len(self.wrappers)} layers: {list(self.wrappers.keys())}")
    
    def _get_layers(self) -> list:
        """Get the list of transformer layers from the model."""
        # Handle different model structures
        if hasattr(self.model, 'model') and hasattr(self.model.model, 'layers'):
            return self.model.model.layers
        elif hasattr(self.model, 'layers'):
            return self.model.layers
        elif hasattr(self.model, 'transformer') and hasattr(self.model.transformer, 'h'):
            return self.model.transformer.h
        else:
            raise ValueError("Unknown model structure - cannot locate layers")
    
    def _set_layer(self, index: int, new_layer: nn.Module):
        """Set a layer at the specified index."""
        if hasattr(self.model, 'model') and hasattr(self.model.model, 'layers'):
            self.model.model.layers[index] = new_layer
        elif hasattr(self.model, 'layers'):
            self.model.layers[index] = new_layer
        elif hasattr(self.model, 'transformer'):
            self.model.transformer.h[index] = new_layer
    
    def get_activations(self, layer_id: int) -> Optional[mx.array]:
        """Get activations from a specific instrumented layer."""
        if layer_id in self.wrappers:
            return self.wrappers[layer_id].get_last_token_activation()
        return None
    
    def get_all_activations(self) -> Dict[int, mx.array]:
        """Get activations from all instrumented layers."""
        result = {}
        for layer_id, wrapper in self.wrappers.items():
            act = wrapper.get_last_token_activation()
            if act is not None:
                result[layer_id] = act
        return result
    
    def clear_all(self):
        """Clear all stored activations."""
        for wrapper in self.wrappers.values():
            wrapper.clear()
    
    def restore_original(self):
        """Restore original layers (remove instrumentation)."""
        for i, original in self._original_layers.items():
            self._set_layer(i, original)
        self.wrappers.clear()
        self._original_layers.clear()

if __name__ == "__main__":
    print("📊 ProbeWrapper Test")
    print("=" * 40)
    
    # Create a mock layer and wrapper
    class MockLayer(nn.Module):
        def __init__(self, dim):
            super().__init__()
            self.linear = nn.Linear(dim, dim)
        
        def __call__(self, x):
            return self.linear(x)
    
    mock_layer = MockLayer(128)
    wrapper = ProbeWrapper(mock_layer, layer_id=15)
    
    # Test forward pass
    x = mx.random.normal((1, 10, 128))
    output = wrapper(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Captured activation shape: {wrapper.activations.shape}")
    print(f"Last token activation shape: {wrapper.get_last_token_activation().shape}")
    print("✅ ProbeWrapper initialized successfully.")
