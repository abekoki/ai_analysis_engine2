# AI Analysis Engine

時系列処理アルゴリズムの課題分析システム - AIを用いた自動分析プラットフォーム

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 概要

AI Analysis Engineは、時系列データを扱うアルゴリズムの課題をAIによって自動的に分析・診断するシステムです。LangGraphをベースとした多段階分析ワークフローにより、データの品質チェック、整合性検証、問題仮説生成・検証、レポート作成までを自動化します。

### 🎯 主な目的

- **自動化された課題分析**: 時系列データの品質・性能問題をAIが自動検出
- **多角的な検証**: RAG + REPLツールによる仕様書照合と実データ検証
- **構造化レポート**: 問題特定から解決提案までを含む詳細レポート生成
- **拡張性**: 複数データセットの逐次処理とスケーラブルなアーキテクチャ

## ✨ 主な機能

### 🔍 分析機能
- **データ品質チェック**: CSVデータの構造・欠損値・統計分析
- **整合性検証**: 仕様書との整合性チェック（自然言語期待値対応）
- **仮説生成**: AIによる問題原因の仮説生成
- **仮説検証**: Pythonコード実行による実データ検証
- **レポート生成**: Markdown形式の構造化レポート

### 🛠️ 技術機能
- **RAG (Retrieval-Augmented Generation)**: 仕様書のベクトル化検索
- **REPL (Read-Eval-Print Loop)**: Pythonコード実行環境
- **LangGraphワークフロー**: 多段階分析プロセスの制御
- **複数データセット処理**: 逐次分析によるスケーラビリティ

## 🚀 インストール

### 環境要件
- Python 3.10+
- uv (パッケージマネージャー)

### インストール手順

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd ai-analysis-engine
```

2. **依存関係のインストール**
```bash
# uvを使用する場合
uv sync

# またはpipを使用する場合
pip install -e .
```

3. **環境変数の設定**
```bash
# OpenAI APIキーを設定
export OPENAI_API_KEY="your-api-key-here"
```

## 💡 使用方法

### コマンドラインオプション

AI Analysis Engineは以下の実行方法をサポートしています：

#### 1. テスト実行（推奨）
```bash
# 付属のテストデータで動作確認
uv run python test_engine.py
```

#### 2. メイン実行スクリプト
```bash
# 基本的な分析実行
uv run python run_analysis.py \
  --algorithm-outputs data/algo_output.csv \
  --core-outputs data/core_output.csv \
  --evaluation-specs docs/eval_spec.md \
  --expected-results "フレーム100-200の間に値1が存在すること"
```

#### 3. メインアプリケーション直接実行
```bash
# main.py を直接実行する場合
uv run python -m ai_analysis_engine.main \
  --algorithm-outputs data/algo_output.csv \
  --core-outputs data/core_output.csv \
  --evaluation-specs docs/eval_spec.md \
  --expected-results "フレーム100-200の間に値1が存在すること"
```

### コマンドライン引数の詳細

| オプション | 必須 | 説明 | 例 |
|-----------|------|------|----|
| `--algorithm-outputs` | ✅ | アルゴリズム出力CSVファイルのパス（複数指定可） | `data/algo_output.csv` |
| `--core-outputs` | ✅ | コアライブラリ出力CSVファイルのパス（複数指定可） | `data/core_output.csv` |
| `--algorithm-specs` | ✅ | アルゴリズム仕様Markdownファイルのパス（複数指定可） | `docs/algo_spec.md` |
| `--algorithm-codes` | ❌ | アルゴリズム実装コードファイルのパス（複数指定可） | `src/algo.py src/utils.py` |
| `--evaluation-specs` | ✅ | 評価仕様Markdownファイルのパス（複数指定可） | `docs/eval_spec.md` |
| `--evaluation-codes` | ❌ | 評価環境実装コードファイルのパス（複数指定可） | `eval/main.py eval/utils.py` |
| `--expected-results` | ✅ | 期待される結果の自然言語記述（複数指定可） | `"フレーム100-200の間に値1が存在すること"` |
| `--dataset-ids` | ❌ | データセットのID（オプション、省略時は自動生成） | `dataset_1` |

#### 引数の対応関係
- `--algorithm-outputs`, `--core-outputs`, `--algorithm-specs`, `--evaluation-specs`, `--expected-results` は同じ順序で対応
- `--algorithm-codes`, `--evaluation-codes` は各データセットに対応するコードファイルのリスト（オプション）
- `--evaluation-specs` は対応するデータセットの評価仕様（不足時は最初の仕様を再利用）
- `--dataset-ids` はオプション（指定しない場合は `dataset_1`, `dataset_2`... が自動生成）
- 各データセットは以下のファイル群で構成：
  - アルゴリズム出力CSV + アルゴリズム仕様書 + アルゴリズムコード（オプション）
  - コアライブラリ出力CSV + 評価環境仕様書 + 評価環境コード（オプション）
  - 期待値記述

### Python API使用

#### 基本的な使用例
```python
from ai_analysis_engine import AIAnalysisEngine

# エンジン初期化
engine = AIAnalysisEngine()

if not engine.initialize():
    print("初期化失敗")
    exit(1)

print("AI Analysis Engine initialized successfully")

# 分析リクエスト作成
state = engine.create_analysis_request(
    algorithm_outputs=["data/algo_output.csv"],
    core_outputs=["data/core_output.csv"],
    algorithm_specs=["docs/algo_spec.md"],
    evaluation_specs=["docs/eval_spec.md"],
    expected_results=["期待される動作の自然言語記述"],
    algorithm_codes=[["src/algo.py", "src/utils.py"]],  # オプション
    evaluation_codes=[["eval/main.py"]],  # オプション
    dataset_ids=["dataset_1"]
)

# 分析実行
results = engine.run_analysis(state)

if "error" in results:
    print(f"Analysis failed: {results['error']}")
else:
    print("Analysis completed successfully!")
    print(f"Reports saved to: output directory")
```

#### 複数データセットの処理
```python
# 複数データセットの一括処理
state = engine.create_analysis_request(
    algorithm_outputs=[
        "data/dataset1_algo.csv",
        "data/dataset2_algo.csv"
    ],
    core_outputs=[
        "data/dataset1_core.csv",
        "data/dataset2_core.csv"
    ],
    algorithm_specs=[
        "docs/dataset1_algo_spec.md",
        "docs/dataset2_algo_spec.md"
    ],
    evaluation_specs=[
        "docs/dataset1_eval_spec.md",
        "docs/dataset2_eval_spec.md"
    ],
    expected_results=[
        "データセット1の期待結果",
        "データセット2の期待結果"
    ],
    algorithm_codes=[
        ["src/dataset1/algo.py", "src/dataset1/utils.py"],
        ["src/dataset2/algo.py", "src/dataset2/utils.py"]
    ],
    evaluation_codes=[
        ["eval/dataset1/main.py"],
        ["eval/dataset2/main.py"]
    ],
    dataset_ids=["dataset_1", "dataset_2"]
)

results = engine.run_analysis(state)
```

#### 詳細な結果取得
```python
# 分析実行
results = engine.run_analysis(state)

# 結果の詳細確認
if "datasets" in results:
    for dataset in results["datasets"]:
        print(f"Dataset: {dataset.id}")
        print(f"Status: {dataset.status}")
        if hasattr(dataset, 'report_content') and dataset.report_content:
            print("Report: Generated")
        else:
            print("Report: Not generated")

# 処理サマリー
processing = results.get("get_processing_summary", {})
if processing:
    print(f"Total: {processing.get('total_datasets', 0)}")
    print(f"Completed: {processing.get('completed', 0)}")
    print(f"Failed: {processing.get('failed', 0)}")
```

### 入力データ形式

#### CSVファイル形式

##### 必須要件
- **エンコーディング**: UTF-8
- **形式**: 時系列データを含むフラット構造
- **ヘッダー**: 必須（1行目が列名）

##### アルゴリズム出力CSV
アルゴリズムの処理結果を含むCSVファイル：
```csv
frame,timestamp,detection_result,confidence
1,2024-01-01 00:00:00,0,0.85
2,2024-01-01 00:00:01,1,0.92
3,2024-01-01 00:00:02,0,0.78
```

##### コアライブラリ出力CSV
コアライブラリの生データを含むCSVファイル：
```csv
frame,timestamp,leye_openness,reye_openness,head_pose_x,head_pose_y
1,2024-01-01 00:00:00,0.85,0.87,15.2,-3.1
2,2024-01-01 00:00:01,0.82,0.89,14.8,-2.9
3,2024-01-01 00:00:02,0.20,0.18,16.1,-1.5
```

#### 期待値記述形式

自然言語で期待される動作を記述。以下の形式で具体的に記述してください：

##### 基本パターン
```
"フレーム区間100-200の間に値1（閉眼検知）が存在すること"
"タイムスタンプ0:10-0:30の間にleye_opennessが0.3未満になること"
```

##### 詳細な条件指定
```
"連続して5フレーム以上、leye_opennessとreye_opennessが両方とも0.2未満になる区間が存在すること"
"フレーム500-1000の間に、detection_resultが1となるフレームが全体の20%以上存在すること"
```

##### 複数条件の組み合わせ
```
"フレーム200-400の間に閉眼検知が発生し、かつフレーム600-800の間に回復パターンが確認できること"
```

### 実際の使用例

#### 例1: 単一データセットの閉眼検知分析
```bash
# 閉眼検知アルゴリズムの分析
uv run python run_analysis.py \
  --algorithm-outputs "_input/sample_data/アルゴリズム出力結果/2.csv" \
  --core-outputs "_input/sample_data/コアライブラリ出力結果/WIN_20250819_10_12_55_Pro_analysis.csv" \
  --algorithm-specs "_input/sample_data/algorithm/01_algorithm_specification/AS_drowsy_detection.md" \
  --algorithm-codes "_input/sample_data/algorithm/src/drowsy_detection/__init__.py" \
    "_input/sample_data/algorithm/src/drowsy_detection/drowsy_detector.py" \
  --evaluation-specs "_input/sample_data/evaluation_engine/docs/EVALUATION_SPEC.md" \
  --evaluation-codes "_input/sample_data/evaluation_engine/main.py" \
  --expected-results "フレーム区間465-593の間に「連続閉眼あり」が存在すること" \
  --dataset-ids "drowsy_detection_test"
```

#### 例2: 複数データセットの一括分析
```bash
# 複数のテストデータセットを一括分析
uv run python run_analysis.py \
  --algorithm-outputs \
    "_input/sample_data/アルゴリズム出力結果/2.csv" \
    "_input/sample_data/アルゴリズム出力結果/4.csv" \
  --core-outputs \
    "_input/sample_data/コアライブラリ出力結果/WIN_20250819_10_12_55_Pro_analysis.csv" \
    "_input/sample_data/コアライブラリ出力結果/WIN_20250819_10_16_17_Pro_analysis.csv" \
  --algorithm-specs \
    "_input/sample_data/algorithm/01_algorithm_specification/AS_drowsy_detection.md" \
    "_input/sample_data/algorithm/01_algorithm_specification/AS_drowsy_detection.md" \
  --algorithm-codes \
    "_input/sample_data/algorithm/src/drowsy_detection/__init__.py _input/sample_data/algorithm/src/drowsy_detection/drowsy_detector.py" \
    "_input/sample_data/algorithm/src/drowsy_detection/__init__.py _input/sample_data/algorithm/src/drowsy_detection/drowsy_detector.py" \
  --evaluation-specs \
    "_input/sample_data/evaluation_engine/docs/EVALUATION_SPEC.md" \
    "_input/sample_data/evaluation_engine/docs/EVALUATION_SPEC.md" \
  --evaluation-codes \
    "_input/sample_data/evaluation_engine/main.py" \
    "_input/sample_data/evaluation_engine/main.py" \
  --expected-results \
    "フレーム区間465-593の間に連続閉眼が検知されること" \
    "フレーム区間300-600の間に眠気状態が検知されること" \
  --dataset-ids \
    "dataset_1" \
    "dataset_2"
```

#### 例3: Python APIを使用した詳細制御
```python
from ai_analysis_engine import AIAnalysisEngine
import os

# 環境変数設定
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# エンジン初期化
engine = AIAnalysisEngine()

if not engine.initialize():
    print("❌ 初期化失敗")
    exit(1)

# カスタム分析設定
analysis_config = {
    "algorithm_outputs": ["data/custom_algo_output.csv"],
    "core_outputs": ["data/custom_core_output.csv"],
    "algorithm_specs": ["docs/custom_algo_spec.md"],
    "evaluation_specs": ["docs/custom_eval_spec.md"],
    "expected_results": [
        "フレーム100-500の間に異常値が検知され、"
        "フレーム600-1000の間に回復パターンが確認できること"
    ],
    "algorithm_codes": [["src/custom/algo.py", "src/custom/utils.py"]],
    "evaluation_codes": [["eval/custom/main.py"]],
    "dataset_ids": ["custom_analysis"]
}

# 分析実行
state = engine.create_analysis_request(**analysis_config)
results = engine.run_analysis(state)

# 結果確認
if "error" in results:
    print(f"❌ 分析失敗: {results['error']}")
else:
    print("✅ 分析完了")
    print(f"📄 レポート数: {len(results.get('datasets', []))}")

    # 各データセットの結果表示
    for dataset in results.get("datasets", []):
        print(f"\n📊 データセット: {dataset.id}")
        print(f"ステータス: {dataset.status}")
        if dataset.report_content:
            print("レポート: 生成済み")
        if dataset.error_message:
            print(f"エラー: {dataset.error_message}")
```

#### 例4: バッチ処理スクリプト
```python
#!/usr/bin/env python3
"""
バッチ分析スクリプト例
"""

from ai_analysis_engine import AIAnalysisEngine
from pathlib import Path
import glob

def batch_analyze(data_dir: str):
    """指定ディレクトリの全データセットを分析"""

    engine = AIAnalysisEngine()
    if not engine.initialize():
        return False

    # データファイルの探索
    algo_files = glob.glob(f"{data_dir}/**/algorithm_output*.csv", recursive=True)
    core_files = glob.glob(f"{data_dir}/**/core_output*.csv", recursive=True)
    spec_files = glob.glob(f"{data_dir}/**/spec*.md", recursive=True)

    if not (algo_files and core_files):
        print("❌ 必要なデータファイルが見つかりません")
        return False

    # 分析実行
    state = engine.create_analysis_request(
        algorithm_outputs=algo_files,
        core_outputs=core_files[:len(algo_files)],  # 対応する数のコアファイルを使用
        algorithm_specs=spec_files[:len(algo_files)] if spec_files else [spec_files[0]] * len(algo_files),
        evaluation_specs=spec_files[:len(algo_files)] if spec_files else [spec_files[0]] * len(algo_files),
        expected_results=[f"データセット{i+1}の期待される動作"] * len(algo_files),
        algorithm_codes=[[] for _ in range(len(algo_files))],  # 空のリスト（コードファイルがない場合）
        evaluation_codes=[[] for _ in range(len(algo_files))],  # 空のリスト（コードファイルがない場合）
        dataset_ids=[f"batch_dataset_{i+1}" for i in range(len(algo_files))]
    )

    results = engine.run_analysis(state)
    return "error" not in results

if __name__ == "__main__":
    success = batch_analyze("./data")
    print("✅ バッチ処理完了" if success else "❌ バッチ処理失敗")
```

## 🏗️ アーキテクチャ

### 全体構成
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Input Data    │───▶│  LangGraph      │───▶│   Analysis      │
│   (CSV + Spec)  │    │  Workflow       │    │   Results       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   AI Agents     │
                       │ - Supervisor    │
                       │ - Data Checker  │
                       │ - Consistency   │
                       │ - Hypothesis    │
                       │ - Verifier      │
                       │ - Reporter      │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Tools         │
                       │ - RAG Tool      │
                       │ - REPL Tool     │
                       └─────────────────┘
```

### ワークフロー
1. **初期化**: RAGベクトルストアの構築
2. **データチェック**: CSVデータの品質分析
3. **整合性チェック**: 仕様書との整合性検証
4. **仮説生成**: AIによる問題原因の推定
5. **検証**: Pythonコード実行による仮説検証
6. **レポート**: 分析結果のMarkdownレポート生成

### コンポーネント詳細

#### RAG Tool
- **機能**: 仕様書のベクトル化と意味検索
- **技術**: FAISS + OpenAI Embeddings
- **セグメント化**: アルゴリズム・エンジン別ベクトルストア

#### REPL Tool
- **機能**: Pythonコード実行とデータ処理
- **技術**: pandas + matplotlib + seaborn
- **用途**: データ分析、プロット生成、仮説検証

## 📊 テスト

### テスト実行
```bash
# 全テスト実行
uv run python test_engine.py

# 特定のデータセットでテスト
uv run python -c "
from ai_analysis_engine import AIAnalysisEngine
engine = AIAnalysisEngine()
engine.initialize()
# テストコード
"
```

### テストデータ
プロジェクトには以下のテストデータが含まれています：
- `_input/sample_data/algorithm/` - アルゴリズム仕様書
- `_input/sample_data/evaluation_engine/` - 評価環境仕様
- `_input/sample_data/アルゴリズム出力結果/` - アルゴリズム出力CSV
- `_input/sample_data/コアライブラリ出力結果/` - コアライブラリ出力CSV

## 📁 プロジェクト構造

```
ai-analysis-engine/
├── src/ai_analysis_engine/
│   ├── __init__.py          # パッケージ初期化
│   ├── main.py              # メインアプリケーション
│   ├── config/              # 設定管理
│   │   ├── __init__.py
│   │   └── config.py        # 設定クラス
│   ├── models/              # データモデル
│   │   ├── __init__.py
│   │   ├── state.py         # LangGraph状態モデル
│   │   └── types.py         # 型定義
│   ├── core/                # LangGraphワークフロー
│   │   ├── __init__.py
│   │   ├── graph.py         # メイングラフ
│   │   └── nodes.py         # ワークフロー各ノード
│   ├── agents/              # AIエージェント
│   │   ├── __init__.py
│   │   ├── supervisor_agent.py
│   │   ├── data_checker_agent.py
│   │   ├── consistency_checker_agent.py
│   │   ├── hypothesis_generator_agent.py
│   │   ├── verifier_agent.py
│   │   └── reporter_agent.py
│   ├── tools/               # ユーティリティツール
│   │   ├── __init__.py
│   │   ├── rag_tool.py      # RAG検索ツール
│   │   └── repl_tool.py     # Python実行ツール
│   └── utils/               # ユーティリティ関数
│       ├── __init__.py
│       ├── logger.py        # ログ管理
│       ├── file_utils.py    # ファイル操作
│       └── text_utils.py    # テキスト処理
├── tests/                   # テストファイル
├── docs/                    # ドキュメント
├── output/                  # 出力結果
├── logs/                    # ログファイル
├── pyproject.toml           # プロジェクト設定
├── test_engine.py           # テスト実行スクリプト
├── run_analysis.py          # 実行スクリプト
└── README.md               # このファイル
```

## 🔧 設定

### 環境変数

#### 必須環境変数
```bash
# OpenAI APIキー（必須）
export OPENAI_API_KEY="your-openai-api-key-here"
```

#### オプション環境変数
```bash
# OpenAI API設定
export OPENAI_MODEL="gpt-4o-mini"          # 使用するモデル
export OPENAI_TEMPERATURE="0.1"           # 生成温度（0.0-1.0、低いほど決定論的）
export OPENAI_MAX_TOKENS="4000"           # 最大トークン数

# システム設定
export LOG_LEVEL="INFO"                   # ログレベル (DEBUG, INFO, WARNING, ERROR)
export DATA_DIR="./data"                  # データディレクトリ
export OUTPUT_DIR="./output"              # 出力ディレクトリ
export LOGS_DIR="./logs"                  # ログディレクトリ

# ベクトルストア設定
export VECTORSTORE_DIR="./data/vectorstore"  # ベクトルストア保存先
export VECTORSTORE_CHUNK_SIZE="1000"         # チャンクサイズ
export VECTORSTORE_CHUNK_OVERLAP="200"       # チャンク重複サイズ

# REPL実行環境設定
export REPL_TIMEOUT="30"                     # 実行タイムアウト（秒）
export REPL_MAX_OUTPUT_LENGTH="5000"         # 最大出力文字数
```

### 設定ファイル詳細

`src/ai_analysis_engine/config/config.py` で以下の設定が可能です：

#### OpenAI設定
```python
openai = OpenAIConfig(
    api_key="your-api-key",           # APIキー
    model="gpt-4o-mini",              # モデル名
    temperature=0.1,                  # 生成温度
    max_tokens=4000                   # 最大トークン数
)
```

#### ベクトルストア設定
```python
vectorstore = VectorStoreConfig(
    persist_directory="./data/vectorstore",  # 保存先ディレクトリ
    chunk_size=1000,                         # チャンクサイズ
    chunk_overlap=200                        # 重複サイズ
)
```

#### REPLツール設定
```python
repl = REPLConfig(
    timeout=30,                              # タイムアウト（秒）
    max_output_length=5000,                  # 最大出力長
    allowed_modules=[                        # 許可モジュール
        "pandas", "numpy", "matplotlib",
        "seaborn", "scipy"
    ]
)
```

#### LangGraphワークフロー設定
```python
langgraph = LangGraphConfig(
    max_iterations=10,                       # 最大反復回数
    checkpoint_path="./data/checkpoints"     # チェックポイント保存先
)
```

### 設定の優先順位

1. **環境変数**（最高優先度）
2. **設定ファイル**（デフォルト値）
3. **ハードコーディングされたデフォルト値**（最低優先度）

### 高度な設定例

#### カスタム設定ファイルの使用
```python
from ai_analysis_engine.config import Config

# カスタム設定の作成
custom_config = Config()
custom_config.openai.model = "gpt-4"  # 高精度モデルを使用
custom_config.openai.temperature = 0.0  # 完全に決定論的に
custom_config.vectorstore.chunk_size = 500  # 小さなチャンクに分割

# エンジン初期化時に設定を適用
engine = AIAnalysisEngine()
engine.config = custom_config  # カスタム設定を適用
```

#### 環境別の設定
```bash
# 開発環境
export OPENAI_MODEL="gpt-4o-mini"
export LOG_LEVEL="DEBUG"
export REPL_TIMEOUT="60"

# 本番環境
export OPENAI_MODEL="gpt-4"
export LOG_LEVEL="WARNING"
export REPL_TIMEOUT="30"
```

### 設定の検証

エンジン初期化時に設定が自動的に検証されます：

```python
engine = AIAnalysisEngine()

if not engine.initialize():
    print("❌ 初期化失敗 - 設定を確認してください")
    exit(1)

# 現在の設定状態を確認
status = engine.get_status()
print(f"設定有効: {status['config_valid']}")
print(f"APIキー設定: {'✅' if status['config_valid'] else '❌'}")
```

## 📊 出力結果

### 出力ディレクトリ構造

分析実行後、以下のディレクトリ構造で結果が出力されます：

```
output/
├── results/
│   ├── analysis_results.json          # メイン分析結果（JSON）
│   ├── error_summary.json             # エラーサマリー（エラー発生時）
│   └── reports/
│       ├── dataset_1_report.md        # 個別データセットレポート
│       ├── dataset_2_report.md        # 個別データセットレポート
│       └── ...
├── plots/
│   └── dataset_1/
│       ├── 2_timeseries.png           # 時系列グラフ
│       └── WIN_20250819_10_12_55_Pro_analysis_timeseries.png
└── ...
```

### レポート内容

#### Markdownレポート（dataset_X_report.md）

各データセットごとに以下の構造のレポートが生成されます：

```markdown
# 個別データ分析レポート - [データセットID]

## 概要
- 結論: [AIによる分析結論]
- 解析対象動画: [データセットID]
- フレーム区間: [分析対象区間]
- 期待値: [期待される動作]
- 検知結果: [実際の検知結果]

## 確認結果
[分析グラフの埋め込み]

## 推奨事項
[改善提案や次のアクション]

## 参照した仕様/コード（抜粋）
[関連仕様書の参照内容]
```

#### JSON結果（analysis_results.json）

プログラム的な処理向けの構造化データ：

```json
{
  "datasets": [
    {
      "id": "dataset_1",
      "status": "completed",
      "algorithm_output_csv": "path/to/algo.csv",
      "core_output_csv": "path/to/core.csv",
      "expected_result": "期待される動作記述",
      "data_summary": {
        "row_count": 1349,
        "columns": ["frame", "timestamp", "value"],
        "data_types": {"frame": "int64", "value": "float64"}
      },
      "consistency_check": {
        "status": "passed",
        "issues": []
      },
      "hypotheses": [
        {
          "hypothesis": "被験者が閉眼していない可能性",
          "confidence": 0.85,
          "evidence": "leye_openness平均値が0.8以上"
        }
      ],
      "verification_results": [
        {
          "code": "df['value'].mean()",
          "result": "0.234",
          "success": true
        }
      ],
      "report_content": "# レポート内容...",
      "error_message": null
    }
  ],
  "start_time": "2024-01-01T10:00:00",
  "end_time": "2024-01-01T10:02:30",
  "get_processing_summary": {
    "total_datasets": 2,
    "completed": 2,
    "failed": 0,
    "in_progress": 0,
    "current_index": 2
  }
}
```

### グラフ出力

#### 時系列グラフ
- **アルゴリズム出力グラフ**: 検知結果の時系列推移
- **コアライブラリ出力グラフ**: 生データの時系列推移
- **ファイル名形式**: `{original_filename}_timeseries.png`
- **対象列**: 自動検知された数値列
- **グラフ種類**: 折れ線グラフ（matplotlib/seaborn使用）

### 出力結果の活用例

#### Pythonでの結果処理
```python
import json
from pathlib import Path

# 結果ファイルの読み込み
with open("output/results/analysis_results.json", "r", encoding="utf-8") as f:
    results = json.load(f)

# 各データセットの処理
for dataset in results["datasets"]:
    print(f"データセット: {dataset['id']}")
    print(f"ステータス: {dataset['status']}")

    if dataset["status"] == "completed":
        # レポートファイルの存在確認
        report_path = Path(f"output/results/reports/{dataset['id']}_report.md")
        if report_path.exists():
            print(f"レポート: {report_path}")

        # データサマリーの表示
        if "data_summary" in dataset:
            summary = dataset["data_summary"]
            print(f"データ行数: {summary['row_count']}")
            print(f"列数: {len(summary['columns'])}")

# 処理サマリーの表示
if "get_processing_summary" in results:
    summary = results["get_processing_summary"]
    print(f"\n処理完了: {summary['completed']}/{summary['total_datasets']}")
```

#### レポートの一括処理
```python
import glob
from pathlib import Path

# 全レポートファイルの取得
report_files = glob.glob("output/results/reports/*_report.md")

for report_file in report_files:
    dataset_id = Path(report_file).stem.replace("_report", "")

    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"=== {dataset_id} のレポート ===")
    # レポート内容の処理
    lines = content.split("\n")
    for line in lines[:10]:  # 最初の10行を表示
        print(line)
    print("...")
```

## 📈 パフォーマンス

### 処理時間目安
- **小規模データ** (1,000行): 30-60秒
- **中規模データ** (10,000行): 2-5分
- **大規模データ** (100,000行): 10-30分

### メモリ使用量
- **基本使用量**: 500MB
- **データ処理時**: 1-2GB (データサイズによる)

### パフォーマンス最適化

#### 大規模データの処理
```bash
# メモリ使用量を抑える設定
export REPL_MAX_OUTPUT_LENGTH="2000"
export VECTORSTORE_CHUNK_SIZE="500"
export LOG_LEVEL="WARNING"
```

#### 並列処理の推奨
```python
# 複数データセットを個別に処理
datasets = ["dataset1", "dataset2", "dataset3"]

for dataset in datasets:
    # 個別処理（並列実行可能）
    process_single_dataset(dataset)
```

## 🐛 トラブルシューティング

### 診断ツール

#### システム状態の確認
```python
from ai_analysis_engine import AIAnalysisEngine

engine = AIAnalysisEngine()
status = engine.get_status()

print("=== システム診断 ===")
print(f"初期化済み: {status['initialized']}")
print(f"設定有効: {status['config_valid']}")
print(f"データディレクトリ: {status['data_dir']}")
print(f"出力ディレクトリ: {status['output_dir']}")
print(f"ログディレクトリ: {status['logs_dir']}")
```

#### 設定検証
```bash
# 環境変数の確認
echo "OpenAI API Key: ${OPENAI_API_KEY:+設定済み}"
echo "Python version: $(python --version)"
echo "uv version: $(uv --version)"

# 依存関係の確認
uv sync --dry-run
```

### よくある問題と解決方法

#### 1. OpenAI API関連エラー

**APIキー未設定**
```
Error: OpenAI API key not found
```
**解決方法**:
```bash
# 環境変数設定
export OPENAI_API_KEY="your-api-key-here"

# または .env ファイル作成
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

**APIレート制限**
```
Error: Rate limit exceeded
```
**解決方法**:
- API使用量を確認
- モデルを変更（gpt-4 → gpt-4o-mini）
- リクエスト間隔を空ける

**API接続エラー**
```
Error: Connection failed
```
**解決方法**:
- ネットワーク接続を確認
- プロキシ設定を確認
- APIエンドポイントの可用性を確認

#### 2. データ処理エラー

**CSVファイル形式エラー**
```
Error: Invalid CSV format
```
**解決方法**:
- UTF-8エンコーディングを確認
- ヘッダー行の存在を確認
- 区切り文字が正しいか確認（カンマ区切り）

**メモリ不足**
```
Error: Out of memory
```
**解決方法**:
```bash
# 設定調整
export REPL_MAX_OUTPUT_LENGTH="2000"
export VECTORSTORE_CHUNK_SIZE="500"

# 大規模データを分割処理
split -l 50000 large_file.csv part_
```

**データ型エラー**
```
Error: Column 'value' contains invalid data
```
**解決方法**:
- CSVファイルのデータ型を確認
- 欠損値（NaN, null）を適切に処理
- 数値列に文字列が混在していないか確認

#### 3. 依存関係エラー

**モジュール未インストール**
```
Error: Module not found: pandas
```
**解決方法**:
```bash
# uvを使用する場合
uv sync --reinstall

# pipを使用する場合
pip install -e . --force-reinstall
```

**バージョン競合**
```
Error: Version conflict in dependencies
```
**解決方法**:
```bash
# 仮想環境再作成
uv venv --python 3.10
source .venv/bin/activate
uv sync
```

#### 4. ベクトルストアエラー

**ベクトルストア初期化失敗**
```
Error: Vector store initialization failed
```
**解決方法**:
```bash
# ベクトルストアディレクトリ削除
rm -rf data/vectorstore/

# 再初期化
python -c "from ai_analysis_engine import AIAnalysisEngine; AIAnalysisEngine().initialize()"
```

**FAISSインデックス破損**
```
Error: FAISS index corrupted
```
**解決方法**:
- ベクトルストアディレクトリを削除して再構築
- メモリ使用量を減らす設定に調整

#### 5. LangGraphワークフローエラー

**ワークフロー停止**
```
Error: Workflow execution timeout
```
**解決方法**:
```bash
# タイムアウト設定延長
export REPL_TIMEOUT="60"
```

**ノード実行エラー**
```
Error: Node execution failed
```
**解決方法**:
- ログファイルを確認
- エラーが発生したノードを特定
- 該当ノードの入力を確認

### ログの確認とデバッグ

#### ログファイルの場所
```bash
# メインログ
tail -f logs/ai_analysis_engine.log

# 詳細ログ確認
tail -n 100 logs/ai_analysis_engine.log | grep ERROR
```

#### デバッグモードでの実行
```bash
# 詳細ログ出力
export LOG_LEVEL="DEBUG"
uv run python test_engine.py

# 特定のコンポーネントのログ確認
tail -f logs/ai_analysis_engine.log | grep "DataChecker"
```

#### ワークフロー状態の確認
```python
# ワークフロー実行中の状態確認
from ai_analysis_engine.core.graph import AnalysisGraph
from ai_analysis_engine.models.state import AnalysisState

graph = AnalysisGraph()
# 状態確認用のメソッドを使用
```

### パフォーマンス問題の解決

#### 処理速度が遅い場合
```bash
# 設定最適化
export OPENAI_MODEL="gpt-4o-mini"  # 高速モデル使用
export VECTORSTORE_CHUNK_SIZE="500"  # 小さなチャンク
export LOG_LEVEL="WARNING"  # ログ出力を減らす
```

#### メモリ使用量が多い場合
```bash
# メモリ最適化設定
export REPL_MAX_OUTPUT_LENGTH="1000"
export VECTORSTORE_CHUNK_OVERLAP="100"
```

### 高度なトラブルシューティング

#### 特定のエラーパターンの調査
```python
# エラーパターン分析
import json
with open("output/results/error_summary.json", "r") as f:
    errors = json.load(f)

for error in errors.get("errors", []):
    print(f"Error: {error}")
```

#### ベクトルストアの健全性チェック
```python
# ベクトルストア状態確認
from ai_analysis_engine.tools.rag_tool import RAGTool

rag_tool = RAGTool()
status = rag_tool.check_vectorstore_health()
print(f"VectorStore health: {status}")
```

#### ネットワーク診断
```bash
# OpenAI API接続テスト
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# DNS解決確認
nslookup api.openai.com
```

### サポート情報

#### ログファイルの提供
問題解決のために以下の情報を準備してください：
- `logs/ai_analysis_engine.log` の関連部分
- `output/results/error_summary.json`
- 使用したコマンドと完全なエラーメッセージ
- システム情報（OS, Pythonバージョン）

#### コミュニティサポート
- Issue作成時は以下の情報を含めてください：
  - エラーメッセージ全文
  - 使用したコマンド
  - 環境情報
  - 再現手順

### 緊急時の対応

#### 分析が停止した場合
1. プロセス確認: `ps aux | grep python`
2. プロセス強制終了: `kill -9 <PID>`
3. 一時ファイル削除: `rm -rf data/checkpoints/*`
4. 再実行

#### データ破損が疑われる場合
1. 出力ディレクトリバックアップ
2. ベクトルストア再構築
3. 小規模データでのテスト実行
4. 段階的なデータ投入

## 🤝 貢献

### 開発環境のセットアップ
```bash
# 開発用依存関係のインストール
uv sync --dev

# テスト実行
uv run pytest

# コードフォーマット
uv run black src/
uv run isort src/
```

### 貢献の流れ
1. Issueを作成または既存のIssueを確認
2. ブランチを作成: `git checkout -b feature/new-feature`
3. 変更を実装
4. テストを追加・実行
5. Pull Requestを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 📞 サポート

### ドキュメント
- [システム仕様書](docs/system_design.md)
- [詳細設計書](docs/detailed_design.md)

### 連絡先
- Issue: [GitHub Issues](https://github.com/your-repo/issues)
- メール: your-email@example.com

---

**AI Analysis Engine** - 時系列データ分析の自動化を革新する
