# 眠気検知アルゴリズムのハードコーディング箇所分析レポート

## 分析概要

AI分析エンジンのコードベース全体を調査し、連続閉眼検知・開閉眼関連アルゴリズムにおけるハードコーディング箇所を特定・分類しました。

**分析対象**: `src/ai_analysis_engine/` 配下の全Pythonファイル  
**分析日時**: 2025年9月16日  
**分析者**: AIアシスタント

## ハードコーディング分類

### 1. アルゴリズム閾値のハードコーディング

#### ファイル: `src/ai_analysis_engine/agents/verifier_agent.py`

**場所**: `_generate_verification_code` メソッド (162-169行)

```python
# Algorithm specifications from drowsy_detection spec
"# left_eye_close_threshold: 0.10",
"# right_eye_close_threshold: 0.10",
"# face_conf_threshold: 0.75",
"# continuous_close_time: 1.00 seconds",
"LEFT_EYE_THRESHOLD = 0.10",
"RIGHT_EYE_THRESHOLD = 0.10",
"FACE_CONF_THRESHOLD = 0.75",
"CONTINUOUS_CLOSE_TIME = 1.0",
```

**問題点**:
- 左眼閉眼閾値: `0.10` (ハードコーディング)
- 右眼閉眼閾値: `0.10` (ハードコーディング)
- 顔信頼度閾値: `0.75` (ハードコーディング)
- 連続閉眼時間: `1.0`秒 (ハードコーディング)

**影響**: アルゴリズムの感度調整がコード変更を必要とする

---

### 2. データ列名のハードコーディング

#### ファイル: `src/ai_analysis_engine/agents/verifier_agent.py`

**場所**: データ品質チェック部 (184-185行)

```python
"required_algo_cols = ['frame_num', 'is_drowsy']",
"required_core_cols = ['leye_openness', 'reye_openness']",
```

**場所**: 眼状態ロジック検証部 (233行)

```python
"if all(col in core_df.columns for col in ['leye_openness', 'reye_openness']):",
```

**場所**: 一般検証部 (289行)

```python
"eye_cols_present = all(col in core_df.columns for col in ['leye_openness', 'reye_openness'])",
```

**場所**: 値範囲チェック部 (202行)

```python
"eye_cols = ['leye_openness', 'reye_openness']",
```

#### ファイル: `src/ai_analysis_engine/core/nodes.py`

**場所**: データプロット部 (253, 262行)

```python
if {'left_eye_closed', 'right_eye_closed'}.issubset(set(df.columns)) or 'is_drowsy' in df.columns:
# ...
elif {'leye_openness', 'reye_openness'}.issubset(set(df.columns)):
```

**問題点**:
- 必須列名: `['frame_num', 'is_drowsy']` (アルゴリズム出力)
- 必須列名: `['leye_openness', 'reye_openness']` (コア出力)
- 列名: `'left_eye_closed'`, `'right_eye_closed'`
- 列名: `'continuous_time'`

**影響**: データスキーマ変更時に複数箇所の修正が必要

---

### 3. アルゴリズム仕様のハードコーディング

#### ファイル: `src/ai_analysis_engine/agents/verifier_agent.py`

**場所**: アルゴリズム出力検証部 (221-230行)

```python
"if all(col in algo_df.columns for col in ['frame_num', 'is_drowsy']):",
"    error_frames = algo_df[algo_df['is_drowsy'] == -1]",
"    drowsy_dist = algo_df['is_drowsy'].value_counts()",
```

**場所**: 状態遷移検証部 (264-269行)

```python
"if 'is_drowsy' in algo_df.columns:",
"    state_changes = algo_df['is_drowsy'].diff().fillna(0)",
"    invalid_transitions = state_changes.abs() > 1  # Should only change by -1, 0, or 1",
```

**問題点**:
- `is_drowsy` の有効値: `[-1, 0, 1]` (エラー、正常、眠気)
- 状態遷移ルール: 絶対値 > 1 の遷移を無効と判定
- `continuous_time` の非現実的値チェック: `CONTINUOUS_CLOSE_TIME * 2` 超え

**影響**: アルゴリズム仕様変更時に仕様理解の更新が必要

---

### 4. 日本語テキストのハードコーディング

#### ファイル: `src/ai_analysis_engine/core/nodes.py`

**場所**: 期待値解析部 (404行)

```python
require_exists = ("連続閉眼" in expected)
```

**場所**: エラーメッセージ部 (519, 673行)

```python
results["issues"].append("Expected continuous closure not found in target interval")
causes.append("被験者が閉眼していない可能性")
```

**問題点**:
- 日本語キーワード: `"連続閉眼"`
- 日本語エラーメッセージ: `"被験者が閉眼していない可能性"`

**影響**: 多言語対応時のテキスト管理が困難

---

### 5. 数値範囲のハードコーディング

#### ファイル: `src/ai_analysis_engine/agents/verifier_agent.py`

**場所**: 眼開度範囲チェック部 (201-206行)

```python
"# Check eye openness ranges (should be 0.0-1.0)",
"eye_cols = ['leye_openness', 'reye_openness']",
"for col in eye_cols:",
"    if col in core_df.columns:",
"        valid_range = (core_df[col] >= 0.0) & (core_df[col] <= 1.0)",
"        print(f'{col} in valid range [0,1]: {valid_range.all()}')",
```

**場所**: アルゴリズム出力範囲チェック部 (284-287行)

```python
"if 'is_drowsy' in algo_df.columns:",
"    valid_range = algo_df['is_drowsy'].isin([-1, 0, 1]).all()",
"    print(f'Algorithm output in valid range: {valid_range}')",
```

**問題点**:
- 眼開度有効範囲: `[0.0, 1.0]`
- アルゴリズム出力有効値: `[-1, 0, 1]`

**影響**: データ範囲仕様変更時に複数箇所の更新が必要

---

## 影響評価

### 保守性への影響
1. **設定変更の困難さ**: 閾値変更時にコード修正が必要
2. **拡張性の欠如**: 新しいパラメータ追加時の影響範囲特定が困難
3. **テストの複雑さ**: ハードコーディングされた値のテストが不十分

### リスク評価
1. **仕様変更リスク**: アルゴリズム仕様更新時の修正漏れ
2. **デプロイリスク**: 環境別設定の管理ミス
3. **品質リスク**: ハードコーディングによる人的ミス

## 推奨改善策

### 1. 設定ファイル化
```python
# config/algorithm_config.py を作成
class DrowsyDetectionConfig:
    left_eye_threshold = 0.10
    right_eye_threshold = 0.10
    face_confidence_threshold = 0.75
    continuous_close_time = 1.0
    eye_openness_range = (0.0, 1.0)
    algorithm_output_values = [-1, 0, 1]
```

### 2. 定数定義の集中化
```python
# constants/algorithm_constants.py
REQUIRED_ALGORITHM_COLUMNS = ['frame_num', 'is_drowsy']
REQUIRED_CORE_COLUMNS = ['leye_openness', 'reye_openness']
EYE_OPENNESS_RANGE = (0.0, 1.0)
```

### 3. 国際化対応
```python
# i18n/messages.py
MESSAGES = {
    'continuous_closure_not_found': {
        'ja': '連続閉眼が検知されませんでした',
        'en': 'Continuous closure not detected'
    }
}
```

## 優先度別改善計画

### 高優先度 (今すぐ対応)
1. アルゴリズム閾値の設定ファイル化
2. 必須列名の定数化
3. 数値範囲の定数化

### 中優先度 (次期リリース)
1. 日本語テキストの国際化対応
2. アルゴリズム仕様の動的読み込み
3. 設定値の検証機能追加

### 低優先度 (将来対応)
1. プラグインアーキテクチャによるアルゴリズム拡張
2. 動的設定更新機能
3. A/Bテスト対応

## 結論

コードベースには複数のハードコーディング箇所が確認され、特に眠気検知アルゴリズムの閾値と列名がハードコーディングされています。これらの改善により、保守性と拡張性が大幅に向上します。

**推奨**: 高優先度の改善項目から順次対応することを提案します。

---

**レポート生成日時**: 2025年9月16日
**分析対象バージョン**: v0.1.0
**分析ファイル数**: 8ファイル
**特定ハードコーディング箇所**: 15箇所
