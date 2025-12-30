#!/usr/bin/env python3
"""
Generate interactive HTML dashboard for moat metrics.

This script creates a visual dashboard showing compliance,
IP portfolio, and overall moat strength.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def load_metrics():
    """Load current moat metrics."""
    metrics_path = 'output/moat/metrics.json'
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            return json.load(f)
    return None


def load_history():
    """Load metrics history for trend charts."""
    history_path = 'output/moat/metrics_history.json'
    if os.path.exists(history_path):
        with open(history_path, 'r') as f:
            return json.load(f)
    return {'entries': []}


def get_level_color(level):
    """Get color for moat level."""
    colors = {
        'developing': '#ffc107',  # Yellow
        'moderate': '#fd7e14',     # Orange
        'strong': '#28a745',       # Green
        'dominant': '#007bff'      # Blue
    }
    return colors.get(level, '#6c757d')


def generate_dashboard_html(metrics, history):
    """Generate the dashboard HTML."""
    level = metrics['moat_strength']['level']
    level_color = get_level_color(level)
    
    # Prepare history data for chart
    history_labels = []
    history_data = []
    for entry in history.get('entries', [])[-30:]:  # Last 30 entries
        date = entry.get('date', '')[:10]
        history_labels.append(date)
        history_data.append(entry.get('moat_strength', 0))
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Strategic Moat Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #1a1a2e;
            --secondary: #16213e;
            --accent: #0f3460;
            --highlight: #e94560;
            --text: #eee;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: var(--text);
            min-height: 100vh;
            padding: 2rem;
        }}
        
        .dashboard {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        
        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, var(--text), var(--highlight));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        header p {{
            opacity: 0.7;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .metric-card {{
            background: var(--secondary);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        
        .metric-card h3 {{
            font-size: 0.9rem;
            opacity: 0.7;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .metric-value {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        .metric-bar {{
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .metric-bar-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 1s ease-out;
        }}
        
        .moat-card {{
            grid-column: span 2;
            text-align: center;
            background: linear-gradient(135deg, var(--accent) 0%, var(--secondary) 100%);
        }}
        
        .moat-level {{
            display: inline-block;
            padding: 0.5rem 1.5rem;
            border-radius: 50px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 1rem;
        }}
        
        .chart-container {{
            background: var(--secondary);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 2rem;
        }}
        
        .chart-container h3 {{
            margin-bottom: 1rem;
        }}
        
        .details-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }}
        
        .details-card {{
            background: var(--secondary);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .details-card h3 {{
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }}
        
        .details-list {{
            list-style: none;
        }}
        
        .details-list li {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        
        .details-list li:last-child {{
            border-bottom: none;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 2rem;
            opacity: 0.5;
            font-size: 0.85rem;
        }}
        
        @media (max-width: 768px) {{
            .moat-card {{
                grid-column: span 1;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <header>
            <h1>🏰 Strategic Moat Dashboard</h1>
            <p>Last updated: {metrics['calculated_at'][:19].replace('T', ' ')} UTC</p>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>📋 Compliance Score</h3>
                <div class="metric-value">{metrics['compliance_score']}%</div>
                <div class="metric-bar">
                    <div class="metric-bar-fill" style="width: {metrics['compliance_score']}%; background: var(--success);"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>💡 IP Portfolio</h3>
                <div class="metric-value">{metrics['ip_portfolio_count']}</div>
                <p style="opacity: 0.7;">Invention Disclosures</p>
            </div>
            
            <div class="metric-card">
                <h3>⚙️ Automation Coverage</h3>
                <div class="metric-value">{metrics['automation_coverage']}%</div>
                <div class="metric-bar">
                    <div class="metric-bar-fill" style="width: {metrics['automation_coverage']}%; background: #9b59b6;"></div>
                </div>
            </div>
            
            <div class="metric-card moat-card">
                <h3>🏰 Overall Moat Strength</h3>
                <div class="metric-value">{metrics['moat_strength']['score']}</div>
                <div class="metric-bar" style="max-width: 300px; margin: 0 auto;">
                    <div class="metric-bar-fill" style="width: {metrics['moat_strength']['score']}%; background: {level_color};"></div>
                </div>
                <div class="moat-level" style="background: {level_color};">
                    {level.upper()}
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>📈 Moat Strength Trend</h3>
            <canvas id="trendChart" height="100"></canvas>
        </div>
        
        <div class="details-grid">
            <div class="details-card">
                <h3>📋 Compliance Details</h3>
                <ul class="details-list">
                    <li><span>SOC2 Controls</span><span>{metrics['details']['compliance']['soc2_controls']}</span></li>
                    <li><span>ISO 27001 Controls</span><span>{metrics['details']['compliance']['iso27001_controls']}</span></li>
                    <li><span>Audit Evidence Packages</span><span>{metrics['details']['compliance']['audit_evidence']}</span></li>
                </ul>
            </div>
            
            <div class="details-card">
                <h3>💡 IP Portfolio Details</h3>
                <ul class="details-list">
                    <li><span>Disclosures</span><span>{metrics['details']['ip']['disclosures']}</span></li>
                    <li><span>Novelty Score</span><span>{metrics['details']['ip']['novelty_score']}</span></li>
                    <li><span>Claims Generated</span><span>{metrics['details']['ip']['claims_generated']}</span></li>
                </ul>
            </div>
            
            <div class="details-card">
                <h3>🧪 Testing Details</h3>
                <ul class="details-list">
                    <li><span>Total Tests</span><span>{metrics['details']['testing']['total_tests']}</span></li>
                    <li><span>Pass Rate</span><span>{metrics['details']['testing']['pass_rate']:.1f}%</span></li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Strategic Moat Automation | Sparse Axion RAG</p>
        </div>
    </div>
    
    <script>
        const ctx = document.getElementById('trendChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(history_labels)},
                datasets: [{{
                    label: 'Moat Strength',
                    data: {json.dumps(history_data)},
                    borderColor: '{level_color}',
                    backgroundColor: '{level_color}33',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        grid: {{
                            color: 'rgba(255,255,255,0.1)'
                        }},
                        ticks: {{
                            color: '#eee'
                        }}
                    }},
                    x: {{
                        grid: {{
                            display: false
                        }},
                        ticks: {{
                            color: '#eee'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    return html


def main():
    print("=" * 60)
    print("Generating Moat Dashboard")
    print("=" * 60)
    
    # Load data
    print("\n🔍 Loading metrics...")
    metrics = load_metrics()
    
    if not metrics:
        print("⚠️  No metrics found. Run calculate_metrics.py first.")
        # Generate placeholder metrics
        metrics = {
            'calculated_at': datetime.utcnow().isoformat(),
            'compliance_score': 0,
            'ip_portfolio_count': 0,
            'ip_portfolio_score': 0,
            'automation_coverage': 0,
            'moat_strength': {'score': 0, 'level': 'developing'},
            'details': {
                'compliance': {'soc2_controls': 0, 'iso27001_controls': 0, 'audit_evidence': 0},
                'ip': {'disclosures': 0, 'novelty_score': 0, 'claims_generated': 0},
                'testing': {'total_tests': 0, 'pass_rate': 0}
            }
        }
    
    history = load_history()
    print(f"   Metrics loaded: moat strength = {metrics['moat_strength']['score']}")
    print(f"   History entries: {len(history.get('entries', []))}")
    
    # Generate dashboard
    print("\n🎨 Generating HTML dashboard...")
    html = generate_dashboard_html(metrics, history)
    
    # Save dashboard
    os.makedirs('output/moat', exist_ok=True)
    dashboard_path = 'output/moat/dashboard.html'
    with open(dashboard_path, 'w') as f:
        f.write(html)
    
    print(f"\n✅ Dashboard generated!")
    print(f"📁 Output saved to: {dashboard_path}")
    print(f"\n💡 Open in browser: file://{os.path.abspath(dashboard_path)}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
