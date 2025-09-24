#!/usr/bin/env python3
"""
AI分析エンジンを独立したパッケージとして設定するスクリプト
"""

import shutil
import os
from pathlib import Path

def setup_as_independent_package(target_path: str):
    """
    ライブラリを独立したパッケージとして設定

    Args:
        target_path: パッケージを作成するディレクトリ
    """

    target_dir = Path(target_path)

    # 1. ディレクトリ構造を作成
    target_dir.mkdir(parents=True, exist_ok=True)

    # 2. ライブラリファイルをコピー
    source_lib = Path(__file__).parent.parent / "src" / "ai_analysis_engine"
    target_lib = target_dir / "ai_analysis_engine"

    def ignore_pycache(dir, files):
        return [f for f in files if f == '__pycache__']

    print(f"📁 ライブラリをコピー: {source_lib} -> {target_lib}")
    shutil.copytree(source_lib, target_lib, ignore=ignore_pycache)

    # 2.5. docsフォルダをinstant_analysisフォルダーにコピー
    source_docs = Path(__file__).parent.parent / "docs"
    if source_docs.exists():
        target_docs = target_dir / "instant_analysis"
        print(f"📁 ドキュメントをコピー: {source_docs} -> {target_docs}")
        shutil.copytree(source_docs, target_docs, ignore=ignore_pycache)
    else:
        print("⚠️  docsフォルダが見つからないためスキップ")

    # 3. pyproject.tomlを作成
    pyproject_content = '''[project]
name = "ai-analysis-engine"
version = "1.0.0"
description = "汎用AI分析エンジンライブラリ"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "langgraph>=0.1.0",
    "langchain>=0.2.0",
    "langchain-openai",
    "langchain-community",
    "faiss-cpu",
    "pandas",
    "matplotlib",
    "seaborn",
    "openai",
    "python-dotenv",
    "tiktoken",
    "pydantic>=2.0.0",
    "typing-extensions",
    "pyyaml>=6.0.2",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.setuptools.packages.find]
where = ["."]
include = ["ai_analysis_engine*"]
'''

    pyproject_file = target_dir / "pyproject.toml"
    pyproject_file.write_text(pyproject_content)
    print(f"✅ pyproject.toml作成: {pyproject_file}")

    # 4. README.mdを作成
    readme_content = '''# AI分析エンジンライブラリ

汎用AI分析エンジン - 時系列データ分析の自動化プラットフォーム

## インストール

```bash
pip install -e .
```

## 使用方法

```python
from ai_analysis_engine import AIAnalysisEngine

engine = AIAnalysisEngine()
engine.initialize()

result = engine.analyze(
    algorithm_output="data/algo.csv",
    core_output="data/core.csv",
    algorithm_spec="docs/spec.md",
    expected_result="期待される動作"
)
```
'''

    readme_file = target_dir / "README.md"
    readme_file.write_text(readme_content)
    print(f"✅ README.md作成: {readme_file}")

    # 5. 使用例ファイルを作成
    example_file = target_dir / "example.py"
    example_content = '''#!/usr/bin/env python3
"""使用例"""

import os
from ai_analysis_engine import AIAnalysisEngine

# APIキー設定
os.environ["OPENAI_API_KEY"] = "your-api-key"

# エンジン初期化
engine = AIAnalysisEngine()
engine.initialize()

# 分析実行
result = engine.analyze(
    algorithm_output="data/algorithm_output.csv",
    core_output="data/core_output.csv",
    algorithm_spec="docs/algorithm_spec.md",
    expected_result="フレーム100-200の間に検知結果が存在すること"
)

print(f"分析結果: {'成功' if result.success else '失敗'}")
'''

    example_file.write_text(example_content)
    print(f"✅ 使用例作成: {example_file}")

    return True

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python setup_as_package.py <target_directory>")
        print("例: python setup_as_package.py ../ai_analysis_package")
        sys.exit(1)

    target_path = sys.argv[1]
    if setup_as_independent_package(target_path):
        print("🎉 パッケージ作成完了!" )
        print(f"📁 パッケージディレクトリ: {target_path}")
        print("📝 次に行うこと:")
        print("   1. cd {target_path}")
        print("   2. pip install -e .")
        print("   3. python example.py")
    else:
        print("❌ パッケージ作成失敗")
        sys.exit(1)
