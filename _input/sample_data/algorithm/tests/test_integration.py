"""
統合テスト

各モジュールを組み合わせた統合テストを実施します。
"""

import pytest
import numpy as np
import sys
import time
from pathlib import Path

# パッケージのルートを追加
sys.path.append(str(Path(__file__).parent.parent))

from source.config.config import Config
from source.config.validators import InputData
from source.core.drowsy_detector import DrowsyDetector


class TestIntegration:
    """統合テスト"""
    
    def test_realistic_scenario(self):
        """現実的なシナリオのテスト"""
        config = Config(
            left_eye_close_threshold=0.30,
            right_eye_close_threshold=0.30,
            continuous_close_time=1.5,
            face_conf_threshold=0.70,
            log_level="ERROR"
        )
        detector = DrowsyDetector(config)
        
        # 現実的なデータシーケンス
        scenarios = [
            # 1. 正常な運転開始 (30フレーム = 1秒)
            [(0.8, 0.85, 0.95) for _ in range(30)],
            
            # 2. 軽いまばたき (6フレーム = 0.2秒)
            [(0.1, 0.1, 0.95) for _ in range(6)],
            
            # 3. 正常状態に戻る (30フレーム = 1秒)
            [(0.8, 0.85, 0.95) for _ in range(30)],
            
            # 4. 疲労による長時間閉眼 (60フレーム = 2秒)
            [(0.15, 0.18, 0.90) for _ in range(60)],
            
            # 5. 覚醒 (30フレーム = 1秒)
            [(0.9, 0.9, 0.95) for _ in range(30)],
            
            # 6. 顔検出失敗 (15フレーム = 0.5秒)
            [(0.8, 0.8, 0.5) for _ in range(15)],
            
            # 7. 正常復帰 (30フレーム = 1秒)
            [(0.8, 0.85, 0.95) for _ in range(30)],
        ]
        
        frame_num = 1
        drowsy_periods = []
        error_count = 0
        current_drowsy_start = None
        
        for scenario in scenarios:
            for left_eye, right_eye, face_conf in scenario:
                input_data = InputData(
                    frame_num=frame_num,
                    left_eye_open=left_eye,
                    right_eye_open=right_eye,
                    face_confidence=face_conf
                )
                
                result = detector.update(input_data)
                
                # 眠気検知の追跡
                if result.is_drowsy == 1 and current_drowsy_start is None:
                    current_drowsy_start = frame_num
                elif result.is_drowsy != 1 and current_drowsy_start is not None:
                    drowsy_periods.append((current_drowsy_start, frame_num - 1))
                    current_drowsy_start = None
                elif result.is_drowsy == -1:
                    error_count += 1
                
                frame_num += 1
        
        # 結果検証
        assert len(drowsy_periods) >= 1, "少なくとも1回の眠気検知があるべき"
        assert error_count > 0, "顔検出失敗によるエラーがあるべき"
        
        # 統計情報の確認
        stats = detector.get_statistics()
        assert stats['data_processor']['total_processed'] > 0
        assert stats['data_processor']['nan_count'] == 0  # NaNは発生しないはず
    
    def test_long_duration_simulation(self):
        """長時間シミュレーションテスト"""
        config = Config(
            continuous_close_time=0.5,  # 短時間でテスト
            log_level="ERROR"
        )
        detector = DrowsyDetector(config)
        
        drowsy_count = 0
        total_frames = 900  # 30fps * 30秒
        
        np.random.seed(42)  # 再現可能な結果のため
        
        for i in range(total_frames):
            # ランダムな開眼度（時々閉眼）
            if i % 100 < 20:  # 20%の確率で閉眼期間
                left_eye = np.random.uniform(0.0, 0.2)
                right_eye = np.random.uniform(0.0, 0.2)
            else:
                left_eye = np.random.uniform(0.5, 1.0)
                right_eye = np.random.uniform(0.5, 1.0)
            
            # 顔検出信頼度もランダム（ほとんどは高い）
            if np.random.random() < 0.05:  # 5%の確率で低信頼度
                face_confidence = np.random.uniform(0.3, 0.6)
            else:
                face_confidence = np.random.uniform(0.8, 1.0)
            
            input_data = InputData(
                frame_num=i+1,
                left_eye_open=left_eye,
                right_eye_open=right_eye,
                face_confidence=face_confidence
            )
            
            result = detector.update(input_data)
            if result.is_drowsy == 1:
                drowsy_count += 1
        
        # 誤検知率チェック（10%以下であることを確認）
        false_positive_rate = drowsy_count / total_frames
        assert false_positive_rate < 0.10, f"誤検知率が高すぎます: {false_positive_rate*100:.1f}%"
        
        # 統計情報の確認
        stats = detector.get_statistics()
        assert stats['data_processor']['total_processed'] == total_frames
        print(f"NaN発生率: {stats['data_processor']['nan_rate']*100:.2f}%")
        print(f"眠気検知率: {false_positive_rate*100:.2f}%")
    
    def test_performance_benchmark(self):
        """パフォーマンスベンチマーク"""
        config = Config(log_level="ERROR")
        detector = DrowsyDetector(config)
        
        num_frames = 1000
        
        # パフォーマンス測定
        start_time = time.time()
        
        for i in range(num_frames):
            input_data = InputData(
                frame_num=i+1,
                left_eye_open=0.5,
                right_eye_open=0.5,
                face_confidence=0.95
            )
            detector.update(input_data)
        
        end_time = time.time()
        duration = end_time - start_time
        fps = num_frames / duration
        
        print(f"処理性能: {fps:.1f} FPS ({duration:.3f}秒で{num_frames}フレーム)")
        
        # 30fps以上の処理速度を期待
        assert fps >= 30.0, f"処理速度が不十分です: {fps:.1f} FPS"
    
    def test_edge_cases(self):
        """エッジケースのテスト"""
        config = Config(log_level="ERROR")
        detector = DrowsyDetector(config)
        
        edge_cases = [
            # 極端な値
            (0.0, 0.0, 1.0),    # 完全閉眼、高信頼度
            (1.0, 1.0, 1.0),    # 完全開眼、高信頼度
            (0.5, 0.5, 0.0),    # 中間値、低信頼度
            
            # 左右の目で異なる値
            (0.0, 1.0, 0.8),    # 左閉眼、右開眼
            (1.0, 0.0, 0.8),    # 左開眼、右閉眼
            
            # 境界値
            (0.30, 0.30, 0.70), # ちょうど閾値
            (0.31, 0.31, 0.71), # 閾値をわずかに超える
            (0.29, 0.29, 0.69), # 閾値をわずかに下回る
        ]
        
        for i, (left_eye, right_eye, face_conf) in enumerate(edge_cases):
            input_data = InputData(
                frame_num=i+1,
                left_eye_open=left_eye,
                right_eye_open=right_eye,
                face_confidence=face_conf
            )
            
            # 例外が発生しないことを確認
            result = detector.update(input_data)
            assert result is not None
            assert result.frame_num == i+1
            assert result.is_drowsy in [-1, 0, 1]
    
    def test_filter_effectiveness(self):
        """フィルタ効果のテスト"""
        # フィルタありの設定
        config_with_filter = Config(
            enable_ema_filter=True,
            ema_alpha=0.3,
            log_level="ERROR"
        )
        detector_with_filter = DrowsyDetector(config_with_filter)
        
        # フィルタなしの設定
        config_without_filter = Config(
            enable_ema_filter=False,
            log_level="ERROR"
        )
        detector_without_filter = DrowsyDetector(config_without_filter)
        
        # ノイズの多いデータ
        np.random.seed(42)
        noisy_data = []
        base_value = 0.7
        
        for i in range(50):
            # ベース値にランダムノイズを追加
            noise = np.random.uniform(-0.3, 0.3)
            noisy_value = max(0.0, min(1.0, base_value + noise))
            noisy_data.append(noisy_value)
        
        results_with_filter = []
        results_without_filter = []
        
        for i, value in enumerate(noisy_data):
            input_data = InputData(
                frame_num=i+1,
                left_eye_open=value,
                right_eye_open=value,
                face_confidence=0.95
            )
            
            result_with = detector_with_filter.update(input_data)
            result_without = detector_without_filter.update(input_data)
            
            results_with_filter.append(result_with)
            results_without_filter.append(result_without)
        
        # フィルタありの方がより安定した結果を示すことを確認
        # （ここでは簡単な確認として、連続した結果の変動を比較）
        
        changes_with_filter = sum(
            1 for i in range(1, len(results_with_filter))
            if results_with_filter[i].is_drowsy != results_with_filter[i-1].is_drowsy
        )
        
        changes_without_filter = sum(
            1 for i in range(1, len(results_without_filter))
            if results_without_filter[i].is_drowsy != results_without_filter[i-1].is_drowsy
        )
        
        print(f"フィルタあり状態変化: {changes_with_filter}")
        print(f"フィルタなし状態変化: {changes_without_filter}")
        
        # フィルタありの方が状態変化が少ない（より安定）ことを期待
        assert changes_with_filter <= changes_without_filter + 2  # 多少の許容差
