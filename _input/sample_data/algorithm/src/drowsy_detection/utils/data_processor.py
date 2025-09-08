"""
データ前処理モジュール

入力データの前処理、NaN値の処理、範囲制限などを提供します。
"""

import numpy as np
from typing import Optional
from drowsy_detection.config.validators import InputData, ProcessedData


class DataProcessor:
    """データ前処理クラス"""
    
    def __init__(self):
        self.last_valid_data: Optional[ProcessedData] = None
        self.nan_count = 0
        self.total_count = 0
    
    def preprocess(self, input_data: InputData) -> ProcessedData:
        self.total_count += 1
        left_eye = self._handle_nan_value(input_data.left_eye_open, "left_eye_open")
        right_eye = self._handle_nan_value(input_data.right_eye_open, "right_eye_open")
        face_conf = self._handle_nan_value(input_data.face_confidence, "face_confidence")
        left_eye = np.clip(left_eye, 0.0, 1.0)
        right_eye = np.clip(right_eye, 0.0, 1.0)
        face_conf = np.clip(face_conf, 0.0, 1.0)
        self.last_valid_data = ProcessedData(
            left_eye_open=left_eye,
            right_eye_open=right_eye,
            face_confidence=face_conf
        )
        return self.last_valid_data
    
    def _handle_nan_value(self, value: float, field_name: str) -> float:
        if np.isnan(value):
            self.nan_count += 1
            if self.last_valid_data is not None:
                if field_name == "left_eye_open":
                    return self.last_valid_data.left_eye_open
                elif field_name == "right_eye_open":
                    return self.last_valid_data.right_eye_open
                elif field_name == "face_confidence":
                    return self.last_valid_data.face_confidence
            return 0.0
        return value
    
    def reset(self) -> None:
        self.last_valid_data = None
        self.nan_count = 0
        self.total_count = 0
    
    def get_statistics(self) -> dict:
        nan_rate = self.nan_count / max(self.total_count, 1)
        return {
            'total_processed': self.total_count,
            'nan_count': self.nan_count,
            'nan_rate': nan_rate,
            'has_last_valid': self.last_valid_data is not None
        }
    
    def apply_smoothing(self, values: list, window_size: int = 3) -> float:
        if not values:
            return 0.0
        recent_values = values[-window_size:]
        return float(np.mean(recent_values))
