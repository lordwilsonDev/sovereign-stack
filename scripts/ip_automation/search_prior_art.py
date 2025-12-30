#!/usr/bin/env python3
"""
Search for prior art using public patent databases.

This script searches for prior art related to invention disclosures
using the Google Patents public interface (no API key required for basic search).
"""

import json
import os
import sys
import urllib.parse
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def load_disclosures():
    """Load invention disclosures to search prior art for."""
    disclosures = []
    disclosure_dir = Path('output/ip_disclosures')
    
    if disclosure_dir.exists():
        for filepath in disclosure_dir.glob('disclosure_*.json'):
            try:
                with open(filepath, 'r') as f:
                    disclosures.append(json.load(f))
            except Exception:
                continue
    
    return disclosures


def extract_search_terms(disclosure):
    """Extract search terms from disclosure for prior art search."""
    terms = []
    
    # Extract from title
    title = disclosure.get('invention', {}).get('title', '')
    if title:
        # Remove common prefixes and clean
        for prefix in ['Software Innovation:', 'Machine Learning System:', 
                       'Algorithm for', 'Optimized Data Structure:', 
                       'Performance-Optimized', 'System Optimization Component:']:
            title = title.replace(prefix, '')
        terms.extend(title.strip().split()[:5])
    
    # Extract from technical field
    field = disclosure.get('invention', {}).get('technical_field', '')
    if field:
        terms.extend(field.split()[:3])
    
    # Extract from indicators
    indicators = disclosure.get('source_reference', {}).get('indicators', [])
    indicator_terms = {
        'ml_component': ['machine learning', 'neural network'],
        'custom_data_structure': ['data structure', 'indexing'],
        'algorithm_implementation': ['algorithm', 'method'],
        'performance_optimization': ['optimization', 'performance'],
        'system_optimization': ['system', 'resource management']
    }
    for ind in indicators:
        if ind in indicator_terms:
            terms.extend(indicator_terms[ind])
    
    # Clean and dedupe
    clean_terms = []
    seen = set()
    for term in terms:
        term = term.strip().lower()
        if term and term not in seen and len(term) > 2:
            clean_terms.append(term)
            seen.add(term)
    
    return clean_terms[:10]


def search_google_patents(search_terms, max_results=10):
    """Search Google Patents for prior art."""
    if not REQUESTS_AVAILABLE:
        return {
            'status': 'skipped',
            'reason': 'requests/beautifulsoup4 not installed',
            'results': []
        }
    
    # Build search query
    query = ' '.join(search_terms)
    encoded_query = urllib.parse.quote(query)
    url = f"https://patents.google.com/?q={encoded_query}&num={max_results}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return {
                'status': 'error',
                'reason': f'HTTP {response.status_code}',
                'results': []
            }
        
        # Parse results
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Extract patent listings (simplified parsing)
        for item in soup.select('article, .result-item, [data-result]')[:max_results]:
            title_elem = item.select_one('h3, .title, [itemprop="name"]')
            link_elem = item.select_one('a[href*="patent"]')
            
            if title_elem:
                result = {
                    'title': title_elem.get_text(strip=True)[:200],
                    'url': link_elem.get('href') if link_elem else None,
                    'relevance': 'potential'
                }
                results.append(result)
        
        return {
            'status': 'success',
            'query': query,
            'search_url': url,
            'result_count': len(results),
            'results': results
        }
        
    except requests.exceptions.Timeout:
        return {
            'status': 'error',
            'reason': 'Request timeout',
            'results': []
        }
    except Exception as e:
        return {
            'status': 'error', 
            'reason': str(e),
            'results': []
        }


def search_with_api_key(search_terms, api_key):
    """Search using USPTO or commercial patent API if key provided."""
    # Placeholder for API-based search
    # Would integrate with USPTO PatentsView API or similar
    return {
        'status': 'not_implemented',
        'reason': 'API-based search not yet implemented',
        'results': []
    }


def analyze_relevance(disclosure, search_results):
    """Analyze relevance of search results to disclosure."""
    title = disclosure.get('invention', {}).get('title', '').lower()
    keywords = set(title.split())
    
    for result in search_results.get('results', []):
        result_title = result.get('title', '').lower()
        common_words = keywords.intersection(set(result_title.split()))
        
        if len(common_words) >= 3:
            result['relevance'] = 'high'
        elif len(common_words) >= 1:
            result['relevance'] = 'medium'
        else:
            result['relevance'] = 'low'
    
    return search_results


def save_prior_art_results(all_results):
    """Save prior art search results."""
    os.makedirs('output/ip_disclosures', exist_ok=True)
    
    output = {
        'searched_at': datetime.utcnow().isoformat(),
        'disclosures_searched': len(all_results),
        'search_results': all_results
    }
    
    with open('output/ip_disclosures/prior_art_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    return output


def main():
    print("=" * 60)
    print("Prior Art Search")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('PATENT_API_KEY')
    if api_key:
        print("✅ Patent API key detected")
    else:
        print("ℹ️  No PATENT_API_KEY set, using web search fallback")
    
    if not REQUESTS_AVAILABLE:
        print("⚠️  requests/beautifulsoup4 not installed")
        print("   Install with: pip install requests beautifulsoup4")
        print("   Skipping prior art search.")
        # Create empty results
        save_prior_art_results([])
        return 0
    
    # Load disclosures
    print("\n🔍 Loading invention disclosures...")
    disclosures = load_disclosures()
    
    if not disclosures:
        print("ℹ️  No disclosures found to search prior art for.")
        save_prior_art_results([])
        return 0
    
    print(f"   Found {len(disclosures)} disclosure(s)")
    
    # Search for each disclosure
    print("\n🔎 Searching prior art...")
    all_results = []
    
    for disclosure in disclosures:
        disclosure_id = disclosure.get('disclosure_id', 'unknown')
        title = disclosure.get('invention', {}).get('title', 'Untitled')
        print(f"\n   Searching for: {disclosure_id}")
        print(f"   Title: {title[:60]}...")
        
        # Extract search terms
        search_terms = extract_search_terms(disclosure)
        print(f"   Terms: {', '.join(search_terms[:5])}")
        
        # Perform search
        if api_key:
            results = search_with_api_key(search_terms, api_key)
        else:
            results = search_google_patents(search_terms)
            # Rate limiting for web search
            time.sleep(1)
        
        # Analyze relevance
        results = analyze_relevance(disclosure, results)
        
        all_results.append({
            'disclosure_id': disclosure_id,
            'disclosure_title': title,
            'search_terms': search_terms,
            'search_results': results
        })
        
        result_count = results.get('result_count', 0)
        high_relevance = sum(1 for r in results.get('results', []) 
                            if r.get('relevance') == 'high')
        print(f"   Results: {result_count} found, {high_relevance} high relevance")
    
    # Save results  
    print("\n💾 Saving prior art results...")
    output = save_prior_art_results(all_results)
    
    # Print summary
    print(f"\n✅ Prior Art Search Complete!")
    print(f"   Disclosures searched: {output['disclosures_searched']}")
    
    total_results = sum(
        r['search_results'].get('result_count', 0) 
        for r in all_results
    )
    print(f"   Total results found: {total_results}")
    print(f"\n📁 Results saved to: output/ip_disclosures/prior_art_results.json")
    print(f"\n⚠️  NOTE: Prior art results require human analysis and attorney review.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
