#!/usr/bin/env python3
"""
AI Analysis Engine Runner

実行例:
python run_analysis.py --algorithm-outputs data/algo_output.csv --core-outputs data/core_output.csv --evaluation-specs docs/eval_spec.md --expected-results "フレーム1-10に値1が存在すること"
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ai_analysis_engine import AIAnalysisEngine
from ai_analysis_engine.utils.logger import setup_logging

def main():
    """Main runner function"""
    # Setup logging
    setup_logging()

    # Initialize engine
    engine = AIAnalysisEngine()

    if not engine.initialize():
        print("❌ Engine initialization failed")
        return 1

    print("✅ AI Analysis Engine initialized successfully")

    # Example usage with sample data
    try:
        # Check if sample data exists
        sample_data_dir = Path("_input/sample_data/algorithm")
        if sample_data_dir.exists():
            print("📊 Sample data found, running analysis...")

            # Use sample data for testing
            state = engine.create_analysis_request(
                algorithm_outputs=[str(sample_data_dir / "test_input.json")],  # This might need adjustment
                core_outputs=[str(Path("_input/sample_data/evaluation_engine/core_lib_output_sample.csv"))],
                evaluation_specs=[str(sample_data_dir / "01_algorithm_specification/AS_drowsy_detection.md")],
                expected_results=["フレーム100-200に値1が存在すること"],
                dataset_ids=["sample_dataset"]
            )

            results = engine.run_analysis(state)

            if "error" in results:
                print(f"❌ Analysis failed: {results['error']}")
                return 1
            else:
                print("✅ Analysis completed successfully")
                print(f"📄 Reports saved to: {results.get('output_dir', 'output directory')}")
                return 0
        else:
            print("ℹ️  No sample data found. Use command line arguments to specify data files.")
            print("   Example: python run_analysis.py --algorithm-outputs data.csv --core-outputs core.csv --evaluation-specs spec.md --expected-results 'expected result'")

    except Exception as e:
        print(f"❌ Analysis execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
