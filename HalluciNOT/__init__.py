"""
HalluciNOT: Document-Grounded Verification for Large Language Models

HalluciNOT is a modular toolkit for detecting, measuring, and mitigating
hallucinations in LLM outputs when working with document-based content.
It leverages rich document structure and metadata to efficiently verify
LLM-generated content against source materials.

The package provides tools for claim extraction, source mapping, confidence
scoring, and hallucination management in LLM-powered applications.
"""

__version__ = '0.1.0'

# Core verification components
from .processor import VerificationProcessor, Verifier
from .claim_extraction.extractor import ClaimExtractor
from .source_mapping.mapper import SourceMapper
from .confidence.scorer import ConfidenceScorer, ConfidenceCalibrator
from .visualization.reporting import ReportGenerator
from .visualization.highlighter import highlight_verification_result
from .handlers.strategies import InterventionSelector
from .handlers.corrections import generate_corrected_response

# Data structures
from .utils.common import (
    Claim,
    ClaimType,
    DocumentChunk,
    DocumentStore,
    SourceReference,
    Intervention,
    InterventionType,
    VerificationResult,
    VerificationReport,
    BoundaryType
)

# ByteMeSumAI integration
from .integration.bytemesumai import (
    ByteMeSumAIAdapter,
    VerificationMetadataEnricher,
    ByteMeSumAIDocumentStore
)

# Version information
__author__ = 'Your Name'
__email__ = 'your.email@example.com'
__all__ = [
    # Core components
    'VerificationProcessor',
    'Verifier',
    'ClaimExtractor',
    'SourceMapper',
    'ConfidenceScorer',
    'ConfidenceCalibrator',
    'ReportGenerator',
    'highlight_verification_result',
    'InterventionSelector',
    'generate_corrected_response',
    
    # Data structures
    'Claim',
    'ClaimType',
    'DocumentChunk',
    'DocumentStore',
    'SourceReference',
    'Intervention',
    'InterventionType',
    'VerificationResult',
    'VerificationReport',
    'BoundaryType',
    
    # ByteMeSumAI integration
    'ByteMeSumAIAdapter',
    'VerificationMetadataEnricher',
    'ByteMeSumAIDocumentStore',
]