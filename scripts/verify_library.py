#!/usr/bin/env python3
"""
AI分析エンジンライブラリの動作確認スクリプト

このスクリプトはライブラリの基本機能を検証します。
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """インポートテスト"""
    print("🔍 インポートテスト...")

    try:
        # 個別にインポートして確認
        from ai_analysis_engine import AIAnalysisEngine
        from ai_analysis_engine import AnalysisConfig
        from ai_analysis_engine import AnalysisResult
        from ai_analysis_engine.models.result import Hypothesis
        from ai_analysis_engine.models.result import AnalysisMetrics
        from ai_analysis_engine.exceptions import (
            ConfigurationError,
            ValidationError,
            AnalysisError,
            TimeoutError
        )
        print("✅ インポート成功")
        return True
    except ImportError as e:
        print(f"❌ インポート失敗: {e}")
        return False

def test_config():
    """設定クラステスト"""
    print("\n🔧 設定クラステスト...")

    try:
        from ai_analysis_engine import AnalysisConfig

        # デフォルト設定
        config = AnalysisConfig()
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.1
        print("✅ デフォルト設定テスト成功")

        # カスタム設定
        custom_config = AnalysisConfig(
            api_key="test-key",
            model="gpt-4",
            temperature=0.5
        )
        assert custom_config.api_key == "test-key"
        assert custom_config.model == "gpt-4"
        assert custom_config.temperature == 0.5
        print("✅ カスタム設定テスト成功")

        # 環境変数設定
        os.environ["AI_ANALYSIS_TEST_MODEL"] = "gpt-3.5-turbo"
        os.environ["AI_ANALYSIS_TEST_TEMP"] = "0.3"

        # 辞書からの設定
        config_dict = {
            "api_key": "dict-key",
            "model": "gpt-4",
            "temperature": 0.2
        }
        dict_config = AnalysisConfig.from_dict(config_dict)
        assert dict_config.api_key == "dict-key"
        assert dict_config.model == "gpt-4"
        print("✅ 辞書設定テスト成功")

        return True
    except Exception as e:
        print(f"❌ 設定クラステスト失敗: {e}")
        return False

def test_result_model():
    """結果モデルテスト"""
    print("\n📊 結果モデルテスト...")

    try:
        from ai_analysis_engine import AnalysisResult
        from ai_analysis_engine.models.result import Hypothesis

        # 成功結果
        hypotheses = [
            Hypothesis(text="テスト仮説1", confidence=0.8),
            Hypothesis(text="テスト仮説2", confidence=0.6)
        ]

        success_result = AnalysisResult.success_result(
            dataset_id="test_dataset",
            report="# テストレポート",
            hypotheses=hypotheses
        )

        assert success_result.success is True
        assert success_result.dataset_id == "test_dataset"
        assert len(success_result.hypotheses) == 2
        print("✅ 成功結果テスト成功")

        # エラー結果
        error_result = AnalysisResult.error_result(
            dataset_id="error_dataset",
            error="テストエラー",
            error_details={"code": 500}
        )

        assert error_result.success is False
        assert error_result.error == "テストエラー"
        print("✅ エラー結果テスト成功")

        # シリアライズテスト
        data_dict = success_result.to_dict()
        assert data_dict["dataset_id"] == "test_dataset"
        assert data_dict["success"] is True

        json_str = success_result.to_json()
        assert "test_dataset" in json_str
        print("✅ シリアライズテスト成功")

        return True
    except Exception as e:
        print(f"❌ 結果モデルテスト失敗: {e}")
        return False

def test_engine_initialization():
    """エンジン初期化テスト"""
    print("\n🚀 エンジン初期化テスト...")

    try:
        from ai_analysis_engine import AIAnalysisEngine, AnalysisConfig
        from ai_analysis_engine.exceptions import ConfigurationError

        # 設定なし初期化
        engine = AIAnalysisEngine()
        assert engine.config is not None
        assert engine.is_initialized() is False
        print("✅ 設定なし初期化テスト成功")

        # 設定付き初期化
        config = AnalysisConfig(api_key="test-key")
        engine_with_config = AIAnalysisEngine(config)
        assert engine_with_config.config.api_key == "test-key"
        print("✅ 設定付き初期化テスト成功")

        # 無効な設定での初期化
        invalid_config = AnalysisConfig(api_key="")
        try:
            AIAnalysisEngine(invalid_config)
            print("❌ 無効設定エラーテスト失敗")
            return False
        except ConfigurationError:
            print("✅ 無効設定エラーテスト成功")

        return True
    except Exception as e:
        print(f"❌ エンジン初期化テスト失敗: {e}")
        return False

def test_validation():
    """入力検証テスト"""
    print("\n✅ 入力検証テスト...")

    try:
        from ai_analysis_engine import AIAnalysisEngine, AnalysisConfig
        from ai_analysis_engine.exceptions import ValidationError

        config = AnalysisConfig(api_key="test-key")
        engine = AIAnalysisEngine(config)
        # モック内部エンジンを設定
        from unittest.mock import Mock
        mock_internal = Mock()
        mock_internal.run_analysis.return_value = {"error": "Mock error"}
        engine._internal_engine = mock_internal
        engine._initialized = True

        # 存在しないファイル
        try:
            engine.analyze(
                algorithm_output="/nonexistent.csv",
                core_output="/nonexistent.csv",
                algorithm_spec="/nonexistent.md",
                expected_result="test"
            )
            print("❌ ファイル存在検証テスト失敗")
            return False
        except ValidationError:
            print("✅ ファイル存在検証テスト成功")

        # 空の期待結果
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
                temp_csv = f.name
            with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
                temp_md = f.name

            try:
                engine.analyze(
                    algorithm_output=temp_csv,
                    core_output=temp_csv,
                    algorithm_spec=temp_md,
                    expected_result=""
                )
                print("❌ 空期待結果検証テスト失敗")
                return False
            except ValidationError:
                print("✅ 空期待結果検証テスト成功")
            finally:
                os.unlink(temp_csv)
                os.unlink(temp_md)
        except Exception as e:
            print(f"❌ 期待結果検証テスト失敗: {e}")
            return False

        return True
    except Exception as e:
        print(f"❌ 入力検証テスト失敗: {e}")
        return False

def test_status_and_shutdown():
    """ステータスとシャットダウンテスト"""
    print("\n📈 ステータス・シャットダウンテスト...")

    try:
        from ai_analysis_engine import AIAnalysisEngine, AnalysisConfig

        config = AnalysisConfig(api_key="test-key")
        engine = AIAnalysisEngine(config)

        # 初期状態のステータス
        status = engine.get_status()
        assert status["initialized"] is False
        assert "version" in status
        print("✅ 初期ステータステスト成功")

        # シャットダウン
        engine.shutdown()
        assert engine.is_initialized() is False
        print("✅ シャットダウンテスト成功")

        return True
    except Exception as e:
        print(f"❌ ステータス・シャットダウンテスト失敗: {e}")
        return False

def main():
    """メイン検証関数"""
    print("🧪 AI分析エンジンライブラリ動作確認")
    print("=" * 50)

    tests = [
        ("インポート", test_imports),
        ("設定クラス", test_config),
        ("結果モデル", test_result_model),
        ("エンジン初期化", test_engine_initialization),
        ("入力検証", test_validation),
        ("ステータス・シャットダウン", test_status_and_shutdown)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"⚠️  {test_name}テストで問題が発生")
        except Exception as e:
            print(f"❌ {test_name}テスト例外: {e}")

    print("\n" + "=" * 50)
    print(f"📊 テスト結果: {passed}/{total} 成功")

    if passed == total:
        print("🎉 すべてのテストに成功しました！")
        print("\n📚 次に行うこと:")
        print("1. pip install -e . でライブラリをインストール")
        print("2. OpenAI APIキーを設定")
        print("3. docs/library_usage.md を参照して使用開始")
        return 0
    else:
        print("⚠️  一部のテストが失敗しました。詳細を確認してください。")
        return 1

if __name__ == "__main__":
    exit(main())
