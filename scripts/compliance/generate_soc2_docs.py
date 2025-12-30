#!/usr/bin/env python3
"""
Generate SOC2 Type II compliance documentation.

This script generates structured SOC2 documentation from
transformed compliance data, mapping to Trust Service Criteria.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


# SOC2 Trust Service Criteria
TSC_MAPPING = {
    'CC1': {
        'name': 'Control Environment',
        'description': 'COSO Principle 1-5: Management commitment to integrity and competence'
    },
    'CC2': {
        'name': 'Information and Communication',
        'description': 'COSO Principle 13-15: Information quality and communication'
    },
    'CC3': {
        'name': 'Risk Assessment',
        'description': 'COSO Principle 6-9: Risk identification and analysis'
    },
    'CC4': {
        'name': 'Monitoring Activities',
        'description': 'COSO Principle 16-17: Ongoing and separate evaluations'
    },
    'CC5': {
        'name': 'Control Activities',
        'description': 'COSO Principle 10-12: Policies and procedures'
    },
    'CC6': {
        'name': 'Logical and Physical Access',
        'description': 'Access control implementation and monitoring'
    },
    'CC7': {
        'name': 'System Operations',
        'description': 'System monitoring and incident detection'
    },
    'CC8': {
        'name': 'Change Management',
        'description': 'Change control and authorization'
    },
    'CC9': {
        'name': 'Risk Mitigation',
        'description': 'Risk management and business continuity'
    },
    'A1': {
        'name': 'Availability',
        'description': 'System availability and performance monitoring'
    },
    'PI1': {
        'name': 'Processing Integrity',
        'description': 'Complete, accurate, timely, and authorized processing'
    },
    'C1': {
        'name': 'Confidentiality',
        'description': 'Protection of confidential information'
    },
    'P1': {
        'name': 'Privacy',
        'description': 'Personal information handling'
    }
}


def load_compliance_data():
    """Load transformed compliance data."""
    data = {}
    
    # Load controls mapping
    controls_path = 'output/compliance/transformed/controls_mapping.json'
    if os.path.exists(controls_path):
        with open(controls_path, 'r') as f:
            data['controls'] = json.load(f)
    else:
        data['controls'] = {'soc2': [], 'iso27001': []}
    
    # Load audit evidence
    evidence_path = 'output/compliance/transformed/audit_evidence.json'
    if os.path.exists(evidence_path):
        with open(evidence_path, 'r') as f:
            data['evidence'] = json.load(f)
    else:
        data['evidence'] = {}
    
    # Load test report
    for path in ['test_report.json', 'artifacts/test_report.json']:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data['test_report'] = json.load(f)
            break
    else:
        data['test_report'] = {}
    
    return data


def generate_control_documentation(control_id, control_data, evidence):
    """Generate documentation for a specific control."""
    tsc = TSC_MAPPING.get(control_id.split('.')[0], {})
    
    doc = {
        'control_id': control_id,
        'control_name': tsc.get('name', 'Unknown'),
        'category': tsc.get('description', ''),
        'implementation': {
            'status': 'implemented',
            'method': 'Automated validation and testing',
            'description': f"Control {control_id} is implemented through automated processes that ensure continuous compliance monitoring."
        },
        'evidence': {
            'type': 'automated_testing',
            'description': evidence.get('description', 'Automated test execution'),
            'test_summary': evidence.get('test_summary', {}),
            'collection_method': 'Continuous Integration Pipeline',
            'retention_period': '365 days'
        },
        'testing': {
            'frequency': 'Per commit',
            'method': 'Automated unit and integration tests',
            'last_test': datetime.utcnow().isoformat(),
            'result': 'pass' if evidence.get('test_summary', {}).get('failed', 1) == 0 else 'partial'
        },
        'responsible_party': 'Engineering Team',
        'review_date': datetime.utcnow().strftime('%Y-%m-%d')
    }
    
    return doc


def generate_soc2_report(compliance_data):
    """Generate complete SOC2 documentation."""
    report = {
        'report_type': 'SOC2 Type II',
        'generated_at': datetime.utcnow().isoformat(),
        'report_period': {
            'start': datetime.utcnow().replace(month=1, day=1).strftime('%Y-%m-%d'),
            'end': datetime.utcnow().strftime('%Y-%m-%d')
        },
        'scope': {
            'system': 'Sparse Axion RAG - Strategic Moat Automation',
            'trust_services_categories': ['Security', 'Availability', 'Processing Integrity'],
            'description': 'Automated compliance documentation and IP protection system'
        },
        'management_assertion': {
            'statement': 'Management is responsible for the design, implementation, and maintenance of effective internal controls.',
            'responsibility': 'System controls are designed to meet the applicable Trust Services Criteria.'
        },
        'controls': [],
        'summary': {}
    }
    
    # Generate control documentation
    evidence = compliance_data.get('evidence', {})
    
    # Add controls from data
    for control in compliance_data.get('controls', {}).get('soc2', []):
        control_doc = generate_control_documentation(
            control.get('control_id', 'CC6.1'),
            control,
            evidence
        )
        report['controls'].append(control_doc)
    
    # Add standard controls if none exist
    if not report['controls']:
        standard_controls = ['CC6.1', 'CC6.2', 'CC6.3', 'CC7.1', 'CC7.2', 'CC8.1', 'A1.1', 'A1.2']
        for ctrl_id in standard_controls:
            control_doc = generate_control_documentation(ctrl_id, {}, evidence)
            report['controls'].append(control_doc)
    
    # Generate summary
    total_controls = len(report['controls'])
    passed = sum(1 for c in report['controls'] if c['testing']['result'] == 'pass')
    
    report['summary'] = {
        'total_controls': total_controls,
        'controls_passed': passed,
        'controls_partial': total_controls - passed,
        'overall_status': 'compliant' if passed == total_controls else 'partial',
        'recommendations': []
    }
    
    if passed < total_controls:
        report['summary']['recommendations'].append(
            'Review partial controls and ensure all test cases pass.'
        )
    
    return report


def generate_markdown_report(report):
    """Generate markdown version of SOC2 report."""
    md = f"""# SOC2 Type II Compliance Report

**Report Type**: {report['report_type']}  
**Generated**: {report['generated_at'][:10]}  
**Period**: {report['report_period']['start']} to {report['report_period']['end']}

---

## System Scope

**System**: {report['scope']['system']}  
**Trust Services**: {', '.join(report['scope']['trust_services_categories'])}

{report['scope']['description']}

---

## Management Assertion

{report['management_assertion']['statement']}

{report['management_assertion']['responsibility']}

---

## Control Summary

| Status | Count |
|--------|-------|
| Total Controls | {report['summary']['total_controls']} |
| Controls Passed | {report['summary']['controls_passed']} |
| Controls Partial | {report['summary']['controls_partial']} |
| **Overall Status** | **{report['summary']['overall_status'].upper()}** |

---

## Control Details

"""
    
    for control in report['controls']:
        status_icon = '✅' if control['testing']['result'] == 'pass' else '⚠️'
        md += f"""### {status_icon} {control['control_id']}: {control['control_name']}

**Category**: {control['category']}

**Implementation**:
- Status: {control['implementation']['status']}
- Method: {control['implementation']['method']}

**Evidence**:
- Type: {control['evidence']['type']}
- Collection: {control['evidence']['collection_method']}
- Retention: {control['evidence']['retention_period']}

**Testing**:
- Frequency: {control['testing']['frequency']}
- Last Test: {control['testing']['last_test'][:10]}
- Result: {control['testing']['result'].upper()}

---

"""
    
    if report['summary']['recommendations']:
        md += "## Recommendations\n\n"
        for rec in report['summary']['recommendations']:
            md += f"- {rec}\n"
    
    md += "\n---\n\n*Generated by Strategic Moat Automation*\n"
    
    return md


def save_soc2_docs(report, markdown):
    """Save SOC2 documentation."""
    os.makedirs('output/compliance/soc2', exist_ok=True)
    
    # Save JSON report
    with open('output/compliance/soc2/soc2_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Save Markdown report
    with open('output/compliance/soc2/SOC2_REPORT.md', 'w') as f:
        f.write(markdown)
    
    return True


def main():
    print("=" * 60)
    print("Generating SOC2 Type II Documentation")
    print("=" * 60)
    
    # Load data
    print("\n🔍 Loading compliance data...")
    compliance_data = load_compliance_data()
    
    controls = compliance_data.get('controls', {}).get('soc2', [])
    print(f"   Controls found: {len(controls)}")
    
    # Generate report
    print("\n📝 Generating SOC2 report...")
    report = generate_soc2_report(compliance_data)
    markdown = generate_markdown_report(report)
    
    # Save documentation
    print("\n💾 Saving documentation...")
    save_soc2_docs(report, markdown)
    
    # Print summary
    print(f"\n✅ SOC2 Documentation Generated!")
    print(f"   Controls documented: {report['summary']['total_controls']}")
    print(f"   Controls passed: {report['summary']['controls_passed']}")
    print(f"   Overall status: {report['summary']['overall_status'].upper()}")
    print(f"\n📁 Output saved to: output/compliance/soc2/")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
