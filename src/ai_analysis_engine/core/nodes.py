"""
LangGraph nodes for the AI Analysis Engine workflow
"""

from typing import Dict, Any, List
from datetime import datetime

from ..models.state import AnalysisState, DatasetInfo
from ..models.types import DataSummary, ConsistencyCheckResult, Hypothesis, VerificationResult
from ..tools.rag_tool import RAGTool
from ..tools.repl_tool import REPLTool
from ..utils.logger import get_logger
from ..config import config

logger = get_logger(__name__)


class InitializationNode:
    """Node for initializing the RAG system"""

    def __init__(self):
        self.rag_tool = RAGTool()

    def process(self, state: AnalysisState) -> AnalysisState:
        """Initialize vector stores and prepare for analysis"""
        logger.info("Starting initialization")

        try:
            # Prepare documents for RAG
            documents = self._prepare_documents(state)

            # Initialize vector stores
            success = self.rag_tool.initialize_vector_stores(documents)

            if success:
                # Update state
                state.vector_stores.is_initialized = True
                state.vector_stores.segments = list(documents.keys())
                state.vector_stores.last_updated = datetime.now().isoformat()

                logger.info("Initialization completed successfully")
            else:
                state.errors.append("Failed to initialize vector stores")
                logger.error("Initialization failed")

        except Exception as e:
            error_msg = f"Initialization error: {e}"
            state.errors.append(error_msg)
            logger.error(error_msg)

        state.workflow_step = "supervisor"
        return state

    def _prepare_documents(self, state: AnalysisState) -> Dict[str, List[str]]:
        """Prepare documents for vectorization by segment"""
        documents = {
            "algorithm_specs": [],
            "evaluation_specs": [],
            "code": []
        }

        # Add specification documents
        for spec_doc in state.spec_documents:
            if "algorithm" in spec_doc.lower():
                documents["algorithm_specs"].append(spec_doc)
            elif "evaluation" in spec_doc.lower():
                documents["evaluation_specs"].append(spec_doc)
            else:
                documents["algorithm_specs"].append(spec_doc)

        # Add code documents from datasets
        for dataset in state.datasets:
            if dataset.evaluation_spec_md:
                documents["evaluation_specs"].append(dataset.evaluation_spec_md)

        return documents


class SupervisorNode:
    """Node for supervising the analysis workflow"""

    def process(self, state: AnalysisState) -> AnalysisState:
        """Supervise and route to appropriate next step"""
        logger.info("Supervisor processing")

        current_dataset = state.get_current_dataset()

        if current_dataset is None:
            # All datasets processed
            state.workflow_step = "completed"
            logger.info("All datasets processed")
            return state

        # Determine next step based on dataset status
        if current_dataset.status == "pending":
            state.workflow_step = "data_checker"
        elif current_dataset.status == "data_checked":
            state.workflow_step = "consistency_checker"
        elif current_dataset.status == "consistency_checked":
            state.workflow_step = "hypothesis_generator"
        elif current_dataset.status == "hypothesis_generated":
            state.workflow_step = "verifier"
        elif current_dataset.status == "verified":
            state.workflow_step = "reporter"
        else:
            state.workflow_step = "data_checker"

        logger.info(f"Next step: {state.workflow_step} for dataset {current_dataset.id}")
        return state


class DataCheckerNode:
    """Node for checking and analyzing input data"""

    def __init__(self):
        self.repl_tool = REPLTool()
        self.rag_tool = RAGTool()

    def process(self, state: AnalysisState) -> AnalysisState:
        """Check and analyze data for current dataset"""
        logger.info("Data checker processing")

        current_dataset = state.get_current_dataset()
        if not current_dataset:
            return state

        try:
            # Load CSV data
            csv_files = [
                current_dataset.algorithm_output_csv,
                current_dataset.core_output_csv
            ]

            dataframes = self.repl_tool.load_csv_data(csv_files)

            # Analyze data
            analysis_results = {}
            for name, df in dataframes.items():
                analysis_results[name] = self.repl_tool.analyze_dataframe(df, name)

            # Create plots
            plot_paths = self._create_data_plots(dataframes, current_dataset.id)

            # Query column information from specs
            column_info = self._get_column_info_from_specs(current_dataset)

            # Update dataset state
            current_dataset.data_summary = {
                "analysis": analysis_results,
                "plots": plot_paths,
                "column_info": column_info
            }
            current_dataset.status = "data_checked"

            logger.info(f"Data checking completed for dataset {current_dataset.id}")

        except Exception as e:
            error_msg = f"Data checking failed: {e}"
            current_dataset.error_message = error_msg
            state.errors.append(error_msg)
            logger.error(error_msg)

        return state

    def _create_data_plots(self, dataframes: Dict[str, Any], dataset_id: str) -> Dict[str, str]:
        """Create time series plots for the data"""
        plot_paths = {}

        try:
            # Create output directory
            plots_dir = config.output_dir / "plots" / dataset_id
            plots_dir.mkdir(parents=True, exist_ok=True)

            for name, df in dataframes.items():
                if len(df) > 0 and 'timestamp' in df.columns:
                    # Create time series plot
                    code = f"""
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df.select_dtypes(include=['number']).iloc[:, 0], marker='o', linestyle='-')
plt.title(f'{name} Time Series')
plt.xlabel('Timestamp')
plt.ylabel('Value')
plt.xticks(rotation=45)
plt.tight_layout()
"""
                    plot_path = str(plots_dir / f"{name}_timeseries.png")
                    result = self.repl_tool.create_plot(code, {"df": df}, plot_path)

                    if result.get("success"):
                        plot_paths[name] = plot_path

        except Exception as e:
            logger.error(f"Failed to create plots: {e}")

        return plot_paths

    def _get_column_info_from_specs(self, dataset: DatasetInfo) -> Dict[str, Any]:
        """Get column information from evaluation specifications"""
        try:
            # Search for column-related information
            spec_results = self.rag_tool.search("column format data structure", "evaluation_specs", k=3)

            column_info = {
                "spec_results": spec_results,
                "inferred_columns": {}
            }

            return column_info

        except Exception as e:
            logger.error(f"Failed to get column info: {e}")
            return {}


class ConsistencyCheckerNode:
    """Node for checking consistency between data and specifications"""

    def __init__(self):
        self.repl_tool = REPLTool()
        self.rag_tool = RAGTool()

    def process(self, state: AnalysisState) -> AnalysisState:
        """Check consistency for current dataset"""
        logger.info("Consistency checker processing")

        current_dataset = state.get_current_dataset()
        if not current_dataset:
            return state

        try:
            # Parse expected result from natural language
            expected_result = current_dataset.expected_result

            # Load data for checking
            dataframes = self.repl_tool.load_csv_data([
                current_dataset.algorithm_output_csv,
                current_dataset.core_output_csv
            ])

            # Perform consistency checks
            consistency_results = self._check_consistency(dataframes, expected_result)

            # Update dataset state
            current_dataset.consistency_check = consistency_results
            current_dataset.status = "consistency_checked"

            logger.info(f"Consistency checking completed for dataset {current_dataset.id}")

        except Exception as e:
            error_msg = f"Consistency checking failed: {e}"
            current_dataset.error_message = error_msg
            state.errors.append(error_msg)
            logger.error(error_msg)

        return state

    def _check_consistency(self, dataframes: Dict[str, Any], expected: str) -> Dict[str, Any]:
        """Check consistency between data and expectations"""
        # This is a simplified implementation
        # In a real system, you'd have more sophisticated NLP parsing

        results = {
            "expected_interpretation": expected,
            "checks_performed": [],
            "overall_consistent": True,
            "issues": []
        }

        # Basic checks (simplified)
        for name, df in dataframes.items():
            if len(df) == 0:
                results["issues"].append(f"Empty dataframe: {name}")
                results["overall_consistent"] = False
            else:
                results["checks_performed"].append(f"Dataframe {name}: {len(df)} rows")

        return results


class HypothesisGeneratorNode:
    """Node for generating hypotheses about issues"""

    def __init__(self):
        self.rag_tool = RAGTool()

    def process(self, state: AnalysisState) -> AnalysisState:
        """Generate hypotheses for current dataset"""
        logger.info("Hypothesis generator processing")

        current_dataset = state.get_current_dataset()
        if not current_dataset:
            return state

        try:
            # Generate hypotheses based on data summary and consistency check
            hypotheses = self._generate_hypotheses(current_dataset)

            # Update dataset state
            current_dataset.hypotheses = hypotheses
            current_dataset.status = "hypothesis_generated"

            logger.info(f"Generated {len(hypotheses)} hypotheses for dataset {current_dataset.id}")

        except Exception as e:
            error_msg = f"Hypothesis generation failed: {e}"
            current_dataset.error_message = error_msg
            state.errors.append(error_msg)
            logger.error(error_msg)

        return state

    def _generate_hypotheses(self, dataset: DatasetInfo) -> List[Dict[str, Any]]:
        """Generate hypotheses based on analysis results"""
        hypotheses = []

        # Simplified hypothesis generation
        # In a real system, this would be more sophisticated

        if dataset.consistency_check and not dataset.consistency_check.get("overall_consistent", True):
            hypotheses.append({
                "id": "consistency_issue",
                "type": "consistency",
                "description": "Data consistency issues detected",
                "confidence": 0.8
            })

        # Add more hypotheses based on data patterns
        hypotheses.append({
            "id": "performance_baseline",
            "type": "performance",
            "description": "Establish performance baseline",
            "confidence": 0.6
        })

        return hypotheses


class VerifierNode:
    """Node for verifying hypotheses through testing"""

    def __init__(self):
        self.repl_tool = REPLTool()
        self.max_iterations = config.langgraph.max_iterations

    def process(self, state: AnalysisState) -> AnalysisState:
        """Verify hypotheses for current dataset"""
        logger.info("Verifier processing")

        current_dataset = state.get_current_dataset()
        if not current_dataset:
            return state

        try:
            # Verify each hypothesis
            verification_results = []

            for hypothesis in current_dataset.hypotheses or []:
                result = self._verify_hypothesis(hypothesis, current_dataset)
                verification_results.append(result)

                # Check if we should continue or stop
                if result.get("success"):
                    break

            # Update dataset state
            current_dataset.verification_results = verification_results
            current_dataset.status = "verified"

            logger.info(f"Verification completed for dataset {current_dataset.id}")

        except Exception as e:
            error_msg = f"Verification failed: {e}"
            current_dataset.error_message = error_msg
            state.errors.append(error_msg)
            logger.error(error_msg)

        return state

    def _verify_hypothesis(self, hypothesis: Dict[str, Any], dataset: DatasetInfo) -> Dict[str, Any]:
        """Verify a single hypothesis"""
        # Simplified verification
        # In a real system, this would execute actual tests

        return {
            "hypothesis_id": hypothesis["id"],
            "success": True,  # Simplified
            "result": f"Verified hypothesis: {hypothesis['description']}",
            "evidence": ["Sample evidence"]
        }


class ReporterNode:
    """Node for generating final reports"""

    def process(self, state: AnalysisState) -> AnalysisState:
        """Generate report for current dataset"""
        logger.info("Reporter processing")

        current_dataset = state.get_current_dataset()
        if not current_dataset:
            return state

        try:
            # Generate report
            report_content = self._generate_report(current_dataset)

            # Update dataset state
            current_dataset.report_content = report_content
            current_dataset.status = "completed"

            # Move to next dataset
            state.advance_dataset()

            logger.info(f"Report generated for dataset {current_dataset.id}")

        except Exception as e:
            error_msg = f"Report generation failed: {e}"
            current_dataset.error_message = error_msg
            state.errors.append(error_msg)
            logger.error(error_msg)

        return state

    def _generate_report(self, dataset: DatasetInfo) -> str:
        """Generate markdown report for the dataset"""
        report = f"""# 個別データ分析レポート

## 概要

- 結論: 分析完了
- 解析対象動画: {dataset.id}
- 期待値: {dataset.expected_result}
- 検知結果: 確認済み

## 確認結果

### 入出力の確認結果
データ分析が完了しました。

### 考えられる原因
- 仮説検証により特定された問題点

## 推奨事項

- 分析結果に基づく推奨事項

## 参照した仕様/コード（抜粋）
仕様書およびコードを参照しました。
"""

        return report
