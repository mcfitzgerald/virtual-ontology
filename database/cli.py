"""CLI for database operations"""

import click
from pathlib import Path
from database.manager import TwinDatabaseManager
from database.integration import TwinDatabaseIntegration


@click.group()
def cli():
    """Twin Database Management CLI"""
    pass


@cli.command()
def init():
    """Initialize database with all tables"""
    manager = TwinDatabaseManager()
    manager.create_all_tables()
    click.echo("✓ Database initialized")


@cli.command()
@click.argument('csv_path', type=click.Path(exists=True))
def import_historical(csv_path):
    """Import historical MES data from CSV"""
    manager = TwinDatabaseManager()
    manager.import_historical_data(Path(csv_path))


@cli.command()
def sync_manifests():
    """Sync configurations from manifest YAMLs"""
    manager = TwinDatabaseManager()
    manager.sync_configurations_from_manifests()


@cli.command()
@click.option('--days', default=1, help='Days to simulate')
@click.option('--type', 'run_type', default='experiment', help='Run type (baseline, experiment, optimization)')
def run_simulation(days, run_type):
    """Run simulation and store in database"""
    integration = TwinDatabaseIntegration()
    run_id = integration.run_simulation_to_db(
        run_type=run_type,
        days=days
    )
    click.echo(f"✓ Simulation complete: {run_id}")


@cli.command()
@click.option('--name', prompt='Experiment name', help='Name of the experiment')
@click.option('--hypothesis', prompt='Hypothesis', help='Experiment hypothesis')
@click.option('--days', default=1, help='Days to simulate')
@click.option('--runs', default=3, help='Number of test runs')
def run_experiment(name, hypothesis, days, runs):
    """Run an experiment with parameter changes"""
    
    # For now, use example parameter changes
    # In production, these would come from user input or config
    parameter_changes = {
        'mtbf_multiplier': 1.2,  # Improve reliability by 20%
        'performance_multiplier': 1.1  # Improve performance by 10%
    }
    
    integration = TwinDatabaseIntegration()
    experiment_id = integration.run_experiment(
        name=name,
        hypothesis=hypothesis,
        parameter_changes=parameter_changes,
        days=days,
        num_runs=runs
    )
    click.echo(f"✓ Experiment complete: {experiment_id}")


@cli.command()
@click.option('--min-confidence', default=0.7, help='Minimum confidence threshold')
def discover_patterns(min_confidence):
    """Discover patterns from experiments"""
    integration = TwinDatabaseIntegration()
    patterns = integration.discover_patterns(min_confidence=min_confidence)
    
    if patterns:
        click.echo(f"✓ Found {len(patterns)} patterns:")
        for pattern in patterns:
            click.echo(f"  - {pattern.pattern_name} (confidence: {pattern.confidence_score:.2f})")
    else:
        click.echo("No patterns discovered yet. Run more experiments.")


@cli.command()
def generate_recommendations():
    """Generate recommendations from patterns"""
    integration = TwinDatabaseIntegration()
    recommendations = integration.generate_recommendations()
    
    if recommendations:
        click.echo(f"✓ Generated {len(recommendations)} recommendations:")
        for rec in recommendations:
            click.echo(f"  - {rec.recommendation_type} (confidence: {rec.confidence:.2f})")
    else:
        click.echo("No recommendations available. Discover patterns first.")


@cli.command()
def status():
    """Show database status"""
    from sqlmodel import Session, select, func
    
    manager = TwinDatabaseManager()
    
    with Session(manager.engine) as session:
        # Count records in each table
        from database.models import (
            HistoricalMESData, EquipmentConfig, ProductConfig,
            TwinRun, SimulationData, Experiment, DiscoveredPattern
        )
        
        click.echo("\n=== Database Status ===")
        click.echo(f"Database: {manager.db_path}")
        click.echo(f"Ontology version: {manager.get_ontology_version()}")
        click.echo(f"Manifest version: {manager.get_manifest_version()}")
        
        click.echo("\n=== Table Counts ===")
        
        # Historical data
        count = session.exec(select(func.count(HistoricalMESData.id))).one()
        click.echo(f"Historical MES Data: {count:,} records")
        
        # Configurations
        count = session.exec(select(func.count(EquipmentConfig.equipment_id))).one()
        click.echo(f"Equipment Configs: {count} items")
        
        count = session.exec(select(func.count(ProductConfig.product_id))).one()
        click.echo(f"Product Configs: {count} items")
        
        # Simulation data
        count = session.exec(select(func.count(TwinRun.run_id))).one()
        click.echo(f"Twin Runs: {count} runs")
        
        count = session.exec(select(func.count(SimulationData.id))).one()
        click.echo(f"Simulation Data: {count:,} records")
        
        # Experiments
        count = session.exec(select(func.count(Experiment.experiment_id))).one()
        click.echo(f"Experiments: {count} experiments")
        
        count = session.exec(select(func.count(DiscoveredPattern.pattern_id))).one()
        click.echo(f"Discovered Patterns: {count} patterns")
        
        # Recent runs
        recent_runs = session.exec(
            select(TwinRun)
            .order_by(TwinRun.started_at.desc())
            .limit(5)
        ).all()
        
        if recent_runs:
            click.echo("\n=== Recent Runs ===")
            for run in recent_runs:
                kpi_summary = {}
                if run.kpi_summary_json:
                    import json
                    kpi_summary = json.loads(run.kpi_summary_json)
                
                click.echo(f"- {run.run_id}")
                click.echo(f"  Type: {run.run_type}, Status: {run.status}")
                if kpi_summary:
                    click.echo(f"  OEE: {kpi_summary.get('mean_oee', 0):.1f}%")


if __name__ == '__main__':
    cli()