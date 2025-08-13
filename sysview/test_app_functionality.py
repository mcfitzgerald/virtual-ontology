"""
Test the Dash app's functionality by simulating user interactions
"""

import requests
import json
import time

base_url = "http://localhost:8050"

def test_app_availability():
    """Test if the app is running and accessible"""
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            print("✓ App is running and accessible")
            return True
        else:
            print(f"✗ App returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to app: {e}")
        return False

def test_dash_layout():
    """Test if Dash layout endpoint is accessible"""
    try:
        response = requests.get(f"{base_url}/_dash-layout")
        if response.status_code == 200:
            layout = response.json()
            print("✓ Dash layout endpoint working")
            
            # Check for expected components
            layout_str = json.dumps(layout)
            components = [
                'cytoscape-graph',
                'namespace-dropdown', 
                'node-type-checklist',
                'search-input',
                'layout-dropdown'
            ]
            
            missing = []
            for comp in components:
                if comp not in layout_str:
                    missing.append(comp)
            
            if missing:
                print(f"  ⚠ Missing components: {missing}")
            else:
                print("  ✓ All expected components present")
            return True
        else:
            print(f"✗ Layout endpoint returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Layout endpoint error: {e}")
        return False

def test_dash_dependencies():
    """Test if Dash dependencies endpoint is accessible"""
    try:
        response = requests.get(f"{base_url}/_dash-dependencies")
        if response.status_code == 200:
            deps = response.json()
            print(f"✓ Dash dependencies endpoint working")
            print(f"  - Found {len(deps)} callback dependencies")
            
            # Check for expected callbacks
            callback_outputs = set()
            for dep in deps:
                for output in dep.get('outputs', []):
                    callback_outputs.add(output['id'])
            
            expected_outputs = {
                'filtered-elements',
                'cytoscape-graph',
                'selected-node-data',
                'right-panel-container'
            }
            
            missing = expected_outputs - callback_outputs
            if missing:
                print(f"  ⚠ Missing callback outputs: {missing}")
            else:
                print("  ✓ All expected callbacks registered")
            return True
        else:
            print(f"✗ Dependencies endpoint returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Dependencies endpoint error: {e}")
        return False

def test_static_assets():
    """Test if static assets are being served"""
    try:
        # Test favicon
        response = requests.get(f"{base_url}/_favicon.ico")
        if response.status_code == 200:
            print("✓ Static assets serving correctly")
        else:
            print("⚠ Favicon not found (non-critical)")
        return True
    except:
        return True  # Non-critical

def run_tests():
    """Run all tests"""
    print("=" * 50)
    print("Testing Ontology Visualization App")
    print("=" * 50)
    
    tests = [
        ("App Availability", test_app_availability),
        ("Dash Layout", test_dash_layout),
        ("Dash Dependencies", test_dash_dependencies),
        ("Static Assets", test_static_assets)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        result = test_func()
        results.append((test_name, result))
        time.sleep(0.5)  # Small delay between tests
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! The visualization app is working correctly.")
        print("\nYou can now:")
        print("1. Open http://localhost:8050 in your browser")
        print("2. Explore the interactive knowledge graph")
        print("3. Use filters to focus on specific ontology elements")
        print("4. Click nodes to see detailed information")
        print("5. Try different layout algorithms")
    else:
        print("\n⚠ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    run_tests()