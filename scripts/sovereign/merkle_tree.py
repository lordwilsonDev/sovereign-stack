"""
Merkle Tree Aggregation for TrustAnchor
Batches token hashes into Merkle roots for efficient SEP signing.
"""

import hashlib
from dataclasses import dataclass
from typing import List, Optional
import time

@dataclass
class MerkleProof:
    """Proof that a leaf exists in the Merkle tree."""
    leaf_hash: str
    leaf_index: int
    siblings: List[str]
    root: str

@dataclass
class SignedBlock:
    """A block of tokens with Merkle root signature."""
    tokens: List[str]
    merkle_root: str
    signature: Optional[str]
    timestamp: float
    block_id: int

class MerkleTree:
    """
    Merkle Tree for batching token hashes.
    
    Solves the SEP throughput problem:
    - SEP can sign ~10-30 ops/sec
    - Model generates ~100+ tokens/sec
    - Solution: Hash N tokens → Sign 1 Merkle root
    """
    
    def __init__(self, hash_fn=None):
        self.hash_fn = hash_fn or self._sha256
        self.leaves: List[str] = []
        self.tree: List[List[str]] = []
    
    def _sha256(self, data: str) -> str:
        """Default hash function."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _combine(self, left: str, right: str) -> str:
        """Combine two hashes."""
        return self.hash_fn(left + right)
    
    def add_leaf(self, data: str) -> int:
        """Add a leaf and return its index."""
        leaf_hash = self.hash_fn(data)
        self.leaves.append(leaf_hash)
        return len(self.leaves) - 1
    
    def build(self) -> str:
        """Build the Merkle tree and return the root."""
        if not self.leaves:
            return self.hash_fn("")
        
        # Start with leaf hashes
        current_level = self.leaves.copy()
        self.tree = [current_level]
        
        # Build tree bottom-up
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # Handle odd number of nodes
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                next_level.append(self._combine(left, right))
            
            self.tree.append(next_level)
            current_level = next_level
        
        return current_level[0]
    
    def get_root(self) -> str:
        """Get the Merkle root (builds if necessary)."""
        if not self.tree or len(self.tree[-1]) != 1:
            return self.build()
        return self.tree[-1][0]
    
    def get_proof(self, index: int) -> MerkleProof:
        """Get Merkle proof for a leaf at given index."""
        if not self.tree:
            self.build()
        
        siblings = []
        current_index = index
        
        for level in self.tree[:-1]:
            # Find sibling index
            if current_index % 2 == 0:
                sibling_index = current_index + 1
            else:
                sibling_index = current_index - 1
            
            # Handle edge case
            if sibling_index < len(level):
                siblings.append(level[sibling_index])
            else:
                siblings.append(level[current_index])
            
            current_index //= 2
        
        return MerkleProof(
            leaf_hash=self.leaves[index],
            leaf_index=index,
            siblings=siblings,
            root=self.get_root()
        )
    
    def verify_proof(self, proof: MerkleProof) -> bool:
        """Verify a Merkle proof."""
        current = proof.leaf_hash
        index = proof.leaf_index
        
        for sibling in proof.siblings:
            if index % 2 == 0:
                current = self._combine(current, sibling)
            else:
                current = self._combine(sibling, current)
            index //= 2
        
        return current == proof.root
    
    def clear(self):
        """Clear the tree for reuse."""
        self.leaves = []
        self.tree = []

class TokenBlocker:
    """
    Accumulates tokens into blocks and produces signed Merkle roots.
    """
    
    def __init__(self, block_size: int = 32, signer=None):
        self.block_size = block_size
        self.signer = signer
        self.current_tokens: List[str] = []
        self.current_tree = MerkleTree()
        self.signed_blocks: List[SignedBlock] = []
        self.block_counter = 0
    
    def add_token(self, token: str) -> Optional[SignedBlock]:
        """
        Add a token. Returns SignedBlock when block is full.
        """
        self.current_tokens.append(token)
        self.current_tree.add_leaf(token)
        
        if len(self.current_tokens) >= self.block_size:
            return self._finalize_block()
        
        return None
    
    def _finalize_block(self) -> SignedBlock:
        """Finalize current block and sign it."""
        root = self.current_tree.get_root()
        
        # Sign with SEP if available
        signature = None
        if self.signer:
            try:
                signature = self.signer.sign(root)
            except:
                pass
        
        block = SignedBlock(
            tokens=self.current_tokens.copy(),
            merkle_root=root,
            signature=signature,
            timestamp=time.time(),
            block_id=self.block_counter
        )
        
        self.signed_blocks.append(block)
        self.block_counter += 1
        
        # Reset for next block
        self.current_tokens = []
        self.current_tree.clear()
        
        return block
    
    def flush(self) -> Optional[SignedBlock]:
        """Flush any remaining tokens as a partial block."""
        if self.current_tokens:
            return self._finalize_block()
        return None
    
    def get_all_blocks(self) -> List[SignedBlock]:
        """Get all signed blocks."""
        return self.signed_blocks

if __name__ == "__main__":
    print("🌳 Merkle Tree Test")
    print("=" * 40)
    
    # Test basic tree
    tree = MerkleTree()
    tokens = ["The", "quick", "brown", "fox", "jumps", "over", "the", "lazy"]
    
    for token in tokens:
        tree.add_leaf(token)
    
    root = tree.build()
    print(f"Tokens: {tokens}")
    print(f"Merkle Root: {root[:32]}...")
    
    # Test proof
    proof = tree.get_proof(3)  # Proof for "fox"
    print(f"\nProof for 'fox' (index 3):")
    print(f"  Leaf hash: {proof.leaf_hash[:32]}...")
    print(f"  Siblings: {len(proof.siblings)} hashes")
    print(f"  Valid: {tree.verify_proof(proof)}")
    
    # Test token blocker
    print("\n📦 TokenBlocker Test (block_size=4)")
    blocker = TokenBlocker(block_size=4)
    
    for i, token in enumerate(tokens):
        block = blocker.add_token(token)
        if block:
            print(f"  Block {block.block_id}: {block.tokens} → {block.merkle_root[:16]}...")
    
    # Flush remaining
    block = blocker.flush()
    if block:
        print(f"  Block {block.block_id}: {block.tokens} → {block.merkle_root[:16]}...")
    
    print(f"\nTotal blocks: {len(blocker.get_all_blocks())}")
    print("✅ Merkle Tree test complete.")
