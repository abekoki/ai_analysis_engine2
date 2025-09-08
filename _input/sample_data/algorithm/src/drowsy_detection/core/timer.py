"""
タイマー管理モジュール

連続時間計測のためのタイマークラスを提供します。
"""

import time
from typing import Optional
from dataclasses import dataclass


@dataclass
class TimerState:
    """タイマー状態データクラス"""
    is_active: bool = False
    start_time: Optional[float] = None
    current_duration: float = 0.0
    last_update_time: Optional[float] = None


class ContinuousTimer:
    """連続時間計測タイマークラス"""
    
    def __init__(self, threshold: float):
        """
        連続時間計測タイマーを初期化
        
        Args:
            threshold: 閾値時間 [s]
        """
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        
        self.threshold = threshold
        self.state = TimerState()
    
    def start(self) -> None:
        """タイマー開始"""
        current_time = time.time()
        self.state.is_active = True
        self.state.start_time = current_time
        self.state.last_update_time = current_time
        self.state.current_duration = 0.0
    
    def stop(self) -> None:
        """タイマー停止"""
        self.state.is_active = False
        self.state.start_time = None
        self.state.last_update_time = None
        self.state.current_duration = 0.0
    
    def update(self, dt: float) -> float:
        """
        タイマー更新
        
        Args:
            dt: 経過時間 [s]
            
        Returns:
            現在の継続時間 [s]
        """
        if not self.state.is_active:
            return 0.0
        
        if dt < 0:
            raise ValueError("dt must be non-negative")
        
        self.state.current_duration += dt
        return self.state.current_duration
    
    def is_threshold_exceeded(self) -> bool:
        """閾値を超えているかチェック"""
        return self.state.current_duration >= self.threshold
    
    def get_current_duration(self) -> float:
        """現在の継続時間を取得"""
        return self.state.current_duration
    
    def reset(self) -> None:
        """タイマーリセット"""
        self.stop()
    
    def get_remaining_time(self) -> float:
        """閾値到達までの残り時間を取得"""
        if not self.state.is_active:
            return self.threshold
        
        remaining = self.threshold - self.state.current_duration
        return max(0.0, remaining)
