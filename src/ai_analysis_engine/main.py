"""
Main application entry point for AI Analysis Engine
"""

import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from .config import config
from .models.state import AnalysisState, DatasetInfo
from .core.graph import AnalysisGraph
from .utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


class AIAnalysisEngine:
    """
    Main application class for the AI Analysis Engine
    """

    def __init__(self):
        self.graph = None
        self.logger = logger

    def initialize(self) -> bool:
        """
        Initialize the analysis engine

        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing AI Analysis Engine...")

            # Ensure directories exist
            config.ensure_directories()

            # Validate API keys
            if not config.validate_api_keys():
                self.logger.error("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
                return False

            # Build the analysis graph
            self.graph = AnalysisGraph()
            self.graph.build_graph()

            self.logger.info("AI Analysis Engine initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize AI Analysis Engine: {e}")
            return False

    def create_analysis_request(self,
                              algorithm_outputs: List[str],
                              core_outputs: List[str],
                              evaluation_specs: List[str],
                              expected_results: List[str],
                              dataset_ids: Optional[List[str]] = None) -> AnalysisState:
        """
        Create an analysis request from input files

        Args:
            algorithm_outputs: List of algorithm output CSV files
            core_outputs: List of core library output CSV files
            evaluation_specs: List of evaluation specification Markdown files
            expected_results: List of expected results (natural language)
            dataset_ids: Optional list of dataset IDs

        Returns:
            AnalysisState object ready for processing
        """
        if len(algorithm_outputs) != len(core_outputs) or len(algorithm_outputs) != len(expected_results):
            raise ValueError("All input lists must have the same length")

        datasets = []

        for i, (algo_csv, core_csv, expected) in enumerate(zip(algorithm_outputs, core_outputs, expected_results)):
            dataset_id = dataset_ids[i] if dataset_ids else f"dataset_{i+1}"

            # Find corresponding evaluation spec
            eval_spec = evaluation_specs[i] if i < len(evaluation_specs) else (evaluation_specs[0] if evaluation_specs else None)

            dataset = DatasetInfo(
                id=dataset_id,
                algorithm_output_csv=algo_csv,
                core_output_csv=core_csv,
                evaluation_spec_md=eval_spec,
                expected_result=expected
            )

            datasets.append(dataset)

        # Create initial state
        state = AnalysisState(
            datasets=datasets,
            spec_documents=evaluation_specs,
            start_time=self._get_current_time()
        )

        self.logger.info(f"Created analysis request with {len(datasets)} datasets")
        return state

    def run_analysis(self, state: AnalysisState) -> Dict[str, Any]:
        """
        Run the complete analysis workflow

        Args:
            state: Analysis state to process

        Returns:
            Analysis results
        """
        if not self.graph:
            raise RuntimeError("Engine not initialized. Call initialize() first.")

        try:
            self.logger.info("Starting analysis workflow...")

            # Run the analysis
            result = self.graph.run_analysis(state.model_dump())

            # Update end time
            result["end_time"] = self._get_current_time()

            # Save results
            self._save_results(result)

            self.logger.info("Analysis workflow completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "end_time": self._get_current_time()
            }

    def _save_results(self, results: Dict[str, Any]) -> None:
        """Save analysis results to files"""
        try:
            output_dir = config.output_dir / "results"
            output_dir.mkdir(exist_ok=True)

            # Save main results
            results_file = output_dir / "analysis_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            # Save individual reports
            if "datasets" in results:
                reports_dir = output_dir / "reports"
                reports_dir.mkdir(exist_ok=True)

                for dataset in results["datasets"]:
                    if dataset.get("report_content"):
                        report_file = reports_dir / f"{dataset['id']}_report.md"
                        with open(report_file, 'w', encoding='utf-8') as f:
                            f.write(dataset["report_content"])

            self.logger.info(f"Results saved to {output_dir}")

        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")

    def _get_current_time(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            "initialized": self.graph is not None,
            "config_valid": config.validate_api_keys(),
            "data_dir": str(config.data_dir),
            "output_dir": str(config.output_dir),
            "logs_dir": str(config.logs_dir)
        }


def main():
    """Main entry point for command line usage"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Analysis Engine for Time Series Data")
    parser.add_argument("--algorithm-outputs", nargs="+", required=True,
                       help="Algorithm output CSV files")
    parser.add_argument("--core-outputs", nargs="+", required=True,
                       help="Core library output CSV files")
    parser.add_argument("--evaluation-specs", nargs="+", required=True,
                       help="Evaluation specification Markdown files")
    parser.add_argument("--expected-results", nargs="+", required=True,
                       help="Expected results (natural language)")
    parser.add_argument("--dataset-ids", nargs="+",
                       help="Dataset IDs (optional)")

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Initialize engine
    engine = AIAnalysisEngine()

    if not engine.initialize():
        logger.error("Failed to initialize engine")
        return 1

    try:
        # Create analysis request
        state = engine.create_analysis_request(
            algorithm_outputs=args.algorithm_outputs,
            core_outputs=args.core_outputs,
            evaluation_specs=args.evaluation_specs,
            expected_results=args.expected_results,
            dataset_ids=args.dataset_ids
        )

        # Run analysis
        results = engine.run_analysis(state)

        if "error" in results:
            logger.error(f"Analysis failed: {results['error']}")
            return 1
        else:
            logger.info("Analysis completed successfully")
            return 0

    except Exception as e:
        logger.error(f"Analysis execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
