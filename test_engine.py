#!/usr/bin/env python3
"""
Test script for AI Analysis Engine

Uses test_dataset.md specified data for testing
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ai_analysis_engine import AIAnalysisEngine
from ai_analysis_engine.utils.logger import setup_logging

def main():
    """Test the AI Analysis Engine with sample data"""

    # Setup logging
    setup_logging()

    print("🚀 Starting AI Analysis Engine Test")
    print("=" * 50)

    # Initialize engine
    engine = AIAnalysisEngine()

    if not engine.initialize():
        print("❌ Engine initialization failed")
        return 1

    print("✅ AI Analysis Engine initialized successfully")

    # Test data paths from test_dataset.md
    base_path = Path("_input/sample_data")

    algorithm_spec = base_path / "algorithm/01_algorithm_specification/AS_drowsy_detection.md"
    evaluation_spec = base_path / "evaluation_engine/docs/EVALUATION_SPEC.md"
    core_output = base_path / "コアライブラリ出力結果/WIN_20250819_10_12_55_Pro_analysis.csv"
    algorithm_output = base_path / "アルゴリズム出力結果/2.csv"

    # Check if files exist
    missing_files = []
    for file_path in [algorithm_spec, evaluation_spec, core_output, algorithm_output]:
        if not file_path.exists():
            missing_files.append(str(file_path))

    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return 1

    print("📁 Test files found:")
    print(f"  📄 Algorithm spec: {algorithm_spec}")
    print(f"  📄 Evaluation spec: {evaluation_spec}")
    print(f"  📊 Core output: {core_output}")
    print(f"  📊 Algorithm output: {algorithm_output}")

    try:
        # Create analysis request
        print("\n📋 Creating analysis request...")
        state = engine.create_analysis_request(
            algorithm_outputs=[str(algorithm_output)],
            core_outputs=[str(core_output)],
            evaluation_specs=[str(evaluation_spec)],
            expected_results=["フレーム100-200の間に値1が存在すること"],
            dataset_ids=["test_drowsy_detection"]
        )

        print(f"✅ Created analysis request with {len(state.datasets)} dataset(s)")

        # Run analysis
        print("\n🔍 Running analysis...")
        results = engine.run_analysis(state)

        if "error" in results:
            print(f"❌ Analysis failed: {results['error']}")
            return 1
        else:
            print("✅ Analysis completed successfully")

            # Show results summary
            if "datasets" in results:
                for dataset in results["datasets"]:
                    print(f"\n📊 Dataset: {dataset.id}")
                    print(f"  Status: {dataset.status or 'unknown'}")
                    if dataset.report_content:
                        print("  Report: Generated")
                    else:
                        print("  Report: Not generated")
            # Show processing summary
            processing = results.get("get_processing_summary", {})
            if processing:
                print("\n📈 Processing Summary:")
                print(f"  Total: {processing.get('total_datasets', 0)}")
                print(f"  Completed: {processing.get('completed', 0)}")
                print(f"  Failed: {processing.get('failed', 0)}")

            print(f"\n💾 Results saved to output directory")
            return 0

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
