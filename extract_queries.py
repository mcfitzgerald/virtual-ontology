#!/usr/bin/env python3
"""
Minimal query extractor for SQLOnt pattern learning.
Extracts successful queries with intents for LLM analysis.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional

def extract_successful_queries(log_file: str = "query_logs.json") -> List[Dict]:
    """Extract successful queries (status 200) with intents."""
    
    with open(log_file, 'r') as f:
        logs = json.load(f)
    
    successful = []
    for entry in logs:
        # Only include successful SQL queries with intents
        if (entry.get('status_code') == 200 and 
            entry.get('endpoint') == '/query' and
            entry.get('intent')):
            
            # Extract SQL from request body or response
            sql = ''
            
            # Try to get SQL from request body first
            request_body = entry.get('request_body', '')
            if request_body and request_body != '@-':
                try:
                    request_data = json.loads(request_body)
                    sql = request_data.get('sql', '')
                except:
                    pass
            
            # If no SQL in request, try to extract from response
            if not sql:
                try:
                    response_data = json.loads(entry.get('response', '{}'))
                    sql = response_data.get('query', '')
                except:
                    pass
            
            if sql:
                # Extract row count from response
                try:
                    response_data = json.loads(entry.get('response', '{}'))
                    row_count = response_data.get('row_count', 0)
                except:
                    row_count = 0
                
                successful.append({
                    'id': entry.get('id'),
                    'timestamp': entry.get('timestamp'),
                    'intent': entry.get('intent'),
                    'sql': sql,
                    'row_count': row_count
                })
    
    return successful

def format_for_llm(queries: List[Dict]) -> str:
    """Format queries for LLM analysis."""
    
    output = {
        'extraction_metadata': {
            'total_queries': len(queries),
            'source': 'query_logs.json',
            'purpose': 'Pattern extraction for SQLOnt learning'
        },
        'successful_queries': queries
    }
    
    return yaml.dump(output, default_flow_style=False, sort_keys=False)

def main():
    # Extract queries
    queries = extract_successful_queries()
    
    if not queries:
        print("No successful queries with intents found.")
        return
    
    # Format for output
    output = format_for_llm(queries)
    
    # Save to file
    output_file = "extracted_patterns.yaml"
    with open(output_file, 'w') as f:
        f.write(output)
    
    print(f"Extracted {len(queries)} successful queries with intents")
    print(f"Output saved to: {output_file}")
    print("\nSample entry:")
    print(yaml.dump(queries[0] if queries else {}, default_flow_style=False))

if __name__ == "__main__":
    main()