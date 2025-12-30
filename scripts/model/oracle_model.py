import mlx.core as mx
import mlx.nn as nn
import math

class BitLinear(nn.Module):
    def __init__(self, input_dims, output_dims, bias=True):
        super().__init__()
        self.weight = mx.random.normal((output_dims, input_dims)) * math.sqrt(2.0 / input_dims)
        if bias:
            self.bias = mx.zeros((output_dims,))
        else:
            self.bias = None

    def __call__(self, x):
        w = self.weight
        mean_w = mx.mean(w)
        w_centered = w - mean_w
        scale = mx.mean(mx.abs(w_centered)) + 1e-5
        w_q = mx.round(mx.clip(w_centered / scale, -1, 1))
        
        x_max = mx.abs(x).max(axis=-1, keepdims=True) + 1e-5
        x_q = x * (127.0 / x_max)
        
        y = mx.matmul(x_q, w_q.T)
        y = y * (x_max * scale / 127.0)
        
        if self.bias is not None:
            y = y + self.bias
        return y

class MultiHeadAttention(nn.Module):
    def __init__(self, dims, num_heads):
        super().__init__()
        self.num_heads = num_heads
        self.query_proj = BitLinear(dims, dims)
        self.key_proj = BitLinear(dims, dims)
        self.value_proj = BitLinear(dims, dims)
        self.out_proj = BitLinear(dims, dims)

    def __call__(self, x, mask=None):
        B, L, D = x.shape
        queries = self.query_proj(x).reshape(B, L, self.num_heads, D // self.num_heads).transpose(0, 2, 1, 3)
        keys = self.key_proj(x).reshape(B, L, self.num_heads, D // self.num_heads).transpose(0, 2, 1, 3)
        values = self.value_proj(x).reshape(B, L, self.num_heads, D // self.num_heads).transpose(0, 2, 1, 3)

        scores = mx.matmul(queries, keys.transpose(0, 1, 3, 2)) / math.sqrt(D // self.num_heads)
        if mask is not None:
            scores = scores + mask
        
        weights = mx.softmax(scores, axis=-1)
        out = mx.matmul(weights, values).transpose(0, 2, 1, 3).reshape(B, L, D)
        return self.out_proj(out)

class TransformerBlock(nn.Module):
    def __init__(self, dims, num_heads, mlp_dims):
        super().__init__()
        self.ln1 = nn.LayerNorm(dims)
        self.attention = MultiHeadAttention(dims, num_heads)
        self.ln2 = nn.LayerNorm(dims)
        self.mlp = nn.Sequential(
            BitLinear(dims, mlp_dims),
            nn.GELU(),
            BitLinear(mlp_dims, dims)
        )

    def __call__(self, x, mask=None):
        x = x + self.attention(self.ln1(x), mask)
        x = x + self.mlp(self.ln2(x))
        return x

class SparseOracle(nn.Module):
    def __init__(self, vocab_size, num_layers, dims, mlp_dims, num_heads):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, dims)
        self.layers = [
            TransformerBlock(dims, num_heads, mlp_dims)
            for _ in range(num_layers)
        ]
        self.out_proj = BitLinear(dims, vocab_size)

    def __call__(self, x):
        mask = nn.MultiHeadAttention.create_additive_causal_mask(x.shape[1])
        x = self.embedding(x)
        for layer in self.layers:
            x = layer(x, mask)
        return self.out_proj(x)

def get_model():
    return SparseOracle(
        vocab_size=32000,
        num_layers=12,
        dims=1024,
        mlp_dims=4096,
        num_heads=16
    )

if __name__ == "__main__":
    model = get_model()
    x = mx.array([[1, 2, 3, 4, 5]])
    y = model(x)
    print(f"Model output shape: {y.shape}")
    print("BitNet b1.58 Sparse Oracle (Manual Refactor) initialized successfully.")
