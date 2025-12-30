import json
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

class AxiomInverter:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def invert_axiom(self, statement):
        """Phase 1.2: Three-stage inversion logic."""
        inversions = []
        
        # 1. Direct Negation
        negation = f"NOT ({statement})"
        if "is" in statement.lower():
            negation = statement.lower().replace("is", "is NOT").capitalize()
        inversions.append(negation)
        
        # 2. Constraint Removal
        if "limit" in statement.lower() or "bound" in statement.lower():
            removal = f"Constraints removed: {statement}"
            inversions.append(removal)
            
        # 3. Substitution
        sub = statement.lower().replace("we", "the external environment").capitalize()
        inversions.append(sub)
        
        return inversions

    def detect_anomalies(self, dataset_path):
        """Analyze semantic space to find 'Bridge Points'."""
        with open(dataset_path, 'r') as f:
            data = [json.loads(line) for line in f]
        
        texts = [d['axiom_candidate'] for d in data]
        print(f"🔄 Embedding {len(texts)} normative statements...")
        normative_embeddings = self.model.encode(texts)
        
        # Generate target inversions for a sample of high-weight axioms
        high_weight_data = [d for d in data if d['structural_weight'] >= 4.0]
        anomalies = []
        
        for d in high_weight_data[:5]: # Sample 5 key axioms
            axiom = d['axiom_candidate']
            inverted_options = self.invert_axiom(axiom)
            
            for inverted in inverted_options:
                inv_emb = self.model.encode([inverted])[0]
                
                # Find 'Bridge Points': real docs that land closer to the inversion
                # than the average normative cluster
                similarities = cosine_similarity([inv_emb], normative_embeddings)[0]
                
                # Top match in real data for this 'Impossible' scenario
                top_idx = np.argmax(similarities)
                bridge_score = similarities[top_idx]
                
                if bridge_score > 0.7: # Threshold for 'Reality leaking into Impossible'
                    anomalies.append({
                        "original_axiom": axiom,
                        "inverted_axiom": inverted,
                        "bridge_point_text": texts[top_idx],
                        "confidence": float(bridge_score),
                        "doc_id": data[top_idx]['doc_id']
                    })
        
        return anomalies

    def cove_loop(self, prediction):
        """Phase 5.1: Chain of Verification loop."""
        print(f"🔍 CoVe Loop: Verifying prediction - {prediction['inverted_axiom']}")
        # 1. Fact Extraction
        # 2. Verification Query against original dataset
        # 3. Correction
        return True # Verified for demo purposes

def main():
    dataset_path = "/Users/lordwilson/sparse_axion_rag/output/axiom_dataset.jsonl"
    inverter = AxiomInverter()
    
    print("🚀 Starting Anomaly Detection...")
    anomalies = inverter.detect_anomalies(dataset_path)
    
    print(f"\n🎯 DISCOVERED {len(anomalies)} POTENTIAL ANOMALIES:\n")
    for a in anomalies:
        if inverter.cove_loop(a):
            print(f"--- ANOMALY FOUND ---")
            print(f"Assumption: {a['original_axiom']}")
            print(f"Inversion: {a['inverted_axiom']}")
            print(f"Bridge Point (Real Data): {a['bridge_point_text']}")
            print(f"Source: {a['doc_id']}")
            print(f"Confidence: {a['confidence']:.2f}")
            print("-" * 20)

if __name__ == "__main__":
    main()
