#!/usr/bin/env python3
"""
Generate invention disclosure forms from novelty analysis.

This script takes the novelty analysis results and generates
structured invention disclosure forms for attorney review.
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path


def load_novelty_analysis():
    """Load novelty analysis results."""
    analysis_path = 'output/ip_disclosures/novelty_analysis.json'
    if os.path.exists(analysis_path):
        with open(analysis_path, 'r') as f:
            return json.load(f)
    return None


def load_existing_disclosures():
    """Load existing disclosures from extract_ip_disclosures.py output."""
    summary_path = 'output/ip_disclosures/summary.json'
    if os.path.exists(summary_path):
        with open(summary_path, 'r') as f:
            return json.load(f)
    return {'disclosures': []}


def get_inventor_info():
    """Get inventor information from git config."""
    try:
        name_result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True, text=True, timeout=5
        )
        email_result = subprocess.run(
            ['git', 'config', 'user.email'],
            capture_output=True, text=True, timeout=5
        )
        return {
            'name': name_result.stdout.strip() or 'Unknown',
            'email': email_result.stdout.strip() or 'unknown@example.com'
        }
    except Exception:
        return {'name': 'Unknown', 'email': 'unknown@example.com'}


def generate_disclosure_from_finding(finding, inventor_info, disclosure_id):
    """Generate a disclosure document from a novelty finding."""
    disclosure = {
        'disclosure_id': disclosure_id,
        'created_at': datetime.utcnow().isoformat(),
        'status': 'draft',
        'requires_review': True,
        
        'inventor': {
            'primary': inventor_info,
            'co_inventors': [],
            'contribution_date': datetime.utcnow().strftime('%Y-%m-%d')
        },
        
        'invention': {
            'title': generate_title(finding),
            'abstract': generate_abstract(finding),
            'technical_field': determine_technical_field(finding),
            'background': generate_background(finding),
            'detailed_description': generate_description(finding),
            'advantages': generate_advantages(finding),
            'claims_preview': generate_claims_preview(finding)
        },
        
        'prior_art': {
            'known_solutions': [],
            'differences': 'To be determined through prior art search',
            'search_status': 'pending'
        },
        
        'commercial_potential': {
            'target_market': determine_market(finding),
            'potential_applications': determine_applications(finding),
            'competitive_advantage': 'Novel implementation approach',
            'licensing_potential': 'To be evaluated'
        },
        
        'source_reference': {
            'file': finding.get('file', 'unknown'),
            'type': finding.get('type', 'unknown'),
            'name': finding.get('name', 'unknown'),
            'line': finding.get('line', 0),
            'indicators': finding.get('indicators', [])
        },
        
        'workflow': {
            'current_stage': 'disclosure_draft',
            'stages': [
                {'name': 'disclosure_draft', 'status': 'current', 'date': datetime.utcnow().isoformat()},
                {'name': 'attorney_review', 'status': 'pending', 'date': None},
                {'name': 'prior_art_search', 'status': 'pending', 'date': None},
                {'name': 'patent_decision', 'status': 'pending', 'date': None},
                {'name': 'patent_filing', 'status': 'pending', 'date': None}
            ],
            'next_action': 'Submit for attorney review'
        }
    }
    
    return disclosure


def generate_title(finding):
    """Generate a descriptive title for the invention."""
    name = finding.get('name', 'Innovation')
    indicators = finding.get('indicators', [])
    
    # Create title based on indicators
    if 'ml_component' in indicators:
        return f"Machine Learning System: {name}"
    elif 'custom_data_structure' in indicators:
        return f"Optimized Data Structure: {name}"
    elif 'algorithm_implementation' in indicators:
        return f"Algorithm for {name.replace('_', ' ').title()}"
    elif 'performance_optimization' in indicators:
        return f"Performance-Optimized {name.replace('_', ' ').title()}"
    elif 'system_optimization' in indicators:
        return f"System Optimization Component: {name}"
    else:
        return f"Software Innovation: {name}"


def generate_abstract(finding):
    """Generate an abstract for the invention."""
    docstring = finding.get('docstring', '')
    name = finding.get('name', 'component')
    indicators = finding.get('indicators', [])
    
    if docstring:
        return docstring[:500]
    
    indicator_descs = {
        'ml_component': 'machine learning',
        'custom_data_structure': 'data organization',
        'algorithm_implementation': 'algorithmic processing',
        'performance_optimization': 'performance enhancement',
        'system_optimization': 'system resource management',
        'documented_innovation': 'novel computation',
        'high_complexity_logic': 'complex decision logic'
    }
    
    areas = [indicator_descs.get(i, i) for i in indicators[:3]]
    areas_str = ', '.join(areas) if areas else 'software engineering'
    
    return (f"A novel software implementation ({name}) providing improvements in "
            f"{areas_str}. This implementation offers enhanced capabilities "
            f"through innovative design patterns and optimized processing logic.")


def generate_background(finding):
    """Generate background section."""
    return ("Current solutions in this technical area may suffer from limitations "
            "in performance, scalability, or flexibility. The present invention "
            "addresses these limitations through a novel implementation approach.")


def generate_description(finding):
    """Generate detailed description."""
    name = finding.get('name', 'component')
    ftype = finding.get('type', 'component')
    indicators = finding.get('indicators', [])
    
    desc = f"The {ftype} '{name}' implements the following novel features:\n\n"
    
    for indicator in indicators:
        if indicator == 'ml_component':
            desc += "- Machine learning component with optimized architecture\n"
        elif indicator == 'custom_data_structure':
            desc += "- Custom data structure for efficient data organization\n"
        elif indicator == 'algorithm_implementation':
            desc += "- Novel algorithmic approach for improved processing\n"
        elif indicator == 'performance_optimization':
            desc += "- Performance optimizations for enhanced throughput\n"
        elif indicator == 'system_optimization':
            desc += "- System-level optimizations for resource efficiency\n"
        elif indicator == 'design_pattern_implementation':
            desc += "- Design pattern implementation for maintainability\n"
        elif indicator == 'high_complexity_logic':
            desc += "- Complex decision logic for sophisticated handling\n"
    
    return desc


def generate_advantages(finding):
    """Generate list of advantages."""
    indicators = finding.get('indicators', [])
    advantages = ['Improved processing efficiency']
    
    if 'ml_component' in indicators:
        advantages.append('Enhanced predictive capabilities')
    if 'performance_optimization' in indicators:
        advantages.append('Reduced latency and improved throughput')
    if 'custom_data_structure' in indicators:
        advantages.append('Optimized memory usage and access patterns')
    if 'system_optimization' in indicators:
        advantages.append('Better resource utilization')
    
    advantages.append('Maintainable and extensible architecture')
    return advantages


def generate_claims_preview(finding):
    """Generate preliminary claims preview."""
    name = finding.get('name', 'component')
    ftype = finding.get('type', 'method')
    
    return [
        f"A computer-implemented {ftype} comprising the steps of: [to be detailed]",
        f"The {ftype} of claim 1, wherein: [specific features to be added]",
        f"A system configured to perform the {ftype} of claim 1"
    ]


def determine_technical_field(finding):
    """Determine the technical field based on indicators."""
    indicators = finding.get('indicators', [])
    
    if 'ml_component' in indicators:
        return "Artificial Intelligence and Machine Learning"
    elif 'custom_data_structure' in indicators:
        return "Data Structures and Algorithms"
    elif 'performance_optimization' in indicators:
        return "High-Performance Computing"
    elif 'system_optimization' in indicators:
        return "Distributed Systems and Resource Management"
    else:
        return "Software Engineering"


def determine_market(finding):
    """Determine target market based on indicators."""
    indicators = finding.get('indicators', [])
    
    if 'ml_component' in indicators:
        return "AI/ML Software, Enterprise Analytics"
    elif 'performance_optimization' in indicators:
        return "Cloud Computing, High-Performance Applications"
    else:
        return "Enterprise Software, SaaS Applications"


def determine_applications(finding):
    """Determine potential applications."""
    indicators = finding.get('indicators', [])
    applications = ['Enterprise software systems']
    
    if 'ml_component' in indicators:
        applications.extend(['Predictive analytics', 'Automated decision systems'])
    if 'performance_optimization' in indicators:
        applications.extend(['Real-time processing', 'High-throughput systems'])
    if 'custom_data_structure' in indicators:
        applications.extend(['Data indexing', 'Search engines'])
    
    return applications


def save_disclosures(disclosures):
    """Save generated disclosures to files."""
    os.makedirs('output/ip_disclosures', exist_ok=True)
    
    for disclosure in disclosures:
        filename = f"output/ip_disclosures/disclosure_{disclosure['disclosure_id']}.json"
        with open(filename, 'w') as f:
            json.dump(disclosure, f, indent=2)
    
    # Update summary
    summary = {
        'generated_at': datetime.utcnow().isoformat(),
        'total_disclosures': len(disclosures),
        'disclosures': [
            {
                'id': d['disclosure_id'],
                'title': d['invention']['title'],
                'status': d['status'],
                'technical_field': d['invention']['technical_field']
            }
            for d in disclosures
        ]
    }
    
    with open('output/ip_disclosures/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary


def main():
    print("=" * 60)
    print("Generating Invention Disclosure Forms")
    print("=" * 60)
    
    # Load novelty analysis
    print("\n🔍 Loading novelty analysis...")
    analysis = load_novelty_analysis()
    
    if not analysis:
        print("⚠️  No novelty analysis found. Run analyze_novelty.py first.")
        return 0
    
    # Get inventor info
    print("👤 Getting inventor information...")
    inventor_info = get_inventor_info()
    print(f"   Inventor: {inventor_info['name']}")
    
    # Load existing disclosures
    existing = load_existing_disclosures()
    existing_count = len(existing.get('disclosures', []))
    
    # Generate disclosures for high-value findings
    print("\n📝 Generating disclosure forms...")
    disclosures = []
    disclosure_counter = existing_count + 1
    
    for file_result in analysis.get('file_results', []):
        for finding in file_result.get('findings', []):
            # Only create disclosures for findings with strong indicators
            if len(finding.get('indicators', [])) >= 2:
                disclosure_id = f"ID-{datetime.utcnow().strftime('%Y%m%d')}-{disclosure_counter:04d}"
                disclosure = generate_disclosure_from_finding(
                    finding, inventor_info, disclosure_id
                )
                disclosures.append(disclosure)
                disclosure_counter += 1
                print(f"   Generated: {disclosure['invention']['title']}")
    
    if not disclosures:
        print("ℹ️  No significant novelty findings to generate disclosures for.")
        return 0
    
    # Save disclosures
    print("\n💾 Saving disclosure forms...")
    summary = save_disclosures(disclosures)
    
    # Print summary
    print(f"\n✅ Disclosure Generation Complete!")
    print(f"   Disclosures generated: {summary['total_disclosures']}")
    for disc in summary['disclosures']:
        print(f"      - {disc['id']}: {disc['title']}")
    print(f"\n📁 Output saved to: output/ip_disclosures/")
    print(f"\n⚠️  IMPORTANT: All disclosures require attorney review before filing!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
