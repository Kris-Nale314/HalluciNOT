"""
Confidence Scoring Module

This module is responsible for calculating confidence scores for claims
based on their alignment with source documents.
"""

from .scorer import ConfidenceScorer, ConfidenceCalibrator

__all__ = ["ConfidenceScorer", "ConfidenceCalibrator"]