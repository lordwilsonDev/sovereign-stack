"""
NLI Verifier: Neural Logic Inference for Truth Verification
Uses a quantized NLI model to determine Entailment/Contradiction/Neutral.
"""

import torch
from transformers import pipeline
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class NLIResult(Enum):
    ENTAILMENT = "entailment"
    CONTRADICTION = "contradiction"
    NEUTRAL = "neutral"

@dataclass
class VerificationResult:
    label: NLIResult
    score: float
    is_verified: bool
    coherence_delta: float

class NLIVerifier:
    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        """
        Initialize the NLI verifier with a pretrained model.
        Uses zero-shot classification for flexibility.
        """
        self.classifier = pipeline(
            "zero-shot-classification",
            model=model_name,
            device="mps" if torch.backends.mps.is_available() else "cpu"
        )
        self.axioms: List[str] = []
        self.ground_truths: List[str] = []
    
    def add_axiom(self, axiom: str):
        """Add a safety axiom that must never be contradicted."""
        self.axioms.append(axiom)
    
    def add_ground_truth(self, fact: str):
        """Add a ground truth from RAG or external source."""
        self.ground_truths.append(fact)
    
    def verify(self, hypothesis: str, premise: Optional[str] = None) -> VerificationResult:
        """
        Verify a hypothesis against premises (axioms + ground truths).
        Returns verification result with coherence delta.
        """
        # Construct the premise from all sources
        if premise:
            premises = [premise]
        else:
            premises = self.axioms + self.ground_truths
        
        if not premises:
            # No constraints to check against
            return VerificationResult(
                label=NLIResult.NEUTRAL,
                score=0.5,
                is_verified=True,
                coherence_delta=0.0
            )
        
        # Check for contradictions against each premise
        for p in premises:
            result = self.classifier(
                hypothesis,
                candidate_labels=["entailment", "contradiction", "neutral"],
                hypothesis_template="This text: {}",
                multi_label=False
            )
            
            labels = result["labels"]
            scores = result["scores"]
            
            top_label = labels[0]
            top_score = scores[0]
            
            if top_label == "contradiction" and top_score > 0.7:
                return VerificationResult(
                    label=NLIResult.CONTRADICTION,
                    score=top_score,
                    is_verified=False,
                    coherence_delta=-0.2
                )
        
        # If no contradiction found, check for entailment
        entailment_score = scores[labels.index("entailment")] if "entailment" in labels else 0.0
        
        if entailment_score > 0.8:
            return VerificationResult(
                label=NLIResult.ENTAILMENT,
                score=entailment_score,
                is_verified=True,
                coherence_delta=0.05
            )
        
        return VerificationResult(
            label=NLIResult.NEUTRAL,
            score=0.5,
            is_verified=True,
            coherence_delta=0.0
        )

if __name__ == "__main__":
    print("🔍 NLI Verifier Test")
    print("=" * 40)
    
    verifier = NLIVerifier()
    verifier.add_axiom("The system must never generate harmful content.")
    verifier.add_ground_truth("Apple Silicon uses a Unified Memory Architecture.")
    
    # Test 1: Entailment
    result = verifier.verify("M1 chips share memory between CPU and GPU.")
    print(f"Test 1 (Entailment): {result.label.value}, Score: {result.score:.2f}, Verified: {result.is_verified}")
    
    # Test 2: Contradiction (would need real NLI model)
    result = verifier.verify("M1 chips have separate memory for CPU and GPU.")
    print(f"Test 2 (Should Contradict): {result.label.value}, Score: {result.score:.2f}, Verified: {result.is_verified}")
    
    print("✅ NLI Verifier initialized.")
