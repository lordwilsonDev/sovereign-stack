#!/usr/bin/env python3
"""
Generate immutable audit trail for compliance evidence.

This script creates a hash-chained audit trail of compliance events
to ensure integrity and non-repudiation of audit evidence.
"""

import json
import os
import sys
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path


def load_existing_audit_trail():
    """Load existing audit trail if present."""
    trail_path = 'output/compliance/audit/audit_trail.json'
    if os.path.exists(trail_path):
        with open(trail_path, 'r') as f:
            return json.load(f)
    return {
        'created_at': datetime.utcnow().isoformat(),
        'chain_id': hashlib.sha256(
            datetime.utcnow().isoformat().encode()
        ).hexdigest()[:16],
        'entries': []
    }


def get_git_info():
    """Get current git commit information."""
    try:
        commit = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
        
        author = subprocess.run(
            ['git', 'log', '-1', '--pretty=%an <%ae>'],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
        
        message = subprocess.run(
            ['git', 'log', '-1', '--pretty=%s'],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
        
        return {
            'commit': commit,
            'author': author,
            'message': message
        }
    except Exception:
        return {
            'commit': 'unknown',
            'author': 'unknown',
            'message': 'unknown'
        }


def calculate_hash(data):
    """Calculate SHA-256 hash of data."""
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()


def create_audit_entry(event_type, event_data, previous_hash):
    """Create a single audit trail entry."""
    timestamp = datetime.utcnow().isoformat()
    git_info = get_git_info()
    
    entry = {
        'sequence': 0,  # Will be set by caller
        'timestamp': timestamp,
        'event_type': event_type,
        'event_data': event_data,
        'actor': {
            'type': 'system',
            'identity': 'strategic-moat-automation',
            'git_commit': git_info['commit'],
            'git_author': git_info['author']
        },
        'previous_hash': previous_hash,
        'entry_hash': ''  # Will be calculated
    }
    
    # Calculate entry hash (includes previous_hash for chain integrity)
    hash_input = {
        'timestamp': entry['timestamp'],
        'event_type': entry['event_type'],
        'event_data': entry['event_data'],
        'previous_hash': entry['previous_hash']
    }
    entry['entry_hash'] = calculate_hash(hash_input)
    
    return entry


def collect_compliance_events():
    """Collect recent compliance events from outputs."""
    events = []
    
    # Check for test execution
    if os.path.exists('test_report.json'):
        with open('test_report.json', 'r') as f:
            report = json.load(f)
        events.append({
            'type': 'test_execution',
            'data': {
                'total_tests': report.get('total_tests', 0),
                'passed': report.get('passed', 0),
                'failed': report.get('failed', 0),
                'pass_rate': report.get('pass_rate', 0)
            }
        })
    
    # Check for compliance transformation
    if os.path.exists('output/compliance/transformed/summary.json'):
        with open('output/compliance/transformed/summary.json', 'r') as f:
            summary = json.load(f)
        events.append({
            'type': 'compliance_transformation',
            'data': {
                'controls_mapped': summary.get('controls_mapped', {}),
                'evidence_packages': summary.get('evidence_packages', 0)
            }
        })
    
    # Check for IP disclosures
    if os.path.exists('output/ip_disclosures/summary.json'):
        with open('output/ip_disclosures/summary.json', 'r') as f:
            summary = json.load(f)
        events.append({
            'type': 'ip_disclosure_generation',
            'data': {
                'disclosures_count': summary.get('total_disclosures', 0)
            }
        })
    
    # Check for SOC2 generation
    if os.path.exists('output/compliance/soc2/soc2_report.json'):
        events.append({
            'type': 'soc2_documentation',
            'data': {
                'generated': True,
                'path': 'output/compliance/soc2/'
            }
        })
    
    # Check for ISO27001 generation
    if os.path.exists('output/compliance/iso27001/iso27001_report.json'):
        events.append({
            'type': 'iso27001_documentation',
            'data': {
                'generated': True,
                'path': 'output/compliance/iso27001/'
            }
        })
    
    return events


def verify_chain_integrity(audit_trail):
    """Verify the integrity of the audit trail chain."""
    entries = audit_trail.get('entries', [])
    
    if not entries:
        return True, "No entries to verify"
    
    for i, entry in enumerate(entries):
        # Verify sequence
        if entry['sequence'] != i:
            return False, f"Sequence mismatch at entry {i}"
        
        # Verify hash chain
        if i > 0:
            if entry['previous_hash'] != entries[i-1]['entry_hash']:
                return False, f"Chain broken at entry {i}"
        
        # Verify entry hash
        hash_input = {
            'timestamp': entry['timestamp'],
            'event_type': entry['event_type'],
            'event_data': entry['event_data'],
            'previous_hash': entry['previous_hash']
        }
        calculated_hash = calculate_hash(hash_input)
        if entry['entry_hash'] != calculated_hash:
            return False, f"Hash mismatch at entry {i}"
    
    return True, f"Chain verified: {len(entries)} entries"


def save_audit_trail(audit_trail):
    """Save audit trail to file."""
    os.makedirs('output/compliance/audit', exist_ok=True)
    
    # Save main audit trail
    with open('output/compliance/audit/audit_trail.json', 'w') as f:
        json.dump(audit_trail, f, indent=2)
    
    # Save verification record
    is_valid, message = verify_chain_integrity(audit_trail)
    verification = {
        'verified_at': datetime.utcnow().isoformat(),
        'chain_id': audit_trail['chain_id'],
        'entry_count': len(audit_trail['entries']),
        'is_valid': is_valid,
        'message': message,
        'latest_hash': audit_trail['entries'][-1]['entry_hash'] if audit_trail['entries'] else None
    }
    
    with open('output/compliance/audit/verification.json', 'w') as f:
        json.dump(verification, f, indent=2)
    
    return verification


def main():
    print("=" * 60)
    print("Generating Audit Trail")
    print("=" * 60)
    
    # Load existing trail
    print("\n🔍 Loading existing audit trail...")
    audit_trail = load_existing_audit_trail()
    existing_count = len(audit_trail['entries'])
    print(f"   Existing entries: {existing_count}")
    
    # Get previous hash
    if audit_trail['entries']:
        previous_hash = audit_trail['entries'][-1]['entry_hash']
    else:
        previous_hash = 'genesis'
    
    # Collect events
    print("\n📋 Collecting compliance events...")
    events = collect_compliance_events()
    print(f"   Events found: {len(events)}")
    
    # Add entries
    print("\n🔗 Adding entries to chain...")
    new_entries = 0
    for event in events:
        entry = create_audit_entry(
            event['type'],
            event['data'],
            previous_hash
        )
        entry['sequence'] = len(audit_trail['entries'])
        audit_trail['entries'].append(entry)
        previous_hash = entry['entry_hash']
        new_entries += 1
        print(f"   Added: {event['type']}")
    
    # Update metadata
    audit_trail['updated_at'] = datetime.utcnow().isoformat()
    
    # Verify and save
    print("\n🔒 Verifying chain integrity...")
    verification = save_audit_trail(audit_trail)
    
    if verification['is_valid']:
        print(f"   ✅ {verification['message']}")
    else:
        print(f"   ❌ {verification['message']}")
    
    # Print summary
    print(f"\n✅ Audit Trail Generated!")
    print(f"   Chain ID: {audit_trail['chain_id']}")
    print(f"   Total entries: {len(audit_trail['entries'])}")
    print(f"   New entries: {new_entries}")
    print(f"   Integrity: {'VALID' if verification['is_valid'] else 'INVALID'}")
    print(f"\n📁 Output saved to: output/compliance/audit/")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
