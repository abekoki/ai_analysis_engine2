"""
設定モジュールのテスト
"""

import pytest
from drowsy_detection.config.config import Config, ConfigValidator
from drowsy_detection.config.validators import InputData, OutputData


class TestConfig:
    """Config クラスのテスト"""
    
    def test_default_config(self):
        """デフォルト設定のテスト"""
        config = Config()
        
        assert config.left_eye_close_threshold == 0.30
        assert config.right_eye_close_threshold == 0.30
        assert config.continuous_close_time == 1.00
        assert config.face_conf_threshold == 0.70
        assert config.log_level == "INFO"
        assert config.enable_debug_log == False
        assert config.enable_ema_filter == True
        assert config.ema_alpha == 0.3
    
    def test_custom_config(self):
        """カスタム設定のテスト"""
        config = Config(
            left_eye_close_threshold=0.25,
            right_eye_close_threshold=0.35,
            continuous_close_time=2.0,
            face_conf_threshold=0.80,
            log_level="DEBUG",
            enable_debug_log=True
        )
        
        assert config.left_eye_close_threshold == 0.25
        assert config.right_eye_close_threshold == 0.35
        assert config.continuous_close_time == 2.0
        assert config.face_conf_threshold == 0.80
        assert config.log_level == "DEBUG"
        assert config.enable_debug_log == True
    
    def test_invalid_threshold_values(self):
        """無効な閾値のテスト"""
        with pytest.raises(ValueError):
            Config(left_eye_close_threshold=-0.1)
        
        with pytest.raises(ValueError):
            Config(left_eye_close_threshold=1.1)
        
        with pytest.raises(ValueError):
            Config(right_eye_close_threshold=-0.1)
        
        with pytest.raises(ValueError):
            Config(right_eye_close_threshold=1.1)
    
    def test_invalid_time_values(self):
        """無効な時間値のテスト"""
        with pytest.raises(ValueError):
            Config(continuous_close_time=0.05)  # 下限未満
        
        with pytest.raises(ValueError):
            Config(continuous_close_time=15.0)  # 上限超過
    
    def test_invalid_log_level(self):
        """無効なログレベルのテスト"""
        with pytest.raises(ValueError):
            Config(log_level="INVALID")
    
    def test_log_level_case_insensitive(self):
        """ログレベルの大文字小文字のテスト"""
        config = Config(log_level="debug")
        assert config.log_level == "DEBUG"
        
        config = Config(log_level="info")
        assert config.log_level == "INFO"


class TestConfigValidator:
    """ConfigValidator クラスのテスト"""
    
    def test_valid_config(self):
        """有効な設定の検証"""
        config = Config()
        assert ConfigValidator.validate_all(config) == True
    
    def test_threshold_validation(self):
        """閾値検証のテスト"""
        # 正常ケース
        config = Config(left_eye_close_threshold=0.5, right_eye_close_threshold=0.5)
        assert ConfigValidator.validate_thresholds(config) == True
    
    def test_time_constraint_validation(self):
        """時間制約検証のテスト"""
        # 正常ケース
        config = Config(continuous_close_time=1.5)
        assert ConfigValidator.validate_time_constraints(config) == True


class TestInputData:
    """InputData クラスのテスト"""
    
    def test_valid_input_data(self):
        """有効な入力データのテスト"""
        data = InputData(
            frame_num=1,
            left_eye_open=0.8,
            right_eye_open=0.9,
            face_confidence=0.95
        )
        
        assert data.frame_num == 1
        assert data.left_eye_open == 0.8
        assert data.right_eye_open == 0.9
        assert data.face_confidence == 0.95
    
    def test_invalid_frame_num(self):
        """無効なフレーム番号のテスト"""
        with pytest.raises(ValueError):
            InputData(
                frame_num=-1,
                left_eye_open=0.8,
                right_eye_open=0.9,
                face_confidence=0.95
            )
    
    def test_invalid_eye_values(self):
        """無効な開眼度のテスト"""
        with pytest.raises(ValueError):
            InputData(
                frame_num=1,
                left_eye_open=-0.1,
                right_eye_open=0.9,
                face_confidence=0.95
            )
        
        with pytest.raises(ValueError):
            InputData(
                frame_num=1,
                left_eye_open=1.1,
                right_eye_open=0.9,
                face_confidence=0.95
            )
    
    def test_invalid_face_confidence(self):
        """無効な顔検出信頼度のテスト"""
        with pytest.raises(ValueError):
            InputData(
                frame_num=1,
                left_eye_open=0.8,
                right_eye_open=0.9,
                face_confidence=-0.1
            )
        
        with pytest.raises(ValueError):
            InputData(
                frame_num=1,
                left_eye_open=0.8,
                right_eye_open=0.9,
                face_confidence=1.1
            )


class TestOutputData:
    """OutputData クラスのテスト"""
    
    def test_valid_output_data(self):
        """有効な出力データのテスト"""
        data = OutputData(
            is_drowsy=1,
            frame_num=10,
            left_eye_closed=True,
            right_eye_closed=True,
            continuous_time=2.5
        )
        
        assert data.is_drowsy == 1
        assert data.frame_num == 10
        assert data.left_eye_closed == True
        assert data.right_eye_closed == True
        assert data.continuous_time == 2.5
        assert data.error_code == None
    
    def test_output_with_error(self):
        """エラー付き出力データのテスト"""
        data = OutputData(
            is_drowsy=-1,
            frame_num=5,
            left_eye_closed=False,
            right_eye_closed=False,
            continuous_time=0.0,
            error_code="LOW_FACE_CONFIDENCE"
        )
        
        assert data.is_drowsy == -1
        assert data.error_code == "LOW_FACE_CONFIDENCE"
    
    def test_invalid_is_drowsy(self):
        """無効な眠気判定値のテスト"""
        with pytest.raises(ValueError):
            OutputData(
                is_drowsy=2,  # 無効な値
                frame_num=1,
                left_eye_closed=False,
                right_eye_closed=False,
                continuous_time=0.0
            )
