"""
Data Checker Agent - Analyzes and validates input data
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

from ..config import config
from ..models.state import AnalysisState, DatasetInfo
from ..tools.rag_tool import RAGTool
from ..tools.repl_tool import REPLTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataCheckerAgent:
    """
    Agent for checking and analyzing input data
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.openai.model,
            temperature=config.openai.temperature,
            api_key=config.openai.api_key
        )

        self.rag_tool = RAGTool()
        self.repl_tool = REPLTool()

        # Setup tools
        self.tools = [
            self._create_rag_search_tool(),
            self._create_data_analysis_tool(),
            self._create_plot_creation_tool()
        ]

        self.prompt = ChatPromptTemplate.from_template("""
あなたはデータ確認エージェントです。与えられたデータセットを分析し、問題点を特定してください。

データセット情報:
{dataset_info}

評価環境仕様:
{evaluation_spec}

期待値:
{expected_result}

以下の観点からデータを分析してください：
1. データの構造と品質
2. 列の意味とフォーマット
3. 欠損値や異常値の確認
4. 時系列データの連続性
5. 仕様との整合性

分析結果を詳細に報告してください。

利用可能なツール:
- rag_search: 仕様書の検索
- analyze_data: データ分析
- create_plot: グラフ作成
""")

    def analyze_data(self, dataset: DatasetInfo) -> Dict[str, Any]:
        """
        Analyze the given dataset

        Args:
            dataset: Dataset to analyze

        Returns:
            Analysis results
        """
        try:
            logger.info(f"Starting data analysis for dataset {dataset.id}")

            # Load evaluation spec
            evaluation_spec = ""
            if dataset.evaluation_spec_md:
                try:
                    with open(dataset.evaluation_spec_md, 'r', encoding='utf-8') as f:
                        evaluation_spec = f.read()
                except Exception as e:
                    logger.warning(f"Failed to load evaluation spec: {e}")

            # Prepare dataset info
            dataset_info = self._prepare_dataset_info(dataset)

            # Use LLM with tools for analysis
            chain = self.prompt | self.llm.bind_tools(self.tools)

            response = chain.invoke({
                "dataset_info": dataset_info,
                "evaluation_spec": evaluation_spec[:2000],  # Limit size
                "expected_result": dataset.expected_result
            })

            # Process tool calls if any
            if hasattr(response, 'tool_calls') and response.tool_calls:
                results = self._execute_tools(response.tool_calls, dataset)
            else:
                results = {"llm_analysis": response.content}

            # Add basic data analysis
            basic_analysis = self._perform_basic_analysis(dataset)
            results.update(basic_analysis)

            logger.info(f"Data analysis completed for dataset {dataset.id}")
            return results

        except Exception as e:
            logger.error(f"Data analysis failed: {e}")
            return {"error": str(e)}

    def _prepare_dataset_info(self, dataset: DatasetInfo) -> str:
        """Prepare dataset information for LLM"""
        info_lines = []

        info_lines.append(f"データセットID: {dataset.id}")
        info_lines.append(f"アルゴリズム出力CSV: {dataset.algorithm_output_csv}")
        info_lines.append(f"コア出力CSV: {dataset.core_output_csv}")
        info_lines.append(f"評価環境仕様: {dataset.evaluation_spec_md}")
        info_lines.append(f"期待値: {dataset.expected_result}")

        return "\n".join(info_lines)

    def _perform_basic_analysis(self, dataset: DatasetInfo) -> Dict[str, Any]:
        """Perform basic data analysis"""
        try:
            # Load CSV files
            csv_files = [dataset.algorithm_output_csv, dataset.core_output_csv]
            dataframes = self.repl_tool.load_csv_data(csv_files)

            analysis = {}

            for name, df in dataframes.items():
                if len(df) > 0:
                    analysis[name] = {
                        "shape": df.shape,
                        "columns": list(df.columns),
                        "dtypes": df.dtypes.to_dict(),
                        "summary_stats": df.describe().to_dict(),
                        "missing_values": df.isnull().sum().to_dict(),
                        "sample_data": df.head(5).to_dict('records')
                    }
                else:
                    analysis[name] = {"error": "Empty or failed to load dataframe"}

            return {"basic_analysis": analysis}

        except Exception as e:
            logger.error(f"Basic analysis failed: {e}")
            return {"basic_analysis_error": str(e)}

    def _create_rag_search_tool(self):
        """Create RAG search tool"""
        @tool
        def rag_search(query: str, segment: str = "evaluation_specs") -> str:
            """Search specification documents for relevant information"""
            try:
                results = self.rag_tool.search(query, segment, k=3)
                return "\n\n".join([
                    f"Content: {r['content']}\nSource: {r['source']}\nScore: {r['score']:.3f}"
                    for r in results
                ])
            except Exception as e:
                return f"Search failed: {e}"

        return rag_search

    def _create_data_analysis_tool(self):
        """Create data analysis tool"""
        @tool
        def analyze_data(csv_path: str, analysis_type: str = "summary") -> str:
            """Analyze CSV data with pandas"""
            try:
                df = self.repl_tool.load_csv_data([csv_path]).get(csv_path.split('/')[-1].split('\\')[-1])

                if df is None or len(df) == 0:
                    return "Failed to load data or empty dataframe"

                if analysis_type == "summary":
                    result = df.describe().to_string()
                elif analysis_type == "info":
                    result = str(df.info())
                elif analysis_type == "missing":
                    result = df.isnull().sum().to_string()
                else:
                    result = df.head(10).to_string()

                return result

            except Exception as e:
                return f"Analysis failed: {e}"

        return analyze_data

    def _create_plot_creation_tool(self):
        """Create plot creation tool"""
        @tool
        def create_plot(csv_path: str, plot_type: str = "timeseries", column: str = None) -> str:
            """Create plots from CSV data"""
            try:
                df = self.repl_tool.load_csv_data([csv_path]).get(csv_path.split('/')[-1].split('\\')[-1])

                if df is None or len(df) == 0:
                    return "Failed to load data"

                # Determine column to plot
                if column is None and len(df.select_dtypes(include=['number']).columns) > 0:
                    column = df.select_dtypes(include=['number']).columns[0]

                if column not in df.columns:
                    return f"Column {column} not found"

                # Create plot code
                if plot_type == "timeseries" and 'timestamp' in df.columns:
                    code = f"""
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
plt.plot(df['timestamp'], df['{column}'])
plt.title('Time Series: {column}')
plt.xlabel('Timestamp')
plt.ylabel('{column}')
plt.xticks(rotation=45)
plt.tight_layout()
"""
                else:
                    code = f"""
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
plt.hist(df['{column}'].dropna(), bins=30, alpha=0.7)
plt.title('Distribution: {column}')
plt.xlabel('{column}')
plt.ylabel('Frequency')
plt.tight_layout()
"""

                result = self.repl_tool.create_plot(code, {"df": df})

                if result.get("success"):
                    return f"Plot created successfully: {result.get('plot_path')}"
                else:
                    return f"Plot creation failed: {result.get('error')}"

            except Exception as e:
                return f"Plot creation failed: {e}"

        return create_plot

    def _execute_tools(self, tool_calls, dataset: DatasetInfo) -> Dict[str, Any]:
        """Execute tool calls and collect results"""
        results = {}

        for tool_call in tool_calls:
            try:
                tool_name = tool_call['name']
                tool_args = tool_call['args']

                if tool_name == 'rag_search':
                    results['rag_results'] = self._create_rag_search_tool()(tool_args.get('query', ''), tool_args.get('segment', 'evaluation_specs'))
                elif tool_name == 'analyze_data':
                    results['data_analysis'] = self._create_data_analysis_tool()(tool_args.get('csv_path', ''), tool_args.get('analysis_type', 'summary'))
                elif tool_name == 'create_plot':
                    results['plot_results'] = self._create_plot_creation_tool()(
                        tool_args.get('csv_path', ''),
                        tool_args.get('plot_type', 'timeseries'),
                        tool_args.get('column')
                    )

            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                results[f'error_{tool_call["name"]}'] = str(e)

        return results
