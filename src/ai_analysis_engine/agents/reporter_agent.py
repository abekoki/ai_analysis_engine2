"""
Reporter Agent - Generates final analysis reports
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pathlib import Path

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
あなたはレポート作成エージェントです。アルゴリズム仕様に基づいて分析結果を正確に解釈し、包括的なレポートを生成してください。

【重要】アルゴリズム仕様を理解し、その仕様に基づいて結果を解釈してください。

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

【レポート作成アプローチ】
1. **アルゴリズム仕様の理解**: 入力パラメータ、判定ロジック、出力形式を把握
2. **結果の仕様準拠解釈**: 分析結果をアルゴリズム仕様に基づいて解釈
3. **問題点の特定**: 仕様と実際の結果の不整合点を明確に指摘
4. **仕様ベースの推奨**: アルゴリズム仕様に準拠した改善提案

以下の構造でMarkdown形式のレポートを作成してください：

# 個別データ分析レポート - {dataset_id}

## 概要

- 結論: [アルゴリズム仕様に基づく分析結果の要約]
- 解析対象動画: {dataset_id}
- フレーム区間: [期待値で指定された区間]
- 期待値: [自然言語の期待値]
- 検知結果: [アルゴリズム仕様に基づく実際の結果]

## 確認結果

### データ構造確認
- アルゴリズム出力: [列名、データ型、欠損値状況]
- コアライブラリ出力: [列名、データ型、欠損値状況]
- 仕様準拠状況: [アルゴリズム仕様との整合性]

### アルゴリズム出力結果の時系列グラフ
![アルゴリズム出力の時系列グラフ](../../plots/{dataset_id}/2_timeseries.png)
アルゴリズム出力の時系列推移（判定結果列, continuous_timeなどの仕様準拠パラメータ）

### コア出力結果の時系列グラフ
![コア出力の時系列グラフ](../../plots/{dataset_id}/WIN_20250819_10_12_55_Pro_analysis_timeseries.png)
コア出力の時系列推移（アルゴリズムへ入力している指標列などの仕様準拠パラメータ）

### 仕様ベースの詳細分析
- アルゴリズム判定ロジックの検証: [閾値、計算ロジックなどの仕様準拠確認]
- エラーパターンの分析: [各種エラー状況]
- 期待値との整合性: [フレーム区間、検知条件の確認]

- 考えられる原因: [アルゴリズム仕様に基づく根本原因分析]

## 推奨事項

- [アルゴリズム仕様準拠の具体的な改善提案]
- [パラメータ調整、データ品質改善などの提案]

## 参照した仕様/コード（抜粋）

### アルゴリズム仕様の関連部分
[仕様書の判定ロジック、閾値、パラメータなどの抜粋]

### 検証で使用したコード
[仮説検証で使用したPythonコードの抜粋]

### 分析結果の仕様準拠評価
[最終的な仕様準拠状況の評価]
""")

    def generate_report(self, dataset: DatasetInfo,
                       analysis_results: Dict[str, Any],
                       hypotheses: List[Hypothesis]) -> str:
        """
        Generate a comprehensive report for the dataset

        Args:
            dataset: Dataset information
            analysis_results: Results from all analyses
            hypotheses: Generated and verified hypotheses

        Returns:
            Markdown report content
        """
        try:
            logger.info(f"Generating report for dataset {dataset.id}")

            # Load algorithm spec
            algorithm_spec = ""
            if dataset.algorithm_spec_md:
                try:
                    with open(dataset.algorithm_spec_md, 'r', encoding='utf-8') as f:
                        algorithm_spec = f.read()
                        logger.info(f"Loaded algorithm spec: {len(algorithm_spec)} characters")
                except Exception as e:
                    logger.warning(f"Failed to load algorithm spec: {e}")

            # Load evaluation spec
            evaluation_spec = ""
            if dataset.evaluation_spec_md:
                try:
                    with open(dataset.evaluation_spec_md, 'r', encoding='utf-8') as f:
                        evaluation_spec = f.read()
                        logger.info(f"Loaded evaluation spec: {len(evaluation_spec)} characters")
                except Exception as e:
                    logger.warning(f"Failed to load evaluation spec: {e}")

            # Debug: Log specification content summaries
            logger.info(f"Algorithm spec preview: {algorithm_spec[:200] if algorithm_spec else 'None'}")
            logger.info(f"Evaluation spec preview: {evaluation_spec[:200] if evaluation_spec else 'None'}")

            # Prepare report data
            dataset_info = self._prepare_dataset_info(dataset)
            analysis_summary = self._summarize_analysis_results(analysis_results)
            hypotheses_summary = self._summarize_hypotheses(hypotheses)

            # Get existing plots from dataset or generate new ones
            plots = self._get_existing_plots(dataset)

            # Use LLM to generate the report
            chain = self.report_prompt | self.llm

            response = chain.invoke({
                "dataset_info": dataset_info,
                "algorithm_spec": algorithm_spec[:3000],  # Prioritize algorithm spec
                "evaluation_spec": evaluation_spec[:2000],
                "analysis_results": analysis_summary,
                "hypotheses_results": hypotheses_summary,
                "dataset_id": dataset.id
            })

            # Replace {dataset_id} placeholder in the response
            report_content = response.content.replace("{dataset_id}", dataset.id)

            report_content = response.content
            logger.info(f"Generated report content length: {len(report_content)}")
            logger.info(f"Report content preview: {report_content[:500]}")

            # Add plots to the report with correct relative paths
            if plots:
                report_content = self._insert_plots_into_report(report_content, plots, dataset.id)

            logger.info(f"Report generated for dataset {dataset.id}")
            return report_content

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return self._generate_fallback_report(dataset, str(e))

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
