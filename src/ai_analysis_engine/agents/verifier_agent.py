"""
Verifier Agent - Verifies hypotheses through testing
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..config import config
from ..models.state import DatasetInfo
from ..models.types import Hypothesis, VerificationResult
from ..tools.repl_tool import REPLTool
from ..tools.rag_tool import RAGTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VerifierAgent:
    """
    Agent for verifying hypotheses through testing and validation
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.openai.model,
            temperature=config.openai.temperature,
            api_key=config.openai.api_key
        )

        self.repl_tool = REPLTool()
        self.rag_tool = RAGTool()
        self.max_iterations = config.langgraph.max_iterations

        self.prompt = ChatPromptTemplate.from_template("""
あなたは検証エージェントです。アルゴリズム仕様に基づいて仮説をテストして検証してください。

【重要】アルゴリズム仕様を理解し、その仕様に基づいて仮説を検証してください。

データセット情報:
{dataset_info}

アルゴリズム仕様:
{algorithm_spec}

評価環境仕様:
{evaluation_spec}

仮説:
{hypothesis_description}

仮説タイプ: {hypothesis_type}
信頼度: {confidence_score}
仕様関連: {spec_reference}

【アルゴリズム仕様に基づく検証アプローチ】
1. **仕様理解**: アルゴリズムの判定ロジックとパラメータを把握
2. **仮説の仕様準拠確認**: 仮説がアルゴリズム仕様と矛盾しないか確認
3. **データ検証**: 実際のデータで仮説をテスト
4. **仕様ベースの評価**: 結果をアルゴリズム仕様に基づいて評価

【検証時の注目点】
- アルゴリズムの判定閾値を列挙し、各閾値と出力結果について確認
- アルゴリズムの計算ロジックを確認
- エラーコードと仕様書のエラーハンドリング
- 入力データの有効範囲と実際の値の比較

Pythonコードを使って仕様に基づいた検証を行い、結果を評価してください。

検証結果を詳細に報告し、アルゴリズム仕様との関連を明確にしてください。
""")

    def verify_hypothesis(self, dataset: DatasetInfo, hypothesis: Hypothesis) -> VerificationResult:
        """
        Verify a hypothesis through testing

        Args:
            dataset: Dataset information
            hypothesis: Hypothesis to verify

        Returns:
            Verification result
        """
        try:
            logger.info(f"Verifying hypothesis {hypothesis.id} for dataset {dataset.id}")

            # Load algorithm spec
            algorithm_spec = ""
            if dataset.algorithm_spec_md:
                try:
                    with open(dataset.algorithm_spec_md, 'r', encoding='utf-8') as f:
                        algorithm_spec = f.read()
                except Exception as e:
                    logger.warning(f"Failed to load algorithm spec: {e}")

            # Load evaluation spec
            evaluation_spec = ""
            if dataset.evaluation_spec_md:
                try:
                    with open(dataset.evaluation_spec_md, 'r', encoding='utf-8') as f:
                        evaluation_spec = f.read()
                except Exception as e:
                    logger.warning(f"Failed to load evaluation spec: {e}")

            # Prepare verification context
            dataset_info = self._prepare_dataset_info(dataset)

            # Generate verification code/tests
            verification_code = self._generate_verification_code(hypothesis, dataset)

            # Execute verification
            verification_result = self._execute_verification(verification_code, dataset)

            # Evaluate results
            evaluation = self._evaluate_verification_results(
                hypothesis, verification_result, dataset
            )

            result = VerificationResult(
                hypothesis_id=hypothesis.id,
                success=evaluation["success"],
                result_details=evaluation["details"],
                code_executed=verification_code,
                output_data=verification_result.get("result"),
                error_message=verification_result.get("error")
            )

            logger.info(f"Verification completed for hypothesis {hypothesis.id}: {result.success}")
            return result

        except Exception as e:
            logger.error(f"Verification failed for hypothesis {hypothesis.id}: {e}")
            return VerificationResult(
                hypothesis_id=hypothesis.id,
                success=False,
                result_details=f"Verification failed: {e}",
                error_message=str(e)
            )

    def _prepare_dataset_info(self, dataset: DatasetInfo) -> str:
        """Prepare dataset information for verification"""
        info_lines = [
            f"データセットID: {dataset.id}",
            f"アルゴリズム出力: {dataset.algorithm_output_csv}",
            f"コア出力: {dataset.core_output_csv}",
            f"期待値: {dataset.expected_result}"
        ]

        return "\n".join(info_lines)

    def _generate_verification_code(self, hypothesis: Hypothesis, dataset: DatasetInfo) -> str:
        """Generate Python code to verify the hypothesis based on algorithm specifications"""
        # Load data
        code_lines = [
            "# Load data for verification based on drowsy detection algorithm specs",
            f"import pandas as pd",
            f"import numpy as np",
            f"algo_df = pd.read_csv('{dataset.algorithm_output_csv}')",
            f"core_df = pd.read_csv('{dataset.core_output_csv}')",
            "",
            "# Algorithm specifications from drowsy_detection spec",
            "# left_eye_close_threshold: 0.10",
            "# right_eye_close_threshold: 0.10",
            "# face_conf_threshold: 0.75",
            "# continuous_close_time: 1.00 seconds",
            "LEFT_EYE_THRESHOLD = 0.10",
            "RIGHT_EYE_THRESHOLD = 0.10",
            "FACE_CONF_THRESHOLD = 0.75",
            "CONTINUOUS_CLOSE_TIME = 1.0",
            ""
        ]

        # Add hypothesis-specific verification code
        if hypothesis.type.value == "data_quality_issue":
            code_lines.extend([
                "# Check data quality according to algorithm specifications",
                "print('=== Data Quality Check ===')",
                "print('Algorithm DF shape:', algo_df.shape)",
                "print('Core DF shape:', core_df.shape)",
                "print('Missing values in algorithm:', algo_df.isnull().sum().sum())",
                "print('Missing values in core:', core_df.isnull().sum().sum())",
                "",
                "# Check if required columns exist (based on algorithm spec)",
                "required_algo_cols = ['frame_num', 'is_drowsy']",
                "required_core_cols = ['leye_openness', 'reye_openness']",
                "",
                "missing_algo_cols = [col for col in required_algo_cols if col not in algo_df.columns]",
                "missing_core_cols = [col for col in required_core_cols if col not in core_df.columns]",
                "",
                "if missing_algo_cols:",
                "    print('Missing algorithm columns:', missing_algo_cols)",
                "if missing_core_cols:",
                "    print('Missing core columns:', missing_core_cols)",
                "",
                "# Check data value ranges (based on algorithm spec)",
                "print('\\n=== Value Range Check ===')",
                "if 'is_drowsy' in algo_df.columns:",
                "    valid_values = algo_df['is_drowsy'].isin([-1, 0, 1]).all()",
                "    print('is_drowsy values valid (-1,0,1):', valid_values)",
                "",
                "# Check eye openness ranges (should be 0.0-1.0)",
                "eye_cols = ['leye_openness', 'reye_openness']",
                "for col in eye_cols:",
                "    if col in core_df.columns:",
                "        valid_range = (core_df[col] >= 0.0) & (core_df[col] <= 1.0)",
                "        print(f'{col} in valid range [0,1]: {valid_range.all()}')",
                "",
                "# Result: Data quality assessment"
            ])

        elif hypothesis.type.value == "consistency_issue" or hypothesis.type.value == "specification_inconsistency":
            code_lines.extend([
                "# Check consistency with algorithm specifications",
                "print('=== Algorithm Specification Consistency Check ===')",
                "",
                "# Check column alignment with spec",
                "print('Algorithm columns:', list(algo_df.columns))",
                "print('Core columns:', list(core_df.columns))",
                "",
                "# Verify algorithm output logic (based on spec)",
                "if all(col in algo_df.columns for col in ['frame_num', 'is_drowsy']):",
                "    print('\\n=== Algorithm Output Validation ===')",
                "    # Check if error states (-1) correlate with missing face confidence",
                "    error_frames = algo_df[algo_df['is_drowsy'] == -1]",
                "    print(f'Frames with error state (-1): {len(error_frames)}')",
                "    ",
                "    # Check drowsy detection distribution",
                "    drowsy_dist = algo_df['is_drowsy'].value_counts()",
                "    print('\\nDrowsy detection distribution:')",
                "    print(drowsy_dist)",
                "",
                "# Check eye state logic (based on spec)",
                "if all(col in core_df.columns for col in ['leye_openness', 'reye_openness']):",
                "    print('\\n=== Eye State Logic Validation ===')",
                "    # Calculate expected eye closure states",
                "    left_closed = core_df['leye_openness'] <= LEFT_EYE_THRESHOLD",
                "    right_closed = core_df['reye_openness'] <= RIGHT_EYE_THRESHOLD",
                "    both_closed = left_closed & right_closed",
                "    ",
                "    print(f'Left eye closed frames: {left_closed.sum()}')",
                "    print(f'Right eye closed frames: {right_closed.sum()}')",
                "    print(f'Both eyes closed frames: {both_closed.sum()}')",
                "",
                "# Result: Specification consistency assessment"
            ])

        elif hypothesis.type.value == "algorithm_bug":
            code_lines.extend([
                "# Check for algorithm bugs based on specifications",
                "print('=== Algorithm Bug Detection ===')",
                "",
                "# Check continuous time calculation (based on spec)",
                "if 'continuous_time' in algo_df.columns:",
                "    print('\\n=== Continuous Time Analysis ===')",
                "    continuous_stats = algo_df['continuous_time'].describe()",
                "    print('Continuous time statistics:')",
                "    print(continuous_stats)",
                "    ",
                "    # Check for unrealistic continuous times",
                "    unrealistic_times = algo_df[algo_df['continuous_time'] > CONTINUOUS_CLOSE_TIME * 2]",
                "    print(f'Frames with unrealistic continuous time: {len(unrealistic_times)}')",
                "",
                "# Check state transitions (based on spec)",
                "if 'is_drowsy' in algo_df.columns:",
                "    print('\\n=== State Transition Analysis ===')",
                "    # Check for invalid state transitions",
                "    state_changes = algo_df['is_drowsy'].diff().fillna(0)",
                "    invalid_transitions = state_changes.abs() > 1  # Should only change by -1, 0, or 1",
                "    print(f'Invalid state transitions: {invalid_transitions.sum()}')",
                "",
                "# Result: Algorithm bug assessment"
            ])

        else:
            # Generic verification with spec-aware checks
            code_lines.extend([
                "# Generic verification with algorithm specification awareness",
                "print('=== General Verification with Spec Context ===')",
                "print('Algorithm DF shape:', algo_df.shape)",
                "print('Core DF shape:', core_df.shape)",
                "",
                "# Basic spec compliance check",
                "spec_compliant = True",
                "if 'is_drowsy' in algo_df.columns:",
                "    valid_range = algo_df['is_drowsy'].isin([-1, 0, 1]).all()",
                "    print(f'Algorithm output in valid range: {valid_range}')",
                "    spec_compliant &= valid_range",
                "",
                "eye_cols_present = all(col in core_df.columns for col in ['leye_openness', 'reye_openness'])",
                "print(f'Required eye columns present: {eye_cols_present}')",
                "spec_compliant &= eye_cols_present",
                "",
                "print(f'Overall spec compliance: {spec_compliant}')",
                "# Result: General specification-aware validation"
            ])

        return "\n".join(code_lines)

    def _execute_verification(self, code: str, dataset: DatasetInfo) -> Dict[str, Any]:
        """Execute verification code"""
        try:
            # Create execution context with data paths
            context = {
                "dataset": dataset,
                "algo_csv": dataset.algorithm_output_csv,
                "core_csv": dataset.core_output_csv
            }

            # Execute the code
            result = self.repl_tool.execute_code(code, context)

            return result

        except Exception as e:
            logger.error(f"Verification execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _evaluate_verification_results(self, hypothesis: Hypothesis,
                                     verification_result: Dict[str, Any],
                                     dataset: DatasetInfo) -> Dict[str, Any]:
        """Evaluate the results of verification"""
        try:
            if not verification_result.get("success"):
                return {
                    "success": False,
                    "details": f"Verification failed: {verification_result.get('error')}"
                }

            # Evaluate based on hypothesis type and results
            stdout = verification_result.get("stdout", "")
            result_data = verification_result.get("result")

            # Simple evaluation logic (can be made more sophisticated)
            if hypothesis.type.value == "data_quality_issue":
                # Check for missing values or empty data
                if "Missing values" in stdout and "0" not in stdout.split("Missing values:")[1].split()[0]:
                    return {
                        "success": True,
                        "details": "Data quality issues confirmed by verification"
                    }

            elif hypothesis.type.value == "consistency_issue":
                # Check for consistency issues
                if "Common columns" in stdout:
                    return {
                        "success": True,
                        "details": "Consistency issues identified in verification"
                    }

            # Default evaluation
            if stdout and len(stdout.strip()) > 0:
                return {
                    "success": True,
                    "details": f"Verification completed successfully: {stdout[:200]}"
                }
            else:
                return {
                    "success": False,
                    "details": "Verification produced no meaningful output"
                }

        except Exception as e:
            logger.error(f"Result evaluation failed: {e}")
            return {
                "success": False,
                "details": f"Evaluation failed: {e}"
            }
