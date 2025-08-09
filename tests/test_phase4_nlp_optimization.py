"""
Test Phase 4: Natural Language Patterns and Optimization
Tests NLP query handling, multi-objective optimization, and disambiguation
"""

import sys
import os
import yaml
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_nl_patterns():
    """Test natural language pattern loading and structure"""
    print("=" * 60)
    print("TESTING PHASE 4: NATURAL LANGUAGE PATTERNS")
    print("=" * 60)
    
    # Test 1: Load patterns file
    print("\n1. PATTERN FILE LOADING")
    print("-" * 40)
    
    pattern_file = "twin/nl_patterns.yaml"
    assert os.path.exists(pattern_file), f"Pattern file not found: {pattern_file}"
    
    with open(pattern_file, 'r') as f:
        patterns = yaml.safe_load(f)
    
    assert patterns is not None, "Failed to load patterns"
    assert "patterns" in patterns, "Missing 'patterns' section"
    assert "parameter_mappings" in patterns, "Missing 'parameter_mappings' section"
    assert "objective_mappings" in patterns, "Missing 'objective_mappings' section"
    
    print(f"✓ Loaded pattern file with {len(patterns)} sections")
    
    # Test 2: Validate pattern categories
    print("\n2. PATTERN CATEGORIES")
    print("-" * 40)
    
    expected_categories = ["impact", "optimize", "diagnose", "compare", "simulate", "recommend"]
    for category in expected_categories:
        assert category in patterns["patterns"], f"Missing category: {category}"
        print(f"✓ Found category: {category} with {len(patterns['patterns'][category])} patterns")
    
    # Test 3: Validate pattern structure
    print("\n3. PATTERN STRUCTURE VALIDATION")
    print("-" * 40)
    
    for category, category_patterns in patterns["patterns"].items():
        for pattern_def in category_patterns:
            assert "pattern" in pattern_def, f"Missing 'pattern' in {category}"
            assert "operation" in pattern_def, f"Missing 'operation' in {category}"
            assert "examples" in pattern_def, f"Missing 'examples' in {category}"
            
    print("✓ All patterns have required fields")
    
    # Test 4: Parameter mappings
    print("\n4. PARAMETER MAPPINGS")
    print("-" * 40)
    
    param_mappings = patterns["parameter_mappings"]
    expected_params = ["maintenance", "quality", "performance", "materials", "operators"]
    
    for param_type in expected_params:
        assert param_type in param_mappings, f"Missing parameter mapping: {param_type}"
    
    print(f"✓ Found {len(param_mappings)} parameter mapping categories")
    
    # Test 5: Objective mappings
    print("\n5. OBJECTIVE MAPPINGS")
    print("-" * 40)
    
    obj_mappings = patterns["objective_mappings"]
    expected_objectives = ["efficiency", "production", "quality", "cost", "reliability"]
    
    for obj_type in expected_objectives:
        assert obj_type in obj_mappings, f"Missing objective mapping: {obj_type}"
    
    print(f"✓ Found {len(obj_mappings)} objective mapping categories")
    
    print("\n✅ NATURAL LANGUAGE PATTERNS TEST PASSED!")
    return True


def test_recommendation_engine():
    """Test multi-objective optimization engine"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 4: RECOMMENDATION ENGINE")
    print("=" * 60)
    
    from twin.recommendation_engine import (
        RecommendationEngine,
        Objective,
        OptimizationResult
    )
    
    engine = RecommendationEngine()
    print("\n✓ RecommendationEngine initialized")
    
    # Test 1: Single objective optimization
    print("\n1. SINGLE OBJECTIVE OPTIMIZATION")
    print("-" * 40)
    
    objectives = [
        Objective("oee", "maximize", "mean_oee")
    ]
    
    results = engine.optimize(
        objectives=objectives,
        population_size=10,
        generations=5,
        verbose=False
    )
    
    assert len(results) > 0, "No optimization results"
    assert isinstance(results[0], OptimizationResult), "Invalid result type"
    assert results[0].feasible, "Solution not feasible"
    
    print(f"✓ Found {len(results)} solutions")
    print(f"  Best OEE objective value: {-results[0].objectives['oee']:.3f}")
    
    # Test 2: Multi-objective optimization
    print("\n2. MULTI-OBJECTIVE OPTIMIZATION")
    print("-" * 40)
    
    objectives = [
        Objective("energy", "minimize", "energy_per_unit"),
        Objective("throughput", "maximize", "total_good_units"),
        Objective("quality", "minimize", "scrap_rate")
    ]
    
    results = engine.optimize(
        objectives=objectives,
        population_size=15,
        generations=10,
        verbose=False
    )
    
    assert len(results) > 0, "No Pareto solutions found"
    
    # Check Pareto optimality
    pareto_front = [r for r in results if r.pareto_rank == 1]
    assert len(pareto_front) > 0, "No solutions in Pareto front"
    
    print(f"✓ Found {len(pareto_front)} Pareto-optimal solutions")
    print(f"  Solutions span {len(objectives)} objectives")
    
    # Test 3: Constrained optimization
    print("\n3. CONSTRAINED OPTIMIZATION")
    print("-" * 40)
    
    constraints = {
        "micro_stop_probability": (0.05, 0.15),  # Tight constraint
        "scrap_multiplier": (1.0, 1.5)  # Quality constraint
    }
    
    results = engine.optimize(
        objectives=[Objective("oee", "maximize", "mean_oee")],
        constraints=constraints,
        population_size=10,
        generations=5,
        verbose=False
    )
    
    # Check constraints are satisfied
    for result in results:
        if result.feasible:
            for param, (min_val, max_val) in constraints.items():
                assert min_val <= result.parameters[param] <= max_val, \
                    f"Constraint violated for {param}"
    
    print(f"✓ Constraints satisfied in {sum(1 for r in results if r.feasible)} solutions")
    
    # Test 4: Scenario-based recommendation
    print("\n4. SCENARIO-BASED RECOMMENDATION")
    print("-" * 40)
    
    scenarios = [
        "optimize for energy efficiency",
        "maximize throughput",
        "reduce maintenance costs"
    ]
    
    for scenario in scenarios:
        recommendation = engine.recommend_for_scenario(
            scenario=scenario,
            save_recommendation=False
        )
        
        assert "error" not in recommendation, f"Error in scenario: {scenario}"
        assert "parameters" in recommendation
        assert "expected_improvements" in recommendation
        
        print(f"✓ Generated recommendation for: '{scenario}'")
    
    # Test 5: Genetic operators
    print("\n5. GENETIC OPERATORS TEST")
    print("-" * 40)
    
    import numpy as np
    
    # Test crossover
    parent1 = np.array([0.1, 0.85, 2.0, 0.85, 0.5])
    parent2 = np.array([0.2, 0.90, 1.5, 0.90, 0.4])
    
    child1, child2 = engine._crossover(parent1, parent2)
    
    assert len(child1) == len(parent1), "Crossover changed chromosome length"
    assert len(child2) == len(parent2), "Crossover changed chromosome length"
    
    print("✓ Crossover operator working")
    
    # Test mutation
    individual = np.array([0.15, 0.85, 2.0, 0.85, 0.5])
    mutated = engine._mutate(individual)
    
    assert len(mutated) == len(individual), "Mutation changed chromosome length"
    
    print("✓ Mutation operator working")
    
    # Test 6: Pareto dominance
    print("\n6. PARETO DOMINANCE TEST")
    print("-" * 40)
    
    # Test dominance checking
    fitness1 = {"obj1": 1.0, "obj2": 2.0}
    fitness2 = {"obj1": 2.0, "obj2": 3.0}
    fitness3 = {"obj1": 1.5, "obj2": 1.5}
    
    assert engine._dominates(fitness1, fitness2), "Failed to identify dominance"
    assert not engine._dominates(fitness2, fitness1), "Incorrect dominance"
    assert not engine._dominates(fitness1, fitness3), "Incorrect non-dominance"
    
    print("✓ Pareto dominance logic correct")
    
    print("\n✅ RECOMMENDATION ENGINE TEST PASSED!")
    return True


def test_disambiguation():
    """Test disambiguation helper"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 4: DISAMBIGUATION HELPER")
    print("=" * 60)
    
    from twin.disambiguation import DisambiguationHelper
    
    helper = DisambiguationHelper()
    print("\n✓ DisambiguationHelper initialized")
    
    # Test 1: Entity identification
    print("\n1. ENTITY IDENTIFICATION")
    print("-" * 40)
    
    test_queries = {
        "What's wrong with Line 2?": {"lines": ["LINE2"]},
        "Compare all shifts": {"shifts": ["shift1", "shift2", "shift3"]},
        "Optimize filler performance": {"equipment": ["FIL"]},
        "Improve quality and OEE": {"metrics": ["quality", "oee"]}
    }
    
    for query, expected in test_queries.items():
        context = helper.get_query_context(query)
        entities = context["entities"]
        
        for entity_type, expected_values in expected.items():
            assert entity_type in entities, f"Missing entity type: {entity_type}"
            for value in expected_values:
                assert value in entities[entity_type], \
                    f"Missing {value} in {entity_type} for query: {query}"
        
        print(f"✓ Correctly identified entities in: '{query[:30]}...'")
    
    # Test 2: Timeframe identification
    print("\n2. TIMEFRAME IDENTIFICATION")
    print("-" * 40)
    
    time_queries = {
        "Show data from today": "today",
        "Compare yesterday's performance": "yesterday",
        "Analyze last week": "last week",
        "What happened this month?": "this month"
    }
    
    for query, expected_pattern in time_queries.items():
        context = helper.get_query_context(query)
        timeframe = context["timeframe"]
        
        if timeframe["explicit"]:
            assert timeframe["explicit"]["pattern"] == expected_pattern, \
                f"Wrong timeframe for: {query}"
            print(f"✓ Identified timeframe '{expected_pattern}' in query")
    
    # Test 3: Parameter hints
    print("\n3. PARAMETER HINTS")
    print("-" * 40)
    
    param_queries = {
        "reduce micro-stops": ["micro_stop_probability"],
        "improve material flow": ["material_reliability"],
        "better quality control": ["scrap_multiplier"],
        "optimize cascade effects": ["cascade_sensitivity"]
    }
    
    for query, expected_params in param_queries.items():
        context = helper.get_query_context(query)
        hints = context["parameter_hints"]
        
        for param in expected_params:
            assert param in hints["likely_parameters"], \
                f"Missing parameter hint {param} for: {query}"
        
        print(f"✓ Identified parameters for: '{query}'")
    
    # Test 4: Entity resolution
    print("\n4. ENTITY RESOLUTION")
    print("-" * 40)
    
    resolutions = [
        ("line", "line 1", "LINE1"),
        ("line", "line2", "LINE2"),
        ("equipment", "filler", "FIL"),
        ("equipment", "packer", "PCK"),
        ("shift", "morning", "shift1"),
        ("shift", "night", "shift3")
    ]
    
    for entity_type, reference, expected in resolutions:
        resolved = helper.resolve_entity(entity_type, reference)
        assert resolved == expected, \
            f"Failed to resolve {reference} to {expected}"
    
    print(f"✓ Successfully resolved {len(resolutions)} entity references")
    
    # Test 5: Suggested clarifications
    print("\n5. SUGGESTED CLARIFICATIONS")
    print("-" * 40)
    
    ambiguous_queries = [
        "Which line is better?",  # Missing timeframe
        "Optimize the system",  # Missing objectives
        "Compare performance",  # Missing entities
        "Improve results"  # Missing specifics
    ]
    
    for query in ambiguous_queries:
        context = helper.get_query_context(query)
        suggestions = context["suggested_clarifications"]
        
        assert len(suggestions) > 0, \
            f"No clarifications suggested for ambiguous query: {query}"
        
        print(f"✓ Generated {len(suggestions)} clarifications for: '{query[:30]}...'")
    
    # Test 6: Context structure
    print("\n6. CONTEXT STRUCTURE")
    print("-" * 40)
    
    context = helper.get_query_context("Test query")
    
    required_fields = [
        "query", "timestamp", "entities", "timeframe",
        "available_data", "current_state", "parameter_hints",
        "suggested_clarifications"
    ]
    
    for field in required_fields:
        assert field in context, f"Missing required field: {field}"
    
    print(f"✓ Context contains all {len(required_fields)} required fields")
    
    print("\n✅ DISAMBIGUATION HELPER TEST PASSED!")
    return True


def test_integration():
    """Test integration between NLP and optimization components"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 4: COMPONENT INTEGRATION")
    print("=" * 60)
    
    from twin.recommendation_engine import RecommendationEngine
    from twin.disambiguation import DisambiguationHelper
    
    # Initialize components
    engine = RecommendationEngine()
    helper = DisambiguationHelper()
    
    print("\n✓ Components initialized")
    
    # Test 1: Query to optimization flow
    print("\n1. QUERY TO OPTIMIZATION FLOW")
    print("-" * 40)
    
    query = "optimize for energy efficiency while maintaining quality"
    
    # Get context
    context = helper.get_query_context(query)
    
    # Generate recommendation based on context
    recommendation = engine.recommend_for_scenario(
        scenario=query,
        save_recommendation=False
    )
    
    assert "error" not in recommendation
    assert "parameters" in recommendation
    assert "expected_improvements" in recommendation
    
    print(f"✓ Successfully processed query: '{query[:40]}...'")
    print(f"  Generated {len(recommendation['parameters'])} parameter changes")
    
    # Test 2: Entity-specific optimization
    print("\n2. ENTITY-SPECIFIC OPTIMIZATION")
    print("-" * 40)
    
    query = "improve Line 2 performance"
    context = helper.get_query_context(query)
    
    # Check entity was identified
    assert "LINE2" in context["entities"]["lines"]
    
    # Generate targeted recommendation
    recommendation = engine.recommend_for_scenario(
        scenario=f"improve performance for {context['entities']['lines'][0]}",
        save_recommendation=False
    )
    
    assert "error" not in recommendation
    print(f"✓ Generated recommendation for: {context['entities']['lines'][0]}")
    
    # Test 3: Multi-metric optimization
    print("\n3. MULTI-METRIC OPTIMIZATION")
    print("-" * 40)
    
    query = "balance throughput, quality, and energy consumption"
    context = helper.get_query_context(query)
    
    # Check multiple metrics identified
    identified_metrics = context["entities"]["metrics"]
    assert len(identified_metrics) >= 2, "Failed to identify multiple metrics"
    
    print(f"✓ Identified {len(identified_metrics)} metrics for optimization")
    
    print("\n✅ COMPONENT INTEGRATION TEST PASSED!")
    return True


if __name__ == "__main__":
    try:
        # Test NL patterns
        test_nl_patterns()
        
        # Test recommendation engine
        test_recommendation_engine()
        
        # Test disambiguation
        test_disambiguation()
        
        # Test integration
        test_integration()
        
        print("\n" + "=" * 60)
        print("✅ ALL PHASE 4 TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)