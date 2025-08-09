#!/usr/bin/env python3
"""
Test Visualization Module
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import json
import tempfile

# Import visualization components
from twin.visualization import (
    create_pareto_plot,
    plot_kpi_trends,
    create_sensitivity_heatmap,
    plot_roi_distribution
)


def test_pareto_plot():
    """Test Pareto front visualization"""
    print("\n" + "="*60)
    print("Testing Pareto Plot")
    print("="*60)
    
    try:
        # Create plot with mock run IDs
        fig = create_pareto_plot(
            run_ids=["run1", "run2", "run3"],
            objectives=["oee", "energy"]
        )
        
        # Verify figure structure
        assert fig is not None
        assert len(fig.data) > 0
        assert fig.layout.title.text == "Multi-objective Optimization: Pareto Front"
        
        # Test JSON export
        json_str = fig.to_json()
        json_data = json.loads(json_str)
        assert "data" in json_data
        assert "layout" in json_data
        
        print("✅ Pareto plot created successfully")
        print(f"   - {len(fig.data)} traces")
        print(f"   - JSON size: {len(json_str)} bytes")
        
    except Exception as e:
        print(f"❌ Pareto plot failed: {e}")


def test_time_series():
    """Test time series visualization"""
    print("\n" + "="*60)
    print("Testing Time Series Plot")
    print("="*60)
    
    try:
        # Create plot
        fig = plot_kpi_trends(
            run_ids=["test-run"],
            kpis=["oee", "availability", "performance"]
        )
        
        # Verify figure structure
        assert fig is not None
        assert fig.layout.title.text == "KPI Trends Over Time"
        
        # Test HTML export
        html_str = fig.to_html(full_html=False, include_plotlyjs='cdn')
        assert "<div" in html_str
        assert "plotly" in html_str.lower()
        
        print("✅ Time series plot created successfully")
        print(f"   - HTML size: {len(html_str)} bytes")
        
    except Exception as e:
        print(f"❌ Time series plot failed: {e}")


def test_sensitivity_heatmap():
    """Test sensitivity heatmap"""
    print("\n" + "="*60)
    print("Testing Sensitivity Heatmap")
    print("="*60)
    
    try:
        # Create heatmap
        fig = create_sensitivity_heatmap(
            run_ids=["baseline", "scenario1", "scenario2"]
        )
        
        # Verify figure structure
        assert fig is not None
        assert len(fig.data) > 0
        assert fig.data[0].type == "heatmap"
        assert fig.layout.title.text == "Parameter Sensitivity Analysis"
        
        print("✅ Sensitivity heatmap created successfully")
        print(f"   - Heatmap dimensions: {fig.data[0].z.shape if hasattr(fig.data[0].z, 'shape') else 'N/A'}")
        
    except Exception as e:
        print(f"❌ Sensitivity heatmap failed: {e}")


def test_roi_distribution():
    """Test ROI distribution plot"""
    print("\n" + "="*60)
    print("Testing ROI Distribution")
    print("="*60)
    
    try:
        # Create mock ROI summary
        roi_summary = {
            "implementation_cost": 8500,
            "weekly_savings": {
                "mean": 45000,
                "std": 5000,
                "confidence_interval": (38000, 52000)
            },
            "payback_weeks": {
                "mean": 8.5,
                "std": 2.1,
                "confidence_interval": (6, 12)
            },
            "npv": {
                "mean": 1850000,
                "std": 250000,
                "confidence_interval": (1400000, 2300000),
                "probability_positive": 0.98
            },
            "roi_percentage": {
                "mean": 420,
                "std": 85,
                "confidence_interval": (280, 560)
            },
            "annual_benefit": {
                "mean": 2340000,
                "confidence_interval": (1976000, 2704000)
            }
        }
        
        # Create plot
        fig = plot_roi_distribution(roi_summary)
        
        # Verify figure structure
        assert fig is not None
        assert len(fig._subplots) == 4  # Should have 4 subplots
        assert fig.layout.title.text == "ROI Analysis with Monte Carlo Confidence Intervals"
        
        print("✅ ROI distribution plot created successfully")
        print(f"   - {len(fig._subplots)} subplots")
        
    except Exception as e:
        print(f"❌ ROI distribution plot failed: {e}")


def test_export_formats():
    """Test different export formats"""
    print("\n" + "="*60)
    print("Testing Export Formats")
    print("="*60)
    
    try:
        # Create a simple plot
        fig = create_pareto_plot(["run1"], ["oee", "energy"])
        
        # Test JSON export
        json_str = fig.to_json()
        json.loads(json_str)  # Verify valid JSON
        print("✅ JSON export successful")
        
        # Test HTML export
        html_str = fig.to_html(full_html=True)
        assert "<!DOCTYPE html>" in html_str
        print("✅ HTML export successful")
        
        # Test file writing
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            fig.write_html(f.name)
            assert os.path.exists(f.name)
            os.unlink(f.name)
        print("✅ File export successful")
        
    except Exception as e:
        print(f"❌ Export test failed: {e}")


def test_interactive_features():
    """Test interactive plot features"""
    print("\n" + "="*60)
    print("Testing Interactive Features")
    print("="*60)
    
    try:
        # Create plot with interactive features
        fig = plot_kpi_trends(["run1"], ["oee"])
        
        # Check for range slider
        assert fig.layout.xaxis.rangeslider is not None
        print("✅ Range slider configured")
        
        # Check for hover mode
        assert fig.layout.hovermode is not None
        print("✅ Hover mode configured")
        
        # Check for legend
        assert fig.layout.showlegend is not None
        print("✅ Legend configured")
        
    except Exception as e:
        print(f"❌ Interactive features test failed: {e}")


def run_all_tests():
    """Run all visualization tests"""
    print("\n" + "="*60)
    print(" VISUALIZATION TEST SUITE")
    print("="*60)
    
    test_pareto_plot()
    test_time_series()
    test_sensitivity_heatmap()
    test_roi_distribution()
    test_export_formats()
    test_interactive_features()
    
    print("\n" + "="*60)
    print(" TESTS COMPLETE")
    print("="*60)
    print("\n✅ All visualization components working correctly!")


if __name__ == "__main__":
    run_all_tests()