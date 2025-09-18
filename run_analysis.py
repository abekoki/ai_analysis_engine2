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

            # Use sample data for testing - aligned with test_dataset.md
            # Check for command line output directory argument
            import sys
            output_dir = None
            if len(sys.argv) > 1 and sys.argv[1] == "--output-dir":
                output_dir = sys.argv[2] if len(sys.argv) > 2 else None

            state = engine.create_analysis_request(
                algorithm_outputs=[str(Path("_input/sample_data/アルゴリズム出力結果/2.csv"))],
                core_outputs=[str(Path("_input/sample_data/コアライブラリ出力結果/WIN_20250819_10_12_55_Pro_analysis.csv"))],
                algorithm_specs=[str(sample_data_dir / "01_algorithm_specification/AS_drowsy_detection.md")],
                evaluation_specs=[str(Path("_input/sample_data/evaluation_engine/docs/EVALUATION_SPEC.md"))],
                expected_results=["フレーム区間465-593の間に「連続閉眼あり」が存在すること"],
                algorithm_codes=[[str(sample_data_dir / "src/drowsy_detection/__init__.py"),
                                str(sample_data_dir / "src/drowsy_detection/drowsy_detector.py"),
                                str(sample_data_dir / "src/drowsy_detection/eye_state.py")]],
                evaluation_codes=[[str(Path("_input/sample_data/evaluation_engine/main.py"))]],
                dataset_ids=["test_dataset"],
                output_dir=output_dir
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
