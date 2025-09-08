"""
設定管理モジュール

連続閉眼検知アルゴリズムの設定クラスと検証機能を提供します。
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
import logging


class Config(BaseModel):
    """連続閉眼検知アルゴリズムの設定クラス"""
    
    # 閾値パラメータ
    left_eye_close_threshold: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="左目の開眼度がこの値以下で閉眼と判定"
    )
    right_eye_close_threshold: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="右目の開眼度がこの値以下で閉眼と判定"
    )
    continuous_close_time: float = Field(
        default=1.00,
        ge=0.1,
        le=10.0,
        description="連続閉眼とみなす時間閾値 [s]"
    )
    face_conf_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="顔検出が有効とみなす信頼度"
    )
    
    # ログ設定
    log_level: str = Field(
        default="INFO",
        description="ログレベル"
    )
    enable_debug_log: bool = Field(
        default=False,
        description="デバッグログ有効化"
    )
    
    # 前処理設定
    enable_ema_filter: bool = Field(
        default=True,
        description="指数移動平均フィルタ有効化"
    )
    ema_alpha: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="EMA フィルタ係数"
    )
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """ログレベルの妥当性を検証"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    class Config:
        """Pydantic設定"""
        validate_assignment = True


class ConfigValidator:
    """設定値の妥当性検証クラス"""
    
    @staticmethod
    def validate_thresholds(config: Config) -> bool:
        """閾値の妥当性を検証"""
        if config.left_eye_close_threshold > 1.0:
            raise ValueError("left_eye_close_threshold must be <= 1.0")
        if config.right_eye_close_threshold > 1.0:
            raise ValueError("right_eye_close_threshold must be <= 1.0")
        return True
    
    @staticmethod
    def validate_time_constraints(config: Config) -> bool:
        """時間制約の妥当性を検証"""
        if config.continuous_close_time < 0.1:
            raise ValueError("continuous_close_time must be >= 0.1")
        return True
    
    @staticmethod
    def validate_all(config: Config) -> bool:
        """全設定値の妥当性を検証"""
        ConfigValidator.validate_thresholds(config)
        ConfigValidator.validate_time_constraints(config)
        return True
