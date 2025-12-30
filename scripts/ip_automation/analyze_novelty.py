#!/usr/bin/env python3
"""
Analyze code for novelty using AST-based analysis.

This script performs deep analysis of Python code changes to identify
potentially novel implementations that may be patentable.
"""

import ast
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class NoveltyAnalyzer(ast.NodeVisitor):
    """AST visitor that identifies novel code patterns."""
    
    def __init__(self):
        self.findings = []
        self.complexity_score = 0
        self.current_class = None
        self.current_function = None
        
    def visit_ClassDef(self, node):
        """Analyze class definitions for novelty indicators."""
        self.current_class = node.name
        
        # Check for novel class patterns
        novelty_indicators = []
        
        # Pattern: Custom data structures
        data_structure_keywords = ['tree', 'graph', 'cache', 'queue', 'stack', 
                                   'heap', 'trie', 'index', 'store', 'buffer']
        if any(kw in node.name.lower() for kw in data_structure_keywords):
            novelty_indicators.append('custom_data_structure')
            self.complexity_score += 3
        
        # Pattern: Design patterns
        pattern_keywords = ['factory', 'singleton', 'observer', 'strategy', 
                           'adapter', 'decorator', 'proxy', 'builder']
        if any(kw in node.name.lower() for kw in pattern_keywords):
            novelty_indicators.append('design_pattern_implementation')
            self.complexity_score += 2
        
        # Pattern: ML/AI components
        ml_keywords = ['model', 'network', 'layer', 'encoder', 'decoder', 
                       'transformer', 'attention', 'embedding']
        if any(kw in node.name.lower() for kw in ml_keywords):
            novelty_indicators.append('ml_component')
            self.complexity_score += 4
        
        # Pattern: Optimization components
        opt_keywords = ['optimizer', 'scheduler', 'balancer', 'allocator', 
                       'manager', 'coordinator', 'orchestrator']
        if any(kw in node.name.lower() for kw in opt_keywords):
            novelty_indicators.append('system_optimization')
            self.complexity_score += 3
        
        if novelty_indicators:
            self.findings.append({
                'type': 'class',
                'name': node.name,
                'line': node.lineno,
                'indicators': novelty_indicators,
                'docstring': ast.get_docstring(node) or '',
                'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
            })
        
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        """Analyze function definitions for novelty indicators."""
        self.current_function = node.name
        novelty_indicators = []
        
        # Pattern: Algorithm implementations
        algo_keywords = ['algorithm', 'solve', 'compute', 'calculate', 'optimize',
                        'search', 'sort', 'merge', 'split', 'parse', 'transform']
        if any(kw in node.name.lower() for kw in algo_keywords):
            novelty_indicators.append('algorithm_implementation')
            self.complexity_score += 3
        
        # Pattern: Performance optimizations
        perf_keywords = ['fast', 'quick', 'efficient', 'parallel', 'async',
                        'batch', 'bulk', 'stream', 'cache', 'memoize']
        if any(kw in node.name.lower() for kw in perf_keywords):
            novelty_indicators.append('performance_optimization')
            self.complexity_score += 2
        
        # Pattern: Novel approaches (from docstring)
        docstring = ast.get_docstring(node) or ''
        novel_docstring_keywords = ['novel', 'innovative', 'unique', 'new approach',
                                    'breakthrough', 'improvement', 'optimization']
        if any(kw in docstring.lower() for kw in novel_docstring_keywords):
            novelty_indicators.append('documented_innovation')
            self.complexity_score += 4
        
        # Analyze complexity (cyclomatic complexity approximation)
        complexity = self._estimate_complexity(node)
        if complexity > 10:
            novelty_indicators.append('high_complexity_logic')
            self.complexity_score += 2
        
        if novelty_indicators:
            self.findings.append({
                'type': 'function',
                'name': node.name,
                'class': self.current_class,
                'line': node.lineno,
                'indicators': novelty_indicators,
                'docstring': docstring[:200] if docstring else '',
                'args': [arg.arg for arg in node.args.args],
                'complexity': complexity
            })
        
        self.generic_visit(node)
        self.current_function = None
    
    def _estimate_complexity(self, node):
        """Estimate cyclomatic complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1
        return complexity


def get_changed_python_files():
    """Get list of Python files changed in recent commits."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~5', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=10
        )
        files = [f for f in result.stdout.strip().split('\n') 
                 if f.endswith('.py') and os.path.exists(f)]
        return files
    except Exception:
        # Fallback: analyze all Python files in scripts directory
        return list(Path('scripts').rglob('*.py'))


def analyze_file(filepath):
    """Analyze a single Python file for novelty."""
    try:
        with open(filepath, 'r') as f:
            source = f.read()
        
        tree = ast.parse(source)
        analyzer = NoveltyAnalyzer()
        analyzer.visit(tree)
        
        return {
            'file': str(filepath),
            'findings': analyzer.findings,
            'complexity_score': analyzer.complexity_score
        }
    except Exception as e:
        return {
            'file': str(filepath),
            'findings': [],
            'complexity_score': 0,
            'error': str(e)
        }


def calculate_novelty_score(analysis_results):
    """Calculate overall novelty score from analysis results."""
    total_score = 0
    finding_types = defaultdict(int)
    
    for result in analysis_results:
        total_score += result.get('complexity_score', 0)
        for finding in result.get('findings', []):
            for indicator in finding.get('indicators', []):
                finding_types[indicator] += 1
    
    # Normalize score
    if total_score > 100:
        total_score = 100
    
    # Determine novelty level
    if total_score >= 70:
        level = 'high'
    elif total_score >= 40:
        level = 'medium'
    elif total_score >= 10:
        level = 'low'
    else:
        level = 'none'
    
    return {
        'score': total_score,
        'level': level,
        'finding_breakdown': dict(finding_types)
    }


def save_analysis(analysis_results, novelty_score):
    """Save novelty analysis results."""
    os.makedirs('output/ip_disclosures', exist_ok=True)
    
    output = {
        'analyzed_at': datetime.utcnow().isoformat(),
        'novelty_score': novelty_score,
        'files_analyzed': len(analysis_results),
        'total_findings': sum(len(r.get('findings', [])) for r in analysis_results),
        'file_results': analysis_results
    }
    
    with open('output/ip_disclosures/novelty_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    return output


def main():
    print("=" * 60)
    print("Novelty Analysis - AST-Based Code Review")
    print("=" * 60)
    
    # Get files to analyze
    print("\n🔍 Finding Python files to analyze...")
    files = get_changed_python_files()
    
    if not files:
        print("ℹ️  No Python files found to analyze.")
        # Create empty analysis
        save_analysis([], {'score': 0, 'level': 'none', 'finding_breakdown': {}})
        print("✅ Novelty analysis complete (no files)")
        return 0
    
    print(f"   Found {len(files)} Python file(s)")
    
    # Analyze files
    print("\n🧠 Performing AST analysis...")
    analysis_results = []
    for filepath in files:
        print(f"   Analyzing: {filepath}")
        result = analyze_file(filepath)
        analysis_results.append(result)
        if result.get('findings'):
            print(f"      → Found {len(result['findings'])} novelty indicator(s)")
    
    # Calculate scores
    print("\n📊 Calculating novelty scores...")
    novelty_score = calculate_novelty_score(analysis_results)
    
    # Save results
    print("\n💾 Saving analysis results...")
    output = save_analysis(analysis_results, novelty_score)
    
    # Print summary
    print(f"\n✅ Novelty Analysis Complete!")
    print(f"   Files analyzed: {output['files_analyzed']}")
    print(f"   Total findings: {output['total_findings']}")
    print(f"   Novelty score:  {novelty_score['score']}/100 ({novelty_score['level']})")
    
    if novelty_score['finding_breakdown']:
        print(f"\n   Finding breakdown:")
        for indicator, count in sorted(novelty_score['finding_breakdown'].items()):
            print(f"      {indicator}: {count}")
    
    print(f"\n📁 Results saved to: output/ip_disclosures/novelty_analysis.json")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
