"""
Master test runner for Virtual Twin implementation
Runs all phase tests and provides summary
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_module(module_name, description):
    """Run a test module and return results"""
    print("\n" + "=" * 70)
    print(f"RUNNING: {description}")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        if module_name == "test_phase1_ontology":
            from test_phase1_ontology import test_twin_ontology, test_sync_health
            test_twin_ontology()
            test_sync_health()
        elif module_name == "test_phase2_parameters":
            from test_phase2_parameters import (
                test_actionable_parameters,
                test_config_transformer,
                test_line_coupling
            )
            test_actionable_parameters()
            test_config_transformer()
            test_line_coupling()
        
        elapsed = time.time() - start_time
        return {
            "module": module_name,
            "description": description,
            "status": "PASSED",
            "time": elapsed,
            "error": None
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "module": module_name,
            "description": description,
            "status": "FAILED",
            "time": elapsed,
            "error": str(e)
        }


def main():
    """Main test runner"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "VIRTUAL TWIN TEST SUITE" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    print(f"\nTest run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define test modules
    test_modules = [
        ("test_phase1_ontology", "Phase 1: Twin Ontology and Sync Health"),
        ("test_phase2_parameters", "Phase 2: Actionable Parameters and Line Coupling"),
    ]
    
    # Run all tests
    results = []
    total_start = time.time()
    
    for module_name, description in test_modules:
        result = run_test_module(module_name, description)
        results.append(result)
    
    total_time = time.time() - total_start
    
    # Print summary
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 25 + "TEST SUMMARY" + " " * 31 + "║")
    print("╚" + "═" * 68 + "╝")
    
    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    
    print(f"\nTotal Tests Run: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total Time: {total_time:.2f} seconds")
    
    print("\n" + "-" * 70)
    print("DETAILED RESULTS:")
    print("-" * 70)
    
    for result in results:
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        print(f"\n{status_icon} {result['description']}")
        print(f"   Status: {result['status']}")
        print(f"   Time: {result['time']:.2f}s")
        if result["error"]:
            print(f"   Error: {result['error']}")
    
    print("\n" + "=" * 70)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Virtual Twin implementation is working correctly.")
        print("=" * 70)
        return 0
    else:
        print(f"⚠️  {failed} TEST(S) FAILED! Please review the errors above.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())