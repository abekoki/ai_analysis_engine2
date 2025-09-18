"""
ライブラリAPIのテスト
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from ai_analysis_engine import (
    AIAnalysisEngine,
    AnalysisConfig,
    AnalysisResult,
    ConfigurationError,
    ValidationError,
    InitializationError
)


class TestAnalysisConfig:
    """設定クラスのテスト"""

    def test_default_config(self):
        """デフォルト設定のテスト"""
        config = AnalysisConfig()
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.1
        assert config.timeout == 300
        assert config.output_dir == "./analysis_results"

    def test_config_validation(self):
        """設定検証のテスト"""
        # 有効な設定
        config = AnalysisConfig(api_key="test-key")
        assert config.validate()

        # 無効な設定
        config = AnalysisConfig(api_key="", temperature=-1.0)
        with pytest.raises(ValueError):
            config.validate()

    def test_config_from_env(self):
        """環境変数からの設定読み込みテスト"""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "env-key",
            "AI_ANALYSIS_MODEL": "gpt-4",
            "AI_ANALYSIS_TEMPERATURE": "0.5"
        }):
            config = AnalysisConfig.from_env()
            assert config.api_key == "env-key"
            assert config.model == "gpt-4"
            assert config.temperature == 0.5

    def test_config_update(self):
        """設定更新のテスト"""
        config = AnalysisConfig(api_key="test-key")
        config.update(model="gpt-4", temperature=0.2)

        assert config.model == "gpt-4"
        assert config.temperature == 0.2


class TestAnalysisResult:
    """結果クラスのテスト"""

    def test_success_result_creation(self):
        """成功結果の作成テスト"""
        from ai_analysis_engine.models.result import Hypothesis

        hypotheses = [Hypothesis(text="Test hypothesis", confidence=0.8)]
        result = AnalysisResult.success_result(
            dataset_id="test_dataset",
            report="# Test Report",
            hypotheses=hypotheses
        )

        assert result.success is True
        assert result.dataset_id == "test_dataset"
        assert result.report == "# Test Report"
        assert len(result.hypotheses) == 1
        assert result.hypotheses[0].text == "Test hypothesis"

    def test_error_result_creation(self):
        """エラー結果の作成テスト"""
        result = AnalysisResult.error_result(
            dataset_id="test_dataset",
            error="Test error",
            error_details={"code": 500}
        )

        assert result.success is False
        assert result.dataset_id == "test_dataset"
        assert result.error == "Test error"
        assert result.error_details["code"] == 500

    def test_result_serialization(self):
        """結果のシリアライズテスト"""
        result = AnalysisResult.success_result(
            dataset_id="test",
            report="Test",
            hypotheses=[]
        )

        # 辞書変換
        data = result.to_dict()
        assert data["success"] is True
        assert data["dataset_id"] == "test"

        # JSON変換
        json_str = result.to_json()
        assert "test" in json_str

        # ファイル保存・読み込み
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            temp_file = f.name

        try:
            result.save_to_file(temp_file)
            loaded_result = AnalysisResult.load_from_file(temp_file)
            assert loaded_result.success == result.success
            assert loaded_result.dataset_id == result.dataset_id
        finally:
            os.unlink(temp_file)


class TestAIAnalysisEngine:
    """メインエンジンのテスト"""

    def test_initialization_without_config(self):
        """設定なしでの初期化テスト"""
        engine = AIAnalysisEngine()
        assert engine.config is not None
        assert engine.is_initialized() is False

    def test_initialization_with_config(self):
        """設定付きでの初期化テスト"""
        config = AnalysisConfig(api_key="test-key")
        engine = AIAnalysisEngine(config)
        assert engine.config.api_key == "test-key"

    def test_invalid_config_initialization(self):
        """無効な設定での初期化テスト"""
        config = AnalysisConfig(api_key="")  # 空のAPIキー

        with pytest.raises(ConfigurationError):
            AIAnalysisEngine(config)

    @patch('ai_analysis_engine.main.AIAnalysisEngine.initialize')
    def test_engine_initialization_success(self, mock_init):
        """エンジン初期化成功のテスト"""
        mock_init.return_value = True

        config = AnalysisConfig(api_key="test-key")
        engine = AIAnalysisEngine(config)

        result = engine.initialize()
        assert result is True
        assert engine.is_initialized() is True

    @patch('ai_analysis_engine.main.AIAnalysisEngine.initialize')
    def test_engine_initialization_failure(self, mock_init):
        """エンジン初期化失敗のテスト"""
        mock_init.return_value = False

        config = AnalysisConfig(api_key="test-key")
        engine = AIAnalysisEngine(config)

        with pytest.raises(InitializationError):
            engine.initialize()

    def test_not_initialized_error(self):
        """初期化前の使用エラーテスト"""
        engine = AIAnalysisEngine(AnalysisConfig(api_key="test-key"))

        with pytest.raises(InitializationError):
            engine.analyze(
                algorithm_output="/fake/path.csv",
                core_output="/fake/path.csv",
                algorithm_spec="/fake/path.md",
                expected_result="test"
            )

    def test_input_validation(self):
        """入力検証のテスト"""
        config = AnalysisConfig(api_key="test-key")
        engine = AIAnalysisEngine(config)
        engine._initialized = True  # モック初期化

        # 存在しないファイル
        with pytest.raises(ValidationError):
            engine.analyze(
                algorithm_output="/nonexistent.csv",
                core_output="/nonexistent.csv",
                algorithm_spec="/nonexistent.md",
                expected_result="test"
            )

        # 無効な拡張子
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_file = f.name

        try:
            with pytest.raises(ValidationError):
                engine.analyze(
                    algorithm_output=temp_file,  # .txtファイル
                    core_output=temp_file,
                    algorithm_spec=temp_file,
                    expected_result="test"
                )
        finally:
            os.unlink(temp_file)

        # 空の期待結果
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_csv = f.name
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            temp_md = f.name

        try:
            with pytest.raises(ValidationError):
                engine.analyze(
                    algorithm_output=temp_csv,
                    core_output=temp_csv,
                    algorithm_spec=temp_md,
                    expected_result=""  # 空の期待結果
                )
        finally:
            os.unlink(temp_csv)
            os.unlink(temp_md)

    def test_status_method(self):
        """ステータス取得のテスト"""
        config = AnalysisConfig(api_key="test-key")
        engine = AIAnalysisEngine(config)

        status = engine.get_status()
        assert status["initialized"] is False
        assert "version" in status
        assert "config" in status

    @patch('ai_analysis_engine.main.AIAnalysisEngine')
    def test_shutdown_method(self, mock_engine_class):
        """シャットダウンテスト"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        config = AnalysisConfig(api_key="test-key")
        engine = AIAnalysisEngine(config)
        engine._internal_engine = mock_engine
        engine._initialized = True

        engine.shutdown()

        assert engine._initialized is False
        assert engine._internal_engine is None

    @pytest.mark.asyncio
    async def test_async_analyze(self):
        """非同期分析のテスト"""
        config = AnalysisConfig(api_key="test-key")
        engine = AIAnalysisEngine(config)
        engine._initialized = True  # モック初期化

        # 実際の分析はモック化されているので、ValidationErrorが発生
        with pytest.raises(ValidationError):
            await engine.analyze_async(
                algorithm_output="/nonexistent.csv",
                core_output="/nonexistent.csv",
                algorithm_spec="/nonexistent.md",
                expected_result="test"
            )


class TestIntegration:
    """統合テスト"""

    def test_full_initialization_flow(self):
        """完全な初期化フローテスト"""
        # このテストは実際の環境ではAPIキーが必要なので、モックを使用
        with patch('ai_analysis_engine.main.AIAnalysisEngine.initialize') as mock_init:
            mock_init.return_value = True

            config = AnalysisConfig(api_key="test-key")
            engine = AIAnalysisEngine(config)

            # 初期化
            result = engine.initialize()
            assert result is True
            assert engine.is_initialized() is True

            # ステータス確認
            status = engine.get_status()
            assert status["initialized"] is True

            # シャットダウン
            engine.shutdown()
            assert engine.is_initialized() is False

    def test_config_persistence(self):
        """設定の永続性テスト"""
        config = AnalysisConfig(
            api_key="test-key",
            model="gpt-4",
            temperature=0.3,
            timeout=600
        )

        engine = AIAnalysisEngine(config)

        # 設定が保持されていることを確認
        assert engine.config.api_key == "test-key"
        assert engine.config.model == "gpt-4"
        assert engine.config.temperature == 0.3
        assert engine.config.timeout == 600
