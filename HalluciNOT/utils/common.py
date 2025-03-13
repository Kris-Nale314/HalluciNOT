"""
Common utilities and data structures for HalluciNOT.

This module defines the core data structures used throughout the
verification process, including claims, document chunks, verification
results, and intervention strategies.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import datetime


class ClaimType(Enum):
    """Types of factual claims that can be extracted and verified."""
    NUMERICAL = "numerical"  # Numbers, quantities, statistics
    TEMPORAL = "temporal"    # Dates, times, durations
    ENTITY = "entity"        # Named entities (people, organizations, etc.)
    CAUSAL = "causal"        # Cause-effect relationships
    COMPARATIVE = "comparative"  # Comparisons between entities or values
    DEFINITIONAL = "definitional"  # Definitions or descriptions
    CITATION = "citation"    # References to external sources
    OTHER = "other"          # Other types of claims


class BoundaryType(Enum):
    """Types of document boundaries for source mapping."""
    SECTION = "section"      # Major document section
    PARAGRAPH = "paragraph"  # Paragraph break
    LIST_ITEM = "list_item"  # Item in a list
    TABLE = "table"          # Table content
    FIGURE = "figure"        # Figure or diagram
    HEADING = "heading"      # Heading or title
    QUOTE = "quote"          # Quoted text
    CODE = "code"            # Code block
    OTHER = "other"          # Other boundary type


class InterventionType(Enum):
    """Types of interventions for handling hallucinations."""
    NONE = "none"                # No intervention needed
    CORRECTION = "correction"    # Replace with corrected information
    UNCERTAINTY = "uncertainty"  # Add uncertainty qualification
    REMOVAL = "removal"          # Remove hallucinated content
    SOURCE_REQUEST = "source_request"  # Request additional sources
    CLARIFICATION = "clarification"  # Ask for clarification


@dataclass
class DocumentChunk:
    """
    Represents a chunk of a document used for verification.
    
    This class is designed to be compatible with chunks created by
    ByteMeSumAI, with additional metadata for verification purposes.
    """
    # Core chunk data
    id: str
    text: str
    source_document: str
    start_idx: int = 0
    end_idx: int = 0
    
    # Metadata for verification
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    # Verification-specific metadata
    boundary_type: Optional[BoundaryType] = None
    parent_section: Optional[str] = None
    related_chunks: List[str] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def has_verification_metadata(self) -> bool:
        """Check if this chunk has verification-specific metadata."""
        return any([
            self.boundary_type is not None,
            self.parent_section is not None,
            self.related_chunks,
            self.entities
        ])


@dataclass
class SourceReference:
    """
    Reference to a source document chunk that supports a claim.
    """
    chunk_id: str
    document_id: str
    text_excerpt: str
    alignment_score: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Claim:
    """
    A factual assertion extracted from an LLM response.
    """
    id: str
    text: str
    type: ClaimType
    start_idx: int
    end_idx: int
    
    # Entities and context
    entities: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Source mapping data
    sources: List[SourceReference] = field(default_factory=list)
    confidence_score: float = 0.0
    verification_notes: str = ""
    
    @property
    def has_source(self) -> bool:
        """Check if this claim has any source references."""
        return len(self.sources) > 0
    
    @property
    def best_source(self) -> Optional[SourceReference]:
        """Get the source with the highest alignment score."""
        if not self.sources:
            return None
        return max(self.sources, key=lambda s: s.alignment_score)


@dataclass
class Intervention:
    """
    A recommended intervention for handling a potential hallucination.
    """
    claim_id: str
    intervention_type: InterventionType
    confidence: float
    recommendation: str
    corrected_text: Optional[str] = None
    explanation: Optional[str] = None


@dataclass
class VerificationReport:
    """
    Detailed report on the verification process and results.
    """
    overall_confidence: float
    verified_claims_count: int
    total_claims_count: int
    hallucination_score: float
    verification_summary: str
    detailed_claims: List[Dict[str, Any]]
    generation_timestamp: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now()
    )


class DocumentStore:
    """
    Collection of document chunks used for verification.
    
    This is a minimal interface that can be implemented by different
    document storage mechanisms (in-memory, vector database, etc.)
    """
    
    def __init__(self, chunks: Optional[List[DocumentChunk]] = None):
        """Initialize with optional list of chunks."""
        self._chunks = chunks or []
    
    def add_chunk(self, chunk: DocumentChunk) -> None:
        """Add a document chunk to the store."""
        self._chunks.append(chunk)
    
    def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Get a chunk by its ID."""
        for chunk in self._chunks:
            if chunk.id == chunk_id:
                return chunk
        return None
    
    def search(self, query: str, limit: int = 5) -> List[DocumentChunk]:
        """
        Search for chunks relevant to a query.
        
        This is a placeholder for more sophisticated search mechanisms
        that would be implemented by specific document stores.
        """
        # This would be replaced with actual search logic
        return self._chunks[:limit]
    
    def get_all_chunks(self) -> List[DocumentChunk]:
        """Get all chunks in the store."""
        return self._chunks
    
    @property
    def count(self) -> int:
        """Get the number of chunks in the store."""
        return len(self._chunks)


@dataclass
class VerificationResult:
    """
    Result of verifying an LLM response against document sources.
    """
    original_response: str
    claims: List[Claim]
    interventions: List[Intervention]
    metadata: Dict[str, Any] = field(default_factory=dict)
    report: Optional[VerificationReport] = None
    
    @property
    def confidence_score(self) -> float:
        """
        Calculate the overall confidence score for the verification.
        
        This is a weighted average of individual claim confidence scores.
        """
        if not self.claims:
            return 0.0
        
        # Simple average for now, but could be more sophisticated
        return sum(c.confidence_score for c in self.claims) / len(self.claims)
    
    @property
    def hallucination_score(self) -> float:
        """
        Calculate a hallucination score based on low-confidence claims.
        
        Higher scores indicate more potential hallucinations.
        """
        if not self.claims:
            return 0.0
        
        # Count claims with low confidence as potential hallucinations
        hallucination_threshold = 0.5  # Could be configurable
        hallucinated_claims = sum(1 for c in self.claims 
                                 if c.confidence_score < hallucination_threshold)
        
        return hallucinated_claims / len(self.claims)
    
    @property
    def requires_intervention(self) -> bool:
        """Check if any interventions are recommended."""
        return any(i.intervention_type != InterventionType.NONE 
                  for i in self.interventions)
    
    def get_claim_by_id(self, claim_id: str) -> Optional[Claim]:
        """Get a claim by its ID."""
        for claim in self.claims:
            if claim.id == claim_id:
                return claim
        return None
    
    def generate_report(self) -> VerificationReport:
        """Generate a detailed verification report."""
        if self.report:
            return self.report
        
        # This would be replaced with actual report generation logic
        # from the ReportGenerator component
        return VerificationReport(
            overall_confidence=self.confidence_score,
            verified_claims_count=sum(1 for c in self.claims if c.has_source),
            total_claims_count=len(self.claims),
            hallucination_score=self.hallucination_score,
            verification_summary="Placeholder summary",
            detailed_claims=[{
                "id": c.id,
                "text": c.text,
                "confidence": c.confidence_score,
                "has_source": c.has_source
            } for c in self.claims]
        )