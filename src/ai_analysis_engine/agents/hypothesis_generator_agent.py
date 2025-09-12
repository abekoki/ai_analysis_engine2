"""
Hypothesis Generator Agent - Generates hypotheses about potential issues
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..config import config
from ..models.state import DatasetInfo
from ..models.types import Hypothesis, HypothesisType
from ..tools.rag_tool import RAGTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class HypothesisGeneratorAgent:
    """
    Agent for generating hypotheses about potential issues in the data
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.openai.model,
            temperature=config.openai.temperature,
            api_key=config.openai.api_key
        )

        self.rag_tool = RAGTool()

        self.prompt = ChatPromptTemplate.from_template("""
あなたは仮説生成エージェントです。アルゴリズム仕様を理解し、データ分析結果に基づいて問題の仮説を生成してください。

【重要】アルゴリズム仕様を理解し、その仕様に基づいて問題の仮説を生成してください。

データセット情報:
{dataset_info}

アルゴリズム仕様:
{algorithm_spec}

評価環境仕様:
{evaluation_spec}

データ分析結果:
{data_analysis}

整合性チェック結果:
{consistency_check}

期待値:
{expected_result}

【アルゴリズム仕様に基づく仮説生成アプローチ】
1. **仕様理解**: アルゴリズムの入力パラメータ、判定ロジック、出力形式を把握
2. **データ分析**: 実際のデータが仕様通りの動作を示しているか確認
3. **問題特定**: 仕様と実際のデータの不整合点を特定
4. **根本原因推定**: 仕様に基づいて問題の根本原因を推定

【考慮すべき仮説タイプ（アルゴリズム仕様準拠）】
1. **仕様不整合（specification_inconsistency）**: データ構造や値がアルゴリズム仕様に準拠していない
2. **パラメータ不適切（parameter_inappropriate）**: 判定閾値やパラメータが不適切
3. **アルゴリズム実装誤り（algorithm_bug）**: アルゴリズムのロジックにバグがある
4. **入力データ品質問題（data_quality_issue）**: 各種入力データに問題がある
5. **環境条件不一致（environment_mismatch）**: 評価環境とアルゴリズム仕様の不一致

【特に注目すべき点】
- アルゴリズムの判定閾値と実際のデータ分布の整合性
- 各種指標の閾値とエラーの関係
- アルゴリズムの詳細な判定ロジック
- 計算内容と閾値の妥当性
- エラーコードと仕様書のエラーハンドリングの一致

各仮説について：
- アルゴリズム仕様との関連を明確に
- 具体的な証拠と仕様書の該当箇所
- 仕様に基づいた修正提案

仮説をJSON形式で生成してください。

応答フォーマット:
```json
{{
    "hypotheses": [
        {{
            "id": "unique_id",
            "type": "hypothesis_type",
            "description": "アルゴリズム仕様に基づく詳細な説明",
            "confidence_score": 0.8,
            "evidence": ["仕様書の該当箇所", "実際のデータとの比較"],
            "spec_reference": "仕様書の関連部分",
            "suggested_fix": "仕様に基づいた修正提案"
        }}
    ]
}}
```
""")

    def generate_hypotheses(self, dataset: DatasetInfo,
                          data_analysis: Dict[str, Any],
                          consistency_check: Dict[str, Any]) -> List[Hypothesis]:
        """
        Generate hypotheses based on analysis results

        Args:
            dataset: Dataset information
            data_analysis: Results from data analysis
            consistency_check: Results from consistency checking

        Returns:
            List of generated hypotheses
        """
        try:
            logger.info(f"Generating hypotheses for dataset {dataset.id}")

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

            # Prepare input data
            dataset_info = self._prepare_dataset_info(dataset)
            analysis_summary = self._summarize_analysis(data_analysis)
            consistency_summary = self._summarize_consistency(consistency_check)

            # Use LLM to generate hypotheses
            chain = self.prompt | self.llm

            response = chain.invoke({
                "dataset_info": dataset_info,
                "algorithm_spec": algorithm_spec[:3000],  # Prioritize algorithm spec
                "evaluation_spec": evaluation_spec[:2000],
                "data_analysis": analysis_summary,
                "consistency_check": consistency_summary,
                "expected_result": dataset.expected_result
            })

            # Parse hypotheses from response
            hypotheses = self._parse_hypotheses(response.content)

            # Add rule-based hypotheses
            rule_based = self._generate_rule_based_hypotheses(
                dataset, data_analysis, consistency_check
            )
            hypotheses.extend(rule_based)

            # Remove duplicates and sort by confidence
            unique_hypotheses = self._deduplicate_hypotheses(hypotheses)
            unique_hypotheses.sort(key=lambda h: h.confidence_score, reverse=True)

            logger.info(f"Generated {len(unique_hypotheses)} hypotheses for dataset {dataset.id}")
            return unique_hypotheses

        except Exception as e:
            logger.error(f"Hypothesis generation failed: {e}")
            # Return fallback hypothesis
            return [
                Hypothesis(
                    id="error_fallback",
                    type=HypothesisType.ALGORITHM_BUG,
                    description="Analysis failed, potential algorithm issue",
                    confidence_score=0.5,
                    evidence=["Analysis error occurred"],
                    suggested_fix="Review analysis pipeline"
                )
            ]

    def _prepare_dataset_info(self, dataset: DatasetInfo) -> str:
        """Prepare dataset information for LLM"""
        info_lines = [
            f"データセットID: {dataset.id}",
            f"期待値: {dataset.expected_result}",
            f"アルゴリズム出力: {dataset.algorithm_output_csv}",
            f"コア出力: {dataset.core_output_csv}"
        ]

        if dataset.error_message:
            info_lines.append(f"エラー: {dataset.error_message}")

        return "\n".join(info_lines)

    def _summarize_analysis(self, data_analysis: Dict[str, Any]) -> str:
        """Summarize data analysis results"""
        if not data_analysis:
            return "データ分析結果なし"

        summary_lines = []

        # Basic analysis summary
        basic = data_analysis.get("basic_analysis", {})
        for name, analysis in basic.items():
            if isinstance(analysis, dict) and "shape" in analysis:
                shape = analysis["shape"]
                summary_lines.append(f"{name}: {shape[0]}行 x {shape[1]}列")

                if "missing_values" in analysis:
                    missing = analysis["missing_values"]
                    total_missing = sum(missing.values())
                    if total_missing > 0:
                        summary_lines.append(f"  欠損値: {total_missing}個")

        return "\n".join(summary_lines)

    def _summarize_consistency(self, consistency_check: Dict[str, Any]) -> str:
        """Summarize consistency check results"""
        if not consistency_check:
            return "整合性チェック結果なし"

        summary_lines = []

        if consistency_check.get("overall_consistent"):
            summary_lines.append("全体的に整合性あり")
        else:
            summary_lines.append("整合性の問題あり")

        issues = consistency_check.get("issues", [])
        if issues:
            summary_lines.append("問題点:")
            for issue in issues[:3]:  # Limit to top 3
                summary_lines.append(f"  - {issue}")

        return "\n".join(summary_lines)

    def _parse_hypotheses(self, response: str) -> List[Hypothesis]:
        """Parse hypotheses from LLM response"""
        hypotheses = []

        try:
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)

                for hypo_data in data.get("hypotheses", []):
                    try:
                        hypothesis = Hypothesis(
                            id=hypo_data["id"],
                            type=HypothesisType(hypo_data["type"]),
                            description=hypo_data["description"],
                            confidence_score=float(hypo_data["confidence_score"]),
                            evidence=hypo_data.get("evidence", []),
                            suggested_fix=hypo_data.get("suggested_fix")
                        )
                        hypotheses.append(hypothesis)
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Invalid hypothesis data: {e}")
                        continue

        except Exception as e:
            logger.warning(f"Failed to parse hypotheses: {e}")

        return hypotheses

    def _generate_rule_based_hypotheses(self, dataset: DatasetInfo,
                                      data_analysis: Dict[str, Any],
                                      consistency_check: Dict[str, Any]) -> List[Hypothesis]:
        """Generate rule-based hypotheses"""
        hypotheses = []

        # Rule 1: High missing values
        if data_analysis.get("basic_analysis"):
            for name, analysis in data_analysis["basic_analysis"].items():
                if isinstance(analysis, dict) and "missing_values" in analysis:
                    missing = analysis["missing_values"]
                    total_missing = sum(missing.values())
                    if total_missing > 0:
                        hypotheses.append(Hypothesis(
                            id=f"missing_values_{name}",
                            type=HypothesisType.DATA_QUALITY_ISSUE,
                            description=f"データ品質問題: {name}に欠損値が存在 ({total_missing}個)",
                            confidence_score=0.7,
                            evidence=[f"欠損値: {missing}"],
                            suggested_fix="欠損値処理の実装またはデータ収集の見直し"
                        ))

        # Rule 2: Consistency issues
        if not consistency_check.get("overall_consistent", True):
            issues = consistency_check.get("issues", [])
            if issues:
                hypotheses.append(Hypothesis(
                    id="consistency_issue",
                    type=HypothesisType.SPECIFICATION_INCONSISTENCY,
                    description=f"仕様不整合: {issues[0]}",
                    confidence_score=0.8,
                    evidence=issues[:3],
                    suggested_fix="仕様書の確認と実装の修正"
                ))

        # Rule 3: Empty dataframes
        if data_analysis.get("basic_analysis"):
            for name, analysis in data_analysis["basic_analysis"].items():
                if isinstance(analysis, dict) and analysis.get("shape", [0, 0])[0] == 0:
                    hypotheses.append(Hypothesis(
                        id=f"empty_data_{name}",
                        type=HypothesisType.DATA_QUALITY_ISSUE,
                        description=f"データ品質問題: {name}が空のデータ",
                        confidence_score=0.9,
                        evidence=["データフレームが空"],
                        suggested_fix="データ生成プロセスの確認"
                    ))

        return hypotheses

    def _deduplicate_hypotheses(self, hypotheses: List[Hypothesis]) -> List[Hypothesis]:
        """Remove duplicate hypotheses"""
        seen = set()
        unique = []

        for hypo in hypotheses:
            # Create a simple signature for deduplication
            signature = (hypo.type.value, hypo.description[:50])

            if signature not in seen:
                seen.add(signature)
                unique.append(hypo)

        return unique
