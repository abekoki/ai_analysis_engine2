"""
コアモジュールのテスト
"""

import pytest
from drowsy_detection.core.timer import ContinuousTimer, TimerState
from drowsy_detection.core.eye_state import EyeStateManager, EyeState


class TestContinuousTimer:
    """ContinuousTimer クラスのテスト"""
    
    def test_timer_initialization(self):
        """タイマー初期化のテスト"""
        timer = ContinuousTimer(1.0)
        
        assert timer.threshold == 1.0
        assert timer.state.is_active == False
        assert timer.state.current_duration == 0.0
    
    def test_invalid_threshold(self):
        """無効な閾値のテスト"""
        with pytest.raises(ValueError):
            ContinuousTimer(0.0)
        
        with pytest.raises(ValueError):
            ContinuousTimer(-1.0)
    
    def test_timer_start_stop(self):
        """タイマーの開始・停止テスト"""
        timer = ContinuousTimer(1.0)
        
        # 開始
        timer.start()
        assert timer.state.is_active == True
        assert timer.state.current_duration == 0.0
        
        # 停止
        timer.stop()
        assert timer.state.is_active == False
        assert timer.state.current_duration == 0.0
    
    def test_timer_update(self):
        """タイマー更新のテスト"""
        timer = ContinuousTimer(1.0)
        
        # 非アクティブ時
        result = timer.update(0.1)
        assert result == 0.0
        
        # アクティブ時
        timer.start()
        result = timer.update(0.3)
        assert result == 0.3
        assert timer.get_current_duration() == 0.3
        
        result = timer.update(0.5)
        assert result == 0.8
        assert timer.get_current_duration() == 0.8
    
    def test_invalid_dt(self):
        """無効な時間差のテスト"""
        timer = ContinuousTimer(1.0)
        timer.start()
        
        with pytest.raises(ValueError):
            timer.update(-0.1)
    
    def test_threshold_exceeded(self):
        """閾値超過判定のテスト"""
        timer = ContinuousTimer(1.0)
        timer.start()
        
        # 閾値未満
        timer.update(0.5)
        assert timer.is_threshold_exceeded() == False
        
        # 閾値到達
        timer.update(0.5)
        assert timer.is_threshold_exceeded() == True
        
        # 閾値超過
        timer.update(0.2)
        assert timer.is_threshold_exceeded() == True
    
    def test_remaining_time(self):
        """残り時間のテスト"""
        timer = ContinuousTimer(2.0)
        
        # 非アクティブ時
        assert timer.get_remaining_time() == 2.0
        
        # アクティブ時
        timer.start()
        timer.update(0.5)
        assert timer.get_remaining_time() == 1.5
        
        timer.update(2.0)  # 閾値超過
        assert timer.get_remaining_time() == 0.0
    
    def test_reset(self):
        """リセットのテスト"""
        timer = ContinuousTimer(1.0)
        timer.start()
        timer.update(0.5)
        
        timer.reset()
        assert timer.state.is_active == False
        assert timer.state.current_duration == 0.0


class TestEyeStateManager:
    """EyeStateManager クラスのテスト"""
    
    def test_manager_initialization(self):
        """マネージャー初期化のテスト"""
        manager = EyeStateManager(close_threshold=0.3)
        
        assert manager.close_threshold == 0.3
        assert manager.enable_filter == True
        assert manager.alpha == 0.3
        assert manager.is_initialized == False
    
    def test_invalid_threshold(self):
        """無効な閾値のテスト"""
        with pytest.raises(ValueError):
            EyeStateManager(close_threshold=-0.1)
        
        with pytest.raises(ValueError):
            EyeStateManager(close_threshold=1.1)
    
    def test_invalid_alpha(self):
        """無効なアルファ値のテスト"""
        with pytest.raises(ValueError):
            EyeStateManager(close_threshold=0.3, alpha=-0.1)
        
        with pytest.raises(ValueError):
            EyeStateManager(close_threshold=0.3, alpha=1.1)
    
    def test_eye_state_update_without_filter(self):
        """フィルタなしでの状態更新テスト"""
        manager = EyeStateManager(close_threshold=0.3, enable_filter=False)
        
        # 開眼状態
        state = manager.update(0.8)
        assert state.is_closed == False
        assert state.open_ratio == 0.8
        assert state.filtered_open_ratio == 0.8
        
        # 閉眼状態
        state = manager.update(0.2)
        assert state.is_closed == True
        assert state.open_ratio == 0.2
        assert state.filtered_open_ratio == 0.2
        
        # 境界値
        state = manager.update(0.3)
        assert state.is_closed == True  # <= 閾値で閉眼
    
    def test_eye_state_update_with_filter(self):
        """フィルタありでの状態更新テスト"""
        manager = EyeStateManager(close_threshold=0.3, enable_filter=True, alpha=0.5)
        
        # 初回
        state = manager.update(0.8)
        assert state.filtered_open_ratio == 0.8  # 初回はそのまま
        assert manager.is_initialized == True
        
        # 2回目
        state = manager.update(0.4)
        expected = 0.5 * 0.4 + 0.5 * 0.8  # alpha * new + (1-alpha) * old
        assert abs(state.filtered_open_ratio - expected) < 1e-6
    
    def test_value_clipping(self):
        """値の範囲制限のテスト"""
        manager = EyeStateManager(close_threshold=0.3)
        
        # 範囲外の値
        state = manager.update(-0.5)
        assert state.open_ratio == 0.0
        
        state = manager.update(1.5)
        assert state.open_ratio == 1.0
    
    def test_reset(self):
        """リセットのテスト"""
        manager = EyeStateManager(close_threshold=0.3)
        
        # 状態を更新
        manager.update(0.8)
        assert manager.is_initialized == True
        
        # リセット
        manager.reset()
        assert manager.is_initialized == False
        assert manager.filtered_value == None
    
    def test_get_filter_state(self):
        """フィルタ状態取得のテスト"""
        manager = EyeStateManager(close_threshold=0.3, alpha=0.4)
        
        # 初期状態
        state = manager.get_filter_state()
        assert state['is_initialized'] == False
        assert state['filtered_value'] == None
        assert state['alpha'] == 0.4
        
        # 更新後
        manager.update(0.7)
        state = manager.get_filter_state()
        assert state['is_initialized'] == True
        assert state['filtered_value'] == 0.7


class TestEyeState:
    """EyeState データクラスのテスト"""
    
    def test_valid_eye_state(self):
        """有効な目の状態のテスト"""
        state = EyeState(
            is_closed=True,
            open_ratio=0.2,
            filtered_open_ratio=0.25
        )
        
        assert state.is_closed == True
        assert state.open_ratio == 0.2
        assert state.filtered_open_ratio == 0.25
    
    def test_invalid_open_ratio(self):
        """無効な開眼度のテスト"""
        with pytest.raises(ValueError):
            EyeState(
                is_closed=False,
                open_ratio=-0.1,
                filtered_open_ratio=0.5
            )
        
        with pytest.raises(ValueError):
            EyeState(
                is_closed=False,
                open_ratio=1.1,
                filtered_open_ratio=0.5
            )
    
    def test_invalid_filtered_ratio(self):
        """無効なフィルタ済み開眼度のテスト"""
        with pytest.raises(ValueError):
            EyeState(
                is_closed=False,
                open_ratio=0.5,
                filtered_open_ratio=-0.1
            )
        
        with pytest.raises(ValueError):
            EyeState(
                is_closed=False,
                open_ratio=0.5,
                filtered_open_ratio=1.1
            )
