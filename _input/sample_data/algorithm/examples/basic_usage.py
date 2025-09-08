"""
基本的な使用例

連続閉眼検知アルゴリズムの基本的な使用方法を示します。
"""

from drowsy_detection.config.config import Config
from drowsy_detection.config.validators import InputData
from drowsy_detection.core.drowsy_detector import DrowsyDetector


def basic_example():
    """基本的な使用例"""
    print("=== 連続閉眼検知アルゴリズム 基本使用例 ===\n")
    
    # 設定
    config = Config(
        left_eye_close_threshold=0.30,
        right_eye_close_threshold=0.30,
        continuous_close_time=1.0,
        face_conf_threshold=0.70,
        log_level="INFO"
    )
    
    print(f"設定: {config.dict()}\n")
    
    # 検出器初期化
    detector = DrowsyDetector(config)
    
    # シミュレーションデータ
    simulation_data = [
        # 正常な開眼状態
        *[{"frame_num": i, "left_eye_open": 0.8, "right_eye_open": 0.9, "face_confidence": 0.95} 
          for i in range(1, 11)],
        
        # 軽い閉眼（短時間）
        *[{"frame_num": i, "left_eye_open": 0.25, "right_eye_open": 0.20, "face_confidence": 0.90} 
          for i in range(11, 21)],
        
        # 開眼に戻る
        *[{"frame_num": i, "left_eye_open": 0.7, "right_eye_open": 0.8, "face_confidence": 0.95} 
          for i in range(21, 31)],
        
        # 長時間閉眼（眠気検知対象）
        *[{"frame_num": i, "left_eye_open": 0.15, "right_eye_open": 0.18, "face_confidence": 0.92} 
          for i in range(31, 71)],  # 40フレーム = 約1.3秒（30fps想定）
        
        # 再び開眼
        *[{"frame_num": i, "left_eye_open": 0.8, "right_eye_open": 0.85, "face_confidence": 0.95} 
          for i in range(71, 81)],
    ]
    
    print("シミュレーション開始...")
    
    # 処理実行
    drowsy_detected = False
    for data in simulation_data:
        input_data = InputData(**data)
        result = detector.update(input_data)
        
        # 重要なイベントのみ表示
        if result.is_drowsy == 1 and not drowsy_detected:
            print(f"⚠️  眠気検知！ フレーム {result.frame_num}")
            print(f"   連続閉眼時間: {result.continuous_time:.2f}秒")
            drowsy_detected = True
        elif result.is_drowsy == 0 and drowsy_detected:
            print(f"✅ 覚醒状態に戻りました フレーム {result.frame_num}")
            drowsy_detected = False
        elif result.is_drowsy == -1:
            print(f"❌ エラー発生 フレーム {result.frame_num}: {result.error_code}")
    
    print("\nシミュレーション完了")
    
    # 統計情報表示
    stats = detector.get_statistics()
    print(f"\n=== 統計情報 ===")
    print(f"処理フレーム数: {stats['last_frame_num']}")
    print(f"最終連続閉眼時間: {stats['current_continuous_time']:.2f}秒")
    print(f"データ前処理統計: {stats['data_processor']}")


def error_handling_example():
    """エラーハンドリング例"""
    print("\n=== エラーハンドリング例 ===\n")
    
    config = Config(face_conf_threshold=0.80)  # 高い閾値を設定
    detector = DrowsyDetector(config)
    
    # 低い顔検出信頼度のデータ
    test_cases = [
        {"frame_num": 1, "left_eye_open": 0.1, "right_eye_open": 0.1, "face_confidence": 0.5},  # 低信頼度
        {"frame_num": 2, "left_eye_open": 0.8, "right_eye_open": 0.9, "face_confidence": 0.95},  # 正常
        {"frame_num": 1, "left_eye_open": 0.5, "right_eye_open": 0.5, "face_confidence": 0.9},   # 無効なフレーム番号
    ]
    
    for data in test_cases:
        input_data = InputData(**data)
        result = detector.update(input_data)
        
        if result.is_drowsy == -1:
            print(f"エラー検出 - フレーム {result.frame_num}: {result.error_code}")
        else:
            print(f"正常処理 - フレーム {result.frame_num}: is_drowsy={result.is_drowsy}")


def custom_config_example():
    """カスタム設定例"""
    print("\n=== カスタム設定例 ===\n")
    
    # より敏感な設定
    sensitive_config = Config(
        left_eye_close_threshold=0.40,   # より高い閾値
        right_eye_close_threshold=0.40,  # より高い閾値
        continuous_close_time=0.5,       # より短い時間
        face_conf_threshold=0.60,        # より低い信頼度閾値
        enable_ema_filter=True,
        ema_alpha=0.5,                   # より反応的なフィルタ
        log_level="DEBUG"
    )
    
    print(f"敏感設定: {sensitive_config.dict()}")
    
    detector = DrowsyDetector(sensitive_config)
    
    # 短時間の閉眼をテスト
    test_data = [
        {"frame_num": i, "left_eye_open": 0.35, "right_eye_open": 0.35, "face_confidence": 0.8}
        for i in range(1, 20)  # 19フレーム = 約0.6秒
    ]
    
    drowsy_count = 0
    for data in test_data:
        input_data = InputData(**data)
        result = detector.update(input_data)
        
        if result.is_drowsy == 1:
            drowsy_count += 1
    
    print(f"敏感設定での眠気検知フレーム数: {drowsy_count}")


if __name__ == "__main__":
    basic_example()
    error_handling_example()
    custom_config_example()
    
    print("\n=== 使用例完了 ===")
    print("詳細なログを確認したい場合は、log_level='DEBUG'を設定してください。")
