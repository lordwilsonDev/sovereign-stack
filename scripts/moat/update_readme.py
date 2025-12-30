#!/usr/bin/env python3
"""
Update README and MOAT_METRICS with current metrics.

This script updates the documentation files with live metrics badges
and detailed breakdowns.
"""

import json
import os
import re
import sys
from datetime import datetime


def load_metrics():
    """Load current moat metrics."""
    metrics_path = 'output/moat/metrics.json'
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            return json.load(f)
    return None


def load_history():
    """Load metrics history."""
    history_path = 'output/moat/metrics_history.json'
    if os.path.exists(history_path):
        with open(history_path, 'r') as f:
            return json.load(f)
    return {'entries': []}


def get_badge_color(level):
    """Get shield.io badge color for moat level."""
    colors = {
        'developing': 'yellow',
        'moderate': 'orange',
        'strong': 'green',
        'dominant': 'blue'
    }
    return colors.get(level, 'gray')


def generate_readme_badges(metrics):
    """Generate badge markdown for README."""
    level = metrics['moat_strength']['level']
    level_color = get_badge_color(level)
    
    # URL encode spaces
    level_display = level.replace(' ', '%20').title()
    
    badges = f'''<!-- MOAT_METRICS_START -->
![Moat Strength](https://img.shields.io/badge/Moat%20Strength-{level_display}-{level_color}?style=for-the-badge)
![Compliance Score](https://img.shields.io/badge/Compliance-{metrics['compliance_score']}%25-green?style=for-the-badge)
![IP Portfolio](https://img.shields.io/badge/IP%20Disclosures-{metrics['ip_portfolio_count']}-blue?style=for-the-badge)
![Automation](https://img.shields.io/badge/Automation-{metrics['automation_coverage']}%25-purple?style=for-the-badge)
<!-- MOAT_METRICS_END -->'''
    
    return badges


def generate_moat_metrics_content(metrics, history):
    """Generate content for MOAT_METRICS.md."""
    level = metrics['moat_strength']['level']
    level_icon = {
        'developing': '🟡',
        'moderate': '🟠',
        'strong': '🟢',
        'dominant': '🔵'
    }.get(level, '⚪')
    
    # Generate history table rows
    history_rows = ""
    for entry in history.get('entries', [])[-10:]:  # Last 10 entries
        date = entry.get('date', '')[:10]
        history_rows += f"| {date} | {entry.get('compliance_score', 0)}% | {entry.get('ip_portfolio_count', 0)} | {entry.get('automation_coverage', 0)}% | {entry.get('moat_strength', 0)} |\n"
    
    if not history_rows:
        history_rows = "| - | - | - | - | - |\n"
    
    content = f'''# Strategic Moat Metrics

> Detailed breakdown of competitive moat indicators.

---

## Current Status

<!-- MOAT_STATUS_START -->
| Metric | Score | Status |
|--------|-------|--------|
| 📋 Compliance Score | {metrics['compliance_score']}% | {'✅ Good' if metrics['compliance_score'] >= 70 else '⚠️ Needs Attention'} |
| 💡 IP Portfolio Count | {metrics['ip_portfolio_count']} | {'✅ Good' if metrics['ip_portfolio_count'] >= 1 else '⚠️ Needs Attention'} |
| ⚙️ Automation Coverage | {metrics['automation_coverage']}% | {'✅ Good' if metrics['automation_coverage'] >= 70 else '⚠️ Needs Attention'} |
| 🏰 **Moat Strength** | **{metrics['moat_strength']['score']}** | {level_icon} {level.title()} |

**Last Updated**: {datetime.utcnow().strftime('%B %Y')}  
**Next Review**: {datetime.utcnow().strftime('%B %Y')}
<!-- MOAT_STATUS_END -->

---

## Metric Definitions

### 📋 Compliance Score (0-100%)

Percentage of compliance controls with automated evidence:

| Framework | Controls Implemented | Target | Coverage |
|-----------|---------------------|--------|----------|
| SOC2 Type II | {metrics['details']['compliance']['soc2_controls']} | 20 | {min(100, int(metrics['details']['compliance']['soc2_controls']/20*100))}% |
| ISO 27001 | {metrics['details']['compliance']['iso27001_controls']} | 40 | {min(100, int(metrics['details']['compliance']['iso27001_controls']/40*100))}% |
| **Combined** | **{metrics['details']['compliance']['soc2_controls'] + metrics['details']['compliance']['iso27001_controls']}** | **60** | **{metrics['compliance_score']}%** |

### 💡 IP Portfolio Count

Intellectual property assets in various stages:

| Stage | Count |
|-------|-------|
| Disclosures (Draft) | {metrics['details']['ip']['disclosures']} |
| Novelty Score | {metrics['details']['ip']['novelty_score']} |
| Claims Generated | {metrics['details']['ip']['claims_generated']} |
| **Total Portfolio** | **{metrics['ip_portfolio_count']}** |

### ⚙️ Automation Coverage (0-100%)

Percentage of processes that run without manual intervention:

| Process | Status |
|---------|--------|
| Test Execution | ✅ Automated |
| Compliance Doc Generation | ✅ Automated |
| IP Disclosure Detection | ✅ Automated |
| Prior Art Search | ✅ Automated |
| Patent Claim Drafting | ✅ Automated |
| Audit Trail | ✅ Automated |
| Metric Calculation | ✅ Automated |
| Dashboard Generation | ✅ Automated |
| README Updates | ✅ Automated |
| **Coverage** | **{metrics['automation_coverage']}%** |

### 🏰 Moat Strength (0-100)

Overall competitive advantage rating:

```
Moat Strength = (Compliance × 0.3) + (IP × 0.4) + (Automation × 0.3)

Current:
= ({metrics['compliance_score']} × 0.3) + ({metrics.get('ip_portfolio_score', 0)} × 0.4) + ({metrics['automation_coverage']} × 0.3)
= {metrics['moat_strength']['score']} → {level.title()}
```

---

## Historical Trend

| Date | Compliance | IP Count | Automation | Moat |
|------|------------|----------|------------|------|
{history_rows}
---

## Improvement Roadmap

### Short-term (30 days)
- [ ] Generate first IP disclosure from existing innovations
- [ ] Complete prior art search integration
- [ ] Achieve 90% automation coverage

### Medium-term (90 days)
- [ ] File first patent application
- [ ] Achieve 95% compliance score
- [ ] Reach "Moderate" moat strength

### Long-term (1 year)
- [ ] Build portfolio of 5+ IP assets
- [ ] Achieve "Strong" moat strength
- [ ] Add GDPR/HIPAA compliance frameworks

---

*Auto-generated by Strategic Moat Automation*
'''
    
    return content


def update_readme(badges):
    """Update README.md with new badges."""
    readme_path = 'README.md'
    
    if not os.path.exists(readme_path):
        print(f"⚠️  {readme_path} not found, skipping")
        return False
    
    with open(readme_path, 'r') as f:
        content = f.read()
    
    # Replace badges between markers
    pattern = r'<!-- MOAT_METRICS_START -->.*?<!-- MOAT_METRICS_END -->'
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, badges, content, flags=re.DOTALL)
    else:
        # Insert after first heading
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('# '):
                lines.insert(i + 1, '\n' + badges + '\n')
                break
        new_content = '\n'.join(lines)
    
    with open(readme_path, 'w') as f:
        f.write(new_content)
    
    return True


def update_moat_metrics_md(content):
    """Update MOAT_METRICS.md with new content."""
    moat_path = 'MOAT_METRICS.md'
    
    with open(moat_path, 'w') as f:
        f.write(content)
    
    return True


def main():
    print("=" * 60)
    print("Updating README with Moat Metrics")
    print("=" * 60)
    
    # Load data
    print("\n🔍 Loading metrics...")
    metrics = load_metrics()
    
    if not metrics:
        print("⚠️  No metrics found. Run calculate_metrics.py first.")
        return 0
    
    history = load_history()
    print(f"   Moat strength: {metrics['moat_strength']['score']} ({metrics['moat_strength']['level']})")
    
    # Generate content
    print("\n📝 Generating badge content...")
    badges = generate_readme_badges(metrics)
    moat_content = generate_moat_metrics_content(metrics, history)
    
    # Update files
    print("\n💾 Updating files...")
    
    if update_readme(badges):
        print("   ✅ README.md updated")
    else:
        print("   ⚠️  README.md not updated")
    
    if update_moat_metrics_md(moat_content):
        print("   ✅ MOAT_METRICS.md updated")
    else:
        print("   ⚠️  MOAT_METRICS.md not updated")
    
    print(f"\n✅ Documentation update complete!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
