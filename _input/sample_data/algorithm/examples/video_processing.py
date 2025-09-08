"""
動画処理の使用例

実際の動画ストリームを想定した連続閉眼検知の使用例を示します。
"""

from drowsy_detection.config.config import Config
from drowsy_detection.config.validators import InputData
from drowsy_detection.core.drowsy_detector import DrowsyDetector


def simulate_video_stream(duration_seconds: int = 30, fps: int = 30):
    """
    動画ストリームをシミュレート
    
    Args:
        duration_seconds: シミュレーション時間（秒）
        fps: フレームレート
    """
    print(f"=== 動画ストリームシミュレーション ({duration_seconds}秒, {fps}fps) ===\n")
    
    # 設定
    config = Config(
        left_eye_close_threshold=0.30,
        right_eye_close_threshold=0.30,
        continuous_close_time=2.0,  # 2秒の連続閉眼で検知
        face_conf_threshold=0.70,
        log_level="INFO",
        enable_ema_filter=True,
        ema_alpha=0.3
    )
    
    # 検出器初期化
    detector = DrowsyDetector(config)
    detector.set_frame_rate(fps)
    
    total_frames = duration_seconds * fps
    drowsy_periods = []
    current_drowsy_start = None
    
    print(f"総フレーム数: {total_frames}")
    print("処理開始...\n")
    
    start_time = time.time()
    
    for frame_num in range(1, total_frames + 1):
        # シナリオベースの開眼度生成
        left_eye, right_eye, face_conf = generate_realistic_data(frame_num, total_frames)
        
        # 入力データ作成
        input_data = InputData(
            frame_num=frame_num,
            left_eye_open=left_eye,
            right_eye_open=right_eye,
            face_confidence=face_conf
        )
        
        # 処理実行
        result = detector.update(input_data)
        
        # 眠気検知の追跡
        if result.is_drowsy == 1 and current_drowsy_start is None:
            current_drowsy_start = frame_num
            print(f"⚠️  眠気検知開始 - フレーム {frame_num} ({frame_num/fps:.1f}秒)")
        elif result.is_drowsy == 0 and current_drowsy_start is not None:
            drowsy_duration = (frame_num - current_drowsy_start) / fps
            drowsy_periods.append((current_drowsy_start, frame_num, drowsy_duration))
            print(f"✅ 覚醒 - フレーム {frame_num} (持続時間: {drowsy_duration:.1f}秒)")
            current_drowsy_start = None
        elif result.is_drowsy == -1:
            print(f"❌ エラー - フレーム {frame_num}: {result.error_code}")
        
        # 進捗表示
        if frame_num % (fps * 5) == 0:  # 5秒ごと
            elapsed = frame_num / fps
            print(f"進捗: {elapsed:.0f}/{duration_seconds}秒 ({elapsed/duration_seconds*100:.0f}%)")
        
        # リアルタイム処理をシミュレート
        time.sleep(1.0 / fps / 10)  # 実際の1/10速度で実行
    
    # 最後の眠気期間を処理
    if current_drowsy_start is not None:
        drowsy_duration = (total_frames - current_drowsy_start) / fps
        drowsy_periods.append((current_drowsy_start, total_frames, drowsy_duration))
    
    processing_time = time.time() - start_time
    
    # 結果報告
    print(f"\n=== 処理完了 ===")
    print(f"処理時間: {processing_time:.2f}秒")
    print(f"平均FPS: {total_frames/processing_time:.1f}")
    print(f"眠気検知回数: {len(drowsy_periods)}")
    
    if drowsy_periods:
        print("\n=== 眠気検知詳細 ===")
        total_drowsy_time = 0
        for i, (start_frame, end_frame, duration) in enumerate(drowsy_periods, 1):
            start_time_sec = start_frame / fps
            end_time_sec = end_frame / fps
            total_drowsy_time += duration
            print(f"{i}. {start_time_sec:.1f}s - {end_time_sec:.1f}s (持続: {duration:.1f}秒)")
        
        print(f"\n総眠気時間: {total_drowsy_time:.1f}秒 ({total_drowsy_time/duration_seconds*100:.1f}%)")
    
    # 統計情報
    stats = detector.get_statistics()
    print(f"\n=== 統計情報 ===")
    print(f"NaN発生率: {stats['data_processor']['nan_rate']*100:.2f}%")
    print(f"最終フィルタ値 (左目): {stats['left_eye_filter']['filtered_value']:.3f}")
    print(f"最終フィルタ値 (右目): {stats['right_eye_filter']['filtered_value']:.3f}")


def generate_realistic_data(frame_num: int, total_frames: int):
    """
    リアルな開眼度データを生成
    
    Args:
        frame_num: 現在のフレーム番号
        total_frames: 総フレーム数
        
    Returns:
        (left_eye_open, right_eye_open, face_confidence)
    """
    progress = frame_num / total_frames
    
    # 基本的な開眼状態
    base_left = 0.8
    base_right = 0.85
    
    # 時間による疲労の増加
    fatigue_factor = progress * 0.3  # 30%まで疲労
    base_left -= fatigue_factor
    base_right -= fatigue_factor
    
    # まばたき（ランダム）
    if random.random() < 0.05:  # 5%の確率でまばたき
        blink_intensity = random.uniform(0.3, 0.8)
        base_left *= (1 - blink_intensity)
        base_right *= (1 - blink_intensity)
    
    # 眠気エピソード（特定の時間帯）
    drowsy_episodes = [
        (0.3, 0.4),   # 30-40%の時点
        (0.7, 0.85),  # 70-85%の時点
    ]
    
    for start, end in drowsy_episodes:
        if start <= progress <= end:
            # 眠気期間中は開眼度が低下
            drowsy_intensity = 0.7 * (1 - abs(progress - (start + end) / 2) / ((end - start) / 2))
            base_left *= (1 - drowsy_intensity)
            base_right *= (1 - drowsy_intensity)
    
    # ノイズ追加
    noise_level = 0.1
    left_eye = base_left + random.uniform(-noise_level, noise_level)
    right_eye = base_right + random.uniform(-noise_level, noise_level)
    
    # 顔検出信頼度（時々低下）
    face_confidence = 0.9
    if random.random() < 0.02:  # 2%の確率で信頼度低下
        face_confidence = random.uniform(0.4, 0.7)
    
    # 値の範囲制限
    left_eye = max(0.0, min(1.0, left_eye))
    right_eye = max(0.0, min(1.0, right_eye))
    face_confidence = max(0.0, min(1.0, face_confidence))
    
    return left_eye, right_eye, face_confidence


def real_time_monitoring_example():
    """リアルタイム監視の例"""
    print("\n=== リアルタイム監視例 ===\n")
    
    config = Config(
        continuous_close_time=1.5,
        log_level="WARNING"  # 重要なメッセージのみ
    )
    
    detector = DrowsyDetector(config)
    alert_count = 0
    
    print("リアルタイム監視開始（10秒間）...")
    
    for i in range(1, 301):  # 300フレーム = 10秒（30fps）
        # センサーからのデータを模擬
        left_eye = random.uniform(0.1, 0.9)
        right_eye = random.uniform(0.1, 0.9)
        face_conf = random.uniform(0.8, 1.0)
        
        # 疲労状態をシミュレート
        if i > 150:  # 5秒後から疲労
            left_eye *= 0.6
            right_eye *= 0.6
        
        input_data = InputData(
            frame_num=i,
            left_eye_open=left_eye,
            right_eye_open=right_eye,
            face_confidence=face_conf
        )
        
        result = detector.update(input_data)
        
        if result.is_drowsy == 1:
            alert_count += 1
            if alert_count == 1:
                print(f"🚨 ALERT: 眠気検知！ 時刻: {i/30:.1f}秒")
        
        # リアルタイム処理間隔
        time.sleep(0.01)  # 実際より高速
    
    print(f"監視完了。アラート発生回数: {alert_count}")


if __name__ == "__main__":
    # 短い動画ストリームをシミュレート
    simulate_video_stream(duration_seconds=20, fps=30)
    
    # リアルタイム監視例
    real_time_monitoring_example()
    
    print("\n=== 動画処理例完了 ===")
    print("実際の使用では、カメラやセンサーからのデータを input_data として渡してください。")
