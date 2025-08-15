import unittest
import os
import logging
from .simulation_runner import SimulationRunner
from .optimization_engine import OptimizationEngine, OptimizationObjective
from .actionable_parameters import ActionableParameters

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class TestSystem(unittest.TestCase):
    def setUp(self):
        logging.info("Setting up test case...")
        self.runner = SimulationRunner(verbose=False)
        self.optimizer = OptimizationEngine(simulation_runner=self.runner)
        logging.info("Setup complete.")

    def test_full_system_run(self):
        # 1. Configure a simulation
        logging.info("Step 1: Configuring simulation...")
        params = ActionableParameters()
        params.set_value("micro_stop_probability", 0.8)
        params.set_value("performance_factor", 1.1)
        logging.info(
            "Simulation configured with parameters: %s", params.get_all_values()
        )

        # 2. Run the simulation
        logging.info("Step 2: Running simulation...")
        simulation_result = self.runner.run_simulation(params, duration_days=7)
        logging.info("Simulation finished with status: %s", simulation_result.status)
        self.assertEqual(simulation_result.status, "completed")
        self.assertIsNotNone(simulation_result.kpi_summary)

        # 3. Verify the output
        logging.info("Step 3: Verifying simulation output...")
        self.assertIn("mean_oee", simulation_result.kpi_summary)
        self.assertGreater(simulation_result.kpi_summary["mean_oee"], 0)
        logging.info(
            "Simulation output verified. Mean OEE: %.2f",
            simulation_result.kpi_summary["mean_oee"],
        )

        # 4. Optimize parameters
        logging.info("Step 4: Optimizing parameters...")
        objectives = [
            OptimizationObjective(name="oee", direction="maximize"),
            OptimizationObjective(name="throughput", direction="maximize"),
        ]
        optimization_results = self.optimizer.optimize(objectives, verbose=True)
        logging.info("Optimization finished.")

        # 5. Validate the results
        logging.info("Step 5: Validating optimization results...")
        self.assertGreater(len(optimization_results), 0)
        best_result = optimization_results[0]
        self.assertTrue(best_result.success)
        self.assertIn("oee", best_result.objectives)
        self.assertIn("throughput", best_result.objectives)
        logging.info(
            "Optimization results validated. Best OEE: %.2f",
            best_result.objectives["oee"],
        )
        logging.info("Test finished successfully.")


if __name__ == "__main__":
    unittest.main()
