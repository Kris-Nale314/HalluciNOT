# Copyright (c) 2025 Kris Naleszkiewicz
# Licensed under the MIT License - see LICENSE file for details
"""
Main Verification Processor

This module provides the main entry point for the verification process,
coordinating the extraction, mapping, scoring, and intervention components.
"""

from typing import List, Dict, Any, Optional, Union
import logging
import uuid

from .claim_extraction.extractor import ClaimExtractor, ClaimMerger
from .source_mapping.mapper import SourceMapper
from .confidence.scorer import ConfidenceScorer
from .handlers.strategies import InterventionSelector
from .utils.common import (
    Claim, DocumentStore, VerificationResult, VerificationReport
)

# Set up logging
logger = logging.getLogger(__name__)


class VerificationProcessor:
    """
    Main processor for verifying LLM responses against source documents.
    
    This class coordinates the entire verification pipeline, from claim
    extraction to confidence scoring and intervention recommendation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the verification processor with configuration options.
        
        Args:
            config: Configuration options for the processor and its components
        """
        self.config = config or {}
        
        # Component-specific configurations
        extractor_config = self.config.get("extractor", {})
        merger_config = self.config.get("merger", {})
        mapper_config = self.config.get("mapper", {})
        scorer_config = self.config.get("scorer", {})
        intervention_config = self.config.get("intervention", {})
        
        # Initialize components
        self.claim_extractor = ClaimExtractor(extractor_config)
        self.claim_merger = ClaimMerger(merger_config)
        self.source_mapper = SourceMapper(mapper_config)
        self.confidence_scorer = ConfidenceScorer(scorer_config)
        self.intervention_selector = InterventionSelector(intervention_config)
        
        # Default settings
        self.enable_claim_merging = self.config.get("enable_claim_merging", True)
        self.auto_generate_report = self.config.get("auto_generate_report", False)
        
        logger.debug("VerificationProcessor initialized with config: %s", self.config)
    
    def verify(
        self, 
        text: str,
        document_store: DocumentStore
    ) -> VerificationResult:
        """
        Verify an LLM response against a document store.
        
        This method runs the complete verification pipeline:
        1. Extract claims from the text
        2. Map claims to source documents
        3. Calculate confidence scores
        4. Recommend interventions for hallucinations
        
        Args:
            text: The LLM-generated text to verify
            document_store: Collection of document chunks to verify against
            
        Returns:
            VerificationResult with claims, confidence scores, and interventions
        """
        logger.info("Starting verification of text (%d characters) against %d document chunks", 
                  len(text), document_store.count)
        
        # Extract claims from the text
        claims = self.extract_claims(text)
        logger.info("Extracted %d claims from text", len(claims))
        
        # Optionally merge related claims
        if self.enable_claim_merging and claims:
            claims = self.claim_merger.merge_claims(claims)
            logger.info("Merged into %d claims", len(claims))
        
        # Map claims to sources
        claims = self.map_claims_to_sources(claims, document_store)
        logger.info("Mapped %d claims to sources", len(claims))
        
        # Score claim confidence
        claims = self.score_claim_confidence(claims)
        logger.info("Scored confidence for %d claims", len(claims))
        
        # Select interventions for hallucinations
        interventions = self.select_interventions(claims)
        logger.info("Selected %d interventions", len(interventions))
        
        # Create verification result
        result = VerificationResult(
            original_response=text,
            claims=claims,
            interventions=interventions,
            metadata={
                "verification_id": str(uuid.uuid4()),
                "text_length": len(text),
                "document_count": document_store.count,
                "claim_count": len(claims),
                "intervention_count": len(interventions)
            }
        )
        
        # Optionally generate report
        if self.auto_generate_report:
            from .visualization.reporting import ReportGenerator
            report_generator = ReportGenerator()
            result.report = report_generator.generate_report(result)
        
        return result
    
    def extract_claims(self, text: str) -> List[Claim]:
        """
        Extract claims from text.
        
        Args:
            text: Text to extract claims from
            
        Returns:
            List of extracted claims
        """
        return self.claim_extractor.extract_claims(text)
    
    def map_claims_to_sources(
        self, 
        claims: List[Claim],
        document_store: DocumentStore
    ) -> List[Claim]:
        """
        Map claims to sources in the document store.
        
        Args:
            claims: Claims to map to sources
            document_store: Document store to search for sources
            
        Returns:
            Claims with source references added
        """
        return self.source_mapper.map_to_sources(claims, document_store)
    
    def score_claim_confidence(self, claims: List[Claim]) -> List[Claim]:
        """
        Calculate confidence scores for claims.
        
        Args:
            claims: Claims to score
            
        Returns:
            Claims with confidence scores added
        """
        return self.confidence_scorer.score_claims(claims)
    
    def select_interventions(self, claims: List[Claim]) -> List[Any]:
        """
        Select interventions for potential hallucinations.
        
        Args:
            claims: Claims to analyze for interventions
            
        Returns:
            List of recommended interventions
        """
        return self.intervention_selector.select_interventions(claims)
    
    def highlight_verification_result(
        self, 
        verification_result: VerificationResult,
        format: str = "html"
    ) -> str:
        """
        Generate highlighted visualization of verification result.
        
        Args:
            verification_result: Verification result to visualize
            format: Output format ('html', 'markdown', or 'text')
            
        Returns:
            Highlighted text with confidence indicators
        """
        from .visualization.highlighter import highlight_verification_result
        return highlight_verification_result(verification_result, format)
    
    def generate_corrected_response(
        self, 
        verification_result: VerificationResult,
        strategy: str = "balanced"
    ) -> str:
        """
        Generate a corrected version of the response.
        
        Args:
            verification_result: Verification result to correct
            strategy: Correction strategy ('conservative', 'balanced', or 'aggressive')
            
        Returns:
            Corrected response text
        """
        from .handlers.corrections import generate_corrected_response
        return generate_corrected_response(verification_result, strategy)
    
    def generate_report(
        self, 
        verification_result: VerificationResult,
        format: str = "html"
    ) -> Union[str, VerificationReport]:
        """
        Generate a detailed report on verification results.
        
        Args:
            verification_result: Verification result to report on
            format: Output format ('html', 'json', or 'object')
            
        Returns:
            Report in the requested format
        """
        from .visualization.reporting import ReportGenerator
        report_generator = ReportGenerator()
        
        if format == "html":
            return report_generator.generate_html_report(verification_result)
        elif format == "json":
            return report_generator.generate_json_report(verification_result)
        else:
            return report_generator.generate_report(verification_result)