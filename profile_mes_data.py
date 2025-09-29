#!/usr/bin/env python3
"""Comprehensive MES data profiling script with OEE analysis.

This script profiles MES data CSV files to understand data quality,
OEE metrics distributions, and operational patterns.
"""

import argparse
import warnings
from pathlib import Path
from typing import Any, Dict

import pandas as pd

warnings.filterwarnings("ignore")


def load_and_validate_data(filepath: Path) -> pd.DataFrame:
    """Load MES data and perform initial validation."""
    print(f"\n{'='*80}")
    print(f"Loading data from: {filepath}")
    print(f"{'='*80}")

    df = pd.read_csv(filepath)

    # Convert Timestamp to datetime
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    print(f"✓ Loaded {len(df):,} records")
    print(f"✓ Date range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
    print(f"✓ Duration: {(df['Timestamp'].max() - df['Timestamp'].min()).days} days")

    return df


def profile_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Profile data quality issues."""
    print(f"\n{'='*80}")
    print("DATA QUALITY ANALYSIS")
    print(f"{'='*80}")

    quality_issues = {}

    # Check for missing values
    print("\n1. Missing Values:")
    missing = df.isnull().sum()
    missing_pct = df.isnull().sum() / len(df) * 100
    for col in missing[missing > 0].index:
        print(f"   - {col}: {missing[col]:,} ({missing_pct[col]:.1f}%)")
    quality_issues["missing_values"] = missing[missing > 0].to_dict()

    # Check for UNKNOWN/Unknown values
    print("\n2. Unknown/Invalid Values:")
    unknown_counts = {}
    for col in df.columns:
        if df[col].dtype == "object":
            unknown = df[col].isin(["UNKNOWN", "Unknown", "Unknown Product", "N/A", "None"]).sum()
            if unknown > 0:
                unknown_pct = unknown / len(df) * 100
                print(f"   - {col}: {unknown:,} UNKNOWN values ({unknown_pct:.1f}%)")
                unknown_counts[col] = unknown
    quality_issues["unknown_values"] = unknown_counts

    # Check for zero production records
    print("\n3. Zero Production Records:")
    zero_prod = df[(df["GoodUnitsProduced"] == 0) & (df["ScrapUnitsProduced"] == 0)]
    zero_prod_pct = len(zero_prod) / len(df) * 100
    print(f"   - Records with zero production: {len(zero_prod):,} ({zero_prod_pct:.1f}%)")
    quality_issues["zero_production"] = len(zero_prod)

    # Check for invalid OEE scores
    print("\n4. Invalid OEE Scores:")
    invalid_oee = df[(df["OEE_Score"] < 0) | (df["OEE_Score"] > 100)]
    print(f"   - Records with OEE < 0 or > 100: {len(invalid_oee):,}")

    # OEE = 0 but production > 0
    oee_zero_with_prod = df[(df["OEE_Score"] == 0) & (df["GoodUnitsProduced"] > 0)]
    print(f"   - OEE=0 but production>0: {len(oee_zero_with_prod):,}")
    quality_issues["invalid_oee"] = len(invalid_oee) + len(oee_zero_with_prod)

    # Check data consistency
    print("\n5. Data Consistency:")
    # Availability = 100% but machine stopped
    avail_100_stopped = df[(df["Availability_Score"] == 100) & (df["MachineStatus"] == "Stopped")]
    print(f"   - Availability=100% but Status=Stopped: {len(avail_100_stopped):,}")

    # Performance > 100%
    perf_over_100 = df[df["Performance_Score"] > 100]
    print(f"   - Performance > 100%: {len(perf_over_100):,}")

    quality_issues["consistency_issues"] = {
        "avail_100_stopped": len(avail_100_stopped),
        "perf_over_100": len(perf_over_100),
    }

    return quality_issues


def analyze_oee_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Comprehensive OEE analysis."""
    print(f"\n{'='*80}")
    print("OEE METRICS ANALYSIS")
    print(f"{'='*80}")

    oee_analysis = {}

    # Overall OEE statistics
    print("\n1. Overall OEE Distribution:")
    oee_stats = df["OEE_Score"].describe()
    print(f"   Mean:   {oee_stats['mean']:.1f}%")
    print(f"   Median: {oee_stats['50%']:.1f}%")
    print(f"   Std:    {oee_stats['std']:.1f}%")
    print(f"   Min:    {oee_stats['min']:.1f}%")
    print(f"   Max:    {oee_stats['max']:.1f}%")
    print(f"   Q1:     {oee_stats['25%']:.1f}%")
    print(f"   Q3:     {oee_stats['75%']:.1f}%")
    oee_analysis["overall_stats"] = oee_stats.to_dict()

    # OEE components
    print("\n2. OEE Components (Mean):")
    print(f"   Availability: {df['Availability_Score'].mean():.1f}%")
    print(f"   Performance:  {df['Performance_Score'].mean():.1f}%")
    print(f"   Quality:      {df['Quality_Score'].mean():.1f}%")
    oee_analysis["components"] = {
        "availability": df["Availability_Score"].mean(),
        "performance": df["Performance_Score"].mean(),
        "quality": df["Quality_Score"].mean(),
    }

    # OEE by Equipment Type
    print("\n3. OEE by Equipment Type:")
    eq_oee = df.groupby("EquipmentType")["OEE_Score"].agg(["mean", "std", "count"])
    for eq_type, row in eq_oee.iterrows():
        if row["count"] > 0:
            print(f"   {eq_type:12s}: {row['mean']:5.1f}% (±{row['std']:4.1f}%) n={row['count']:,}")
    oee_analysis["by_equipment"] = eq_oee.to_dict("index")

    # OEE by Line
    print("\n4. OEE by Production Line:")
    line_oee = df.groupby("LineID")["OEE_Score"].agg(["mean", "std", "count"])
    for line, row in line_oee.iterrows():
        if row["count"] > 0:
            print(f"   Line {str(line):6s}: {row['mean']:5.1f}% (±{row['std']:4.1f}%) n={row['count']:,}")
    oee_analysis["by_line"] = line_oee.to_dict("index")

    # OEE distribution buckets
    print("\n5. OEE Distribution (% of records):")
    bins = [0, 20, 40, 60, 80, 100]
    labels = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
    df["OEE_Bucket"] = pd.cut(df["OEE_Score"], bins=bins, labels=labels, include_lowest=True)
    oee_dist = df["OEE_Bucket"].value_counts(normalize=True) * 100
    for bucket in labels:
        if bucket in oee_dist.index:
            print(f"   {bucket:8s}: {oee_dist[bucket]:5.1f}%")
    oee_analysis["distribution"] = oee_dist.to_dict()

    # World-class OEE analysis (>85%)
    world_class = df[df["OEE_Score"] >= 85]
    print(f"\n6. World-Class OEE (≥85%): {len(world_class):,} records ({len(world_class)/len(df)*100:.1f}%)")

    return oee_analysis


def analyze_production_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze production metrics."""
    print(f"\n{'='*80}")
    print("PRODUCTION METRICS ANALYSIS")
    print(f"{'='*80}")

    prod_analysis = {}

    # Total production
    print("\n1. Total Production:")
    total_good = df["GoodUnitsProduced"].sum()
    total_scrap = df["ScrapUnitsProduced"].sum()
    total_units = total_good + total_scrap
    scrap_rate = (total_scrap / total_units * 100) if total_units > 0 else 0

    print(f"   Good Units:  {total_good:,}")
    print(f"   Scrap Units: {total_scrap:,}")
    print(f"   Total Units: {total_units:,}")
    print(f"   Scrap Rate:  {scrap_rate:.2f}%")
    prod_analysis["totals"] = {"good": total_good, "scrap": total_scrap, "total": total_units, "scrap_rate": scrap_rate}

    # Production by product
    print("\n2. Production by Product (Top 10):")
    prod_by_product = (
        df.groupby("ProductID")
        .agg({"GoodUnitsProduced": "sum", "ScrapUnitsProduced": "sum"})
        .sort_values("GoodUnitsProduced", ascending=False)
        .head(10)
    )

    for product, row in prod_by_product.iterrows():
        total = row["GoodUnitsProduced"] + row["ScrapUnitsProduced"]
        scrap_pct = (row["ScrapUnitsProduced"] / total * 100) if total > 0 else 0
        print(
            f"   {product:12s}: {row['GoodUnitsProduced']:8,} good, {row['ScrapUnitsProduced']:5,} scrap ({scrap_pct:4.1f}%)"
        )
    prod_analysis["by_product"] = prod_by_product.to_dict("index")

    # Throughput analysis
    print("\n3. Throughput Analysis (units per 5-min interval):")
    throughput_stats = df["GoodUnitsProduced"].describe()
    print(f"   Mean:   {throughput_stats['mean']:.1f}")
    print(f"   Median: {throughput_stats['50%']:.1f}")
    print(f"   Max:    {throughput_stats['max']:.0f}")
    print(f"   Std:    {throughput_stats['std']:.1f}")
    prod_analysis["throughput"] = throughput_stats.to_dict()

    return prod_analysis


def analyze_downtime(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze downtime patterns."""
    print(f"\n{'='*80}")
    print("DOWNTIME ANALYSIS")
    print(f"{'='*80}")

    downtime_analysis = {}

    # Machine status distribution
    print("\n1. Machine Status Distribution:")
    status_dist = df["MachineStatus"].value_counts()
    status_pct = df["MachineStatus"].value_counts(normalize=True) * 100
    for status in status_dist.index:
        print(f"   {status:12s}: {status_dist[status]:6,} ({status_pct[status]:5.1f}%)")
    downtime_analysis["status_distribution"] = status_dist.to_dict()

    # Downtime reasons
    stopped_df = df[df["MachineStatus"] == "Stopped"]
    if len(stopped_df) > 0:
        print("\n2. Downtime Reasons (when Stopped):")
        reasons = stopped_df["DowntimeReason"].value_counts().head(10)
        reason_pct = stopped_df["DowntimeReason"].value_counts(normalize=True).head(10) * 100
        for reason in reasons.index:
            if pd.notna(reason) and reason != "":
                print(f"   {reason:12s}: {reasons[reason]:5,} ({reason_pct[reason]:5.1f}%)")
        downtime_analysis["reasons"] = reasons.to_dict()

    # Downtime by equipment type
    print("\n3. Downtime by Equipment Type:")
    eq_downtime = df[df["MachineStatus"] == "Stopped"].groupby("EquipmentType").size()
    eq_total = df.groupby("EquipmentType").size()
    eq_downtime_pct = (eq_downtime / eq_total * 100).sort_values(ascending=False)
    for eq_type in eq_downtime_pct.index:
        print(f"   {eq_type:12s}: {eq_downtime_pct[eq_type]:5.1f}%")
    downtime_analysis["by_equipment"] = eq_downtime_pct.to_dict()

    return downtime_analysis


def analyze_temporal_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze temporal patterns in the data."""
    print(f"\n{'='*80}")
    print("TEMPORAL PATTERNS ANALYSIS")
    print(f"{'='*80}")

    temporal_analysis = {}

    # Add time-based features
    df["Hour"] = df["Timestamp"].dt.hour
    df["DayOfWeek"] = df["Timestamp"].dt.dayofweek
    df["Date"] = df["Timestamp"].dt.date

    # OEE by hour of day
    print("\n1. OEE by Hour of Day:")
    hourly_oee = df.groupby("Hour")["OEE_Score"].mean().sort_index()
    for hour in range(0, 24, 4):
        if hour in hourly_oee.index:
            print(f"   {hour:02d}:00-{hour+3:02d}:59: {hourly_oee[hour:hour+4].mean():.1f}%")
    temporal_analysis["hourly_oee"] = hourly_oee.to_dict()

    # Daily production trend
    print("\n2. Daily Production Trend:")
    daily_prod = df.groupby("Date")["GoodUnitsProduced"].sum()
    print(f"   Mean daily production: {daily_prod.mean():.0f} units")
    print(f"   Std deviation:         {daily_prod.std():.0f} units")
    print(f"   Min daily production:  {daily_prod.min():.0f} units")
    print(f"   Max daily production:  {daily_prod.max():.0f} units")
    temporal_analysis["daily_production"] = {
        "mean": daily_prod.mean(),
        "std": daily_prod.std(),
        "min": daily_prod.min(),
        "max": daily_prod.max(),
    }

    return temporal_analysis


def generate_summary_report(
    df: pd.DataFrame, filepath: Path, quality: Dict, oee: Dict, production: Dict, downtime: Dict, temporal: Dict
) -> None:
    """Generate a summary report."""
    print(f"\n{'='*80}")
    print("EXECUTIVE SUMMARY")
    print(f"{'='*80}")

    print(f"\nDataset: {filepath.name}")
    print(f"Records: {len(df):,}")
    print(f"Period:  {(df['Timestamp'].max() - df['Timestamp'].min()).days} days")

    # Key metrics
    print("\nKey Performance Indicators:")
    print(
        f"  • Average OEE:        {oee['components']['availability']*oee['components']['performance']*oee['components']['quality']/10000:.1f}%"
    )
    print(f"  • Total Production:   {production['totals']['total']:,} units")
    print(f"  • Overall Scrap Rate: {production['totals']['scrap_rate']:.2f}%")
    print(f"  • Downtime %:         {(df['MachineStatus']=='Stopped').mean()*100:.1f}%")

    # Data quality score
    total_issues = sum(
        [
            len(quality["missing_values"]),
            sum(quality["unknown_values"].values()),
            quality["zero_production"],
            quality["invalid_oee"],
        ]
    )
    quality_score = max(0, 100 - (total_issues / len(df) * 100))
    print(f"\nData Quality Score: {quality_score:.1f}/100")

    # Critical issues
    print("\nCritical Issues:")
    if sum(quality["unknown_values"].values()) > len(df) * 0.1:
        print("  ⚠️  High proportion of UNKNOWN values")
    if quality["zero_production"] > len(df) * 0.5:
        print("  ⚠️  Majority of records show zero production")
    if oee["components"]["availability"] < 50:
        print("  ⚠️  Low availability indicates significant downtime")
    if oee["components"]["performance"] < 50:
        print("  ⚠️  Low performance indicates speed losses")
    if production["totals"]["scrap_rate"] > 10:
        print("  ⚠️  High scrap rate affecting quality")

    # Recommendations
    print("\nRecommendations:")
    if "unknown_values" in quality and quality["unknown_values"]:
        print("  • Fix data collection for fields with UNKNOWN values")
    if quality["zero_production"] > len(df) * 0.2:
        print("  • Investigate periods of zero production")
    if oee["overall_stats"]["std"] > 30:
        print("  • High OEE variability - focus on consistency")
    if len(downtime.get("reasons", {})) > 0:
        top_reason = list(downtime["reasons"].keys())[0] if downtime["reasons"] else "Unknown"
        print(f"  • Address top downtime reason: {top_reason}")


def compare_datasets(df1: pd.DataFrame, df2: pd.DataFrame, name1: str = "Dataset 1", name2: str = "Dataset 2") -> None:
    """Compare two MES datasets."""
    print(f"\n{'='*80}")
    print(f"COMPARISON: {name1} vs {name2}")
    print(f"{'='*80}")

    print("\n1. Size Comparison:")
    print(f"   {name1:20s}: {len(df1):,} records")
    print(f"   {name2:20s}: {len(df2):,} records")

    print("\n2. OEE Comparison:")
    oee1 = df1["OEE_Score"].mean()
    oee2 = df2["OEE_Score"].mean()
    print(f"   {name1:20s}: {oee1:.1f}%")
    print(f"   {name2:20s}: {oee2:.1f}%")
    print(f"   Difference:           {oee2-oee1:+.1f}%")

    print("\n3. Production Comparison:")
    prod1 = df1["GoodUnitsProduced"].sum()
    prod2 = df2["GoodUnitsProduced"].sum()
    print(f"   {name1:20s}: {prod1:,} units")
    print(f"   {name2:20s}: {prod2:,} units")

    print("\n4. Data Quality Comparison:")
    unknown1 = df1["ProductID"].isin(["UNKNOWN", "Unknown"]).mean() * 100
    unknown2 = df2["ProductID"].isin(["UNKNOWN", "Unknown"]).mean() * 100
    print("   Unknown Products:")
    print(f"   {name1:20s}: {unknown1:.1f}%")
    print(f"   {name2:20s}: {unknown2:.1f}%")

    zero1 = ((df1["GoodUnitsProduced"] == 0) & (df1["ScrapUnitsProduced"] == 0)).mean() * 100
    zero2 = ((df2["GoodUnitsProduced"] == 0) & (df2["ScrapUnitsProduced"] == 0)).mean() * 100
    print("   Zero Production:")
    print(f"   {name1:20s}: {zero1:.1f}%")
    print(f"   {name2:20s}: {zero2:.1f}%")


def main():
    """Main profiling function."""
    parser = argparse.ArgumentParser(description="Profile MES data with OEE analysis")
    parser.add_argument("filepath", type=str, help="Path to MES CSV file to profile")
    parser.add_argument("--compare", type=str, help="Optional second file to compare against")
    parser.add_argument("--output", type=str, help="Save detailed report to file")

    args = parser.parse_args()

    # Load and profile primary dataset
    filepath = Path(args.filepath)
    if not filepath.exists():
        print(f"Error: File {filepath} not found")
        return 1

    df = load_and_validate_data(filepath)

    # Run all analyses
    quality_analysis = profile_data_quality(df)
    oee_analysis = analyze_oee_metrics(df)
    production_analysis = analyze_production_metrics(df)
    downtime_analysis = analyze_downtime(df)
    temporal_analysis = analyze_temporal_patterns(df)

    # Generate summary
    generate_summary_report(
        df, filepath, quality_analysis, oee_analysis, production_analysis, downtime_analysis, temporal_analysis
    )

    # Compare if second file provided
    if args.compare:
        compare_path = Path(args.compare)
        if compare_path.exists():
            df2 = load_and_validate_data(compare_path)
            compare_datasets(df, df2, filepath.name, compare_path.name)

    # Save report if requested
    if args.output:
        print(f"\n✓ Report saved to {args.output}")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
