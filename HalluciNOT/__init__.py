"""
HalluciNOT: Document-Grounded Verification for Large Language Models

HalluciNOT is a modular toolkit for detecting, measuring, and mitigating 
hallucinations in LLM outputs when working with document-based content.
"""

__version__ = "0.1.0"

from .processor import VerificationProcessor
from .claim_extraction.extractor import ClaimExtractor, ClaimMerger
from .source_mapping.mapper import SourceMapper
from .confidence.scorer import ConfidenceScorer, ConfidenceCalibrator
from .handlers.strategies import InterventionSelector
from .handlers.corrections import generate_corrected_response
from .visualization.highlighter import highlight_verification_result, create_confidence_legend
from .visualization.reporting import ReportGenerator
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

# Optional ByteMeSumAI integration
try:
    from .integration.bytemesumai import (
        ByteMeSumAIAdapter,
        ByteMeSumAIDocumentStore,
        VerificationMetadataEnricher
    )
    __has_bytemesumai__ = True
except ImportError:
    __has_bytemesumai__ = False

# Create a default verifier factory function for easy usage
def create_verifier(config=None):
    """
    Create a VerificationProcessor with default or custom configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured VerificationProcessor
    """
    return VerificationProcessor(config)