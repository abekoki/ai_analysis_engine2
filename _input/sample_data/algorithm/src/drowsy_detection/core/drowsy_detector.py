"""
連続閉眼検知アルゴリズム メインモジュール

開眼度と顔検出信頼度を入力として、連続閉眼状態を検知します。
"""

from typing import Optional
import time
from drowsy_detection.config.config import Config
from drowsy_detection.config.validators import InputData, OutputData
from drowsy_detection.core.eye_state import EyeStateManager, EyeState
from drowsy_detection.core.timer import ContinuousTimer
from drowsy_detection.utils.logger import Logger
from drowsy_detection.utils.data_processor import DataProcessor


class DrowsyDetector:
    """連続閉眼検知アルゴリズムメインクラス"""
    
    def __init__(self, config: Config):
        """
        連続閉眼検知器を初期化
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
        self.logger = Logger(config.log_level, config.enable_debug_log)
        
        # 目の状態管理
        self.left_eye_manager = EyeStateManager(
            close_threshold=config.left_eye_close_threshold,
            enable_filter=config.enable_ema_filter,
            alpha=config.ema_alpha
        )
        self.right_eye_manager = EyeStateManager(
            close_threshold=config.right_eye_close_threshold,
            enable_filter=config.enable_ema_filter,
            alpha=config.ema_alpha
        )
        
        # タイマー管理
        self.timer = ContinuousTimer(config.continuous_close_time)
        
        # データ前処理
        self.data_processor = DataProcessor()
        
        # 状態管理
        self.last_frame_num = -1
        self.last_valid_result: Optional[OutputData] = None
        self.frame_rate = 30.0  # フレームレート（デフォルト30fps）
        
        self.logger.info(f"DrowsyDetector initialized with config: {config.dict()}")
    
    def update(self, input_data: InputData) -> OutputData:
        """
        アルゴリズム更新処理
        
        Args:
            input_data: 入力データ
            
        Returns:
            判定結果
        """
        start_time = time.time()
        
        try:
            # フレーム番号チェック
            if input_data.frame_num <= self.last_frame_num:
                self.logger.warning(f"Invalid frame number: {input_data.frame_num} <= {self.last_frame_num}")
                return self._create_error_output(input_data.frame_num, "INVALID_FRAME_NUM")
            
            # 顔検出信頼度チェック
            if input_data.face_confidence < self.config.face_conf_threshold:
                self.logger.debug(f"Low face confidence: {input_data.face_confidence} < {self.config.face_conf_threshold}")
                self._reset_state()
                return self._create_error_output(input_data.frame_num, "LOW_FACE_CONFIDENCE")
            
            # データ前処理
            processed_data = self.data_processor.preprocess(input_data)
            
            # 目の状態更新
            left_eye_state = self.left_eye_manager.update(processed_data.left_eye_open)
            right_eye_state = self.right_eye_manager.update(processed_data.right_eye_open)
            
            # 連続閉眼判定
            result = self._evaluate_drowsy_state(
                input_data.frame_num,
                left_eye_state,
                right_eye_state
            )
            
            # 状態更新
            self.last_frame_num = input_data.frame_num
            self.last_valid_result = result
            
            # パフォーマンスログ
            duration = time.time() - start_time
            self.logger.log_performance("update", duration)
            
            self.logger.debug(f"Frame {input_data.frame_num}: is_drowsy={result.is_drowsy}, "
                            f"left_closed={result.left_eye_closed}, right_closed={result.right_eye_closed}, "
                            f"continuous_time={result.continuous_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in update: {str(e)}")
            return self._create_error_output(input_data.frame_num, "INTERNAL_ERROR")
    
    def _evaluate_drowsy_state(
        self,
        frame_num: int,
        left_eye_state: EyeState,
        right_eye_state: EyeState
    ) -> OutputData:
        """
        眠気状態を評価
        
        Args:
            frame_num: フレーム番号
            left_eye_state: 左目の状態
            right_eye_state: 右目の状態
            
        Returns:
            判定結果
        """
        # 両目が閉眼状態かチェック
        both_eyes_closed = left_eye_state.is_closed and right_eye_state.is_closed
        
        if both_eyes_closed:
            # タイマー開始または更新
            if not self.timer.state.is_active:
                self.timer.start()
                self.logger.debug("Timer started - both eyes closed")
            
            # フレーム間隔を計算（フレームレートベース）
            dt = 1.0 / self.frame_rate
            self.timer.update(dt)
            
            # 閾値チェック
            if self.timer.is_threshold_exceeded():
                is_drowsy = 1
                self.logger.info(f"Drowsiness detected at frame {frame_num}")
            else:
                is_drowsy = 0
        else:
            # タイマーリセット
            if self.timer.state.is_active:
                self.logger.debug("Timer stopped - eyes opened")
            self.timer.stop()
            is_drowsy = 0
        
        return OutputData(
            is_drowsy=is_drowsy,
            frame_num=frame_num,
            left_eye_closed=left_eye_state.is_closed,
            right_eye_closed=right_eye_state.is_closed,
            continuous_time=self.timer.get_current_duration(),
            error_code=None
        )
    
    def _reset_state(self) -> None:
        """状態リセット"""
        self.timer.stop()
        self.left_eye_manager.reset()
        self.right_eye_manager.reset()
        self.logger.debug("State reset")
    
    def _create_error_output(self, frame_num: int, error_code: str) -> OutputData:
        """
        エラー出力を作成
        
        Args:
            frame_num: フレーム番号
            error_code: エラーコード
            
        Returns:
            エラー結果
        """
        return OutputData(
            is_drowsy=-1,
            frame_num=frame_num,
            left_eye_closed=False,
            right_eye_closed=False,
            continuous_time=0.0,
            error_code=error_code
        )
    
    def reset(self) -> None:
        """完全リセット"""
        self._reset_state()
        self.last_frame_num = -1
        self.last_valid_result = None
        self.data_processor.reset()
        self.logger.info("DrowsyDetector reset")
    
    def set_frame_rate(self, fps: float) -> None:
        """
        フレームレートを設定
        
        Args:
            fps: フレームレート
        """
        if fps <= 0:
            raise ValueError("Frame rate must be positive")
        
        self.frame_rate = fps
        self.logger.info(f"Frame rate set to {fps} fps")
    
    def get_statistics(self) -> dict:
        """統計情報を取得"""
        processor_stats = self.data_processor.get_statistics()
        left_filter_state = self.left_eye_manager.get_filter_state()
        right_filter_state = self.right_eye_manager.get_filter_state()
        
        return {
            'last_frame_num': self.last_frame_num,
            'timer_active': self.timer.state.is_active,
            'current_continuous_time': self.timer.get_current_duration(),
            'frame_rate': self.frame_rate,
            'data_processor': processor_stats,
            'left_eye_filter': left_filter_state,
            'right_eye_filter': right_filter_state
        }
