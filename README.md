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

### 基本的な使用例

#### 1. テスト実行
```bash
# 付属のテストデータで動作確認
uv run python test_engine.py
```

#### 2. コマンドライン実行
```bash
# 基本的な分析実行
uv run python run_analysis.py \
  --algorithm-outputs data/algo_output.csv \
  --core-outputs data/core_output.csv \
  --evaluation-specs docs/eval_spec.md \
  --expected-results "フレーム100-200の間に値1が存在すること"
```

#### 3. Python API使用
```python
from ai_analysis_engine import AIAnalysisEngine

# エンジン初期化
engine = AIAnalysisEngine()
engine.initialize()

# 分析リクエスト作成
state = engine.create_analysis_request(
    algorithm_outputs=["data/algo_output.csv"],
    core_outputs=["data/core_output.csv"],
    evaluation_specs=["docs/eval_spec.md"],
    expected_results=["期待される動作の自然言語記述"],
    dataset_ids=["dataset_1"]
)

# 分析実行
results = engine.run_analysis(state)
print("Analysis completed!")
```

### 入力データ形式

#### CSVファイル
- **エンコーディング**: UTF-8
- **形式**: 時系列データを含むフラット構造
- **例**:
```csv
timestamp,value,confidence
2024-01-01 00:00:00,0.85,0.92
2024-01-01 00:00:01,0.87,0.89
```

#### 期待値記述
自然言語で期待される動作を記述：
```
"フレーム100-200の間に列'value'に1が存在すること"
"タイムスタンプ0-10秒の間に検知値が0.8を超えること"
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
```bash
# OpenAI API設定
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# システム設定（オプション）
LOG_LEVEL=INFO
DATA_DIR=./data
OUTPUT_DIR=./output
```

### 設定ファイル
`src/ai_analysis_engine/config/config.py` で以下の設定が可能です：
- OpenAI API設定
- ベクトルストア設定
- REPL実行環境設定
- LangGraphワークフロー設定

## 📈 パフォーマンス

### 処理時間目安
- **小規模データ** (1,000行): 30-60秒
- **中規模データ** (10,000行): 2-5分
- **大規模データ** (100,000行): 10-30分

### メモリ使用量
- **基本使用量**: 500MB
- **データ処理時**: 1-2GB (データサイズによる)

## 🐛 トラブルシューティング

### よくある問題

#### 1. OpenAI APIエラー
```
Error: OpenAI API key not found
```
**解決方法**: 環境変数 `OPENAI_API_KEY` を設定してください。

#### 2. メモリ不足
```
Error: Out of memory
```
**解決方法**: 大きなデータを分割して処理するか、システムメモリを増設してください。

#### 3. 依存関係エラー
```
Error: Module not found
```
**解決方法**:
```bash
# uvを使用する場合
uv sync --reinstall

# pipを使用する場合
pip install -e . --force-reinstall
```

### ログの確認
```bash
# ログファイルの場所
tail -f logs/ai_analysis_engine.log
```

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
