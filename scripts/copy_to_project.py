#!/usr/bin/env python3
"""
AI分析エンジンライブラリを他のプロジェクトにコピーするスクリプト
"""

import shutil
import os
from pathlib import Path

def copy_library_to_project(target_project_path: str, library_name: str = "ai_analysis_engine"):
    """
    ライブラリを他のプロジェクトにコピー

    Args:
        target_project_path: コピー先プロジェクトのパス
        library_name: ライブラリ名（デフォルト: ai_analysis_engine）
    """

    source_path = Path(__file__).parent.parent / "src" / "ai_analysis_engine"
    target_path = Path(target_project_path) / library_name

    print(f"📁 ライブラリをコピーします...")
    print(f"   コピー元: {source_path}")
    print(f"   コピー先: {target_path}")

    # 対象ディレクトリが存在するか確認
    if not source_path.exists():
        print(f"❌ コピー元ディレクトリが見つかりません: {source_path}")
        return False

    # コピー先の親ディレクトリを作成
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # 既存のディレクトリがある場合は削除
    if target_path.exists():
        print(f"⚠️  既存のディレクトリを削除: {target_path}")
        shutil.rmtree(target_path)

    # ライブラリをコピー（__pycache__は除外）
    def ignore_pycache(dir, files):
        return [f for f in files if f == '__pycache__']

    shutil.copytree(source_path, target_path, ignore=ignore_pycache)

    print("✅ ライブラリコピー完了")
    print(f"   コピーしたファイル数: {len(list(target_path.rglob('*.py')))}")

    # __init__.pyファイルを作成してプロジェクト内でインポート可能にする
    init_file = Path(target_project_path) / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# AI Analysis Engine Library\n")

    return True

def create_usage_example(target_project_path: str):
    """使用例ファイルを作成"""
    example_file = Path(target_project_path) / "example_usage.py"

    example_code = '''#!/usr/bin/env python3
"""
AI分析エンジンの使用例
"""

import os
from ai_analysis_engine import AIAnalysisEngine, AnalysisConfig

def main():
    """メイン処理"""

    # 1. APIキーを設定
    os.environ["OPENAI_API_KEY"] = "your-api-key-here"

    # 2. 設定を作成
    config = AnalysisConfig(
        model="gpt-4o-mini",
        timeout=300
    )

    # 3. エンジンを初期化
    engine = AIAnalysisEngine(config)
    if not engine.initialize():
        print("❌ 初期化失敗")
        return

    print("✅ AI分析エンジン初期化完了")

    # 4. 分析を実行
    result = engine.analyze(
        algorithm_output="data/algorithm_output.csv",
        core_output="data/core_output.csv",
        algorithm_spec="docs/algorithm_spec.md",
        expected_result="フレーム100-200の間に検知結果が存在すること"
    )

    # 5. 結果を確認
    if result.success:
        print("✅ 分析成功!")
        print(f"レポート: {result.report[:200]}...")
        print(f"生成された仮説数: {len(result.hypotheses)}")
    else:
        print(f"❌ 分析失敗: {result.error}")

if __name__ == "__main__":
    main()
'''

    example_file.write_text(example_code)
    print(f"✅ 使用例ファイル作成: {example_file}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python copy_to_project.py <target_project_path> [library_name]")
        print("例: python copy_to_project.py ../my_project libs/ai_analysis")
        sys.exit(1)

    target_path = sys.argv[1]
    library_name = sys.argv[2] if len(sys.argv) > 2 else "ai_analysis_engine"

    if copy_library_to_project(target_path, library_name):
        create_usage_example(target_path)
        print("\n🎉 移植完了!")
        print("📝 使用方法:")
        print(f"   cd {target_path}")
        print("   python example_usage.py")
    else:
        print("❌ 移植失敗")
        sys.exit(1)
