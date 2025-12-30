#!/usr/bin/env python3
"""
Analyze validation data to determine if compliance documentation or IP disclosures are needed.

This script examines test results and code changes to identify:
1. Security-relevant changes requiring compliance updates
2. Novel implementations requiring IP disclosure
3. Data quality issues requiring attention
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess


def load_test_report():
    """Load test report from various possible locations."""
    possible_paths = [
        'test_report.json',
        'artifacts/test_report.json',
        'output/test_report.json'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    
    print("Warning: No test report found, generating sample data")
    return {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'pass_rate': 0.0
    }


def analyze_git_changes():
    """Analyze recent git changes for security and novelty indicators."""
    try:
        # Get changed files in last commit
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=10
        )
        changed_files = result.stdout.strip().split('\n') if result.stdout else []
        
        # Get commit message
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            capture_output=True,
            text=True,
            timeout=10
        )
        commit_message = result.stdout.strip()
        
        return {
            'changed_files': changed_files,
            'commit_message': commit_message,
            'file_count': len([f for f in changed_files if f])
        }
    except Exception as e:
        print(f"Warning: Could not analyze git changes: {e}")
        return {
            'changed_files': [],
            'commit_message': '',
            'file_count': 0
        }


def check_compliance_triggers(test_report, git_changes):
    """Determine if compliance documentation is needed."""
    triggers = []
    
    # Trigger 1: Test failures (potential security issues)
    if test_report.get('failed', 0) > 0:
        triggers.append('test_failures')
    
    # Trigger 2: Security-related file changes
    security_keywords = ['auth', 'security', 'crypto', 'password', 'token', 'key']
    for file in git_changes.get('changed_files', []):
        if any(keyword in file.lower() for keyword in security_keywords):
            triggers.append('security_file_change')
            break
    
    # Trigger 3: Compliance-related keywords in commit
    compliance_keywords = ['gdpr', 'hipaa', 'soc2', 'iso27001', 'compliance', 'audit']
    commit_msg = git_changes.get('commit_message', '').lower()
    if any(keyword in commit_msg for keyword in compliance_keywords):
        triggers.append('compliance_keyword')
    
    # Trigger 4: Significant code changes (>5 files)
    if git_changes.get('file_count', 0) > 5:
        triggers.append('significant_changes')
    
    return len(triggers) > 0, triggers


def check_ip_triggers(test_report, git_changes):
    """Determine if IP disclosure is needed."""
    triggers = []
    
    # Trigger 1: New algorithms or novel implementations
    novelty_keywords = ['algorithm', 'novel', 'innovative', 'optimization', 'breakthrough']
    commit_msg = git_changes.get('commit_message', '').lower()
    if any(keyword in commit_msg for keyword in novelty_keywords):
        triggers.append('novelty_keyword')
    
    # Trigger 2: New test validations (potential novel features)
    if test_report.get('total_tests', 0) > 0:
        triggers.append('new_validations')
    
    # Trigger 3: Performance improvements
    if 'performance' in commit_msg or 'optimization' in commit_msg:
        triggers.append('performance_improvement')
    
    # Trigger 4: New workflow or system files
    workflow_files = [f for f in git_changes.get('changed_files', []) 
                     if 'workflow' in f.lower() or 'system' in f.lower()]
    if workflow_files:
        triggers.append('new_workflow')
    
    return len(triggers) > 0, triggers


def save_analysis_results(compliance_needed, compliance_triggers, 
                          ip_needed, ip_triggers, test_report, git_changes):
    """Save analysis results for downstream processing."""
    os.makedirs('output/analysis', exist_ok=True)
    
    analysis = {
        'timestamp': datetime.utcnow().isoformat(),
        'compliance': {
            'needed': compliance_needed,
            'triggers': compliance_triggers
        },
        'ip_disclosure': {
            'needed': ip_needed,
            'triggers': ip_triggers
        },
        'test_report_summary': {
            'total_tests': test_report.get('total_tests', 0),
            'passed': test_report.get('passed', 0),
            'failed': test_report.get('failed', 0),
            'pass_rate': test_report.get('pass_rate', 0.0)
        },
        'git_changes_summary': {
            'file_count': git_changes.get('file_count', 0),
            'commit_message': git_changes.get('commit_message', '')[:200]
        }
    }
    
    with open('output/analysis/validation_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    return analysis


def set_github_outputs(compliance_needed, ip_needed):
    """Set GitHub Actions outputs."""
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"compliance_needed={str(compliance_needed).lower()}\n")
            f.write(f"ip_disclosure_needed={str(ip_needed).lower()}\n")
    else:
        print(f"::set-output name=compliance_needed::{str(compliance_needed).lower()}")
        print(f"::set-output name=ip_disclosure_needed::{str(ip_needed).lower()}")


def main():
    print("=" * 60)
    print("Analyzing Validation Data")
    print("=" * 60)
    
    # Load data
    test_report = load_test_report()
    git_changes = analyze_git_changes()
    
    # Check triggers
    compliance_needed, compliance_triggers = check_compliance_triggers(test_report, git_changes)
    ip_needed, ip_triggers = check_ip_triggers(test_report, git_changes)
    
    # Save results
    analysis = save_analysis_results(
        compliance_needed, compliance_triggers,
        ip_needed, ip_triggers,
        test_report, git_changes
    )
    
    # Set outputs
    set_github_outputs(compliance_needed, ip_needed)
    
    # Print summary
    print(f"\n📊 Analysis Results:")
    print(f"  Compliance Documentation Needed: {compliance_needed}")
    if compliance_triggers:
        print(f"    Triggers: {', '.join(compliance_triggers)}")
    print(f"  IP Disclosure Needed: {ip_needed}")
    if ip_triggers:
        print(f"    Triggers: {', '.join(ip_triggers)}")
    print(f"\n  Test Summary: {test_report.get('passed', 0)}/{test_report.get('total_tests', 0)} passed")
    print(f"  Files Changed: {git_changes.get('file_count', 0)}")
    print(f"\n✅ Analysis complete. Results saved to output/analysis/validation_analysis.json")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
