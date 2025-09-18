"""
ライブラリAPI - 上位システム統合向けのシンプルなインターフェース
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from .main import AIAnalysisEngine as _InternalEngine
from .config.library_config import AnalysisConfig
from .models.result import AnalysisResult, Hypothesis, AnalysisMetrics
from .exceptions import (
    AIAnalysisError,
    ConfigurationError,
    ValidationError,
    AnalysisError,
    TimeoutError,
    InitializationError
)


class AIAnalysisEngine:
    """
    AI分析エンジンライブラリ - 上位システム統合向け

    シンプルで使いやすいAPIを提供し、複雑な内部処理を隠蔽
    """

    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        エンジン初期化

        Args:
            config: 分析設定（Noneの場合はデフォルト設定を使用）
        """
        self.config = config or AnalysisConfig.from_env()
        self._internal_engine = None
        self._initialized = False

        # 設定検証
        try:
            self.config.validate()
        except ValueError as e:
            raise ConfigurationError(f"Invalid configuration: {e}")

    def initialize(self) -> bool:
        """
        エンジンの初期化

        Returns:
            bool: 初期化成功の場合True

        Raises:
            InitializationError: 初期化失敗時
        """
        try:
            if self._internal_engine is None:
                self._internal_engine = _InternalEngine()

            if not self._internal_engine.initialize():
                raise InitializationError("Failed to initialize internal engine")

            self._initialized = True
            return True

        except Exception as e:
            raise InitializationError(f"Engine initialization failed: {e}")

    def is_initialized(self) -> bool:
        """
        初期化状態を確認

        Returns:
            bool: 初期化済みの場合True
        """
        return self._initialized and self._internal_engine is not None

    def analyze(
        self,
        algorithm_output: str,
        core_output: str,
        algorithm_spec: str,
        expected_result: str,
        algorithm_codes: Optional[List[str]] = None,
        evaluation_specs: Optional[List[str]] = None,
        evaluation_codes: Optional[List[str]] = None,
        dataset_id: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> AnalysisResult:
        """
        単一データセットの分析を実行

        Args:
            algorithm_output: アルゴリズム出力CSVファイルパス
            core_output: コアライブラリ出力CSVファイルパス
            algorithm_spec: アルゴリズム仕様Markdownファイルパス
            expected_result: 期待される結果の自然言語記述
            algorithm_codes: アルゴリズム実装コードファイルパスのリスト
            evaluation_specs: 評価仕様Markdownファイルパスのリスト
            evaluation_codes: 評価環境コードファイルパスのリスト
            dataset_id: データセットID（Noneの場合は自動生成）
            timeout: タイムアウト時間（秒、Noneの場合は設定値を使用）

        Returns:
            AnalysisResult: 分析結果

        Raises:
            ValidationError: 入力検証エラー
            AnalysisError: 分析実行エラー
            TimeoutError: タイムアウト
        """
        if not self.is_initialized():
            raise InitializationError("Engine not initialized. Call initialize() first.")

        # 入力検証
        self._validate_inputs(
            algorithm_output, core_output, algorithm_spec, expected_result
        )

        # データセットIDの設定
        if dataset_id is None:
            dataset_id = f"dataset_{int(time.time())}"

        # タイムアウト設定
        actual_timeout = timeout or self.config.timeout

        try:
            # 内部エンジン用のリクエスト作成
            state = self._internal_engine.create_analysis_request(
                algorithm_outputs=[algorithm_output],
                core_outputs=[core_output],
                algorithm_specs=[algorithm_spec],
                evaluation_specs=evaluation_specs or [algorithm_spec],  # デフォルトでアルゴリズム仕様を使用
                expected_results=[expected_result],
                algorithm_codes=algorithm_codes,
                evaluation_codes=evaluation_codes,
                dataset_ids=[dataset_id],
                output_dir=self.config.output_dir
            )

            # 分析実行（タイムアウト付き）
            start_time = time.time()
            result = self._run_with_timeout(
                self._internal_engine.run_analysis(state),
                actual_timeout
            )
            execution_time = time.time() - start_time

            # 結果の変換
            return self._convert_to_library_result(
                result, dataset_id, execution_time
            )

        except asyncio.TimeoutError:
            raise TimeoutError(f"Analysis timed out after {actual_timeout} seconds")
        except Exception as e:
            raise AnalysisError(f"Analysis failed: {e}")

    async def analyze_async(
        self,
        algorithm_output: str,
        core_output: str,
        algorithm_spec: str,
        expected_result: str,
        algorithm_codes: Optional[List[str]] = None,
        evaluation_specs: Optional[List[str]] = None,
        evaluation_codes: Optional[List[str]] = None,
        dataset_id: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> AnalysisResult:
        """
        単一データセットの分析を非同期実行

        Args:
            algorithm_output: アルゴリズム出力CSVファイルパス
            core_output: コアライブラリ出力CSVファイルパス
            algorithm_spec: アルゴリズム仕様Markdownファイルパス
            expected_result: 期待される結果の自然言語記述
            algorithm_codes: アルゴリズム実装コードファイルパスのリスト
            evaluation_specs: 評価仕様Markdownファイルパスのリスト
            evaluation_codes: 評価環境コードファイルパスのリスト
            dataset_id: データセットID（Noneの場合は自動生成）
            timeout: タイムアウト時間（秒、Noneの場合は設定値を使用）

        Returns:
            AnalysisResult: 分析結果
        """
        # 現在の実装は同期処理なので、非同期ラッパーを提供
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.analyze,
            algorithm_output,
            core_output,
            algorithm_spec,
            expected_result,
            algorithm_codes,
            evaluation_specs,
            evaluation_codes,
            dataset_id,
            timeout
        )

    def analyze_batch(
        self,
        datasets: List[Dict[str, Any]],
        timeout: Optional[int] = None
    ) -> List[AnalysisResult]:
        """
        複数データセットの一括分析を実行

        Args:
            datasets: データセット情報のリスト
                各要素は以下の形式:
                {
                    "algorithm_output": "path/to/algo.csv",
                    "core_output": "path/to/core.csv",
                    "algorithm_spec": "path/to/spec.md",
                    "expected_result": "期待される動作",
                    "algorithm_codes": ["path/to/code.py"],  # オプション
                    "evaluation_specs": ["path/to/eval.md"], # オプション
                    "evaluation_codes": ["path/to/eval.py"], # オプション
                    "dataset_id": "custom_id"                # オプション
                }
            timeout: 全体のタイムアウト時間（秒）

        Returns:
            List[AnalysisResult]: 分析結果のリスト

        Raises:
            ValidationError: 入力検証エラー
            AnalysisError: 分析実行エラー
        """
        if not self.is_initialized():
            raise InitializationError("Engine not initialized. Call initialize() first.")

        results = []
        start_time = time.time()
        actual_timeout = timeout or self.config.timeout

        for i, dataset in enumerate(datasets):
            if time.time() - start_time > actual_timeout:
                raise TimeoutError(f"Batch analysis timed out after {actual_timeout} seconds")

            try:
                result = self.analyze(
                    algorithm_output=dataset["algorithm_output"],
                    core_output=dataset["core_output"],
                    algorithm_spec=dataset["algorithm_spec"],
                    expected_result=dataset["expected_result"],
                    algorithm_codes=dataset.get("algorithm_codes"),
                    evaluation_specs=dataset.get("evaluation_specs"),
                    evaluation_codes=dataset.get("evaluation_codes"),
                    dataset_id=dataset.get("dataset_id"),
                    timeout=max(30, actual_timeout - int(time.time() - start_time))  # 残り時間
                )
                results.append(result)

            except Exception as e:
                # エラーが発生しても処理を継続
                dataset_id = dataset.get("dataset_id", f"dataset_{i}")
                error_result = AnalysisResult.error_result(
                    dataset_id=dataset_id,
                    error=str(e),
                    error_details={"batch_index": i}
                )
                results.append(error_result)

        return results

    def get_status(self) -> Dict[str, Any]:
        """
        エンジンの現在の状態を取得

        Returns:
            Dict[str, Any]: 状態情報
        """
        if not self._internal_engine:
            return {
                "initialized": False,
                "config_valid": self.config.validate() if self.config else False,
                "version": "1.0.0"
            }

        internal_status = self._internal_engine.get_status()
        return {
            "initialized": self._initialized,
            "config_valid": self.config.validate() if self.config else False,
            "internal_engine_ready": internal_status.get("initialized", False),
            "version": "1.0.0",
            "config": {
                "model": self.config.model,
                "timeout": self.config.timeout,
                "output_dir": self.config.output_dir
            }
        }

    def shutdown(self) -> None:
        """
        エンジンのクリーンアップ

        内部リソースの解放とクリーンアップを行う
        """
        if self._internal_engine:
            # 内部エンジンのクリーンアップ（必要に応じて）
            pass

        self._initialized = False
        self._internal_engine = None

    def _validate_inputs(
        self,
        algorithm_output: str,
        core_output: str,
        algorithm_spec: str,
        expected_result: str
    ) -> None:
        """入力パラメータの検証"""
        # ファイル存在チェック
        for file_path, name in [
            (algorithm_output, "algorithm_output"),
            (core_output, "core_output"),
            (algorithm_spec, "algorithm_spec")
        ]:
            if not Path(file_path).exists():
                raise ValidationError(f"{name} file does not exist: {file_path}")

        # ファイル拡張子チェック
        if not algorithm_output.lower().endswith('.csv'):
            raise ValidationError("algorithm_output must be a CSV file")
        if not core_output.lower().endswith('.csv'):
            raise ValidationError("core_output must be a CSV file")
        if not algorithm_spec.lower().endswith(('.md', '.txt')):
            raise ValidationError("algorithm_spec must be a Markdown or text file")

        # 期待結果のチェック
        if not expected_result.strip():
            raise ValidationError("expected_result cannot be empty")

    def _run_with_timeout(self, func_result, timeout: int):
        """タイムアウト付きで関数を実行"""
        import threading
        import queue

        result_queue = queue.Queue()

        def run_func():
            try:
                result_queue.put(func_result)
            except Exception as e:
                result_queue.put(e)

        thread = threading.Thread(target=run_func)
        thread.daemon = True
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            raise TimeoutError(f"Analysis timed out after {timeout} seconds")

        result = result_queue.get()
        if isinstance(result, Exception):
            raise result

        return result

    def _convert_to_library_result(
        self,
        internal_result: Dict[str, Any],
        dataset_id: str,
        execution_time: float
    ) -> AnalysisResult:
        """内部結果をライブラリ結果に変換"""
        if "error" in internal_result:
            return AnalysisResult.error_result(
                dataset_id=dataset_id,
                error=internal_result["error"],
                error_details=internal_result
            )

        # 仮説の抽出
        hypotheses = []
        if "datasets" in internal_result and internal_result["datasets"]:
            dataset = internal_result["datasets"][0]

            # 仮説の抽出（内部形式から変換）
            if hasattr(dataset, 'hypotheses') and dataset.hypotheses:
                for hyp in dataset.hypotheses:
                    if isinstance(hyp, dict):
                        hypotheses.append(Hypothesis(
                            text=hyp.get('hypothesis', ''),
                            confidence=hyp.get('confidence', 0.5),
                            evidence=hyp.get('evidence', []),
                            category=hyp.get('category', 'general')
                        ))

        # レポートの取得
        report = None
        report_path = None
        if "datasets" in internal_result and internal_result["datasets"]:
            dataset = internal_result["datasets"][0]
            if hasattr(dataset, 'report_content') and dataset.report_content:
                report = dataset.report_content
                # レポートファイルパスの推定
                report_path = f"{self.config.output_dir}/results/reports/{dataset_id}_report.md"

        # プロットの取得
        plots = []
        if "datasets" in internal_result and internal_result["datasets"]:
            # プロットファイルの検索（簡易実装）
            import glob
            plot_pattern = f"{self.config.output_dir}/results/reports/plots/{dataset_id}/*.png"
            plots = glob.glob(plot_pattern)

        # メトリクスの作成
        metrics = AnalysisMetrics(
            execution_time=execution_time,
            data_points_processed=len(internal_result.get("datasets", [])),
            hypotheses_generated=len(hypotheses),
            plots_generated=len(plots)
        )

        return AnalysisResult.success_result(
            dataset_id=dataset_id,
            report=report,
            hypotheses=hypotheses,
            plots=plots,
            metrics=metrics,
            report_path=report_path,
            summary=f"Analysis completed for {dataset_id}"
        )
