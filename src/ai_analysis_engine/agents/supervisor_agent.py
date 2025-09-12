"""
Supervisor Agent - Controls the overall analysis workflow
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..config import config
from ..models.state import AnalysisState
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SupervisorAgent:
    """
    Supervisor agent that controls the analysis workflow
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.openai.model,
            temperature=config.openai.temperature,
            api_key=config.openai.api_key
        )

        self.prompt = ChatPromptTemplate.from_template("""
あなたは時系列データ分析システムの監督者です。現在の状態に基づいて、次の適切なアクションを決定してください。

現在の状態:
{state_summary}

利用可能なアクション:
- data_checker: データの確認と分析
- consistency_checker: データと仕様の整合性チェック
- hypothesis_generator: 問題仮説の生成
- verifier: 仮説の検証
- reporter: レポート生成

次のステップを決定し、理由を説明してください。

応答フォーマット:
```json
{{
    "next_action": "アクション名",
    "reason": "決定理由",
    "dataset_id": "対象データセットID"
}}
```
""")

    def decide_next_action(self, state: AnalysisState) -> Dict[str, Any]:
        """
        Decide the next action based on current state

        Args:
            state: Current analysis state

        Returns:
            Dictionary with next action decision
        """
        try:
            # Prepare state summary
            state_summary = self._create_state_summary(state)

            # Get LLM decision
            chain = self.prompt | self.llm

            response = chain.invoke({
                "state_summary": state_summary
            })

            # Parse response
            decision = self._parse_llm_response(response.content)

            logger.info(f"Supervisor decided: {decision}")
            return decision

        except Exception as e:
            logger.error(f"Supervisor decision failed: {e}")
            # Fallback decision
            return {
                "next_action": "data_checker",
                "reason": "Error in decision making, defaulting to data_checker",
                "dataset_id": state.get_current_dataset().id if state.get_current_dataset() else None
            }

    def _create_state_summary(self, state: AnalysisState) -> str:
        """Create a summary of the current state for the LLM"""
        summary_lines = []

        summary_lines.append(f"ワークフローステップ: {state.workflow_step}")
        summary_lines.append(f"データセット数: {len(state.datasets)}")
        summary_lines.append(f"現在のデータセットインデックス: {state.current_dataset_index}")

        # Current dataset info
        current_dataset = state.get_current_dataset()
        if current_dataset:
            summary_lines.append(f"現在のデータセット: {current_dataset.id}")
            summary_lines.append(f"ステータス: {current_dataset.status}")
            summary_lines.append(f"期待値: {current_dataset.expected_result}")

            if current_dataset.error_message:
                summary_lines.append(f"エラー: {current_dataset.error_message}")

        # Processing summary
        processing = state.get_processing_summary()
        summary_lines.append(f"完了: {processing['completed']}/{processing['total_datasets']}")
        summary_lines.append(f"失敗: {processing['failed']}")

        # Errors
        if state.errors:
            summary_lines.append(f"システムエラー数: {len(state.errors)}")

        return "\n".join(summary_lines)

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract decision"""
        try:
            # Extract JSON from response
            import json
            import re

            # Find JSON in response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without markdown
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                json_str = json_match.group(0) if json_match else response

            decision = json.loads(json_str)

            # Validate required fields
            required_fields = ["next_action", "reason"]
            for field in required_fields:
                if field not in decision:
                    raise ValueError(f"Missing required field: {field}")

            return decision

        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            # Return fallback
            return {
                "next_action": "data_checker",
                "reason": f"Failed to parse response: {e}",
                "dataset_id": None
            }
