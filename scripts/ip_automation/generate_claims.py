#!/usr/bin/env python3
"""
Generate preliminary patent claims from invention disclosures.

This script generates structured patent claims in proper format
for attorney review and refinement.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def load_disclosures():
    """Load invention disclosures."""
    disclosures = []
    disclosure_dir = Path('output/ip_disclosures')
    
    if disclosure_dir.exists():
        for filepath in disclosure_dir.glob('disclosure_*.json'):
            try:
                with open(filepath, 'r') as f:
                    disclosures.append(json.load(f))
            except Exception:
                continue
    
    return disclosures


def load_novelty_analysis():
    """Load novelty analysis for additional context."""
    analysis_path = 'output/ip_disclosures/novelty_analysis.json'
    if os.path.exists(analysis_path):
        with open(analysis_path, 'r') as f:
            return json.load(f)
    return None


def generate_claims_for_disclosure(disclosure, novelty_data=None):
    """Generate patent claims for a single disclosure."""
    invention = disclosure.get('invention', {})
    source = disclosure.get('source_reference', {})
    indicators = source.get('indicators', [])
    
    claims = {
        'disclosure_id': disclosure.get('disclosure_id'),
        'title': invention.get('title', 'Untitled Invention'),
        'claims': [],
        'claim_strategy': determine_claim_strategy(indicators),
        'generated_at': datetime.utcnow().isoformat(),
        'status': 'draft',
        'requires_attorney_review': True
    }
    
    # Generate independent claims
    independent_claims = generate_independent_claims(invention, source, indicators)
    claims['claims'].extend(independent_claims)
    
    # Generate dependent claims
    dependent_claims = generate_dependent_claims(invention, source, indicators)
    claims['claims'].extend(dependent_claims)
    
    # Add system claims
    system_claims = generate_system_claims(invention, source, indicators)
    claims['claims'].extend(system_claims)
    
    return claims


def determine_claim_strategy(indicators):
    """Determine the most appropriate claim strategy."""
    if 'ml_component' in indicators:
        return {
            'type': 'method_and_system',
            'focus': 'Data processing and model architecture',
            'notes': 'Consider both training method and inference system claims'
        }
    elif 'algorithm_implementation' in indicators:
        return {
            'type': 'method_primary',
            'focus': 'Algorithmic steps and processing logic',
            'notes': 'Emphasize novel computational steps'
        }
    elif 'custom_data_structure' in indicators:
        return {
            'type': 'apparatus_primary',
            'focus': 'Data organization and access patterns',
            'notes': 'Consider memory organization and retrieval claims'
        }
    elif 'performance_optimization' in indicators:
        return {
            'type': 'method_and_system',
            'focus': 'Performance improvement techniques',
            'notes': 'Quantify performance improvements where possible'
        }
    else:
        return {
            'type': 'method_and_system',
            'focus': 'General software implementation',
            'notes': 'Consider both method and system claim formats'
        }


def generate_independent_claims(invention, source, indicators):
    """Generate independent patent claims."""
    claims = []
    claim_number = 1
    
    # Method claim (Claim 1)
    method_preamble = "A computer-implemented method"
    method_body = generate_method_claim_body(invention, source, indicators)
    
    claims.append({
        'number': claim_number,
        'type': 'independent',
        'category': 'method',
        'text': f"{claim_number}. {method_preamble} comprising:\n{method_body}",
        'elements': extract_claim_elements(method_body)
    })
    claim_number += 1
    
    # System claim (typically Claim 8 or similar)
    system_preamble = "A system"
    system_body = generate_system_claim_body(invention, source, indicators)
    
    claims.append({
        'number': claim_number,
        'type': 'independent',
        'category': 'system',
        'text': f"{claim_number}. {system_preamble} comprising:\n{system_body}",
        'elements': extract_claim_elements(system_body)
    })
    claim_number += 1
    
    # CRM claim (Computer Readable Medium)
    crm_preamble = "A non-transitory computer-readable medium"
    crm_body = generate_crm_claim_body(invention, source, indicators)
    
    claims.append({
        'number': claim_number,
        'type': 'independent',
        'category': 'crm',
        'text': f"{claim_number}. {crm_preamble} storing instructions that, when executed by a processor, cause the processor to:\n{crm_body}",
        'elements': extract_claim_elements(crm_body)
    })
    
    return claims


def generate_method_claim_body(invention, source, indicators):
    """Generate the body of a method claim."""
    steps = []
    
    # Add receiving step
    steps.append("receiving, by a processor, input data for processing;")
    
    # Add processing steps based on indicators
    if 'ml_component' in indicators:
        steps.append("applying, by the processor, a machine learning model to the input data to generate intermediate representations;")
        steps.append("transforming the intermediate representations through one or more processing layers;")
    
    if 'algorithm_implementation' in indicators:
        steps.append("executing, by the processor, an algorithmic process on the input data, the algorithmic process comprising:")
        steps.append("    determining one or more computational parameters based on characteristics of the input data;")
        steps.append("    iteratively processing the input data according to the determined parameters;")
    
    if 'custom_data_structure' in indicators:
        steps.append("organizing the input data into a structured format optimized for efficient access;")
        steps.append("indexing the structured data to enable rapid retrieval operations;")
    
    if 'performance_optimization' in indicators:
        steps.append("optimizing processing operations based on system resource availability;")
        steps.append("caching intermediate results to reduce redundant computations;")
    
    # Add output step
    steps.append("generating, by the processor, output data based on the processing; and")
    steps.append("providing the output data for subsequent use.")
    
    return '\n'.join(f"    {step}" for step in steps)


def generate_system_claim_body(invention, source, indicators):
    """Generate the body of a system claim."""
    elements = []
    
    elements.append("one or more processors;")
    elements.append("memory coupled to the one or more processors, the memory storing instructions that, when executed by the one or more processors, cause the system to:")
    
    # Add functional elements based on indicators
    if 'ml_component' in indicators:
        elements.append("    implement a machine learning component configured to process input data;")
    
    if 'algorithm_implementation' in indicators:
        elements.append("    execute an algorithmic processing module;")
    
    if 'custom_data_structure' in indicators:
        elements.append("    maintain an optimized data structure for efficient data organization;")
    
    if 'performance_optimization' in indicators:
        elements.append("    apply performance optimization techniques during data processing;")
    
    elements.append("    generate output data based on the processing operations.")
    
    return '\n'.join(f"    {elem}" for elem in elements)


def generate_crm_claim_body(invention, source, indicators):
    """Generate the body of a CRM claim."""
    steps = []
    
    steps.append("receive input data;")
    
    if 'ml_component' in indicators:
        steps.append("process the input data using a trained model;")
    
    if 'algorithm_implementation' in indicators:
        steps.append("apply algorithmic processing to transform the input data;")
    
    steps.append("generate output based on the processing; and")
    steps.append("store or transmit the output.")
    
    return '\n'.join(f"    {step}" for step in steps)


def generate_dependent_claims(invention, source, indicators):
    """Generate dependent patent claims."""
    claims = []
    base_claim = 1  # Reference to independent claim
    claim_number = 4  # Start after independent claims
    
    # Add specific limitations based on indicators
    if 'ml_component' in indicators:
        claims.append({
            'number': claim_number,
            'type': 'dependent',
            'depends_on': base_claim,
            'category': 'method',
            'text': f"{claim_number}. The method of claim {base_claim}, wherein the machine learning model comprises a neural network architecture.",
            'elements': ['neural network architecture']
        })
        claim_number += 1
        
        claims.append({
            'number': claim_number,
            'type': 'dependent',
            'depends_on': claim_number - 1,
            'category': 'method',
            'text': f"{claim_number}. The method of claim {claim_number - 1}, wherein the neural network architecture comprises one or more transformer layers.",
            'elements': ['transformer layers']
        })
        claim_number += 1
    
    if 'performance_optimization' in indicators:
        claims.append({
            'number': claim_number,
            'type': 'dependent',
            'depends_on': base_claim,
            'category': 'method',
            'text': f"{claim_number}. The method of claim {base_claim}, further comprising caching results of the processing to optimize subsequent operations.",
            'elements': ['caching', 'optimization']
        })
        claim_number += 1
    
    if 'algorithm_implementation' in indicators:
        claims.append({
            'number': claim_number,
            'type': 'dependent',
            'depends_on': base_claim,
            'category': 'method',
            'text': f"{claim_number}. The method of claim {base_claim}, wherein the algorithmic process is executed iteratively until a convergence criterion is satisfied.",
            'elements': ['iterative execution', 'convergence criterion']
        })
        claim_number += 1
    
    if 'custom_data_structure' in indicators:
        claims.append({
            'number': claim_number,
            'type': 'dependent',
            'depends_on': base_claim,
            'category': 'method',
            'text': f"{claim_number}. The method of claim {base_claim}, wherein the structured format comprises a tree-based index for logarithmic-time access.",
            'elements': ['tree-based index', 'logarithmic-time access']
        })
        claim_number += 1
    
    return claims


def generate_system_claims(invention, source, indicators):
    """Generate additional system-specific claims."""
    claims = []
    claim_number = 10  # Start at claim 10 for system variations
    
    claims.append({
        'number': claim_number,
        'type': 'dependent',
        'depends_on': 2,  # System independent claim
        'category': 'system',
        'text': f"{claim_number}. The system of claim 2, wherein the one or more processors comprise a graphics processing unit (GPU) configured for parallel processing.",
        'elements': ['GPU', 'parallel processing']
    })
    claim_number += 1
    
    claims.append({
        'number': claim_number,
        'type': 'dependent',
        'depends_on': 2,
        'category': 'system',
        'text': f"{claim_number}. The system of claim 2, further comprising a network interface for receiving the input data from a remote source.",
        'elements': ['network interface', 'remote data']
    })
    
    return claims


def extract_claim_elements(claim_text):
    """Extract key claim elements for analysis."""
    elements = []
    lines = claim_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and not line.endswith(':'):
            # Extract key phrases
            if 'comprising' in line.lower():
                elements.append('comprising')
            if 'receiving' in line.lower():
                elements.append('receiving step')
            if 'processing' in line.lower():
                elements.append('processing step')
            if 'generating' in line.lower():
                elements.append('generating step')
    
    return list(set(elements))


def save_claims(all_claims):
    """Save generated claims to file."""
    os.makedirs('output/ip_disclosures', exist_ok=True)
    
    output = {
        'generated_at': datetime.utcnow().isoformat(),
        'total_claim_sets': len(all_claims),
        'disclaimer': 'DRAFT CLAIMS - REQUIRES ATTORNEY REVIEW AND REFINEMENT',
        'claim_sets': all_claims
    }
    
    with open('output/ip_disclosures/preliminary_claims.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    return output


def main():
    print("=" * 60)
    print("Generating Preliminary Patent Claims")
    print("=" * 60)
    
    # Load disclosures
    print("\n🔍 Loading invention disclosures...")
    disclosures = load_disclosures()
    
    if not disclosures:
        print("ℹ️  No disclosures found. Run generate_disclosures.py first.")
        return 0
    
    print(f"   Found {len(disclosures)} disclosure(s)")
    
    # Load novelty analysis for context
    novelty = load_novelty_analysis()
    
    # Generate claims
    print("\n📝 Generating patent claims...")
    all_claims = []
    
    for disclosure in disclosures:
        disclosure_id = disclosure.get('disclosure_id', 'unknown')
        title = disclosure.get('invention', {}).get('title', 'Untitled')
        print(f"\n   Processing: {disclosure_id}")
        print(f"   Title: {title[:50]}...")
        
        claims = generate_claims_for_disclosure(disclosure, novelty)
        all_claims.append(claims)
        
        claim_count = len(claims['claims'])
        print(f"   Generated: {claim_count} claims")
        print(f"   Strategy: {claims['claim_strategy']['type']}")
    
    # Save claims
    print("\n💾 Saving preliminary claims...")
    output = save_claims(all_claims)
    
    # Print summary
    total_claims = sum(len(cs['claims']) for cs in all_claims)
    print(f"\n✅ Claims Generation Complete!")
    print(f"   Claim sets generated: {output['total_claim_sets']}")
    print(f"   Total claims: {total_claims}")
    print(f"\n📁 Output saved to: output/ip_disclosures/preliminary_claims.json")
    print(f"\n⚠️  IMPORTANT: These are DRAFT claims.")
    print(f"   Attorney review and refinement is REQUIRED before filing.")
    print(f"   Claims should be tailored to specific prior art findings.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
