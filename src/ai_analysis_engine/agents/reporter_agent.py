"""
Reporter Agent - Generates final analysis reports
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config.config import AlgorithmConfig

from ..config import config
from ..models.state import DatasetInfo
from ..models.types import Hypothesis
from ..tools.repl_tool import REPLTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ReporterAgent:
    """
    Agent for generating final analysis reports
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.openai.model,
            temperature=config.openai.temperature,
            api_key=config.openai.api_key
        )

        self.repl_tool = REPLTool()

        self.report_prompt = ChatPromptTemplate.from_template("""
あなたは汎用レポート作成エージェントです。このシステムは様々なアルゴリズムに対して適用可能な汎用AI分析エンジンです。

**重要指示**:
- 特定のアルゴリズム（眠気検知、顔認識など）に固有の用語は使用せず、汎用的な表現を使用してください
- 信頼度条件、前提条件、品質条件などの汎用的な用語を使用してください
- アルゴリズム仕様に基づきつつ、特定のアルゴリズムに依存しない表現を心がけてください



【レポート構造】
1. **概要**: 結論、解析対象動画、フレーム区間、期待値、検知結果
2. **確認結果**: グラフ表示、分析結果、考えられる原因
3. **推奨事項**: 具体的な改善提案
4. **参照した仕様/コード（抜粋）**: 使用した仕様書の参照

【結論作成のガイドライン】
- 「考えられる原因」項目の内容を端的に整理する
- ユーザーに直感的にわかりやすい表現を使用する
- 技術的な詳細は避け、問題の本質を明確に伝える
- 1-2文程度の簡潔なまとめとする

【アルゴリズム仕様に基づくレポート項目】
- **評価指標確認**: {thresholds}と実際のデータ分布の比較
- **入力特徴量検証**: {input_columns}の妥当性と分布分析
- **出力形式確認**: {output_columns}の仕様準拠状況
- **値範囲検証**: {value_ranges}の遵守状況確認
- **前提条件分析**: 検知結果が有効となるための信頼度・品質条件の充足状況

データセット情報:
{dataset_info}

アルゴリズム仕様:
{algorithm_spec}

評価環境仕様:
{evaluation_spec}

分析結果:
{analysis_results}

仮説と検証結果:
{hypotheses_results}

【レポート作成ガイドライン】

# 個別データ分析レポート - {dataset_id}

## 概要

- 結論: [考えられる原因を端的に整理したユーザーに直感的にわかりやすい内容]
- 解析対象動画: {dataset_id}
- フレーム区間: [データセットから取得したフレーム区間]
- 期待値: [データセットから取得した期待値]
- 検知結果: [分析結果に基づく検知結果]

## 確認結果

![アルゴリズム出力結果のグラフ](./plots/{dataset_id}/algorithm_output_plot.png)
アルゴリズム出力結果
<!-- アルゴリズム出力データの時系列グラフ（閾値付き）-->

![コア出力結果のグラフ](./plots/{dataset_id}/core_output_plot.png)
コア出力結果
<!-- コア出力データの時系列グラフ（閾値付き）-->

<!-- 上記のグラフを生成後、閉眼傾向があるかを仮説検証にて確認し、結果を以下に記載 -->
- 入出力の確認結果: [具体的な数値分析結果]

- 考えられる原因: [分析結果に基づき、1つ以上の原因を箇点で整理]


## 推奨事項

- [具体的な改善提案と次のステップ]

## 参照した仕様/コード（抜粋）
... <!-- 仮説検証にて参照した仕様/コードをすべて記載-->

---

""")

    def generate_report(self, dataset: DatasetInfo,
                       analysis_results: Dict[str, Any],
                       hypotheses: List[Hypothesis]) -> str:
        """
        Generate a comprehensive report for the dataset using algorithm configuration

        Args:
            dataset: Dataset information
            analysis_results: Results from all analyses
            hypotheses: Generated and verified hypotheses

        Returns:
            Markdown report content
        """
        try:
            logger.info(f"Generating report for dataset {dataset.id}")

            # Load algorithm configuration dynamically
            algorithm_config = self._load_algorithm_config(dataset)

            # Load specifications
            algorithm_spec = ""
            if dataset.algorithm_spec_md:
                try:
                    with open(dataset.algorithm_spec_md, 'r', encoding='utf-8') as f:
                        algorithm_spec = f.read()
                        logger.info(f"Loaded algorithm spec: {len(algorithm_spec)} characters")
                except Exception as e:
                    logger.warning(f"Failed to load algorithm spec: {e}")

            evaluation_spec = ""
            if dataset.evaluation_spec_md:
                try:
                    with open(dataset.evaluation_spec_md, 'r', encoding='utf-8') as f:
                        evaluation_spec = f.read()
                        logger.info(f"Loaded evaluation spec: {len(evaluation_spec)} characters")
                except Exception as e:
                    logger.warning(f"Failed to load evaluation spec: {e}")

            # Prepare algorithm-specific context
            algorithm_context = self._prepare_algorithm_context(algorithm_config)

            # Debug: Log specification content summaries
            logger.info(f"Algorithm spec preview: {algorithm_spec[:200] if algorithm_spec else 'None'}")
            logger.info(f"Evaluation spec preview: {evaluation_spec[:200] if evaluation_spec else 'None'}")

            # Generate visualization plots
            self._generate_visualization_plots(dataset, algorithm_config)

            # Prepare report data
            dataset_info = self._prepare_dataset_info(dataset)
            analysis_summary = self._summarize_analysis_results(analysis_results)
            hypotheses_summary = self._summarize_hypotheses(hypotheses)

            # Use LLM to generate report with algorithm context
            chain = self.report_prompt | self.llm

            response = chain.invoke({
                "dataset_id": dataset.id,
                "dataset_info": dataset_info,
                "algorithm_spec": algorithm_spec[:3000],
                "evaluation_spec": evaluation_spec[:2000],
                "analysis_results": analysis_summary,
                "hypotheses_results": hypotheses_summary,
                **algorithm_context
            })

            # Process the LLM response
            report_content = response.content.strip()

            # Add algorithm configuration info to report
            if algorithm_config:
                report_content += f"\n\n## アルゴリズム設定情報\n"
                report_content += f"- アルゴリズム名: {algorithm_config.name}\n"
                report_content += f"- 閾値設定: {algorithm_config.thresholds}\n"
                report_content += f"- 必須列: {algorithm_config.required_columns}\n"

            logger.info(f"Generated report for dataset {dataset.id}: {len(report_content)} characters")
            return report_content

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            # Return basic error report
            return f"""# エラーレポート - {dataset.id}

## エラー発生
レポート生成中にエラーが発生しました: {e}

## 基本情報
- データセットID: {dataset.id}
- 期待値: {dataset.expected_result}
"""

    def _generate_visualization_plots(self, dataset: DatasetInfo, algorithm_config: 'AlgorithmConfig'):
        """Generate visualization plots for algorithm and core output data"""
        try:
            logger.info(f"Generating visualization plots for dataset {dataset.id}")

            # Create plots directory in the same location as reports
            plots_dir = Path("output/results/reports/plots") / dataset.id
            plots_dir.mkdir(parents=True, exist_ok=True)

            # Load data using REPL tool
            algorithm_data_path = dataset.algorithm_output_csv
            core_data_path = dataset.core_output_csv

            if algorithm_data_path and core_data_path:
                # Generate algorithm output plot
                self._generate_algorithm_output_plot(algorithm_data_path, algorithm_config, plots_dir / "algorithm_output_plot.png")

                # Generate core output plot
                self._generate_core_output_plot(core_data_path, algorithm_config, plots_dir / "core_output_plot.png")

                logger.info(f"Generated plots for dataset {dataset.id}")
            else:
                logger.warning(f"Data paths not available for dataset {dataset.id}")

        except Exception as e:
            logger.error(f"Failed to generate plots for dataset {dataset.id}: {e}")

    def _generate_algorithm_output_plot(self, data_path: str, algorithm_config: 'AlgorithmConfig', output_path: Path):
        """Generate plot for algorithm output data with thresholds"""
        try:
            # Extract threshold information outside f-string
            thresholds_code = ""
            if hasattr(algorithm_config, 'thresholds') and algorithm_config.thresholds:
                thresholds_list = []
                for threshold_name, threshold_value in algorithm_config.thresholds.items():
                    thresholds_list.append(f"('{threshold_name}', {threshold_value})")
                thresholds_code = f"thresholds = [{', '.join(thresholds_list)}]"
            else:
                thresholds_code = "thresholds = []"

            # Determine plot columns and thresholds dynamically
            plot_columns_code = ""
            if hasattr(algorithm_config, 'output_columns') and algorithm_config.output_columns:
                # Use output columns from algorithm config
                output_cols = [col for col in algorithm_config.output_columns if col]
                if output_cols:
                    plot_columns_code = f"plot_columns = {output_cols}"
                else:
                    plot_columns_code = "plot_columns = df.columns[:min(5, len(df.columns))]"  # Default to first 5 columns
            else:
                plot_columns_code = "plot_columns = df.columns[:min(5, len(df.columns))]"  # Default to first 5 columns

            # Create plot generation code
            plot_code = f"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv(r'{data_path}')

# Thresholds configuration
{thresholds_code}

# Determine columns to plot
{plot_columns_code}

# Filter to columns that exist in the data
plot_columns = [col for col in plot_columns if col in df.columns]
if not plot_columns:
    plot_columns = df.columns[:min(5, len(df.columns))]

# Create figure with subplots
fig, axes = plt.subplots(len(plot_columns), 1, figsize=(12, 4*len(plot_columns)))
if len(plot_columns) == 1:
    axes = [axes]

# Plot each column with thresholds
for i, col in enumerate(plot_columns):
    axes[i].plot(df.index, df[col], label=col, linewidth=2)

    # Add threshold lines if available and column matches threshold
    for threshold_name, threshold_value in thresholds:
        # Apply threshold if column name matches threshold name (case-insensitive partial match)
        if threshold_name.lower().replace('_threshold', '').replace('_', '') in col.lower():
            label_text = f'{{threshold_name}}: {{threshold_value}}'
            axes[i].axhline(y=threshold_value, color='red', linestyle='--', label=label_text)

    axes[i].set_title(f'{{col}} - Algorithm Output')
    axes[i].set_xlabel('Frame')
    axes[i].set_ylabel('Value')
    axes[i].legend()
    axes[i].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(r'{output_path}', dpi=150, bbox_inches='tight')
plt.close()
"""

            # Execute plot generation
            result = self.repl_tool.execute_code(plot_code)
            if result.get('success'):
                logger.info(f"Generated algorithm output plot: {output_path}")
            else:
                logger.error(f"Failed to generate algorithm output plot: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error generating algorithm output plot: {e}")

    def _generate_core_output_plot(self, data_path: str, algorithm_config: 'AlgorithmConfig', output_path: Path):
        """Generate plot for core output data with thresholds"""
        try:
            # Extract input columns and thresholds outside f-string
            input_cols = algorithm_config.input_columns if hasattr(algorithm_config, 'input_columns') else []
            input_cols_str = str(input_cols)

            thresholds_code = ""
            if hasattr(algorithm_config, 'thresholds') and algorithm_config.thresholds:
                thresholds_list = []
                for threshold_name, threshold_value in algorithm_config.thresholds.items():
                    thresholds_list.append(f"('{threshold_name}', {threshold_value})")
                thresholds_code = f"thresholds = [{', '.join(thresholds_list)}]"
            else:
                thresholds_code = "thresholds = []"

            # Create plot generation code
            plot_code = f"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv(r'{data_path}')

# Input columns and thresholds configuration
input_cols = {input_cols_str}
{thresholds_code}

# Determine columns to plot from input columns
plot_cols = []
if input_cols:
    plot_cols = [col for col in input_cols if col in df.columns]

# If no input columns specified or none exist, determine columns dynamically based on data types and threshold names
if not plot_cols:
    # First, try to find columns that match threshold names
    threshold_base_names = []
    for threshold_name in thresholds:
        base_name = threshold_name[0].lower().replace('_threshold', '').replace('_', '')
        threshold_base_names.append(base_name)

    # Look for columns that match threshold names
    for col in df.columns:
        col_lower = col.lower()
        if any(base_name in col_lower for base_name in threshold_base_names):
            plot_cols.append(col)

    # If still no matches, look for numeric columns (likely to be features)
    if not plot_cols:
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64'] and col.lower() not in ['frame', 'index', 'timestamp']:
                plot_cols.append(col)
                if len(plot_cols) >= 6:  # Limit to 6 columns max
                    break

# If still no columns, use first few numeric columns
if not plot_cols:
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            plot_cols.append(col)
            if len(plot_cols) >= 6:  # Limit to 6 columns max
                break

# Ensure we have at least one column to plot
if len(plot_cols) == 0:
    print("No columns available for plotting")
else:
    fig, axes = plt.subplots(len(plot_cols), 1, figsize=(12, 4*len(plot_cols)))
    if len(plot_cols) == 1:
        axes = [axes]

    # Plot each input column with thresholds
    for i, col in enumerate(plot_cols):
        axes[i].plot(df.index, df[col], label=col, linewidth=2)

        # Add threshold lines if available and column matches threshold
        for threshold_name, threshold_value in thresholds:
            # Apply threshold if column name matches threshold name (case-insensitive partial match)
            if threshold_name.lower().replace('_threshold', '').replace('_', '') in col.lower():
                label_text = f'{{threshold_name}}: {{threshold_value}}'
                axes[i].axhline(y=threshold_value, color='red', linestyle='--', label=label_text)

        axes[i].set_title(f'{{col}} - Core Input Feature')
        axes[i].set_xlabel('Frame')
        axes[i].set_ylabel('Value')
        axes[i].legend()
        axes[i].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(r'{output_path}', dpi=150, bbox_inches='tight')
    plt.close()
"""

            # Execute plot generation
            result = self.repl_tool.execute_code(plot_code)
            if result.get('success'):
                logger.info(f"Generated core output plot: {output_path}")
            else:
                logger.error(f"Failed to generate core output plot: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error generating core output plot: {e}")

    def _load_algorithm_config(self, dataset: DatasetInfo):
        """
        Load algorithm configuration from dataset specification

        Args:
            dataset: Dataset information

        Returns:
            AlgorithmConfig: Loaded configuration
        """
        if dataset.algorithm_spec_md:
            try:
                return config.load_algorithm_config_from_file(dataset.algorithm_spec_md)
            except Exception as e:
                logger.warning(f"Failed to load algorithm config from file: {e}")

        # Return default configuration
        from ..config.config import AlgorithmConfig
        return AlgorithmConfig()

    def _prepare_algorithm_context(self, algorithm_config) -> Dict[str, Any]:
        """
        Prepare algorithm-specific context for LLM

        Args:
            algorithm_config: AlgorithmConfig object

        Returns:
            Dictionary with algorithm context
        """
        return {
            "input_columns": algorithm_config.input_columns,
            "output_columns": algorithm_config.output_columns,
            "thresholds": algorithm_config.thresholds,
            "value_ranges": algorithm_config.value_ranges,
            "valid_values": algorithm_config.valid_values
        }

    def _prepare_dataset_info(self, dataset: DatasetInfo) -> str:
        """Prepare dataset information for report generation"""
        info_lines = [
            f"データセットID: {dataset.id}",
            f"期待値: {dataset.expected_result}",
            f"アルゴリズム出力: {dataset.algorithm_output_csv}",
            f"コア出力: {dataset.core_output_csv}",
            f"評価環境仕様: {dataset.evaluation_spec_md}"
        ]

        return "\n".join(info_lines)

    def _summarize_analysis_results(self, analysis_results: Dict[str, Any]) -> str:
        """Summarize analysis results"""
        if not analysis_results:
            return "分析結果なし"

        summary_lines = []

        # Data analysis summary
        if "basic_analysis" in analysis_results:
            basic = analysis_results["basic_analysis"]
            for name, analysis in basic.items():
                if isinstance(analysis, dict) and "shape" in analysis:
                    shape = analysis["shape"]
                    summary_lines.append(f"{name}: {shape[0]}行 x {shape[1]}列")

        # Consistency summary
        if "consistency_check" in analysis_results:
            consistency = analysis_results["consistency_check"]
            if consistency.get("overall_consistent"):
                summary_lines.append("整合性: 問題なし")
            else:
                issues = consistency.get("issues", [])
                summary_lines.append(f"整合性の問題: {len(issues)}個")

        return "\n".join(summary_lines)

    def _summarize_hypotheses(self, hypotheses: List[Hypothesis]) -> str:
        """Summarize hypotheses and their verification results"""
        if not hypotheses:
            return "仮説なし"

        summary_lines = []

        for hypo in hypotheses:
            status = "検証済み" if hypo.verification_status.value == "verified" else "未検証"
            summary_lines.append(f"- {hypo.type.value}: {hypo.description}")
            summary_lines.append(f"  信頼度: {hypo.confidence_score:.2f}, 状態: {status}")

            if hypo.suggested_fix:
                summary_lines.append(f"  提案修正: {hypo.suggested_fix}")

        return "\n".join(summary_lines)

    def _get_existing_plots(self, dataset: DatasetInfo) -> Dict[str, str]:
        """Get existing plots for the dataset"""
        plots = {}

        try:
            # Get plots directory
            plots_dir = config.output_dir / "plots" / dataset.id

            if plots_dir.exists():
                # Find plot files
                for png_file in plots_dir.glob("*.png"):
                    file_name = png_file.stem

                    # Categorize plots based on filename
                    if ('2' in file_name or '4' in file_name or 'algo' in file_name.lower() or
                        'is_drowsy' in file_name.lower() or file_name.endswith('_timeseries')):
                        plots['algorithm'] = str(png_file)
                    elif ('WIN_' in file_name or 'analysis' in file_name.lower() or
                          'leye' in file_name.lower() or 'reye' in file_name.lower() or
                          'confidence' in file_name.lower()):
                        plots['core'] = str(png_file)

            logger.info(f"Found existing plots for {dataset.id}: {list(plots.keys())}")

        except Exception as e:
            logger.error(f"Failed to get existing plots: {e}")

        return plots

    def _generate_report_plots(self, dataset: DatasetInfo) -> Dict[str, str]:
        """Generate plots for the report"""
        plots = {}

        try:
            # Create plots directory for this dataset
            plots_dir = config.output_dir / "reports" / dataset.id
            plots_dir.mkdir(parents=True, exist_ok=True)

            # Load data
            dataframes = self.repl_tool.load_csv_data([
                dataset.algorithm_output_csv,
                dataset.core_output_csv
            ])

            # Generate time series plots
            for name, df in dataframes.items():
                if len(df) > 0 and len(df.select_dtypes(include=['number']).columns) > 0:
                    # Get first numeric column
                    numeric_col = df.select_dtypes(include=['number']).columns[0]

                    # Create plot
                    code = f"""
import matplotlib.pyplot as plt
import pandas as pd

# Create time series plot
plt.figure(figsize=(12, 6))

if 'timestamp' in df.columns:
    plt.plot(df['timestamp'], df['{numeric_col}'], marker='o', linestyle='-')
    plt.xlabel('Timestamp')
else:
    plt.plot(df.index, df['{numeric_col}'], marker='o', linestyle='-')
    plt.xlabel('Index')

plt.ylabel('{numeric_col}')
plt.title('{name} - {numeric_col} Time Series')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
plt.tight_layout()
"""

                    plot_path = str(plots_dir / f"{name}_{numeric_col}_timeseries.png")
                    result = self.repl_tool.create_plot(code, {"df": df}, plot_path)

                    if result.get("success"):
                        plots[name] = plot_path

        except Exception as e:
            logger.error(f"Failed to generate report plots: {e}")

        return plots

    def _insert_plots_into_report(self, report_content: str, plots: Dict[str, str], dataset_id: str) -> str:
        """Insert plot references into the report with correct relative paths"""
        # Insert algorithm output plot
        if "algorithm" in plots:
            # Convert absolute path to relative path from reports directory
            # reports/dataset_report.md -> ../../plots/dataset/filename.png
            relative_path = f"../../plots/{dataset_id}/{Path(plots['algorithm']).name}"
            plot_ref = f"\n![アルゴリズム出力結果の時系列グラフ]({relative_path})\n"
            report_content = report_content.replace(
                "### アルゴリズム出力結果の当該タスク区間における時系列グラフ",
                "### アルゴリズム出力結果の当該タスク区間における時系列グラフ" + plot_ref
            )

        # Insert core output plot
        if "core" in plots:
            # Convert absolute path to relative path from reports directory
            relative_path = f"../../plots/{dataset_id}/{Path(plots['core']).name}"
            plot_ref = f"\n![コア出力結果の時系列グラフ]({relative_path})\n"
            report_content = report_content.replace(
                "### コア出力結果の当該タスク区間における時系列グラフ",
                "### コア出力結果の当該タスク区間における時系列グラフ" + plot_ref
            )

        return report_content

    def _generate_fallback_report(self, dataset: DatasetInfo, error: str) -> str:
        """Generate a fallback report in case of errors"""
        return f"""# 個別データ分析レポート

## 概要

- 結論 : 分析中にエラーが発生しました
- 解析対象動画： {dataset.id}
- 期待値： {dataset.expected_result}
- 検知結果： エラーにより確認できませんでした

## エラー情報

{error}

## 推奨事項

- エラーの原因を調査してください
- ログを確認して問題を特定してください
"""
