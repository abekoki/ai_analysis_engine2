# 連続閉眼検知アルゴリズム (Drowsy Detection Algorithm)

## 概要

本プロジェクトは、左右の目の開眼度情報から連続閉眼状態を検知するアルゴリズムを実装したものです。ドライバーや作業者の眠気・注意力低下を早期に検知し、安全性向上を目的としています。

## 主な特徴

- **リアルタイム処理**: 60 fps まで対応可能な軽量アルゴリズム
- **高精度検知**: 顔検出信頼度を組み合わせた誤検知低減
- **モジュール化**: Python 実装を基準とし、C++ への移植を考慮した設計
- **組込み対応**: CPU ベース（組込み SoC 含む）、GPU 不要

## 技術仕様

### 入力
- フレーム番号 (int)
- 左目の開眼度 (float, 0.0〜1.0)
- 右目の開眼度 (float, 0.0〜1.0)
- 顔検出信頼度 (float, 0.0〜1.0)

### 出力
- 連続閉眼状態フラグ (int)
  - `1`: 連続閉眼状態
  - `0`: 非連続閉眼状態
  - `-1`: エラー

### パラメータ
- 左目閉眼閾値: 0.30 (デフォルト)
- 右目閉眼閾値: 0.30 (デフォルト)
- 連続閉眼時間: 1.00秒 (デフォルト)
- 顔検出信頼度閾値: 0.70 (デフォルト)

## 詳細仕様

詳細な仕様については以下をご参照ください：
- [連続閉眼検知アルゴリズム仕様書](./01_algorithm_specification/AS_drowsy_detection.md)

## 開発環境

- 言語: Python 3.10+
- 主要ライブラリ: numpy, pydantic
- パッケージ構成: src レイアウト (`src/drowsy_detection`)

### インストール

```bash
# リポジトリ直からインストール（タグ例: v0.1.0）
pip install git+https://github.com/abekoki/drowsy_detection.git@v0.1.0

# 開発（ローカル）
uv pip install -e .
uv pip install -e .[dev]
```

### CLI

```bash
# 入力データを処理
drowsy-detect --input path/to/data.json --output result.json

# サンプル生成
drowsy-detect --create-sample-config config.json
drowsy-detect --create-sample-input input.json --frames 100
```

## プロジェクト構成

```
drowsy_detection/
├── 00_requirements/
├── 01_algorithm_specification/
├── 02_specific_design/
├── 03_source/                   # 旧構成（残置）
├── src/
│   └── drowsy_detection/
│       ├── cli/
│       ├── config/
│       ├── core/
│       └── utils/
├── examples/
├── tests/
├── README.md
├── pyproject.toml
└── log.md
```

## ライセンス

MIT License（`LICENSE`を参照）

## 貢献

[貢献方法を記載予定]

---

**注意**: 本プロジェクトは開発中です。詳細な実装や使用方法については、仕様書をご確認ください。
