#!/usr/bin/env python3
"""
Sign compliance documents cryptographically.

This script creates HMAC-SHA256 signatures for compliance documents
to ensure authenticity and integrity.
"""

import json
import os
import sys
import hmac
import hashlib
from datetime import datetime
from pathlib import Path


def get_signing_key():
    """Get signing key from environment or generate one."""
    key = os.getenv('COMPLIANCE_SIGNING_KEY')
    
    if not key:
        # Generate a deterministic key based on chain ID if no env key
        audit_path = 'output/compliance/audit/audit_trail.json'
        if os.path.exists(audit_path):
            with open(audit_path, 'r') as f:
                audit = json.load(f)
            key = audit.get('chain_id', 'default-key')
        else:
            key = 'default-development-key'
        
        return key.encode(), False  # Key, is_production
    
    return key.encode(), True


def calculate_file_hash(filepath):
    """Calculate SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def sign_content(content, key):
    """Create HMAC-SHA256 signature."""
    if isinstance(content, str):
        content = content.encode()
    return hmac.new(key, content, hashlib.sha256).hexdigest()


def verify_signature(content, signature, key):
    """Verify HMAC-SHA256 signature."""
    if isinstance(content, str):
        content = content.encode()
    expected = hmac.new(key, content, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def collect_documents_to_sign():
    """Collect compliance documents for signing."""
    documents = []
    
    # SOC2 documents
    soc2_dir = Path('output/compliance/soc2')
    if soc2_dir.exists():
        for filepath in soc2_dir.glob('*.json'):
            documents.append({
                'path': str(filepath),
                'type': 'soc2',
                'name': filepath.name
            })
        for filepath in soc2_dir.glob('*.md'):
            documents.append({
                'path': str(filepath),
                'type': 'soc2',
                'name': filepath.name
            })
    
    # ISO 27001 documents
    iso_dir = Path('output/compliance/iso27001')
    if iso_dir.exists():
        for filepath in iso_dir.glob('*.json'):
            documents.append({
                'path': str(filepath),
                'type': 'iso27001',
                'name': filepath.name
            })
        for filepath in iso_dir.glob('*.md'):
            documents.append({
                'path': str(filepath),
                'type': 'iso27001',
                'name': filepath.name
            })
    
    # Audit trail
    audit_path = Path('output/compliance/audit/audit_trail.json')
    if audit_path.exists():
        documents.append({
            'path': str(audit_path),
            'type': 'audit',
            'name': audit_path.name
        })
    
    # Transformed compliance data
    transformed_dir = Path('output/compliance/transformed')
    if transformed_dir.exists():
        for filepath in transformed_dir.glob('*.json'):
            documents.append({
                'path': str(filepath),
                'type': 'transformed',
                'name': filepath.name
            })
    
    return documents


def sign_document(doc, key):
    """Sign a single document."""
    filepath = doc['path']
    
    if not os.path.exists(filepath):
        return None
    
    # Calculate file hash
    file_hash = calculate_file_hash(filepath)
    
    # Create signature payload
    payload = {
        'file_path': filepath,
        'file_hash': file_hash,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Sign the payload
    signature = sign_content(json.dumps(payload, sort_keys=True), key)
    
    return {
        'document': doc['name'],
        'document_type': doc['type'],
        'file_path': filepath,
        'file_hash': file_hash,
        'signature': signature,
        'timestamp': payload['timestamp'],
        'algorithm': 'HMAC-SHA256'
    }


def create_signed_manifest(signatures, is_production):
    """Create a manifest of all signed documents."""
    manifest = {
        'created_at': datetime.utcnow().isoformat(),
        'environment': 'production' if is_production else 'development',
        'signing_algorithm': 'HMAC-SHA256',
        'document_count': len(signatures),
        'signatures': signatures,
        'verification': {
            'method': 'HMAC-SHA256 signature verification',
            'key_source': 'COMPLIANCE_SIGNING_KEY environment variable' if is_production else 'development key (audit chain ID)',
            'instructions': 'Verify each document by computing HMAC-SHA256 of the file hash with the signing key'
        }
    }
    
    # Sign the manifest itself
    manifest_content = json.dumps({
        'document_count': manifest['document_count'],
        'signatures': manifest['signatures']
    }, sort_keys=True)
    
    key = os.getenv('COMPLIANCE_SIGNING_KEY', 'default-key').encode()
    manifest['manifest_signature'] = sign_content(manifest_content, key)
    
    return manifest


def save_manifest(manifest):
    """Save signed manifest."""
    os.makedirs('output/compliance/signed', exist_ok=True)
    
    manifest_path = 'output/compliance/signed/manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Also save a summary
    summary = {
        'created_at': manifest['created_at'],
        'environment': manifest['environment'],
        'document_count': manifest['document_count'],
        'documents': [s['document'] for s in manifest['signatures']]
    }
    
    with open('output/compliance/signed/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return manifest_path


def main():
    print("=" * 60)
    print("Signing Compliance Documents")
    print("=" * 60)
    
    # Get signing key
    print("\n🔑 Getting signing key...")
    key, is_production = get_signing_key()
    
    if is_production:
        print("   ✅ Using production signing key (COMPLIANCE_SIGNING_KEY)")
    else:
        print("   ⚠️  Using development key (set COMPLIANCE_SIGNING_KEY for production)")
    
    # Collect documents
    print("\n📋 Collecting documents to sign...")
    documents = collect_documents_to_sign()
    print(f"   Found {len(documents)} document(s)")
    
    if not documents:
        print("   ℹ️  No documents found to sign.")
        return 0
    
    # Sign documents
    print("\n✍️  Signing documents...")
    signatures = []
    for doc in documents:
        signature = sign_document(doc, key)
        if signature:
            signatures.append(signature)
            print(f"   ✅ Signed: {doc['name']}")
        else:
            print(f"   ⚠️  Skipped: {doc['name']} (not found)")
    
    # Create manifest
    print("\n📦 Creating signed manifest...")
    manifest = create_signed_manifest(signatures, is_production)
    manifest_path = save_manifest(manifest)
    
    # Print summary
    print(f"\n✅ Document Signing Complete!")
    print(f"   Documents signed: {len(signatures)}")
    print(f"   Environment: {manifest['environment']}")
    print(f"   Algorithm: {manifest['signing_algorithm']}")
    print(f"\n📁 Manifest saved to: {manifest_path}")
    
    if not is_production:
        print(f"\n⚠️  NOTE: Using development key. For production:")
        print(f"   export COMPLIANCE_SIGNING_KEY='your-secret-key'")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
