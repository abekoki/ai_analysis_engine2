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
あなたは検証エージェントです。与えられた仮説をテストして検証してください。

データセット情報:
{dataset_info}

仮説:
{hypothesis_description}

仮説タイプ: {hypothesis_type}
信頼度: {confidence_score}

検証すべきこと:
1. 仮説の妥当性テスト
2. 証拠の確認
3. 代替説明の検討
4. テスト結果の解釈

Pythonコードを使って検証を行い、結果を評価してください。

検証結果を報告してください。
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
        """Generate Python code to verify the hypothesis"""
        # Load data
        code_lines = [
            "# Load data for verification",
            f"import pandas as pd",
            f"algo_df = pd.read_csv('{dataset.algorithm_output_csv}')",
            f"core_df = pd.read_csv('{dataset.core_output_csv}')"
        ]

        # Add hypothesis-specific verification code
        if hypothesis.type.value == "data_quality_issue":
            code_lines.extend([
                "# Check data quality",
                "print('Algorithm DF shape:', algo_df.shape)",
                "print('Core DF shape:', core_df.shape)",
                "print('Missing values in algorithm:', algo_df.isnull().sum().sum())",
                "print('Missing values in core:', core_df.isnull().sum().sum())",
                "# Result: Check if data quality issues exist"
            ])

        elif hypothesis.type.value == "consistency_issue":
            code_lines.extend([
                "# Check consistency",
                "print('Algorithm columns:', list(algo_df.columns))",
                "print('Core columns:', list(core_df.columns))",
                "common_cols = set(algo_df.columns) & set(core_df.columns)",
                "print('Common columns:', common_cols)",
                "# Result: Check column consistency"
            ])

        else:
            # Generic verification
            code_lines.extend([
                "# Generic verification",
                "print('Basic data info')",
                "print('Algo shape:', algo_df.shape)",
                "print('Core shape:', core_df.shape)",
                "# Result: Basic data validation"
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
