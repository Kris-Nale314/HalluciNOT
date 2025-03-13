"""
Confidence Scoring Module

This module is responsible for calculating confidence scores for claims
based on their alignment with source documents. It assesses how well each
claim is supported by the available evidence.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import math

from ..utils.common import Claim, ClaimType

# Set up logging
logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Calculates confidence scores for claims based on source alignment.
    
    The scorer assesses how well each claim is supported by the available
    evidence and assigns a confidence score between 0 and 1.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the confidence scorer with configuration options.
        
        Args:
            config: Configuration options for confidence scoring
        """
        self.config = config or {}
        
        # Default configuration values
        self.unsupported_claim_score = self.config.get("unsupported_claim_score", 0.0)
        self.claim_type_weights = self.config.get("claim_type_weights", {
            ClaimType.NUMERICAL.value: 1.2,   # Higher weight for numerical claims
            ClaimType.TEMPORAL.value: 1.1,    # Higher weight for temporal claims
            ClaimType.ENTITY.value: 1.0,      # Standard weight for entity claims
            ClaimType.CAUSAL.value: 0.9,      # Lower weight for causal claims (harder to verify)
            ClaimType.COMPARATIVE.value: 1.0,  # Standard weight for comparative claims
            ClaimType.DEFINITIONAL.value: 1.1, # Higher weight for definitional claims
            ClaimType.CITATION.value: 1.2,     # Higher weight for citation claims
            ClaimType.OTHER.value: 0.8         # Lower weight for unclassified claims
        })
        
        logger.debug("ConfidenceScorer initialized with config: %s", self.config)
    
    def score_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Calculate confidence scores for a list of claims.
        
        Args:
            claims: List of claims with source references
            
        Returns:
            The same claims with confidence scores added
        """
        logger.debug("Scoring confidence for %d claims", len(claims))
        
        for claim in claims:
            claim.confidence_score = self._calculate_claim_confidence(claim)
            
        return claims
    
    def _calculate_claim_confidence(self, claim: Claim) -> float:
        """
        Calculate the confidence score for a single claim.
        
        This score represents how well the claim is supported by
        its associated sources.
        """
        # If the claim has no sources, assign the unsupported score
        if not claim.sources:
            logger.debug("Claim has no sources, assigning score: %f", 
                       self.unsupported_claim_score)
            return self.unsupported_claim_score
        
        # Get the base confidence from source alignment scores
        base_confidence = self._calculate_base_confidence(claim)
        logger.debug("Base confidence from sources: %f", base_confidence)
        
        # Apply claim type-specific weighting
        weighted_confidence = self._apply_claim_type_weighting(claim, base_confidence)
        logger.debug("After claim type weighting: %f", weighted_confidence)
        
        # Adjust for other factors
        adjusted_confidence = self._apply_confidence_adjustments(claim, weighted_confidence)
        logger.debug("Final adjusted confidence: %f", adjusted_confidence)
        
        # Ensure the confidence is in the range [0, 1]
        return max(0.0, min(1.0, adjusted_confidence))
    
    def _calculate_base_confidence(self, claim: Claim) -> float:
        """
        Calculate base confidence from source alignment scores.
        
        This uses the alignment scores of all sources associated
        with the claim, with an emphasis on the best source.
        """
        if not claim.sources:
            return 0.0
        
        # Get all alignment scores
        alignment_scores = [source.alignment_score for source in claim.sources]
        
        # Calculate a weighted average that emphasizes the best source
        # but still considers other sources
        best_score = max(alignment_scores)
        avg_score = sum(alignment_scores) / len(alignment_scores)
        
        # Weight the best score more heavily than the average
        base_confidence = (0.7 * best_score) + (0.3 * avg_score)
        
        # Boost confidence if multiple sources agree
        if len(alignment_scores) > 1 and min(alignment_scores) > 0.5:
            # Apply a bonus based on the number of good sources
            source_bonus = min(0.2, 0.05 * len(alignment_scores))
            base_confidence = min(1.0, base_confidence + source_bonus)
        
        return base_confidence
    
    def _apply_claim_type_weighting(
        self, 
        claim: Claim, 
        base_confidence: float
    ) -> float:
        """
        Apply claim type-specific weighting to the confidence score.
        
        Different types of claims may have different confidence
        characteristics based on how easy they are to verify.
        """
        # Get the weight for this claim type
        claim_type_key = claim.type.value
        weight = self.claim_type_weights.get(claim_type_key, 1.0)
        
        # Apply the weight, ensuring the result stays in [0, 1]
        if weight < 1.0:
            # Reduce confidence
            weighted_confidence = base_confidence * weight
        else:
            # Increase confidence, but ensure it doesn't exceed 1.0
            increase = (weight - 1.0) * base_confidence * (1.0 - base_confidence)
            weighted_confidence = base_confidence + increase
        
        return max(0.0, min(1.0, weighted_confidence))
    
    def _apply_confidence_adjustments(
        self, 
        claim: Claim, 
        weighted_confidence: float
    ) -> float:
        """
        Apply additional adjustments to the confidence score.
        
        These adjustments account for factors beyond source alignment
        and claim type, such as complexity, specificity, etc.
        """
        adjusted_confidence = weighted_confidence
        
        # Adjust for claim complexity (longer claims may be more complex)
        # This is a simple heuristic - could be more sophisticated
        if len(claim.text) > 100:
            # Slightly reduce confidence for very complex claims
            complexity_factor = 0.95
            adjusted_confidence *= complexity_factor
        
        # Adjust for entity matching
        if claim.entities:
            # Check if entities in the claim are found in the sources
            entity_texts = [entity["text"].lower() for entity in claim.entities]
            
            entity_matches = 0
            total_sources = len(claim.sources)
            
            if total_sources > 0:
                for source in claim.sources:
                    excerpt_lower = source.text_excerpt.lower()
                    for entity in entity_texts:
                        if entity in excerpt_lower:
                            entity_matches += 1
                            break
                
                # If a high proportion of sources contain relevant entities, boost confidence
                if entity_matches > 0:
                    entity_match_ratio = entity_matches / total_sources
                    entity_boost = 0.1 * entity_match_ratio
                    adjusted_confidence = min(1.0, adjusted_confidence + entity_boost)
        
        # Apply a small penalty for claims that have borderline alignment scores
        # This creates more separation between highly confident and borderline claims
        if 0.5 < weighted_confidence < 0.7:
            penalty = 0.05
            adjusted_confidence -= penalty
        
        return adjusted_confidence


class ConfidenceCalibrator:
    """
    Calibrates confidence scores based on historical verification results.
    
    This class is used to adjust confidence scores to better reflect
    actual verification accuracy, based on historical data.
    """
    
    def __init__(self, calibration_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the calibrator with optional calibration data.
        
        Args:
            calibration_data: Historical data for calibration
        """
        self.calibration_data = calibration_data or {}
        self._calibration_model = None
        
        # Initialize calibration model if data is provided
        if self.calibration_data:
            self._build_calibration_model()
    
    def _build_calibration_model(self):
        """Build a calibration model from historical data."""
        # This would implement a calibration model based on collected data
        # Placeholder for now
        self._calibration_model = True
    
    def calibrate_score(
        self, 
        score: float,
        claim_type: ClaimType
    ) -> float:
        """
        Calibrate a confidence score based on historical accuracy.
        
        Args:
            score: Raw confidence score to calibrate
            claim_type: Type of the claim
            
        Returns:
            Calibrated confidence score
        """
        # If no calibration model is available, return the original score
        if not self._calibration_model:
            return score
        
        # This would apply the calibration model to adjust the score
        # Placeholder for now - just applies a simple adjustment
        
        # Example: Use Platt scaling or isotonic regression for calibration
        claim_type_key = claim_type.value
        
        # Get calibration parameters for this claim type (if available)
        a = self.calibration_data.get(f"{claim_type_key}_a", 1.0)
        b = self.calibration_data.get(f"{claim_type_key}_b", 0.0)
        
        # Apply sigmoid calibration (Platt scaling)
        calibrated = 1.0 / (1.0 + math.exp(-(a * score + b)))
        
        return calibrated