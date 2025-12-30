#!/usr/bin/env python3
"""
Calculate strategic moat metrics from compliance and IP data.

This script analyzes all output artifacts to calculate real
moat strength metrics and trends.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def load_compliance_data():
    """Load compliance-related data."""
    data = {
        'controls_mapped': {'soc2': 0, 'iso27001': 0},
        'audit_evidence': 0,
        'timeline_events': 0
    }
    
    # Load transformed compliance data
    summary_path = 'output/compliance/transformed/summary.json'
    if os.path.exists(summary_path):
        with open(summary_path, 'r') as f:
            summary = json.load(f)
            data['controls_mapped'] = summary.get('controls_mapped', data['controls_mapped'])
            data['audit_evidence'] = summary.get('evidence_packages', 0)
            data['timeline_events'] = summary.get('timeline_events', 0)
    
    return data


def load_ip_data():
    """Load IP disclosure data."""
    data = {
        'disclosures': [],
        'novelty_score': 0,
        'claims_generated': 0
    }
    
    # Load disclosure summary
    summary_path = 'output/ip_disclosures/summary.json'
    if os.path.exists(summary_path):
        with open(summary_path, 'r') as f:
            summary = json.load(f)
            data['disclosures'] = summary.get('disclosures', [])
    
    # Load novelty analysis
    novelty_path = 'output/ip_disclosures/novelty_analysis.json'
    if os.path.exists(novelty_path):
        with open(novelty_path, 'r') as f:
            novelty = json.load(f)
            data['novelty_score'] = novelty.get('novelty_score', {}).get('score', 0)
    
    # Load claims
    claims_path = 'output/ip_disclosures/preliminary_claims.json'
    if os.path.exists(claims_path):
        with open(claims_path, 'r') as f:
            claims = json.load(f)
            for claim_set in claims.get('claim_sets', []):
                data['claims_generated'] += len(claim_set.get('claims', []))
    
    return data


def load_test_report():
    """Load test report if available."""
    for path in ['test_report.json', 'artifacts/test_report.json', 'output/test_report.json']:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    return None


def calculate_compliance_score(compliance_data):
    """Calculate compliance score (0-100)."""
    # Base scores for each framework
    soc2_controls = compliance_data['controls_mapped'].get('soc2', 0)
    iso_controls = compliance_data['controls_mapped'].get('iso27001', 0)
    
    # Assume targets
    soc2_target = 20
    iso_target = 40
    
    soc2_score = min(100, (soc2_controls / soc2_target) * 100) if soc2_target > 0 else 0
    iso_score = min(100, (iso_controls / iso_target) * 100) if iso_target > 0 else 0
    
    # Weight: SOC2 = 50%, ISO = 50%
    combined_score = (soc2_score * 0.5) + (iso_score * 0.5)
    
    # Bonus for audit evidence
    if compliance_data['audit_evidence'] > 0:
        combined_score = min(100, combined_score + 5)
    
    return round(combined_score)


def calculate_ip_score(ip_data):
    """Calculate IP portfolio score (0-100)."""
    disclosure_count = len(ip_data['disclosures'])
    novelty_score = ip_data['novelty_score']
    claims_count = ip_data['claims_generated']
    
    # Score based on portfolio depth
    # Each disclosure is worth up to 15 points (diminishing returns)
    disclosure_score = min(60, disclosure_count * 15)
    
    # Novelty contributes up to 20 points
    novelty_contribution = min(20, novelty_score * 0.2)
    
    # Claims contribute up to 20 points
    claims_contribution = min(20, claims_count * 2)
    
    total = disclosure_score + novelty_contribution + claims_contribution
    return round(min(100, total))


def calculate_automation_coverage():
    """Calculate automation coverage score (0-100)."""
    # Check which automation scripts are fully implemented
    scripts = {
        'scripts/compliance/analyze_validation_data.py': True,
        'scripts/compliance/transform_to_compliance.py': True,
        'scripts/compliance/generate_soc2_docs.py': True,
        'scripts/compliance/generate_iso27001_docs.py': True,
        'scripts/compliance/generate_audit_trail.py': True,
        'scripts/compliance/sign_documents.py': True,
        'scripts/ip_automation/extract_ip_disclosures.py': True,
        'scripts/ip_automation/analyze_novelty.py': True,
        'scripts/ip_automation/generate_disclosures.py': True,
        'scripts/ip_automation/search_prior_art.py': True,
        'scripts/ip_automation/generate_claims.py': True,
        'scripts/moat/calculate_metrics.py': True,
        'scripts/moat/generate_dashboard.py': True,
        'scripts/moat/update_readme.py': True,
    }
    
    # Check existence and non-stub status
    implemented = 0
    for script, expected in scripts.items():
        if os.path.exists(script):
            with open(script, 'r') as f:
                content = f.read()
                # Consider implemented if more than 500 chars (not a stub)
                if len(content) > 500:
                    implemented += 1
    
    coverage = (implemented / len(scripts)) * 100
    return round(coverage)


def calculate_moat_strength(compliance_score, ip_score, automation_score):
    """Calculate overall moat strength."""
    # Weighted formula
    # Compliance: 30% (table stakes)
    # IP: 40% (differentiator)
    # Automation: 30% (efficiency)
    
    weighted_score = (
        compliance_score * 0.30 +
        ip_score * 0.40 +
        automation_score * 0.30
    )
    
    # Determine level
    if weighted_score >= 91:
        level = 'dominant'
    elif weighted_score >= 71:
        level = 'strong'
    elif weighted_score >= 41:
        level = 'moderate'
    else:
        level = 'developing'
    
    return {
        'score': round(weighted_score),
        'level': level
    }


def load_historical_metrics():
    """Load historical metrics if available."""
    history_path = 'output/moat/metrics_history.json'
    if os.path.exists(history_path):
        with open(history_path, 'r') as f:
            return json.load(f)
    return {'entries': []}


def save_metrics(metrics, history):
    """Save metrics and update history."""
    os.makedirs('output/moat', exist_ok=True)
    
    # Save current metrics
    with open('output/moat/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Update history
    history['entries'].append({
        'date': metrics['calculated_at'],
        'compliance_score': metrics['compliance_score'],
        'ip_portfolio_count': metrics['ip_portfolio_count'],
        'automation_coverage': metrics['automation_coverage'],
        'moat_strength': metrics['moat_strength']['score']
    })
    
    # Keep last 100 entries
    history['entries'] = history['entries'][-100:]
    
    with open('output/moat/metrics_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    return metrics


def main():
    print("=" * 60)
    print("Calculating Strategic Moat Metrics")
    print("=" * 60)
    
    # Load data
    print("\n🔍 Loading data sources...")
    compliance_data = load_compliance_data()
    ip_data = load_ip_data()
    test_report = load_test_report()
    history = load_historical_metrics()
    
    print(f"   Compliance controls: SOC2={compliance_data['controls_mapped']['soc2']}, ISO={compliance_data['controls_mapped']['iso27001']}")
    print(f"   IP disclosures: {len(ip_data['disclosures'])}")
    print(f"   Test report: {'Found' if test_report else 'Not found'}")
    
    # Calculate scores
    print("\n📊 Calculating metrics...")
    compliance_score = calculate_compliance_score(compliance_data)
    ip_score = calculate_ip_score(ip_data)
    automation_score = calculate_automation_coverage()
    moat_strength = calculate_moat_strength(compliance_score, ip_score, automation_score)
    
    # Build metrics object
    metrics = {
        'calculated_at': datetime.utcnow().isoformat(),
        'compliance_score': compliance_score,
        'ip_portfolio_count': len(ip_data['disclosures']),
        'ip_portfolio_score': ip_score,
        'automation_coverage': automation_score,
        'moat_strength': moat_strength,
        'details': {
            'compliance': {
                'soc2_controls': compliance_data['controls_mapped']['soc2'],
                'iso27001_controls': compliance_data['controls_mapped']['iso27001'],
                'audit_evidence': compliance_data['audit_evidence']
            },
            'ip': {
                'disclosures': len(ip_data['disclosures']),
                'novelty_score': ip_data['novelty_score'],
                'claims_generated': ip_data['claims_generated']
            },
            'testing': {
                'total_tests': test_report.get('total_tests', 0) if test_report else 0,
                'pass_rate': test_report.get('pass_rate', 0) if test_report else 0
            }
        },
        'trend': {
            'entries': len(history['entries']),
            'previous_moat_score': history['entries'][-1]['moat_strength'] if history['entries'] else None
        }
    }
    
    # Save metrics
    print("\n💾 Saving metrics...")
    save_metrics(metrics, history)
    
    # Print summary
    print(f"\n✅ Metrics Calculation Complete!")
    print(f"\n   📋 Compliance Score:    {compliance_score}%")
    print(f"   💡 IP Portfolio Count:  {len(ip_data['disclosures'])}")
    print(f"   ⚙️  Automation Coverage: {automation_score}%")
    print(f"   🏰 Moat Strength:       {moat_strength['score']} ({moat_strength['level'].upper()})")
    
    if metrics['trend']['previous_moat_score']:
        delta = moat_strength['score'] - metrics['trend']['previous_moat_score']
        trend_icon = '📈' if delta > 0 else ('📉' if delta < 0 else '➡️')
        print(f"   {trend_icon} Trend:              {'+' if delta >= 0 else ''}{delta} points")
    
    print(f"\n📁 Metrics saved to: output/moat/metrics.json")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
