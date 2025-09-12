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
あなたはレポート作成エージェントです。分析結果を基に包括的なレポートを生成してください。

データセット情報:
{dataset_info}

分析結果:
{analysis_results}

仮説と検証結果:
{hypotheses_results}

以下の構造でMarkdown形式のレポートを作成してください：

# 個別データ分析レポート

## 概要

- 結論 : [分析結果の要約]
- 解析対象動画： [データセット情報]
- フレーム区間: [該当区間]
- 期待値：[期待値]
- 検知結果： [実際の結果]

## 確認結果

[データの確認結果を記述]

### アルゴリズム出力結果の当該タスク区間における時系列グラフ
[グラフの説明]

### コア出力結果の当該タスク区間における時系列グラフ
[グラフの説明]

- 入出力の確認結果：[詳細な確認結果]

- 考えられる原因1 : [主要な問題点]

## 推奨事項

- [具体的な推奨事項]

## 参照した仕様/コード（抜粋）
[関連する仕様やコードの抜粋]
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

            # Prepare report data
            dataset_info = self._prepare_dataset_info(dataset)
            analysis_summary = self._summarize_analysis_results(analysis_results)
            hypotheses_summary = self._summarize_hypotheses(hypotheses)

            # Generate plots for the report
            plots = self._generate_report_plots(dataset)

            # Use LLM to generate the report
            chain = self.report_prompt | self.llm

            response = chain.invoke({
                "dataset_info": dataset_info,
                "analysis_results": analysis_summary,
                "hypotheses_results": hypotheses_summary
            })

            report_content = response.content

            # Add plots to the report
            if plots:
                report_content = self._insert_plots_into_report(report_content, plots)

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

    def _insert_plots_into_report(self, report_content: str, plots: Dict[str, str]) -> str:
        """Insert plot references into the report"""
        # Insert algorithm output plot
        if "algorithm" in plots:
            plot_ref = f"\n![アルゴリズム出力結果の時系列グラフ]({plots['algorithm']})\n"
            report_content = report_content.replace(
                "### アルゴリズム出力結果の当該タスク区間における時系列グラフ",
                "### アルゴリズム出力結果の当該タスク区間における時系列グラフ" + plot_ref
            )

        # Insert core output plot
        if "core" in plots:
            plot_ref = f"\n![コア出力結果の時系列グラフ]({plots['core']})\n"
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
