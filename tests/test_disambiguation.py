#!/usr/bin/env python3
"""Test disambiguation helper functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twin.disambiguation import DisambiguationHelper

def test_disambiguation():
    """Test the disambiguation helper with fixed queries"""
    print("Testing Disambiguation Helper")
    print("=" * 60)
    
    helper = DisambiguationHelper()
    
    # Test queries
    test_queries = [
        "What's the OEE for line 2?",
        "Why is the filler performing poorly?",
        "Optimize for better quality",
        "Show me performance trends",
        "What products are we running?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        try:
            context = helper.get_query_context(query)
            
            # Show identified entities
            if any(context["entities"].values()):
                print("Identified entities:")
                for entity_type, entities in context["entities"].items():
                    if entities:
                        print(f"  {entity_type}: {entities}")
            
            # Show available data
            if "data_range" in context.get("available_data", {}):
                data = context["available_data"]
                if data.get("data_range"):
                    print(f"Data range: {data['data_range']['start']} to {data['data_range']['end']}")
                if data.get("lines"):
                    print(f"Available lines: {data['lines']}")
                if data.get("recent_runs"):
                    print(f"Recent runs: {len(data['recent_runs'])} found")
            
            # Show parameter hints
            if context["parameter_hints"]["likely_parameters"]:
                print(f"Likely parameters: {context['parameter_hints']['likely_parameters']}")
            
            # Show suggestions
            if context["suggested_clarifications"]:
                print("Suggested clarifications:")
                for suggestion in context["suggested_clarifications"]:
                    print(f"  - {suggestion}")
                    
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n✅ Disambiguation helper test complete!")

if __name__ == "__main__":
    test_disambiguation()