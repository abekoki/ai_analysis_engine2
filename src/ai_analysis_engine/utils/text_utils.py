"""
Text processing utilities
"""

import re
import json
from typing import Dict, Any, Optional, List

from .logger import get_logger

logger = get_logger(__name__)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text response

    Args:
        text: Text containing JSON

    Returns:
        Extracted JSON object or None
    """
    try:
        # Find JSON-like content in text
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, text, re.DOTALL)

        if match:
            json_str = match.group()
            # Clean up common issues
            json_str = json_str.replace('```json', '').replace('```', '')
            return json.loads(json_str)
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to extract JSON from text: {e}")
        return None


def clean_text(text: str) -> str:
    """
    Clean and normalize text

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())

    # Remove non-printable characters except newlines and tabs
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')

    return text


def split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into chunks with overlap for better context retention

    Args:
        text: Text to split
        chunk_size: Size of each chunk
        overlap: Overlap between chunks

    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # If not the last chunk, try to find a good breaking point
        if end < len(text):
            # Look for sentence endings within the last 100 characters
            last_period = text.rfind('.', end - 100, end)
            last_newline = text.rfind('\n', end - 100, end)
            last_space = text.rfind(' ', end - 50, end)

            # Use the latest good breaking point
            break_point = max(last_period, last_newline, last_space)
            if break_point > start + chunk_size // 2:
                end = break_point + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position with overlap
        start = max(end - overlap, start + 1)

        # Prevent infinite loop
        if start >= len(text):
            break

    return chunks


def extract_frame_range(text: str) -> Optional[tuple]:
    """
    Extract frame range from natural language text

    Args:
        text: Natural language text describing frame range

    Returns:
        Tuple of (start_frame, end_frame) or None
    """
    # Patterns for frame ranges
    patterns = [
        r'フレーム\s*(\d+)\s*から\s*(\d+)',
        r'frame\s*(\d+)\s*to\s*(\d+)',
        r'(\d+)\s*-\s*(\d+)\s*フレーム',
        r'frames?\s+(\d+)\s*(?:to|-)\s*(\d+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                start = int(match.group(1))
                end = int(match.group(2))
                return (start, end)
            except (ValueError, IndexError):
                continue

    return None


def extract_column_info(text: str) -> List[str]:
    """
    Extract column names mentioned in text

    Args:
        text: Text mentioning column names

    Returns:
        List of column names found
    """
    # Common column patterns
    patterns = [
        r'列\s*[\'\"]([^\'\"]+)[\'\"]',
        r'column\s*[\'\"]([^\'\"]+)[\'\"]',
        r'カラム\s*[\'\"]([^\'\"]+)[\'\"]',
        r'フィールド\s*[\'\"]([^\'\"]+)[\'\"]'
    ]

    columns = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        columns.extend(matches)

    # Also try to find unquoted column names (more risky)
    unquoted_pattern = r'\b(?:列|column|カラム|フィールド)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    unquoted_matches = re.findall(unquoted_pattern, text, re.IGNORECASE)
    columns.extend(unquoted_matches)

    return list(set(columns))  # Remove duplicates


def extract_expected_value(text: str) -> Optional[str]:
    """
    Extract expected value from natural language description

    Args:
        text: Natural language description

    Returns:
        Expected value description
    """
    # Look for patterns like "should be 1", "should contain", "must have", etc.
    patterns = [
        r'(?:期待値|expected|期待される|should be|must be|値は)\s*[:]*\s*(.+?)(?:\。|\.|$|です|である)',
        r'(?:検知結果|detection result|結果は)\s*[:]*\s*(.+?)(?:\。|\.|$|です|である)',
        r'(?:条件|condition|ルール|rule)\s*[:]*\s*(.+?)(?:\。|\.|$|です|である)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            if value:
                return clean_text(value)

    return None


def parse_boolean_condition(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse boolean conditions from natural language

    Args:
        text: Natural language condition

    Returns:
        Dictionary with parsed condition or None
    """
    # Simple pattern matching for common conditions
    conditions = {
        'equals': r'(?:==|=|equals?|等しい|同じ)\s*(\d+)',
        'greater_than': r'(?:>|より大きい|greater than)\s*(\d+)',
        'less_than': r'(?:<|より小さい|less than)\s*(\d+)',
        'contains': r'含む?\s*(.+?)(?:\s|$)',
        'exists': r'存在する?\s*(.+?)(?:\s|$)'
    }

    for condition_type, pattern in conditions.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                'type': condition_type,
                'value': match.group(1) if match.groups() else True,
                'original_text': text
            }

    return None


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple text similarity score

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0

    # Simple word overlap similarity
    words1 = set(clean_text(text1).lower().split())
    words2 = set(clean_text(text2).lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union)
