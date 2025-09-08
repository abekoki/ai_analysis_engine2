"""
データ検証モジュール

入力データ、出力データ、前処理済みデータのモデル定義と検証機能を提供します。
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
import numpy as np
from dataclasses import dataclass


class InputData(BaseModel):
    """アルゴリズム入力データモデル"""
    
    frame_num: int = Field(
        description="フレーム番号（単調増加）"
    )
    left_eye_open: float = Field(
        ge=0.0,
        le=1.0,
        description="左目の開眼度 (0.0〜1.0)"
    )
    right_eye_open: float = Field(
        ge=0.0,
        le=1.0,
        description="右目の開眼度 (0.0〜1.0)"
    )
    face_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="顔検出信頼度 (0.0〜1.0)"
    )
    
    @validator('frame_num')
    def validate_frame_num(cls, v):
        """フレーム番号の妥当性を検証"""
        if v < 0:
            raise ValueError("frame_num must be non-negative")
        return v
    
    @validator('left_eye_open', 'right_eye_open', 'face_confidence')
    def validate_float_values(cls, v):
        """浮動小数点値の妥当性を検証"""
        if np.isnan(v):
            raise ValueError("Input values cannot be NaN")
        return v


class OutputData(BaseModel):
    """アルゴリズム出力データモデル"""
    
    is_drowsy: int = Field(
        description="連続閉眼状態判定結果"
    )
    frame_num: int = Field(
        description="対応するフレーム番号"
    )
    left_eye_closed: bool = Field(
        description="左目閉眼フラグ"
    )
    right_eye_closed: bool = Field(
        description="右目閉眼フラグ"
    )
    continuous_time: float = Field(
        description="現在の連続閉眼時間 [s]"
    )
    error_code: Optional[str] = Field(
        default=None,
        description="エラーコード（エラー時のみ）"
    )
    
    @validator('is_drowsy')
    def validate_is_drowsy(cls, v):
        """眠気判定結果の妥当性を検証"""
        valid_values = [-1, 0, 1]
        if v not in valid_values:
            raise ValueError(f"is_drowsy must be one of {valid_values}")
        return v


@dataclass
class ProcessedData:
    """前処理済みデータクラス"""
    left_eye_open: float
    right_eye_open: float
    face_confidence: float
    
    def __post_init__(self):
        """データクラス初期化後の検証"""
        # 値の範囲チェック
        if not (0.0 <= self.left_eye_open <= 1.0):
            raise ValueError("left_eye_open must be between 0.0 and 1.0")
        if not (0.0 <= self.right_eye_open <= 1.0):
            raise ValueError("right_eye_open must be between 0.0 and 1.0")
        if not (0.0 <= self.face_confidence <= 1.0):
            raise ValueError("face_confidence must be between 0.0 and 1.0")
