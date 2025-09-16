"""
眠気検知アルゴリズムのハードコーディング改善提案
============================================

このファイルは、特定されたハードコーディング箇所に対する
改善提案の実装例を示しています。
"""

# ================================
# 1. 設定ファイル化の提案
# ================================

class DrowsyDetectionConfig:
    """眠気検知アルゴリズムの設定クラス"""

    # 眼閾値設定
    LEFT_EYE_CLOSE_THRESHOLD = 0.10
    RIGHT_EYE_CLOSE_THRESHOLD = 0.10
    FACE_CONFIDENCE_THRESHOLD = 0.75

    # 時間設定
    CONTINUOUS_CLOSE_TIME_SECONDS = 1.0
    MAX_CONTINUOUS_TIME_MULTIPLIER = 2.0  # 非現実的時間の判定用

    # データ範囲設定
    EYE_OPENNESS_RANGE = (0.0, 1.0)
    ALGORITHM_OUTPUT_VALID_VALUES = [-1, 0, 1]  # -1:エラー, 0:正常, 1:眠気

    # 最大状態遷移
    MAX_STATE_TRANSITION = 1

    @classmethod
    def get_eye_thresholds(cls):
        """眼閾値を取得"""
        return {
            'left': cls.LEFT_EYE_CLOSE_THRESHOLD,
            'right': cls.RIGHT_EYE_CLOSE_THRESHOLD
        }

    @classmethod
    def get_all_thresholds(cls):
        """全閾値を取得"""
        return {
            'left_eye': cls.LEFT_EYE_CLOSE_THRESHOLD,
            'right_eye': cls.RIGHT_EYE_CLOSE_THRESHOLD,
            'face_confidence': cls.FACE_CONFIDENCE_THRESHOLD,
            'continuous_time': cls.CONTINUOUS_CLOSE_TIME_SECONDS
        }


# ================================
# 2. 定数定義の集中化
# ================================

class AlgorithmConstants:
    """アルゴリズム関連定数"""

    # 必須列名
    REQUIRED_ALGORITHM_COLUMNS = ['frame_num', 'is_drowsy']
    REQUIRED_CORE_COLUMNS = ['leye_openness', 'reye_openness']

    # オプション列名
    OPTIONAL_COLUMNS = {
        'algorithm': ['continuous_time', 'error_code', 'confidence'],
        'core': ['left_eye_closed', 'right_eye_closed', 'face_confidence']
    }

    # 列名マッピング
    COLUMN_MAPPINGS = {
        'left_eye_openness': 'leye_openness',
        'right_eye_openness': 'reye_openness',
        'drowsy_detection': 'is_drowsy',
        'continuous_closure_time': 'continuous_time'
    }

    @classmethod
    def get_required_columns(cls, data_type='algorithm'):
        """データタイプに応じた必須列を取得"""
        if data_type == 'algorithm':
            return cls.REQUIRED_ALGORITHM_COLUMNS
        elif data_type == 'core':
            return cls.REQUIRED_CORE_COLUMNS
        else:
            return []


# ================================
# 3. 国際化対応
# ================================

class AlgorithmMessages:
    """アルゴリズム関連メッセージ"""

    MESSAGES = {
        'continuous_closure_not_found': {
            'ja': '連続閉眼が検知されませんでした',
            'en': 'Continuous closure not detected'
        },
        'subject_not_closed_eyes': {
            'ja': '被験者が閉眼していない可能性があります',
            'en': 'Subject may not have closed eyes'
        },
        'invalid_threshold': {
            'ja': '無効な閾値が設定されています',
            'en': 'Invalid threshold configured'
        },
        'missing_required_columns': {
            'ja': '必須列が不足しています: {columns}',
            'en': 'Missing required columns: {columns}'
        }
    }

    @classmethod
    def get_message(cls, key, language='ja', **kwargs):
        """言語指定でメッセージを取得"""
        message = cls.MESSAGES.get(key, {}).get(language, key)
        return message.format(**kwargs) if kwargs else message


# ================================
# 4. 検証関数の改善例
# ================================

class AlgorithmValidator:
    """アルゴリズム検証クラス"""

    def __init__(self, config=None, constants=None, messages=None):
        self.config = config or DrowsyDetectionConfig()
        self.constants = constants or AlgorithmConstants()
        self.messages = messages or AlgorithmMessages()

    def validate_eye_openness_range(self, df, columns):
        """眼開度範囲の検証"""
        range_min, range_max = self.config.EYE_OPENNESS_RANGE
        results = {}

        for col in columns:
            if col in df.columns:
                valid_range = (df[col] >= range_min) & (df[col] <= range_max)
                results[col] = {
                    'valid': valid_range.all(),
                    'invalid_count': (~valid_range).sum(),
                    'range': self.config.EYE_OPENNESS_RANGE
                }

        return results

    def validate_algorithm_output(self, df, column='is_drowsy'):
        """アルゴリズム出力の検証"""
        if column not in df.columns:
            return {'error': self.messages.get_message('missing_required_columns',
                                                     columns=[column])}

        valid_values = self.config.ALGORITHM_OUTPUT_VALID_VALUES
        valid_mask = df[column].isin(valid_values)

        return {
            'valid': valid_mask.all(),
            'invalid_count': (~valid_mask).sum(),
            'valid_values': valid_values,
            'distribution': df[column].value_counts().to_dict()
        }

    def validate_state_transitions(self, df, column='is_drowsy'):
        """状態遷移の検証"""
        if column not in df.columns:
            return {'error': self.messages.get_message('missing_required_columns',
                                                     columns=[column])}

        state_changes = df[column].diff().fillna(0)
        max_transition = self.config.MAX_STATE_TRANSITION

        invalid_transitions = state_changes.abs() > max_transition
        valid_transitions = ~invalid_transitions

        return {
            'valid': valid_transitions.all(),
            'invalid_count': invalid_transitions.sum(),
            'max_allowed_transition': max_transition,
            'transitions': state_changes.value_counts().to_dict()
        }

    def validate_continuous_time(self, df, column='continuous_time'):
        """連続時間の検証"""
        if column not in df.columns:
            return {'valid': True, 'message': 'Continuous time column not present'}

        continuous_time = df[column]
        max_realistic_time = (self.config.CONTINUOUS_CLOSE_TIME_SECONDS *
                             self.config.MAX_CONTINUOUS_TIME_MULTIPLIER)

        unrealistic_times = continuous_time > max_realistic_time

        return {
            'valid': not unrealistic_times.any(),
            'unrealistic_count': unrealistic_times.sum(),
            'max_realistic_time': max_realistic_time,
            'statistics': continuous_time.describe().to_dict()
        }


# ================================
# 5. 使用例
# ================================

def demonstrate_improved_validation():
    """改善された検証の使用例"""
    import pandas as pd

    # 設定インスタンス
    config = DrowsyDetectionConfig()
    validator = AlgorithmValidator(config=config)

    # サンプルデータ
    sample_data = {
        'leye_openness': [0.8, 0.2, 0.9, 0.1, 0.7],
        'reye_openness': [0.7, 0.3, 0.8, 0.2, 0.6],
        'is_drowsy': [0, 0, 1, -1, 0],
        'continuous_time': [0.0, 0.0, 0.5, 0.0, 0.0]
    }
    df = pd.DataFrame(sample_data)

    # 検証実行
    eye_validation = validator.validate_eye_openness_range(
        df, ['leye_openness', 'reye_openness']
    )

    algorithm_validation = validator.validate_algorithm_output(df)

    transition_validation = validator.validate_state_transitions(df)

    continuous_validation = validator.validate_continuous_time(df)

    # 結果表示
    print("=== Eye Openness Validation ===")
    for col, result in eye_validation.items():
        print(f"{col}: Valid={result['valid']}, Range={result['range']}")

    print("\n=== Algorithm Output Validation ===")
    print(f"Valid: {algorithm_validation['valid']}")
    print(f"Distribution: {algorithm_validation['distribution']}")

    print("\n=== State Transition Validation ===")
    print(f"Valid: {transition_validation['valid']}")

    print("\n=== Continuous Time Validation ===")
    print(f"Valid: {continuous_validation['valid']}")


if __name__ == "__main__":
    demonstrate_improved_validation()
