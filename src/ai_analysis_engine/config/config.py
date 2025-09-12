"""
Configuration management for the AI Analysis Engine
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path


class OpenAIConfig(BaseModel):
    """OpenAI API configuration"""
    api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.1)
    max_tokens: int = Field(default=4000)


class VectorStoreConfig(BaseModel):
    """Vector store configuration"""
    persist_directory: str = Field(default="./data/vectorstore")
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)


class REPLConfig(BaseModel):
    """REPL tool configuration"""
    timeout: int = Field(default=30)
    max_output_length: int = Field(default=5000)
    allowed_modules: list = Field(default_factory=lambda: ["pandas", "numpy", "matplotlib"])


class LangGraphConfig(BaseModel):
    """LangGraph configuration"""
    max_iterations: int = Field(default=10)
    checkpoint_path: str = Field(default="./data/checkpoints")


class Config:
    """Main configuration class"""

    def __init__(self):
        self.openai = OpenAIConfig()
        self.vectorstore = VectorStoreConfig()
        self.repl = REPLConfig()
        self.langgraph = LangGraphConfig()

        # Project paths
        self.project_root = Path(".")
        self.data_dir = Path("./data")
        self.output_dir = Path("./output")
        self.logs_dir = Path("./logs")

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables"""
        return cls()

    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        directories = [
            self.data_dir,
            self.output_dir,
            self.logs_dir,
            Path(self.vectorstore.persist_directory),
            Path(self.langgraph.checkpoint_path)
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_vectorstore_path(self, segment: str) -> str:
        """Get vectorstore path for specific segment"""
        return str(Path(self.vectorstore.persist_directory) / f"{segment}_vectorstore")

    def validate_api_keys(self) -> bool:
        """Validate required API keys"""
        return bool(self.openai.api_key.strip())


# Global configuration instance
config = Config()
