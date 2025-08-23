"""Integration with twin model"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import simpy
from sqlmodel import Session
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.manager import TwinDatabaseManager
from database.repositories import *
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction.mes_transducer import MESTransducer

# Import configuration
try:
    from config.config_loader import ConfigLoader
    _db_config = ConfigLoader.load_config('database')
except:
    # Fallback for testing
    _db_config = {'testing': {'base_seed': 42}}


class TwinDatabaseIntegration:
    """Integrate twin model with database"""
    
    def __init__(self, db_manager: Optional[TwinDatabaseManager] = None):
        self.db_manager = db_manager or TwinDatabaseManager()
        
    def run_simulation_to_db(self,
                            run_type: str = "experiment",
                            parameters: Dict[str, Any] = None,
                            days: int = 1,
                            parent_run_id: Optional[str] = None) -> str:
        """Run simulation and store results in database"""
        
        parameters = parameters or {}
        
        # Get versions
        ontology_version = self.db_manager.get_ontology_version()
        manifest_version = self.db_manager.get_manifest_version()
        
        with Session(self.db_manager.engine) as session:
            # Create run record
            run_repo = TwinRunRepository(session)
            run = run_repo.create_run(
                run_type=run_type,
                ontology_version=ontology_version,
                manifest_version=manifest_version,
                parameters=parameters,
                parent_run_id=parent_run_id
            )
            
            try:
                # Update status to running
                run_repo.update_run_status(run.run_id, "running")
                
                # Build and run model
                from pathlib import Path
                builder = OntologyDrivenModelBuilder(
                    Path(self.db_manager.ontology_path),
                    Path(self.db_manager.manifest_dir)
                )
                
                env = simpy.Environment()
                model = builder.build_model(env)
                
                # Run simulation
                env.run(until=days * 24 * 60)
                
                # Collect observables
                all_observables = []
                for primitive_id, primitive in builder.primitives.items():
                    if hasattr(primitive, 'observables'):
                        for obs in primitive.observables:
                            obs['primitive_id'] = primitive_id
                            obs['primitive_type'] = type(primitive).__name__
                            all_observables.append(obs)
                
                # Transduce to MES format
                transducer = MESTransducer()
                mes_df = transducer.process_observables(
                    all_observables,
                    builder.manifests
                )
                
                # Store simulation data
                sim_repo = SimulationDataRepository(session)
                sim_repo.store_simulation_data(run.run_id, mes_df)
                
                # Calculate KPIs
                kpi_summary = sim_repo.calculate_kpi_snapshot(run.run_id)
                
                # Create KPI snapshot
                kpi_repo = KPIRepository(session)
                kpi_repo.create_kpi_snapshot(
                    run_id=run.run_id,
                    entity_type="overall",
                    entity_id="LINE1",
                    kpis=kpi_summary,
                    period_start=datetime.utcnow(),
                    period_end=datetime.utcnow()
                )
                
                # Update run as completed
                run_repo.update_run_status(
                    run.run_id, 
                    "completed",
                    kpi_summary
                )
                
                print(f"✓ Simulation complete: {run.run_id}")
                print(f"  Mean OEE: {kpi_summary.get('mean_oee', 0):.1f}%")
                print(f"  Total Good Units: {kpi_summary.get('total_good_units', 0):,}")
                
                return run.run_id
                
            except Exception as e:
                run_repo.update_run_status(run.run_id, "failed")
                raise e
    
    def run_experiment(self,
                      name: str,
                      hypothesis: str,
                      parameter_changes: Dict[str, Any],
                      days: int = 1,
                      num_runs: int = 3) -> str:
        """Run an experiment with parameter changes"""
        
        with Session(self.db_manager.engine) as session:
            # Get baseline run
            run_repo = TwinRunRepository(session)
            baseline = run_repo.get_baseline_run()
            
            if not baseline:
                # Create baseline first
                print("Creating baseline run...")
                baseline_id = self.run_simulation_to_db(
                    run_type="baseline",
                    days=days
                )
                baseline = session.get(TwinRun, baseline_id)
            
            # Create experiment
            exp_repo = ExperimentRepository(session)
            experiment = exp_repo.create_experiment(
                name=name,
                hypothesis=hypothesis,
                baseline_run_id=baseline.run_id,
                parameter_changes=parameter_changes
            )
            
            print(f"✓ Created experiment: {experiment.experiment_id}")
            
            # Run test simulations
            test_run_ids = []
            for i in range(num_runs):
                print(f"Running test {i+1}/{num_runs}...")
                
                # Apply parameter changes
                test_params = parameter_changes.copy()
                base_seed = _db_config.get('testing', {}).get('base_seed', 42)
                test_params['seed'] = base_seed + i  # Different seeds from config
                
                run_id = self.run_simulation_to_db(
                    run_type="experiment",
                    parameters=test_params,
                    days=days,
                    parent_run_id=baseline.run_id
                )
                
                test_run_ids.append(run_id)
                exp_repo.add_test_run(experiment.experiment_id, run_id)
            
            # Analyze results
            results_summary = self._analyze_experiment_results(
                session, baseline.run_id, test_run_ids
            )
            
            # Complete experiment
            conclusion = self._generate_conclusion(results_summary)
            exp_repo.complete_experiment(
                experiment.experiment_id,
                results_summary,
                conclusion
            )
            
            print(f"✓ Experiment complete: {experiment.experiment_id}")
            print(f"  Conclusion: {conclusion}")
            
            return experiment.experiment_id
    
    def _analyze_experiment_results(self,
                                   session: Session,
                                   baseline_id: str,
                                   test_run_ids: List[str]) -> Dict[str, Any]:
        """Analyze experiment results"""
        
        kpi_repo = KPIRepository(session)
        comparisons = []
        
        for test_id in test_run_ids:
            try:
                comparison = kpi_repo.create_comparison(baseline_id, test_id)
                comparisons.append({
                    'run_id': test_id,
                    'oee_delta': comparison.oee_delta,
                    'production_delta': comparison.production_delta
                })
            except Exception as e:
                print(f"Warning: Could not compare {test_id}: {e}")
        
        # Calculate average improvements
        if comparisons:
            avg_oee_delta = sum(c['oee_delta'] for c in comparisons) / len(comparisons)
            avg_production_delta = sum(c['production_delta'] for c in comparisons) / len(comparisons)
        else:
            avg_oee_delta = 0
            avg_production_delta = 0
        
        return {
            'num_runs': len(test_run_ids),
            'comparisons': comparisons,
            'avg_oee_delta': avg_oee_delta,
            'avg_production_delta': avg_production_delta
        }
    
    def _generate_conclusion(self, results: Dict[str, Any]) -> str:
        """Generate conclusion from experiment results"""
        
        oee_delta = results.get('avg_oee_delta', 0)
        production_delta = results.get('avg_production_delta', 0)
        
        if oee_delta > 5:
            return f"Significant improvement: +{oee_delta:.1f}% OEE, +{production_delta:,} units"
        elif oee_delta > 0:
            return f"Minor improvement: +{oee_delta:.1f}% OEE, +{production_delta:,} units"
        elif oee_delta < -5:
            return f"Significant degradation: {oee_delta:.1f}% OEE, {production_delta:,} units"
        else:
            return f"No significant change: {oee_delta:.1f}% OEE, {production_delta:,} units"
    
    def discover_patterns(self, 
                         min_confidence: float = 0.7) -> List[DiscoveredPattern]:
        """Discover patterns from completed experiments"""
        
        with Session(self.db_manager.engine) as session:
            # Query completed experiments
            statement = select(Experiment).where(
                Experiment.status == "completed"
            )
            experiments = session.exec(statement).all()
            
            patterns = []
            pattern_repo = PatternRepository(session)
            
            # Analyze each experiment for patterns
            for exp in experiments:
                if not exp.results_summary_json:
                    continue
                    
                results = json.loads(exp.results_summary_json)
                
                # Look for significant improvements
                if results.get('avg_oee_delta', 0) > 5:
                    pattern = pattern_repo.create_pattern(
                        pattern_type="correlation",
                        pattern_name=f"Parameter set improves OEE",
                        description=f"Parameters from {exp.experiment_name} improve OEE by {results['avg_oee_delta']:.1f}%",
                        evidence=results,
                        experiment_ids=[exp.experiment_id],
                        confidence_score=min(0.9, results['avg_oee_delta'] / 10)
                    )
                    patterns.append(pattern)
            
            print(f"✓ Discovered {len(patterns)} patterns")
            return patterns
    
    def generate_recommendations(self) -> List[ParameterRecommendation]:
        """Generate recommendations from discovered patterns"""
        
        with Session(self.db_manager.engine) as session:
            # Get validated patterns
            statement = select(DiscoveredPattern).where(
                DiscoveredPattern.confidence_score >= 0.7
            )
            patterns = session.exec(statement).all()
            
            recommendations = []
            rec_repo = RecommendationRepository(session)
            
            for pattern in patterns:
                # Generate recommendation from pattern
                evidence = json.loads(pattern.evidence_json)
                
                if evidence.get('avg_oee_delta', 0) > 0:
                    # Extract experiment to get parameters
                    exp_id = json.loads(pattern.experiment_ids_json)[0]
                    experiment = session.get(Experiment, exp_id)
                    
                    if experiment:
                        parameters = json.loads(experiment.parameter_changes_json)
                        
                        recommendation = rec_repo.create_recommendation(
                            pattern_id=pattern.pattern_id,
                            recommendation_type="efficiency",
                            parameter_adjustments=parameters,
                            expected_improvement={
                                'oee': evidence['avg_oee_delta'],
                                'production': evidence['avg_production_delta']
                            },
                            confidence=pattern.confidence_score
                        )
                        recommendations.append(recommendation)
            
            print(f"✓ Generated {len(recommendations)} recommendations")
            return recommendations