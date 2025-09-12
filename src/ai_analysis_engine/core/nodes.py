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
                state.vector_stores.segments = {segment: f"vectorstore_{segment}" for segment in documents.keys()}
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
            "algorithm_code": [],
            "evaluation_code": []
        }

        # Add specification documents
        for spec_doc in state.spec_documents:
            if "algorithm" in spec_doc.lower():
                documents["algorithm_specs"].append(spec_doc)
            elif "evaluation" in spec_doc.lower():
                documents["evaluation_specs"].append(spec_doc)
            else:
                documents["algorithm_specs"].append(spec_doc)

        # Add code documents
        for code_doc in state.code_documents:
            if "algorithm" in code_doc.lower() or code_doc.endswith(('.py', '.cpp', '.java', '.js', '.ts')):
                documents["algorithm_code"].append(code_doc)
            else:
                documents["evaluation_code"].append(code_doc)

        # Add dataset-specific documents
        for dataset in state.datasets:
            if dataset.algorithm_spec_md:
                documents["algorithm_specs"].append(dataset.algorithm_spec_md)
            if dataset.evaluation_spec_md:
                documents["evaluation_specs"].append(dataset.evaluation_spec_md)

            # Add algorithm code files
            documents["algorithm_code"].extend(dataset.algorithm_code_files)

            # Add evaluation code files
            documents["evaluation_code"].extend(dataset.evaluation_code_files)

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
        if current_dataset.status == "failed":
            # If failed, advance to next dataset
            state.advance_dataset()
            if state.get_current_dataset():
                state.workflow_step = "data_checker"
            else:
                state.workflow_step = "completed"
        elif current_dataset.status == "pending":
            state.workflow_step = "data_checker"
        elif current_dataset.status == "data_checked":
            state.workflow_step = "consistency_checker"
        elif current_dataset.status == "consistency_checked":
            state.workflow_step = "hypothesis_generator"
        elif current_dataset.status == "hypothesis_generated":
            state.workflow_step = "verifier"
        elif current_dataset.status == "verified":
            state.workflow_step = "reporter"
        elif current_dataset.status == "completed":
            # Advance to next dataset
            state.advance_dataset()
            if state.get_current_dataset():
                state.workflow_step = "data_checker"
            else:
                state.workflow_step = "completed"
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
            logger.info(f"Loaded {len(dataframes)} dataframes: {list(dataframes.keys())}")

            # Analyze data
            analysis_results = {}
            for name, df in dataframes.items():
                try:
                    logger.info(f"Analyzing dataframe {name} with shape {df.shape}")
                    analysis_results[name] = self.repl_tool.analyze_dataframe(df, name)
                except Exception as e:
                    logger.error(f"Failed to analyze dataframe {name}: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    analysis_results[name] = {"error": str(e)}

            # Create plots
            logger.info("Creating data plots")
            plot_paths = self._create_data_plots(dataframes, current_dataset.id)
            logger.info(f"Created plot paths: {plot_paths}")

            # Query column information from specs
            logger.info("Getting column information from specs")
            try:
                column_info = self._get_column_info_from_specs(current_dataset)
                logger.info(f"Column info keys: {list(column_info.keys()) if column_info else 'None'}")
            except Exception as e:
                logger.error(f"Failed to get column info: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                column_info = {}

            # Update dataset state
            current_dataset.data_summary = {
                "analysis": analysis_results,
                "plots": plot_paths,
                "column_info": column_info
            }
            current_dataset.status = "data_checked"

            # Store analysis results in state for later use
            logger.info("Storing analysis results in state")
            try:
                if not hasattr(state, 'analysis_results'):
                    state.analysis_results = {}
                state.analysis_results[current_dataset.id] = {
                    "analysis": analysis_results,
                    "plots": plot_paths,
                    "column_info": column_info
                }
                logger.info(f"Successfully stored results for dataset {current_dataset.id}")
            except Exception as e:
                logger.error(f"Failed to store analysis results: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

            logger.info(f"Data checking completed for dataset {current_dataset.id}")

        except Exception as e:
            error_msg = f"Data checking failed: {e}"
            current_dataset.error_message = error_msg
            current_dataset.status = "failed"
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
                if len(df) == 0:
                    continue

                # Determine x axis (prefer frame-based)
                x_col = None
                if 'frame_num' in df.columns:
                    x_col = 'frame_num'
                elif 'frame' in df.columns:
                    x_col = 'frame'

                # Determine y series depending on file type
                y_series = []
                y_label = 'Value'
                if {'left_eye_closed', 'right_eye_closed'}.issubset(set(df.columns)) or 'is_drowsy' in df.columns:
                    # Algorithm output: plot drowsy/closed as 0/1
                    if 'is_drowsy' in df.columns:
                        y_series.append(('is_drowsy', 'is_drowsy'))
                        y_label = 'is_drowsy'
                    if 'left_eye_closed' in df.columns:
                        y_series.append(('left_eye_closed', 'left_eye_closed'))
                    if 'right_eye_closed' in df.columns:
                        y_series.append(('right_eye_closed', 'right_eye_closed'))
                elif {'leye_openness', 'reye_openness'}.issubset(set(df.columns)):
                    # Core output: plot openness for both eyes
                    y_series.append(('leye_openness', 'Left Eye Openness'))
                    y_series.append(('reye_openness', 'Right Eye Openness'))
                    y_label = 'Eye Openness'
                else:
                    # Fallback: plot first numeric column
                    num_cols = df.select_dtypes(include=['number']).columns
                    if len(num_cols) > 0:
                        y_series.append((num_cols[0], str(num_cols[0])))

                if x_col is None and len(y_series) == 0:
                    continue

                # Build plotting code
                series_code_lines = []
                for col, label in y_series:
                    # Booleans to int for visualization
                    series_code_lines.append(f"(df['{col}'].astype(int) if df['{col}'].dtype == 'bool' else df['{col}'])")
                series_code = "\n".join([f"plt.plot(df['{x_col}'] if '{x_col}' in df.columns else df.index, {line}, label='{label}')" for (line, (_, label)) in zip(series_code_lines, y_series)])

                code = f"""
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 6))
{series_code}
plt.title(f'{name} Time Series')
plt.xlabel('{x_col if x_col else 'Index'}')
plt.ylabel('{y_label}')
plt.legend()
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
            logger.info("Searching for column information in specs")
            # Search for column-related information
            spec_results = self.rag_tool.search("column format data structure", "evaluation_specs", k=3)
            logger.info(f"Found {len(spec_results)} spec results")

            column_info = {
                "spec_results": spec_results,
                "inferred_columns": {}
            }

            return column_info

        except Exception as e:
            logger.error(f"Failed to get column info: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
        import re
        import numpy as np

        results = {
            "expected_interpretation": expected,
            "checks_performed": [],
            "overall_consistent": True,
            "issues": [],
            "target_interval": None,
            "require_exists": False,
            "detection": {
                "exists": False,
                "longest_run": 0,
                "runs": []
            },
            "eye_openness_stats": {}
        }

        # Basic file presence checks
        for name, df in dataframes.items():
            if len(df) == 0:
                results["issues"].append(f"Empty dataframe: {name}")
            else:
                results["checks_performed"].append(f"Dataframe {name}: {len(df)} rows")

        # Parse expected text: frame interval and keyword
        m = re.search(r"フレーム(?:区間)?\s*(\d+)\s*[-〜~]\s*(\d+)", expected)
        if m:
            start_f = int(m.group(1))
            end_f = int(m.group(2))
            if start_f > end_f:
                start_f, end_f = end_f, start_f
            results["target_interval"] = {"start": start_f, "end": end_f}

        require_exists = ("連続閉眼" in expected)
        results["require_exists"] = require_exists

        # Analyze eye openness from core output
        core_df = None
        for df in dataframes.values():
            cols = set(df.columns)
            if any(col for col in cols if 'openness' in col.lower()):
                core_df = df.copy()
                break

        if core_df is not None:
            frame_col = 'frame' if 'frame' in core_df.columns else None
            openness_cols = [col for col in core_df.columns if 'openness' in col.lower()]

            if openness_cols and frame_col and results["target_interval"]:
                s = results["target_interval"]["start"]
                e = results["target_interval"]["end"]
                sub = core_df[(core_df[frame_col] >= s) & (core_df[frame_col] <= e)]

                if len(sub) > 0:
                    stats = {}
                    for col in openness_cols:
                        mean_val = float(sub[col].mean())
                        stats[col] = {
                            "mean": round(mean_val, 3),
                            "min": float(sub[col].min()),
                            "max": float(sub[col].max())
                        }
                    results["eye_openness_stats"] = stats

        # Try to detect continuous eye closure in algorithm output (generic approach)
        algo_df = None
        for df in dataframes.values():
            cols = set(df.columns)
            if 'frame_num' in cols or 'frame' in cols:
                # Look for boolean/binary columns that might indicate closure/drowsiness
                closure_cols = [col for col in cols if any(keyword in col.lower()
                    for keyword in ['closed', 'drowsy', 'sleep', 'blink'])]
                if closure_cols:
                    algo_df = df.copy()
                    break

        if algo_df is None:
            results["issues"].append("Algorithm dataframe not found for detection")
            results["overall_consistent"] = False
            return results

        # Select frame column
        frame_col = 'frame_num' if 'frame_num' in algo_df.columns else ('frame' if 'frame' in algo_df.columns else None)
        if frame_col is None:
            results["issues"].append("Frame column not found in algorithm output")
            results["overall_consistent"] = False
            return results

        # Restrict to interval if provided
        if results["target_interval"]:
            s = results["target_interval"]["start"]
            e = results["target_interval"]["end"]
            algo_df = algo_df[(algo_df[frame_col] >= s) & (algo_df[frame_col] <= e)]

        # Build closed boolean series (generic approach)
        closed_series = None

        # Try different strategies to identify closure indicators
        closure_cols = [col for col in algo_df.columns if any(keyword in col.lower()
            for keyword in ['closed', 'drowsy', 'sleep', 'blink'])]

        if closure_cols:
            # Combine all closure indicators
            combined_closed = np.zeros(len(algo_df), dtype=bool)
            for col in closure_cols:
                if algo_df[col].dtype == bool:
                    combined_closed |= algo_df[col].astype(bool)
                elif algo_df[col].dtype in ['int64', 'float64']:
                    combined_closed |= (algo_df[col] > 0)
            closed_series = combined_closed

        if closed_series is None or closed_series.size == 0:
            results["issues"].append("No closure indicators found in algorithm output")
            results["overall_consistent"] = False
            return results

        # Detect runs of consecutive True (length >= 2)
        runs = []
        longest = 0
        if closed_series.size > 0:
            start_idx = None
            for idx, val in enumerate(closed_series):
                if val and start_idx is None:
                    start_idx = idx
                if (not val or idx == len(closed_series) - 1) and start_idx is not None:
                    end_idx = idx if val and idx == len(closed_series) - 1 else idx - 1
                    run_len = end_idx - start_idx + 1
                    if run_len >= 2:
                        # Map back to frame numbers
                        frame_values = algo_df[frame_col].to_numpy()
                        runs.append({
                            "start_frame": int(frame_values[start_idx]),
                            "end_frame": int(frame_values[end_idx]),
                            "length": int(run_len)
                        })
                        longest = max(longest, run_len)
                    start_idx = None

        exists = len(runs) > 0
        results["detection"] = {
            "exists": exists,
            "longest_run": int(longest),
            "runs": runs
        }

        # Consistency decision
        if require_exists and not exists:
            results["overall_consistent"] = False
            results["issues"].append("Expected continuous closure not found in target interval")
        else:
            results["overall_consistent"] = True

        return results


class HypothesisGeneratorNode:
    """Node for generating hypotheses about issues"""

    def __init__(self):
        from ..agents.hypothesis_generator_agent import HypothesisGeneratorAgent
        self.hypothesis_agent = HypothesisGeneratorAgent()
        self.rag_tool = RAGTool()

    def process(self, state: AnalysisState) -> AnalysisState:
        """Generate hypotheses for current dataset"""
        logger.info("Hypothesis generator processing")

        current_dataset = state.get_current_dataset()
        if not current_dataset:
            return state

        try:
            # Get analysis results and consistency check from state/dataset
            analysis_results = getattr(state, 'analysis_results', {}).get(current_dataset.id, {})
            consistency_check = current_dataset.consistency_check if current_dataset.consistency_check else {}

            # Generate hypotheses using HypothesisGeneratorAgent
            hypotheses = self.hypothesis_agent.generate_hypotheses(
                current_dataset, analysis_results, consistency_check
            )

            # Update dataset state
            current_dataset.hypotheses = hypotheses
            current_dataset.status = "hypothesis_generated"

            # Store hypotheses in state for later use
            if not hasattr(state, 'hypotheses'):
                state.hypotheses = {}
            state.hypotheses[current_dataset.id] = hypotheses

            logger.info(f"Generated {len(hypotheses)} hypotheses for dataset {current_dataset.id}")

        except Exception as e:
            error_msg = f"Hypothesis generation failed: {e}"
            current_dataset.error_message = error_msg
            current_dataset.status = "failed"
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
        from ..agents.verifier_agent import VerifierAgent
        self.verifier_agent = VerifierAgent()
        self.max_iterations = config.langgraph.max_iterations

    def process(self, state: AnalysisState) -> AnalysisState:
        """Verify hypotheses for current dataset"""
        logger.info("Verifier processing")

        current_dataset = state.get_current_dataset()
        if not current_dataset:
            return state

        try:
            # Verify each hypothesis using VerifierAgent
            verification_results = []

            for hypothesis in current_dataset.hypotheses or []:
                if hasattr(hypothesis, 'model_dump'):  # Pydantic model
                    # Convert Hypothesis object to dict for compatibility
                    hypothesis_dict = hypothesis.model_dump()
                    result = self.verifier_agent.verify_hypothesis(current_dataset, hypothesis)
                else:
                    # Legacy dict format
                    result = self._verify_hypothesis(hypothesis, current_dataset)

                verification_results.append(result)

                # Check if we should continue or stop
                if hasattr(result, 'success'):
                    if result.success:
                        break
                elif isinstance(result, dict) and result.get("success"):
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
        # Use consistency check results and core data to assign likely causes
        success = True
        causes = []
        evidence = []

        cc = dataset.consistency_check or {}
        require_exists = cc.get("require_exists", False)
        detection = (cc.get("detection") or {})
        exists = bool(detection.get("exists", False))
        eye_stats = cc.get("eye_openness_stats", {})

        if require_exists and not exists:
            success = False

            # Analyze eye openness statistics
            if eye_stats:
                for col, stats in eye_stats.items():
                    mean_val = stats.get("mean", 1.0)
                    evidence.append(f"{col}平均={mean_val}")

                    if mean_val < 0.3:
                        causes.append("被験者が閉眼していない可能性")
                    elif mean_val > 0.7:
                        causes.append("コアの検出機能に問題がある可能性")
                    else:
                        causes.append("閾値設定ミスの可能性")

            if not eye_stats:
                causes.append("被験者のタスク不正の可能性")
                causes.append("コアの検出機能に問題がある可能性")

        if not causes:
            causes.append("仕様通り動作")

        return {
            "hypothesis_id": hypothesis["id"],
            "success": success,
            "result": "検証完了",
            "causes": causes,
            "evidence": evidence
        }


class ReporterNode:
    """Node for generating final reports"""

    def __init__(self):
        from ..agents.reporter_agent import ReporterAgent
        self.reporter_agent = ReporterAgent()

    def process(self, state: AnalysisState) -> AnalysisState:
        """Generate report for current dataset"""
        logger.info("Reporter processing")

        current_dataset = state.get_current_dataset()
        if not current_dataset:
            return state

        try:
            # Get analysis results and hypotheses from state
            analysis_results = state.analysis_results.get(current_dataset.id, {}) if hasattr(state, 'analysis_results') else {}
            hypotheses = state.hypotheses.get(current_dataset.id, []) if hasattr(state, 'hypotheses') and isinstance(state.hypotheses, dict) else []

            # Generate report using ReporterAgent
            report_content = self.reporter_agent.generate_report(
                current_dataset, analysis_results, hypotheses
            )

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
