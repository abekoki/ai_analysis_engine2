"""
DrowsyDetector メインクラスのテスト
"""

import pytest
import numpy as np
from drowsy_detection.config.config import Config
from drowsy_detection.config.validators import InputData
from drowsy_detection.core.drowsy_detector import DrowsyDetector


class TestDrowsyDetector:
    """DrowsyDetector 単体テスト"""
    
    @pytest.fixture
    def config(self):
        """テスト用設定"""
        return Config(
            left_eye_close_threshold=0.30,
            right_eye_close_threshold=0.30,
            continuous_close_time=1.0,
            face_conf_threshold=0.70,
            log_level="ERROR"  # テスト中はエラーのみ表示
        )
    
    @pytest.fixture
    def detector(self, config):
        """テスト用検出器"""
        return DrowsyDetector(config)
    
    def test_initialization(self, config):
        """初期化のテスト"""
        detector = DrowsyDetector(config)
        
        assert detector.config == config
        assert detector.last_frame_num == -1
        assert detector.last_valid_result is None
        assert detector.frame_rate == 30.0
    
    def test_normal_operation(self, detector):
        """正常動作テスト"""
        # 開眼状態
        input_data = InputData(
            frame_num=1,
            left_eye_open=0.8,
            right_eye_open=0.9,
            face_confidence=0.95
        )
        result = detector.update(input_data)
        
        assert result.is_drowsy == 0
        assert result.left_eye_closed == False
        assert result.right_eye_closed == False
        assert result.continuous_time == 0.0
        assert result.error_code is None
    
    def test_continuous_eye_closure(self, detector):
        """連続閉眼テスト"""
        # 30fps * 1.2秒 = 36フレームで閉眼状態を継続
        for i in range(36):
            input_data = InputData(
                frame_num=i+1,
                left_eye_open=0.1,
                right_eye_open=0.1,
                face_confidence=0.95
            )
            result = detector.update(input_data)
        
        # 1秒を超えているので眠気検知
        assert result.is_drowsy == 1
        assert result.left_eye_closed == True
        assert result.right_eye_closed == True
        assert result.continuous_time >= 1.0
    
    def test_intermittent_closure(self, detector):
        """断続的閉眼テスト"""
        # 閉眼→開眼→閉眼を繰り返す（連続閉眼にならない）
        for cycle in range(3):
            # 閉眼 (10フレーム)
            for i in range(10):
                frame_num = cycle * 20 + i + 1
                input_data = InputData(
                    frame_num=frame_num,
                    left_eye_open=0.1,
                    right_eye_open=0.1,
                    face_confidence=0.95
                )
                result = detector.update(input_data)
            
            # 開眼 (10フレーム)
            for i in range(10):
                frame_num = cycle * 20 + i + 11
                input_data = InputData(
                    frame_num=frame_num,
                    left_eye_open=0.8,
                    right_eye_open=0.8,
                    face_confidence=0.95
                )
                result = detector.update(input_data)
                
                # 開眼時はタイマーがリセットされる
                assert result.continuous_time == 0.0
                assert result.is_drowsy == 0
    
    def test_low_face_confidence(self, detector):
        """低信頼度テスト"""
        input_data = InputData(
            frame_num=1,
            left_eye_open=0.1,
            right_eye_open=0.1,
            face_confidence=0.5  # 閾値(0.7)以下
        )
        result = detector.update(input_data)
        
        assert result.is_drowsy == -1
        assert result.error_code == "LOW_FACE_CONFIDENCE"
    
    def test_invalid_frame_number(self, detector):
        """無効なフレーム番号のテスト"""
        # 最初のフレーム
        input_data1 = InputData(
            frame_num=5,
            left_eye_open=0.8,
            right_eye_open=0.8,
            face_confidence=0.95
        )
        detector.update(input_data1)
        
        # より小さいフレーム番号
        input_data2 = InputData(
            frame_num=3,
            left_eye_open=0.8,
            right_eye_open=0.8,
            face_confidence=0.95
        )
        result = detector.update(input_data2)
        
        assert result.is_drowsy == -1
        assert result.error_code == "INVALID_FRAME_NUM"
    
    def test_one_eye_closed(self, detector):
        """片目のみ閉眼のテスト"""
        input_data = InputData(
            frame_num=1,
            left_eye_open=0.1,  # 閉眼
            right_eye_open=0.8,  # 開眼
            face_confidence=0.95
        )
        result = detector.update(input_data)
        
        assert result.is_drowsy == 0  # 両目が閉眼でないので眠気なし
        assert result.left_eye_closed == True
        assert result.right_eye_closed == False
        assert result.continuous_time == 0.0
    
    def test_reset_functionality(self, detector):
        """リセット機能のテスト"""
        # 状態を変更
        input_data = InputData(
            frame_num=5,
            left_eye_open=0.1,
            right_eye_open=0.1,
            face_confidence=0.95
        )
        detector.update(input_data)
        
        # リセット前の状態確認
        assert detector.last_frame_num == 5
        assert detector.last_valid_result is not None
        
        # リセット実行
        detector.reset()
        
        # リセット後の状態確認
        assert detector.last_frame_num == -1
        assert detector.last_valid_result is None
        assert detector.timer.state.is_active == False
    
    def test_frame_rate_setting(self, detector):
        """フレームレート設定のテスト"""
        # デフォルト値確認
        assert detector.frame_rate == 30.0
        
        # 新しい値を設定
        detector.set_frame_rate(60.0)
        assert detector.frame_rate == 60.0
        
        # 無効な値
        with pytest.raises(ValueError):
            detector.set_frame_rate(0.0)
        
        with pytest.raises(ValueError):
            detector.set_frame_rate(-10.0)
    
    def test_statistics(self, detector):
        """統計情報のテスト"""
        # 初期統計
        stats = detector.get_statistics()
        assert stats['last_frame_num'] == -1
        assert stats['timer_active'] == False
        assert stats['current_continuous_time'] == 0.0
        assert stats['frame_rate'] == 30.0
        
        # いくつかの処理を実行
        input_data = InputData(
            frame_num=1,
            left_eye_open=0.1,
            right_eye_open=0.1,
            face_confidence=0.95
        )
        detector.update(input_data)
        
        # 統計を再取得
        stats = detector.get_statistics()
        assert stats['last_frame_num'] == 1
        assert stats['timer_active'] == True
        assert 'data_processor' in stats
        assert 'left_eye_filter' in stats
        assert 'right_eye_filter' in stats
    
    def test_boundary_values(self, detector):
        """境界値のテスト"""
        # 閾値ちょうどの値
        input_data = InputData(
            frame_num=1,
            left_eye_open=0.30,  # 閾値と同じ
            right_eye_open=0.30,  # 閾値と同じ
            face_confidence=0.70  # 閾値と同じ
        )
        result = detector.update(input_data)
        
        # 閾値以下なので閉眼と判定される
        assert result.left_eye_closed == True
        assert result.right_eye_closed == True
        
        # 顔信頼度は閾値以上なので正常処理
        assert result.is_drowsy == 0  # まだ時間不足
        assert result.error_code is None
    
    def test_long_session(self, detector):
        """長時間セッションのテスト"""
        drowsy_count = 0
        
        # 長時間の処理をシミュレート
        for i in range(1, 301):  # 300フレーム = 10秒
            if i % 100 < 50:  # 半分の時間は閉眼
                left_eye, right_eye = 0.1, 0.1
            else:
                left_eye, right_eye = 0.8, 0.8
            
            input_data = InputData(
                frame_num=i,
                left_eye_open=left_eye,
                right_eye_open=right_eye,
                face_confidence=0.95
            )
            
            result = detector.update(input_data)
            if result.is_drowsy == 1:
                drowsy_count += 1
        
        # 眠気が検知されることを確認
        assert drowsy_count > 0
        
        # 統計情報で処理された件数を確認
        stats = detector.get_statistics()
        assert stats['data_processor']['total_processed'] == 300
