"""
Hallucination Handling Module

This module is responsible for selecting and implementing appropriate
intervention strategies when hallucinations are detected.
"""

from .strategies import InterventionSelector
from .corrections import generate_corrected_response

__all__ = ["InterventionSelector", "generate_corrected_response"]