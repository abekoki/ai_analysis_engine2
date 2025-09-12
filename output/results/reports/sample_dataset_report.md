# 個別データ分析レポート - sample_dataset

## 概要

- 結論: アルゴリズムは期待値に対して不整合な結果を示しました。フレーム区間36-136において「連続閉眼あり」との期待値があるにもかかわらず、アルゴリズム出力はそれを検知できていない可能性があります。
- 解析対象動画: sample_dataset
- フレーム区間: 36-136
- 期待値: フレーム区間36-136の間に「連続閉眼あり」が存在すること
- 検知結果: アルゴリズム出力は期待値に対して不一致であり、連続閉眼状態を検知できていない可能性があります。

## 確認結果

### データ構造確認
- アルゴリズム出力:
  - 列名: `is_drowsy`
  - データ型: int
  - 欠損値状況: なし
- コアライブラリ出力:
  - 列名: `frame`, `leye_openness`, `reye_openness`, `confidence`
  - データ型: int, float, float, float
  - 欠損値状況: なし
- 仕様準拠状況: アルゴリズム出力は仕様に準拠しており、必要なフィールドが全て存在しています。

### アルゴリズム出力結果の時系列グラフ
![アルゴリズム出力の時系列グラフ](path_to_algorithm_output_graph.png)
アルゴリズム出力の時系列推移（`is_drowsy`の判定結果）

### コア出力結果の時系列グラフ
![コア出力の時系列グラフ](path_to_core_output_graph.png)
コア出力の時系列推移（`leye_openness`, `reye_openness`, `confidence`の推移）

### 仕様ベースの詳細分析
- アルゴリズム判定ロジックの検証: 
  - `left_eye_close_threshold`と`right_eye_close_threshold`は共に0.10に設定されており、開眼度がこの値以下であれば閉眼と判定されます。
  - `continuous_close_time`は1.00秒に設定されており、両目が閉眼状態であるフラグがこの時間以上継続した場合に「連続閉眼あり」と判定されます。
- エラーパターンの分析: 
  - アルゴリズム出力において、信頼度が0.50であるため、顔検出信頼度が`face_conf_threshold`（0.75）を下回っている可能性があります。この場合、アルゴリズムはスキップされ、エラーコードが返されることになります。
- 期待値との整合性: 
  - フレーム区間36-136において、期待値は「連続閉眼あり」であるにもかかわらず、アルゴリズム出力がそれを示さないため、期待値との整合性が取れていません。

- 考えられる原因: 
  - 顔検出信頼度が低いため、アルゴリズムがフレームをスキップしている可能性があります。また、開眼度のデータが期待値に対して不十分である可能性も考えられます。

## 推奨事項

- アルゴリズムの信頼度閾値を見直し、顔検出信頼度が低い場合でも、他の条件を考慮して判定を行うように改善することを推奨します。
- 開眼度のデータ品質を向上させるために、データ収集環境やカメラの設定を見直すことを検討してください。
- 連続閉眼状態の検知に必要な時間閾値を調整し、より短い時間での検知を可能にすることも一つの改善策です。

## 参照した仕様/コード（抜粋）

### アルゴリズム仕様の関連部分
- `left_eye_close_threshold`: 左目の開眼度がこの値以下で閉眼と判定 (デフォルト: 0.10)
- `right_eye_close_threshold`: 右目の開眼度がこの値以下で閉眼と判定 (デフォルト: 0.10)
- `continuous_close_time`: 連続閉眼とみなす時間閾値 [s] (デフォルト: 1.00)

### 検証で使用したコード
```python
if face_confidence < face_conf_threshold:
    reset_timer()
    return is_drowsy=-1  # エラー

# 左右それぞれの目の閉眼判定
left_eye_closed = left_eye_open <= left_eye_close_threshold
right_eye_closed = right_eye_open <= right_eye_close_threshold

# 両目が閉眼状態かチェック
if left_eye_closed and right_eye_closed:
    update_timer(dt)
    if timer >= continuous_close_time:
        return is_drowsy=1   # 連続閉眼状態
    else:
        return is_drowsy=0   # 両目閉眼中だが時間不足
else:
    reset_timer()
    return is_drowsy=0       # 非連続閉眼状態
```

### 分析結果の仕様準拠評価
- アルゴリズム出力は仕様に準拠しているが、期待値との整合性が取れていないため、さらなる改善が必要です。