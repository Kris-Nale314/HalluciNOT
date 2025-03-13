"""
Hallucination Handling Module - Intervention Strategies

This module is responsible for selecting and implementing appropriate
intervention strategies when hallucinations are detected in LLM responses.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

from ..utils.common import Claim, Intervention, InterventionType, VerificationResult

# Set up logging
logger = logging.getLogger(__name__)


class InterventionSelector:
    """
    Selects appropriate intervention strategies for handling hallucinations.
    
    The selector analyzes verified claims and recommends interventions
    based on confidence scores, claim types, and other factors.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the intervention selector with configuration options.
        
        Args:
            config: Configuration options for intervention selection
        """
        self.config = config or {}
        
        # Default configuration values
        self.hallucination_threshold = self.config.get("hallucination_threshold", 0.3)
        self.uncertain_threshold = self.config.get("uncertain_threshold", 0.7)
        self.intervention_aggressiveness = self.config.get("intervention_aggressiveness", 0.5)
        
        logger.debug("InterventionSelector initialized with config: %s", self.config)
    
    def select_interventions(self, claims: List[Claim]) -> List[Intervention]:
        """
        Select appropriate interventions for a list of claims.
        
        Args:
            claims: List of claims with confidence scores
            
        Returns:
            List of recommended interventions
        """
        logger.debug("Selecting interventions for %d claims", len(claims))
        
        interventions = []
        
        for claim in claims:
            intervention = self._select_claim_intervention(claim)
            if intervention.intervention_type != InterventionType.NONE:
                interventions.append(intervention)
        
        logger.info("Selected %d interventions for %d claims", 
                  len(interventions), len(claims))
        
        return interventions
    
    def _select_claim_intervention(self, claim: Claim) -> Intervention:
        """
        Select an appropriate intervention for a single claim.
        
        The intervention is based on the claim's confidence score,
        claim type, and other factors.
        """
        confidence = claim.confidence_score
        
        # Determine intervention type based on confidence
        if confidence < self.hallucination_threshold:
            # Low confidence suggests a hallucination
            intervention_type = self._determine_low_confidence_intervention(claim)
        elif confidence < self.uncertain_threshold:
            # Medium confidence suggests uncertainty
            intervention_type = InterventionType.UNCERTAINTY
        else:
            # High confidence suggests no intervention needed
            intervention_type = InterventionType.NONE
        
        # Generate a recommendation based on the intervention type
        recommendation = self._generate_recommendation(claim, intervention_type)
        
        # Create the intervention
        intervention = Intervention(
            claim_id=claim.id,
            intervention_type=intervention_type,
            confidence=self._calculate_intervention_confidence(claim, intervention_type),
            recommendation=recommendation,
            corrected_text=self._generate_corrected_text(claim, intervention_type) if intervention_type == InterventionType.CORRECTION else None,
            explanation=self._generate_explanation(claim, intervention_type) if intervention_type != InterventionType.NONE else None
        )
        
        return intervention
    
    def _determine_low_confidence_intervention(self, claim: Claim) -> InterventionType:
        """
        Determine the best intervention for a low-confidence claim.
        
        Different types of claims may benefit from different interventions.
        """
        # If we have partial support, use uncertainty
        if claim.sources and claim.confidence_score > 0.1:
            return InterventionType.UNCERTAINTY
        
        # If we have no sources at all, consider whether to remove or correct
        if self.intervention_aggressiveness > 0.7:
            # Aggressive approach: remove unsupported claims
            return InterventionType.REMOVAL
        else:
            # Conservative approach: try to correct if possible
            return InterventionType.CORRECTION if claim.has_source else InterventionType.REMOVAL
    
    def _generate_recommendation(
        self, 
        claim: Claim, 
        intervention_type: InterventionType
    ) -> str:
        """
        Generate a recommendation for handling the claim.
        
        The recommendation is a human-readable guidance for how
        to address the potential hallucination.
        """
        if intervention_type == InterventionType.NONE:
            return "No intervention needed - claim is well-supported"
        
        if intervention_type == InterventionType.CORRECTION:
            if claim.has_source:
                return f"Replace with corrected information from source: {claim.best_source.chunk_id}"
            else:
                return "Replace with corrected information or remove (no source available)"
        
        if intervention_type == InterventionType.UNCERTAINTY:
            return "Add uncertainty qualification to indicate limited source support"
        
        if intervention_type == InterventionType.REMOVAL:
            return "Remove this claim as it lacks sufficient source support"
        
        if intervention_type == InterventionType.SOURCE_REQUEST:
            return "Request additional sources to verify this claim"
        
        if intervention_type == InterventionType.CLARIFICATION:
            return "Seek clarification on this claim before proceeding"
        
        return "Unknown intervention type"
    
    def _calculate_intervention_confidence(
        self, 
        claim: Claim, 
        intervention_type: InterventionType
    ) -> float:
        """
        Calculate confidence in the recommended intervention.
        
        This represents how confident we are that this is the
        right intervention for this claim.
        """
        # Base confidence in the intervention
        base_confidence = 0.7
        
        # Adjust based on claim confidence and intervention type
        if intervention_type == InterventionType.NONE:
            # Higher claim confidence means higher intervention confidence
            return min(1.0, claim.confidence_score + 0.1)
            
        if intervention_type == InterventionType.CORRECTION:
            # Confidence in correction depends on having good sources
            if claim.has_source and claim.best_source.alignment_score > 0.7:
                return 0.9  # High confidence if we have a good source
            return 0.6  # Lower confidence otherwise
        
        if intervention_type == InterventionType.UNCERTAINTY:
            # High confidence in uncertainty for borderline cases
            if 0.2 < claim.confidence_score < 0.6:
                return 0.9
            return 0.7
        
        if intervention_type == InterventionType.REMOVAL:
            # Higher confidence in removal for very low confidence claims
            if claim.confidence_score < 0.1:
                return 0.9
            return 0.7
        
        # Default confidence for other intervention types
        return base_confidence
    
    def _generate_corrected_text(
        self, 
        claim: Claim, 
        intervention_type: InterventionType
    ) -> Optional[str]:
        """
        Generate corrected text for a claim if correction is recommended.
        
        This uses the best available source to create a corrected version
        of the claim that is better supported by evidence.
        """
        if intervention_type != InterventionType.CORRECTION:
            return None
        
        if not claim.has_source:
            return None
        
        # Get the best source for correction
        best_source = claim.best_source
        
        # This is a simplified approach - in practice, would use more
        # sophisticated techniques for generating corrections
        
        # For now, just use the source excerpt as the correction
        # In practice, might want to maintain style of original claim
        return best_source.text_excerpt
    
    def _generate_explanation(
        self, 
        claim: Claim, 
        intervention_type: InterventionType
    ) -> Optional[str]:
        """
        Generate an explanation for the recommended intervention.
        
        This explanation provides context for why a particular
        intervention was recommended.
        """
        if intervention_type == InterventionType.NONE:
            return None
        
        if intervention_type == InterventionType.CORRECTION:
            if claim.has_source:
                source = claim.best_source
                return (f"Claim has low confidence score ({claim.confidence_score:.2f}) but "
                        f"a relevant source was found. Source excerpt: '{source.text_excerpt}' "
                        f"has alignment score {source.alignment_score:.2f}")
            else:
                return (f"Claim has low confidence score ({claim.confidence_score:.2f}) and "
                        "no supporting sources were found.")
        
        if intervention_type == InterventionType.UNCERTAINTY:
            return (f"Claim has borderline confidence score ({claim.confidence_score:.2f}). "
                    f"Has {len(claim.sources)} partial sources, but support is limited.")
        
        if intervention_type == InterventionType.REMOVAL:
            return (f"Claim has very low confidence score ({claim.confidence_score:.2f}) and "
                    f"insufficient source support ({len(claim.sources)} sources).")
        
        if intervention_type == InterventionType.SOURCE_REQUEST:
            return (f"Claim requires additional sources to verify. Current confidence: {claim.confidence_score:.2f}")
        
        if intervention_type == InterventionType.CLARIFICATION:
            return (f"Claim is ambiguous and may benefit from clarification. Confidence: {claim.confidence_score:.2f}")
        
        return f"Intervention selected due to low confidence score: {claim.confidence_score:.2f}"