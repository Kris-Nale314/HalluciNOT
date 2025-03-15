"""
Claim Extraction Module

This module is responsible for extracting discrete factual claims from
LLM responses and classifying them by type.
"""

from .extractor import ClaimExtractor, ClaimMerger

__all__ = ["ClaimExtractor", "ClaimMerger"]