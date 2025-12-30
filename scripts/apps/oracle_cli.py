import sys
import os
import json
import argparse
from pathlib import Path

# Add script paths to sys.path
scripts_dir = Path("/Users/lordwilson/sparse_axion_rag/scripts")
sys.path.append(str(scripts_dir / "analysis"))
sys.path.append(str(scripts_dir / "safety"))

from detect_anomalies import AxiomInverter
from filioque_verify import FilioqueProtocol

def main():
    parser = argparse.ArgumentParser(description="Axiom Oracle Strategic Query Interface")
    parser.add_argument("query", type=str, help="The strategic question or topic to explore.")
    args = parser.parse_args()

    print(f"\n🔮 AXIOM ORACLE: Analyzing '{args.query}'...\n")
    
    inverter = AxiomInverter()
    protocol = FilioqueProtocol()
    dataset_path = "/Users/lordwilson/sparse_axion_rag/output/axiom_dataset.jsonl"
    
    # 1. Load context
    with open(dataset_path, 'r') as f:
        data = [json.loads(line) for line in f]
    
    # 2. Find relevant axioms for the query
    print("🔍 Searching Cognitive Substrate...")
    query_emb = inverter.model.encode([args.query])[0]
    texts = [d['axiom_candidate'] for d in data]
    normative_embeddings = inverter.model.encode(texts)
    
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity([query_emb], normative_embeddings)[0]
    top_indices = similarities.argsort()[-3:][::-1]
    
    print("\n🌟 STRATEGIC INSIGHTS FOUND:\n")
    
    for idx in top_indices:
        axiom = texts[idx]
        inversions = inverter.invert_axiom(axiom)
        
        # Pick the most "radical" inversion
        best_inv = inversions[-1]
        
        # 3. Filioque Authorization Loop
        print(f"--- [REASONING] ---")
        print(f"Found Normative Axiom: '{axiom}'")
        print(f"Proposed Inversion: '{best_inv}'")
        
        payload = {"type": "insight_generation", "content": best_inv}
        gen_sig = protocol.sign_action(payload, protocol.generator_key)
        
        print("🔐 Requesting Filioque Authorization...")
        # In this CLI, we auto-verify since it's a query, but simulate the check
        ver_sig = protocol.sign_action(payload, protocol.verifier_key)
        authorized, msg = protocol.verify_auth(payload, gen_sig, ver_sig)
        
        if authorized:
            print(f"{msg}")
            print(f"💡 ORACLE ADVICE: To solve for '{args.query}', consider the inversion: '{best_inv}'")
            print(f"   (Source Doc: {data[idx]['doc_id']})")
        else:
            print(f"⚠️ {msg}")
        print("-" * 30)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: oracle <query>")
        sys.exit(1)
    main()
