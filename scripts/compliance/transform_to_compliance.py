#!/usr/bin/env python3
"""
Transform validation data into compliance-ready format.

This script takes test results and converts them into structured data
that can be used for compliance documentation (SOC2, ISO 27001, etc.).
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import hashlib


def load_validation_analysis():
    """Load the validation analysis results."""
    analysis_path = 'output/analysis/validation_analysis.json'
    if os.path.exists(analysis_path):
        with open(analysis_path, 'r') as f:
            return json.load(f)
    return None


def load_test_report():
    """Load test report."""
    possible_paths = [
        'test_report.json',
        'artifacts/test_report.json',
        'output/test_report.json'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    return {}


def map_tests_to_controls(test_report):
    """Map test results to compliance controls."""
    # SOC2 Trust Service Criteria mapping
    soc2_mapping = {
        'security': 'CC6.1',  # Logical and Physical Access Controls
        'availability': 'A1.1',  # Availability commitments
        'integrity': 'PI1.1',  # Processing Integrity
        'confidentiality': 'C1.1',  # Confidentiality commitments
        'privacy': 'P1.1'  # Privacy commitments
    }
    
    # ISO 27001 control mapping
    iso27001_mapping = {
        'access_control': 'A.9',
        'cryptography': 'A.10',
        'operations_security': 'A.12',
        'communications_security': 'A.13',
        'system_acquisition': 'A.14'
    }
    
    controls = {
        'soc2': [],
        'iso27001': [],
        'custom': []
    }
    
    # Map test results to controls
    total_tests = test_report.get('total_tests', 0)
    passed_tests = test_report.get('passed', 0)
    
    if total_tests > 0:
        controls['soc2'].append({
            'control_id': 'CC6.1',
            'control_name': 'Logical and Physical Access Controls',
            'evidence': f'{passed_tests}/{total_tests} validation tests passed',
            'status': 'pass' if passed_tests == total_tests else 'partial',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        controls['iso27001'].append({
            'control_id': 'A.12.1.2',
            'control_name': 'Change Management',
            'evidence': f'Automated testing validates all changes',
            'status': 'implemented',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return controls


def create_audit_evidence(test_report, controls):
    """Create audit evidence package."""
    evidence = {
        'evidence_id': hashlib.sha256(
            f"{datetime.utcnow().isoformat()}{json.dumps(test_report)}".encode()
        ).hexdigest()[:16],
        'created_at': datetime.utcnow().isoformat(),
        'evidence_type': 'automated_testing',
        'description': 'Empirical validation test results',
        'test_summary': {
            'total_tests': test_report.get('total_tests', 0),
            'passed': test_report.get('passed', 0),
            'failed': test_report.get('failed', 0),
            'pass_rate': test_report.get('pass_rate', 0.0)
        },
        'controls_addressed': {
            'soc2': [c['control_id'] for c in controls.get('soc2', [])],
            'iso27001': [c['control_id'] for c in controls.get('iso27001', [])]
        },
        'attestation': {
            'automated': True,
            'human_reviewed': False,
            'reviewer': None,
            'review_date': None
        }
    }
    
    return evidence


def create_compliance_timeline(test_report):
    """Create timeline of compliance-relevant events."""
    timeline = {
        'period_start': datetime.utcnow().replace(day=1).isoformat(),
        'period_end': datetime.utcnow().isoformat(),
        'events': [
            {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': 'validation_test',
                'description': 'Automated validation tests executed',
                'result': 'pass' if test_report.get('failed', 0) == 0 else 'partial',
                'details': test_report
            }
        ]
    }
    
    return timeline


def save_compliance_data(controls, evidence, timeline):
    """Save transformed compliance data."""
    os.makedirs('output/compliance/transformed', exist_ok=True)
    
    # Save controls mapping
    with open('output/compliance/transformed/controls_mapping.json', 'w') as f:
        json.dump(controls, f, indent=2)
    
    # Save audit evidence
    with open('output/compliance/transformed/audit_evidence.json', 'w') as f:
        json.dump(evidence, f, indent=2)
    
    # Save timeline
    with open('output/compliance/transformed/compliance_timeline.json', 'w') as f:
        json.dump(timeline, f, indent=2)
    
    # Create summary
    summary = {
        'transformation_date': datetime.utcnow().isoformat(),
        'controls_mapped': {
            'soc2': len(controls.get('soc2', [])),
            'iso27001': len(controls.get('iso27001', []))
        },
        'evidence_packages': 1,
        'timeline_events': len(timeline.get('events', []))
    }
    
    with open('output/compliance/transformed/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary


def main():
    print("=" * 60)
    print("Transforming Validation Data to Compliance Format")
    print("=" * 60)
    
    # Load data
    analysis = load_validation_analysis()
    test_report = load_test_report()
    
    if not analysis:
        print("⚠️  No validation analysis found. Running with test report only.")
    
    # Transform data
    print("\n📋 Mapping tests to compliance controls...")
    controls = map_tests_to_controls(test_report)
    
    print("📦 Creating audit evidence package...")
    evidence = create_audit_evidence(test_report, controls)
    
    print("📅 Creating compliance timeline...")
    timeline = create_compliance_timeline(test_report)
    
    # Save results
    print("💾 Saving transformed data...")
    summary = save_compliance_data(controls, evidence, timeline)
    
    # Print summary
    print(f"\n✅ Transformation complete!")
    print(f"  SOC2 controls mapped: {summary['controls_mapped']['soc2']}")
    print(f"  ISO 27001 controls mapped: {summary['controls_mapped']['iso27001']}")
    print(f"  Evidence packages created: {summary['evidence_packages']}")
    print(f"  Timeline events: {summary['timeline_events']}")
    print(f"\n📁 Output saved to: output/compliance/transformed/")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
