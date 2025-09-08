# 連続閉眼検知アルゴリズムのパッケージ化指示書

## 1. 目的
`abekoki/drowsy_detection` リポジトリをPythonパッケージとして公開・配布可能な形式に整備し、評価モジュールから依存として利用できるようにする。この指示書では、パッケージ化の具体的な手順と注意点を明確にし、開発担当者に実装を依頼する。

## 2. 背景
現在のリポジトリ構造はモジュール化が進んでいるが（`03_source/`配下に`__init__.py`や`pyproject.toml`が存在）、`pip install`で直接インストール可能なPythonパッケージとしては未整備。評価モジュールから最新のアルゴリズムをクローンする案はGit管理上非推奨（ネストされたリポジトリ問題や再現性喪失リスク）。パッケージ化により、依存管理を簡潔にし、評価モジュールの開発効率と再現性を向上させる。

## 3. パッケージ化の要件
- **目標**: `pip install git+https://github.com/abekoki/drowsy_detection.git@<tag>` でインストール可能。
- **互換性**: Python 3.10以上（`.python-version`準拠）。
- **依存**: numpy, pydantic, opencv-python（仕様書に基づく）。開発用にpytest等。
- **テスト**: 既存テスト（`tests/`）を維持し、カバレッジ100%を目指す。
- **ドキュメント**: README.mdにインストール・使用例を明記。APIドキュメント生成推奨。

## 4. 指示内容
以下の手順を担当者は実行してください。作業はGitHub上でブランチ（例: `feature/package`)を作成し、プルリクエストでレビューを経てマージ。

### 4.1 パッケージ構造の整理
- **タスク**: ソースコードを `src/drowsy_detection/` に移行し、標準的なPythonパッケージ構造に。
  - 現在の `03_source/` を `src/drowsy_detection/` にリネーム。
  - インポートパスを修正（例: `from source.core...` → `from drowsy_detection.core...`）。
  - 不要ファイル（`__pycache__`, `log.md`）は削除または`.gitignore`確認。
- **注意**: テスト（`tests/`）や例（`examples/`）のインポートも更新。`__init__.py`で公開API（例: `DrowsyDetector`）をエクスポート。

### 4.2 pyproject.tomlの整備
- **タスク**: `pyproject.toml` を以下のように更新し、ビルド・依存管理を明確化。
  ```toml
  [build-system]
  requires = ["setuptools >= 61.0", "wheel"]
  build-backend = "setuptools.build_meta"

  [project]
  name = "drowsy-detection"
  version = "0.1.0"  # 初回リリース用。git tagで管理
  description = "Continuous Eye Closure Detection Algorithm"
  authors = [{ name = "abekoki", email = "your@email.com" }]
  license = { text = "MIT" }  # ライセンス未定なら要相談
  requires-python = ">=3.10"
  dependencies = [
    "numpy>=1.20",
    "pydantic>=2.0",
    "opencv-python>=4.5",
  ]

  [project.optional-dependencies]
  dev = ["pytest", "pytest-cov", "black"]

  [project.entry-points.console_scripts]
  drowsy-detect = "drowsy_detection.cli.main:main"
  ```
- **注意**:
  - 依存バージョンを仕様書（numpy, pydantic, opencv-python）と一致させる。
  - `MANIFEST.in`で不要ファイル除外（例: `exclude __pycache__/*`）。
  - バージョンは動的に（`[tool.setuptools.dynamic]`でgit tagから）設定推奨。

### 4.3 ビルドとテスト
- **タスク**:
  1. ローカルで `pip install -e .` し、動作確認。
  2. 既存テスト（`pytest tests/`）を実行し、NaNやエッジケース（AS_drowsy_detection.mdの3.4節）をカバー。
- **注意**:
  - `uv.lock`を活用し、依存バージョンを固定。
  - カバレッジレポート生成（`pytest --cov`）で100%を目指す。
  - GitHub ActionsでCI設定（push時にテスト実行）。

### 4.4 ドキュメント更新
- **タスク**:
  - `README.md`に以下を追加:
    - インストール手順（例: `pip install git+https://github.com/abekoki/drowsy_detection.git@v0.1.0`）。
    - 基本使用例（`examples/basic_usage.py`から引用）。
    - AS_drowsy_detection.mdへのリンク。
  - Sphinx/mkdocsでAPIドキュメント生成（`docs/`に）。
- **注意**: 公開APIを明確に（例: `DrowsyDetector`のみエクスポート）。

### 4.5 セキュリティと最適化
- **タスク**:
  - Pydanticで入力検証強化（`config/validators.py`の既存実装確認）。
  - 依存の脆弱性チェック（`pip install safety; safety check`）。
  - opencv-python-headless検討（軽量化のため）。
- **注意**: 擬似コードの`dt=1/30`固定（core/drowsy_detector.py）を可変フレームレート対応に（例: `set_frame_rate`活用）。

### 4.6 リリース準備
- **タスク**:
  - Gitタグ作成（`git tag v0.1.0; git push --tags`）。
  - GitHub Releasesにwheelアップロード。
  - 評価モジュール向けに依存指定例を提供（`requirements.txt`に`drowsy-detection==0.1.0`）。
- **注意**: Semantic Versioning採用。変更履歴は`CHANGELOG.md`に。

## 5. 注意点
- **互換性**: Python 3.10+、C++移植（AS_drowsy_detection.md 1.3節）を考慮し、シンプルな実装を維持。
- **エラーハンドリング**: NaN補完やエラーコード（SD_drowsy_detection_python.md 6.1節）を厳格に。
- **パフォーマンス**: 30fps以上（SD_drowsy_detection_python.md 5.1節）を確保。プロファイリング（`cProfile`）で検証。
- **CI/CD**: GitHub Actionsでテスト自動化（例: `.github/workflows/test.yml`）。
- **依存管理**: `uv.lock`で一貫性確保。依存バージョンの衝突に注意。

