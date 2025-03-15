"""
Visualization Module

This module provides functionality for highlighting verification results
and generating detailed reports.
"""

from .highlighter import highlight_verification_result, create_confidence_legend
from .reporting import ReportGenerator

__all__ = ["highlight_verification_result", "create_confidence_legend", "ReportGenerator"]