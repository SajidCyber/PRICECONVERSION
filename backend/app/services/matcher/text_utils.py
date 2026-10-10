"""Text Normalization and String Similarity Algorithms."""

import re
from typing import List, Set, Tuple

STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "for", "with", "by", "of", "to",
    "is", "it", "from", "as", "new", "best", "hot", "deal", "pack", "set", "original",
    "inch", "inches", "cm", "mm", "brand", "edition", "version", "pro", "plus", "max"
}


def normalize_title(text: str) -> str:
    """Cleans, lowercases, and strips non-alphanumeric noise from product titles."""
    if not text:
        return ""
    text = text.lower()
    # Replace separators with spaces
    text = re.sub(r"[-_/.,|()]", " ", text)
    # Remove remaining non-alphanumerics
    text = re.sub(r"[^\w\s]", "", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str, remove_stopwords: bool = True) -> Set[str]:
    """Tokenizes text into a set of meaningful word tokens."""
    clean = normalize_title(text)
    tokens = clean.split()
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
    return set(tokens)


def extract_model_numbers(text: str) -> Set[str]:
    """Extracts alphanumeric model codes, chips, or SKU fragments (e.g. M3, WH1000XM5, S24)."""
    # Alphanumeric patterns containing at least one digit and one letter (e.g., WH1000XM5, M3, RTX4090)
    matches = re.findall(r"\b[A-Za-z0-9]*[0-9]+[A-Za-z0-9]*\b", text.upper())
    # Filter out pure numbers or single digit noise
    return {m for m in matches if len(m) >= 2 and not m.isdigit()}


def jaccard_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Computes Jaccard index between two token sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / len(union)


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Computes normalized Levenshtein similarity ratio between 0.0 and 1.0."""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)
    # Initialize matrix
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # Deletion
                dp[i][j - 1] + 1,      # Insertion
                dp[i - 1][j - 1] + cost  # Substitution
            )

    distance = dp[len1][len2]
    max_len = max(len1, len2)
    return 1.0 - (distance / max_len)
