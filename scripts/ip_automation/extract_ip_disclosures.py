#!/usr/bin/env python3
"""
Extract IP disclosures from code changes and test results.

This script analyzes code for novel implementations that may be patentable
and generates invention disclosure forms.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import re


def analyze_code_changes():
    """Analyze code changes for novel implementations."""
    try:
        # Get diff of last commit
        result = subprocess.run(
            ['git', 'diff', 'HEAD~1', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=30
        )
        diff_content = result.stdout
        
        # Get commit info
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=format:%H|%an|%ae|%at|%s|%b'],
            capture_output=True,
            text=True,
            timeout=10
        )
        commit_info = result.stdout.strip().split('|')
        
        return {
            'diff': diff_content,
            'commit_hash': commit_info[0] if len(commit_info) > 0 else '',
            'author_name': commit_info[1] if len(commit_info) > 1 else '',
            'author_email': commit_info[2] if len(commit_info) > 2 else '',
            'timestamp': commit_info[3] if len(commit_info) > 3 else '',
            'subject': commit_info[4] if len(commit_info) > 4 else '',
            'body': commit_info[5] if len(commit_info) > 5 else ''
        }
    except Exception as e:
        print(f"Warning: Could not analyze code changes: {e}")
        return {}


def detect_novel_patterns(code_changes):
    """Detect patterns that indicate novel implementations."""
    novelty_indicators = []
    diff = code_changes.get('diff', '')
    
    # Pattern 1: New algorithms
    algorithm_patterns = [
        r'def\s+(\w*algorithm\w*)',
        r'class\s+(\w*Algorithm\w*)',
        r'#.*novel.*algorithm',
        r'#.*new.*approach'
    ]
    
    for pattern in algorithm_patterns:
        matches = re.findall(pattern, diff, re.IGNORECASE)
        if matches:
            novelty_indicators.append({
                'type': 'algorithm',
                'pattern': pattern,
                'matches': matches[:5]  # Limit to 5 matches
            })
    
    # Pattern 2: Optimization techniques
    optimization_patterns = [
        r'#.*optimization',
        r'#.*performance.*improvement',
        r'def\s+(\w*optimize\w*)',
        r'#.*faster.*than'
    ]
    
    for pattern in optimization_patterns:
        matches = re.findall(pattern, diff, re.IGNORECASE)
        if matches:
            novelty_indicators.append({
                'type': 'optimization',
                'pattern': pattern,
                'matches': matches[:5]
            })
    
    # Pattern 3: Novel data structures
    datastructure_patterns = [
        r'class\s+(\w*Tree\w*)',
        r'class\s+(\w*Graph\w*)',
        r'class\s+(\w*Cache\w*)',
        r'#.*custom.*data.*structure'
    ]
    
    for pattern in datastructure_patterns:
        matches = re.findall(pattern, diff, re.IGNORECASE)
        if matches:
            novelty_indicators.append({
                'type': 'data_structure',
                'pattern': pattern,
                'matches': matches[:5]
            })
    
    # Pattern 4: Machine learning innovations
    ml_patterns = [
        r'#.*novel.*model',
        r'#.*new.*architecture',
        r'class\s+(\w*Model\w*)',
        r'def\s+(\w*train\w*)',
        r'#.*breakthrough'
    ]
    
    for pattern in ml_patterns:
        matches = re.findall(pattern, diff, re.IGNORECASE)
        if matches:
            novelty_indicators.append({
                'type': 'ml_innovation',
                'pattern': pattern,
                'matches': matches[:5]
            })
    
    return novelty_indicators


def extract_technical_description(code_changes, novelty_indicators):
    """Extract technical description for invention disclosure."""
    description = {
        'title': code_changes.get('subject', 'Untitled Innovation'),
        'summary': code_changes.get('body', ''),
        'technical_field': 'Software Engineering',
        'background': 'Improvements to software systems and methods',
        'novel_aspects': []
    }
    
    # Extract novel aspects from indicators
    for indicator in novelty_indicators:
        aspect = {
            'type': indicator['type'],
            'description': f"Novel {indicator['type']} implementation",
            'evidence': indicator.get('matches', [])
        }
        description['novel_aspects'].append(aspect)
    
    return description


def generate_invention_disclosure(code_changes, novelty_indicators, technical_desc):
    """Generate invention disclosure form."""
    disclosure = {
        'disclosure_id': f"ID-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        'created_at': datetime.utcnow().isoformat(),
        'status': 'draft',
        'inventor': {
            'name': code_changes.get('author_name', 'Unknown'),
            'email': code_changes.get('author_email', ''),
            'contribution': 'Primary inventor'
        },
        'invention': {
            'title': technical_desc['title'],
            'summary': technical_desc['summary'],
            'technical_field': technical_desc['technical_field'],
            'background': technical_desc['background'],
            'description': technical_desc['novel_aspects'],
            'advantages': [
                'Improved performance',
                'Enhanced reliability',
                'Better scalability'
            ]
        },
        'prior_art': {
            'known_solutions': [],
            'differences': 'Novel approach not found in prior art',
            'search_needed': True
        },
        'commercial_potential': {
            'market': 'Enterprise software',
            'applications': ['Cloud computing', 'Data processing', 'AI/ML systems'],
            'competitive_advantage': 'Unique implementation approach'
        },
        'source_code': {
            'commit_hash': code_changes.get('commit_hash', ''),
            'repository': os.getenv('GITHUB_REPOSITORY', 'unknown'),
            'files_changed': len(novelty_indicators)
        },
        'next_steps': [
            'Attorney review required',
            'Prior art search needed',
            'Determine filing strategy'
        ]
    }
    
    return disclosure


def save_ip_disclosures(disclosures):
    """Save IP disclosure documents."""
    os.makedirs('output/ip_disclosures', exist_ok=True)
    
    for i, disclosure in enumerate(disclosures):
        filename = f"output/ip_disclosures/disclosure_{disclosure['disclosure_id']}.json"
        with open(filename, 'w') as f:
            json.dump(disclosure, f, indent=2)
    
    # Create summary
    summary = {
        'generated_at': datetime.utcnow().isoformat(),
        'total_disclosures': len(disclosures),
        'disclosures': [
            {
                'id': d['disclosure_id'],
                'title': d['invention']['title'],
                'inventor': d['inventor']['name'],
                'status': d['status']
            }
            for d in disclosures
        ]
    }
    
    with open('output/ip_disclosures/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary


def main():
    print("=" * 60)
    print("Extracting IP Disclosures")
    print("=" * 60)
    
    # Analyze code changes
    print("\n🔍 Analyzing code changes...")
    code_changes = analyze_code_changes()
    
    if not code_changes.get('diff'):
        print("⚠️  No code changes detected. Skipping IP extraction.")
        # Create empty summary
        os.makedirs('output/ip_disclosures', exist_ok=True)
        with open('output/ip_disclosures/summary.json', 'w') as f:
            json.dump({'total_disclosures': 0, 'disclosures': []}, f)
        return 0
    
    # Detect novel patterns
    print("🧠 Detecting novel patterns...")
    novelty_indicators = detect_novel_patterns(code_changes)
    
    if not novelty_indicators:
        print("ℹ️  No novel patterns detected. No IP disclosures generated.")
        os.makedirs('output/ip_disclosures', exist_ok=True)
        with open('output/ip_disclosures/summary.json', 'w') as f:
            json.dump({'total_disclosures': 0, 'disclosures': []}, f)
        return 0
    
    print(f"  Found {len(novelty_indicators)} novelty indicators")
    
    # Extract technical description
    print("📝 Extracting technical description...")
    technical_desc = extract_technical_description(code_changes, novelty_indicators)
    
    # Generate disclosure
    print("📦 Generating invention disclosure...")
    disclosure = generate_invention_disclosure(code_changes, novelty_indicators, technical_desc)
    
    # Save disclosures
    print("💾 Saving IP disclosures...")
    summary = save_ip_disclosures([disclosure])
    
    # Print summary
    print(f"\n✅ IP extraction complete!")
    print(f"  Disclosures generated: {summary['total_disclosures']}")
    for disc in summary['disclosures']:
        print(f"    - {disc['id']}: {disc['title']}")
    print(f"\n📁 Output saved to: output/ip_disclosures/")
    print(f"\n⚠️  IMPORTANT: Attorney review required before filing!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
