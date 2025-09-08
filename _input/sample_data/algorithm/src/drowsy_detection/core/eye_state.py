"""
目の状態管理モジュール

目の開眼・閉眼状態の管理と指数移動平均フィルタ機能を提供します。
"""

from dataclasses import dataclass
from typing import Tuple
import numpy as np


@dataclass
class EyeState:
    """目の状態データクラス"""
    is_closed: bool
    open_ratio: float
    filtered_open_ratio: float
    
    def __post_init__(self):
        """データクラス初期化後の検証"""
        if not (0.0 <= self.open_ratio <= 1.0):
            raise ValueError("open_ratio must be between 0.0 and 1.0")
        if not (0.0 <= self.filtered_open_ratio <= 1.0):
            raise ValueError("filtered_open_ratio must be between 0.0 and 1.0")


class EyeStateManager:
    """目の状態管理クラス"""
    
    def __init__(self, close_threshold: float, enable_filter: bool = True, alpha: float = 0.3):
        """
        目の状態管理クラスを初期化
        
        Args:
            close_threshold: 閉眼判定閾値
            enable_filter: フィルタ有効化フラグ
            alpha: EMA フィルタ係数
        """
        if not (0.0 <= close_threshold <= 1.0):
            raise ValueError("close_threshold must be between 0.0 and 1.0")
        if not (0.0 <= alpha <= 1.0):
            raise ValueError("alpha must be between 0.0 and 1.0")
        
        self.close_threshold = close_threshold
        self.enable_filter = enable_filter
        self.alpha = alpha
        self.filtered_value = None
        self.is_initialized = False
    
    def update(self, open_ratio: float) -> EyeState:
        """
        目の状態を更新
        
        Args:
            open_ratio: 開眼度 (0.0〜1.0)
            
        Returns:
            更新された目の状態
        """
        # 入力値の正規化
        normalized_ratio = np.clip(open_ratio, 0.0, 1.0)
        
        # フィルタ適用
        if self.enable_filter:
            filtered_ratio = self._apply_ema_filter(normalized_ratio)
        else:
            filtered_ratio = normalized_ratio
        
        # 閉眼判定
        is_closed = filtered_ratio <= self.close_threshold
        
        return EyeState(
            is_closed=is_closed,
            open_ratio=normalized_ratio,
            filtered_open_ratio=filtered_ratio
        )
    
    def _apply_ema_filter(self, value: float) -> float:
        """
        指数移動平均フィルタを適用
        
        Args:
            value: 入力値
            
        Returns:
            フィルタ済み値
        """
        if not self.is_initialized:
            self.filtered_value = value
            self.is_initialized = True
        else:
            self.filtered_value = self.alpha * value + (1 - self.alpha) * self.filtered_value
        
        return self.filtered_value
    
    def reset(self) -> None:
        """状態リセット"""
        self.filtered_value = None
        self.is_initialized = False
    
    def get_filter_state(self) -> dict:
        """フィルタの現在状態を取得"""
        return {
            'is_initialized': self.is_initialized,
            'filtered_value': self.filtered_value,
            'alpha': self.alpha
        }
