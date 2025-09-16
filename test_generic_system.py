#!/usr/bin/env python3
"""
Test script for the generic AI analysis engine system
Tests the new configuration system and agent integrations
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_analysis_engine.config.config import Config, AlgorithmConfig
from ai_analysis_engine.models.state import DatasetInfo
from ai_analysis_engine.agents.data_checker_agent import DataCheckerAgent
from ai_analysis_engine.agents.hypothesis_generator_agent import HypothesisGeneratorAgent
from ai_analysis_engine.agents.verifier_agent import VerifierAgent
from ai_analysis_engine.agents.reporter_agent import ReporterAgent

def test_algorithm_config_parsing():
    """Test algorithm configuration parsing from specification file"""
    print("=== Testing Algorithm Configuration Parsing ===")

    # Initialize config
    config = Config()

    # Test specification file path
    spec_file = Path("_input/sample_data/algorithm/01_algorithm_specification/AS_drowsy_detection.md")

    if spec_file.exists():
        print(f"Loading specification from: {spec_file}")

        # Load algorithm configuration
        algo_config = config.load_algorithm_config_from_file(str(spec_file))

        print("✓ Algorithm configuration loaded successfully")
        print(f"  Name: {algo_config.name}")
        print(f"  Input columns: {algo_config.input_columns}")
        print(f"  Output columns: {algo_config.output_columns}")
        print(f"  Thresholds: {algo_config.thresholds}")
        print(f"  Value ranges: {algo_config.value_ranges}")
        print(f"  Valid values: {algo_config.valid_values}")

        return algo_config
    else:
        print(f"✗ Specification file not found: {spec_file}")
        return None

def test_agents_initialization(algo_config):
    """Test agent initialization with algorithm configuration"""
    print("\n=== Testing Agent Initialization ===")

    try:
        # Initialize agents
        data_checker = DataCheckerAgent()
        hypothesis_generator = HypothesisGeneratorAgent()
        verifier = VerifierAgent()
        reporter = ReporterAgent()

        print("✓ All agents initialized successfully")

        # Test algorithm context preparation
        if algo_config:
            # Test DataCheckerAgent context preparation
            context = data_checker._prepare_algorithm_context(algo_config)
            print(f"✓ DataCheckerAgent context: {len(context)} items")

            # Test HypothesisGeneratorAgent context preparation
            hypo_context = hypothesis_generator._prepare_algorithm_context(algo_config)
            print(f"✓ HypothesisGeneratorAgent context: {len(hypo_context)} items")

            # Test VerifierAgent context preparation
            ver_context = verifier._prepare_algorithm_context(algo_config)
            print(f"✓ VerifierAgent context: {len(ver_context)} items")

            # Test ReporterAgent context preparation
            rep_context = reporter._prepare_algorithm_context(algo_config)
            print(f"✓ ReporterAgent context: {len(rep_context)} items")

        return {
            'data_checker': data_checker,
            'hypothesis_generator': hypothesis_generator,
            'verifier': verifier,
            'reporter': reporter
        }

    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")
        return None

def test_dataset_creation():
    """Test dataset information creation"""
    print("\n=== Testing Dataset Creation ===")

    try:
        # Create test dataset
        dataset = DatasetInfo(
            id="test_dataset_001",
            algorithm_output_csv="_input/sample_data/アルゴリズム出力結果/4.csv",
            core_output_csv="_input/sample_data/コアライブラリ出力結果/WIN_20250819_10_16_17_Pro_analysis.csv",
            algorithm_spec_md="_input/sample_data/algorithm/01_algorithm_specification/AS_drowsy_detection.md",
            algorithm_code_files=[
                "_input/sample_data/algorithm/src/drowsy_detection/core/drowsy_detetector.py",
                "_input/sample_data/algorithm/src/drowsy_detection/core/eye_state.py"
            ],
            evaluation_spec_md="_input/sample_data/evaluation_engine/docs/EVALUATION_SPEC.md",
            evaluation_code_files=[
                "_input/sample_data/evaluation_engine/main.py"
            ],
            expected_result="フレーム区間36-136の間に「連続閉眼あり」が存在すること"
        )

        print("✓ Dataset created successfully")
        print(f"  ID: {dataset.id}")
        print(f"  Algorithm output: {dataset.algorithm_output_csv}")
        print(f"  Core output: {dataset.core_output_csv}")
        print(f"  Algorithm spec: {dataset.algorithm_spec_md}")
        print(f"  Expected result: {dataset.expected_result}")

        return dataset

    except Exception as e:
        print(f"✗ Dataset creation failed: {e}")
        return None

def test_data_analysis_flow(agents, dataset, algo_config):
    """Test the complete data analysis flow"""
    print("\n=== Testing Data Analysis Flow ===")

    try:
        # Test DataCheckerAgent
        print("Testing DataCheckerAgent...")
        analysis_results = agents['data_checker'].analyze_data(dataset)
        print(f"✓ DataCheckerAgent completed. Results keys: {list(analysis_results.keys())}")

        # Test HypothesisGeneratorAgent
        print("Testing HypothesisGeneratorAgent...")
        hypotheses = agents['hypothesis_generator'].generate_hypotheses(
            dataset, analysis_results, {}
        )
        print(f"✓ HypothesisGeneratorAgent completed. Generated {len(hypotheses)} hypotheses")

        # Test VerifierAgent (if hypotheses exist)
        if hypotheses:
            print("Testing VerifierAgent...")
            verification_result = agents['verifier'].verify_hypothesis(
                dataset, hypotheses[0]
            )
            print(f"✓ VerifierAgent completed. Success: {verification_result.success}")

        # Test ReporterAgent
        print("Testing ReporterAgent...")
        report = agents['reporter'].generate_report(
            dataset, analysis_results, hypotheses
        )
        print(f"✓ ReporterAgent completed. Report length: {len(report)} characters")

        # Debug: Show first 500 characters of report
        print("\n--- Report Preview ---")
        print(report[:500])
        print("--- End Preview ---")

        # Save report to file for verification
        import os
        os.makedirs("output/results/reports", exist_ok=True)
        report_file = f"output/results/reports/{dataset.id}_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✓ Report saved to: {report_file}")

        return True

    except Exception as e:
        print(f"✗ Data analysis flow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 Starting Generic AI Analysis Engine System Test")
    print("=" * 60)

    # Test 1: Algorithm configuration parsing
    algo_config = test_algorithm_config_parsing()

    # Test improved configuration parsing
    if algo_config:
        print(f"✓ Face confidence threshold: {algo_config.thresholds.get('face_conf_threshold', 'Not found')}")
        print(f"✓ Left eye threshold: {algo_config.thresholds.get('left_eye_close_threshold', 'Not found')}")
        print(f"✓ Right eye threshold: {algo_config.thresholds.get('right_eye_close_threshold', 'Not found')}")
        print(f"✓ Continuous close time: {algo_config.thresholds.get('continuous_close_time', 'Not found')}")

        print(f"✓ Input columns found: {len(algo_config.input_columns)}")
        for col in algo_config.input_columns:
            print(f"  - {col}")

        print(f"✓ Output columns: {algo_config.output_columns}")
        print(f"✓ Valid values for is_drowsy: {algo_config.valid_values.get('is_drowsy', 'Not found')}")

    # Test 2: Agent initialization
    agents = test_agents_initialization(algo_config)

    # Test 3: Dataset creation
    dataset = test_dataset_creation()

    # Test 4: Complete analysis flow
    if agents and dataset and algo_config:
        success = test_data_analysis_flow(agents, dataset, algo_config)

        if success:
            print("\n" + "=" * 60)
            print("🎉 All tests completed successfully!")
            print("The generic AI analysis engine is working properly.")
        else:
            print("\n" + "=" * 60)
            print("❌ Some tests failed. Check the output above for details.")
    else:
        print("\n" + "=" * 60)
        print("❌ Prerequisites not met. Cannot run complete analysis flow.")

if __name__ == "__main__":
    main()
