"""
Hallucination Handling Module - Correction Generation

This module is responsible for generating corrected responses based on
verification results and intervention strategies.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
import re
import logging

from ..utils.common import VerificationResult, Claim, InterventionType

# Set up logging
logger = logging.getLogger(__name__)


def generate_corrected_response(
    verification_result: VerificationResult,
    strategy: str = "conservative"
) -> str:
    """
    Generate a corrected version of the response based on verification results.
    
    Args:
        verification_result: Verification result with interventions
        strategy: Correction strategy ('conservative', 'balanced', or 'aggressive')
        
    Returns:
        Corrected response text
    """
    logger.debug("Generating corrected response with %s strategy", strategy)
    
    # If no interventions are needed, return the original response
    if not verification_result.requires_intervention:
        logger.debug("No interventions required, returning original response")
        return verification_result.original_response
    
    # Select correction strategy
    if strategy == "conservative":
        return _conservative_correction(verification_result)
    elif strategy == "aggressive":
        return _aggressive_correction(verification_result)
    else:  # balanced is the default
        return _balanced_correction(verification_result)


def _conservative_correction(verification_result: VerificationResult) -> str:
    """
    Apply a conservative correction strategy.
    
    This strategy only makes minimal changes to the original response,
    primarily adding uncertainty qualifiers and clarifications.
    """
    logger.debug("Applying conservative correction strategy")
    
    corrected_text = verification_result.original_response
    
    # Get all claims sorted by position (to process from end to beginning)
    all_claims = sorted(
        verification_result.claims, 
        key=lambda c: c.start_idx,
        reverse=True  # Process from end to beginning to avoid index shifts
    )
    
    # Process each claim and its corresponding intervention
    for claim in all_claims:
        # Find the intervention for this claim
        intervention = next(
            (i for i in verification_result.interventions if i.claim_id == claim.id), 
            None
        )
        
        if not intervention:
            continue
        
        # Apply the intervention based on its type
        if intervention.intervention_type == InterventionType.UNCERTAINTY:
            # Add uncertainty qualifier
            corrected_text = _add_uncertainty_qualifier(
                corrected_text, claim, conservative=True
            )
        
        elif intervention.intervention_type == InterventionType.CORRECTION:
            # Only apply corrections with high intervention confidence
            if intervention.confidence > 0.8 and intervention.corrected_text:
                corrected_text = _apply_correction(
                    corrected_text, claim, intervention.corrected_text
                )
    
    return corrected_text


def _balanced_correction(verification_result: VerificationResult) -> str:
    """
    Apply a balanced correction strategy.
    
    This strategy makes moderate changes, including corrections,
    uncertainty qualifiers, and limited removals.
    """
    logger.debug("Applying balanced correction strategy")
    
    corrected_text = verification_result.original_response
    
    # Get all claims sorted by position (to process from end to beginning)
    all_claims = sorted(
        verification_result.claims, 
        key=lambda c: c.start_idx,
        reverse=True  # Process from end to beginning to avoid index shifts
    )
    
    # Process each claim and its corresponding intervention
    for claim in all_claims:
        # Find the intervention for this claim
        intervention = next(
            (i for i in verification_result.interventions if i.claim_id == claim.id), 
            None
        )
        
        if not intervention:
            continue
        
        # Apply the intervention based on its type
        if intervention.intervention_type == InterventionType.UNCERTAINTY:
            # Add uncertainty qualifier
            corrected_text = _add_uncertainty_qualifier(
                corrected_text, claim, conservative=False
            )
        
        elif intervention.intervention_type == InterventionType.CORRECTION:
            # Apply corrections with reasonable confidence
            if intervention.confidence > 0.6 and intervention.corrected_text:
                corrected_text = _apply_correction(
                    corrected_text, claim, intervention.corrected_text
                )
        
        elif intervention.intervention_type == InterventionType.REMOVAL:
            # Only remove claims with very low confidence
            if claim.confidence_score < 0.2:
                corrected_text = _remove_claim(corrected_text, claim)
    
    return corrected_text


def _aggressive_correction(verification_result: VerificationResult) -> str:
    """
    Apply an aggressive correction strategy.
    
    This strategy makes extensive changes, including corrections,
    removals, and restructuring where necessary.
    """
    logger.debug("Applying aggressive correction strategy")
    
    corrected_text = verification_result.original_response
    
    # Get all claims sorted by position (to process from end to beginning)
    all_claims = sorted(
        verification_result.claims, 
        key=lambda c: c.start_idx,
        reverse=True  # Process from end to beginning to avoid index shifts
    )
    
    # Process each claim and its corresponding intervention
    for claim in all_claims:
        # Find the intervention for this claim
        intervention = next(
            (i for i in verification_result.interventions if i.claim_id == claim.id), 
            None
        )
        
        if not intervention:
            continue
        
        # Apply the intervention based on its type
        if intervention.intervention_type == InterventionType.UNCERTAINTY:
            # For aggressive strategy, prefer correction over uncertainty
            if claim.has_source and claim.best_source.alignment_score > 0.4:
                corrected_text = _apply_correction(
                    corrected_text, claim, claim.best_source.text_excerpt
                )
            else:
                # Add uncertainty qualifier
                corrected_text = _add_uncertainty_qualifier(
                    corrected_text, claim, conservative=False
                )
        
        elif intervention.intervention_type == InterventionType.CORRECTION:
            # Apply corrections more liberally
            if intervention.corrected_text:
                corrected_text = _apply_correction(
                    corrected_text, claim, intervention.corrected_text
                )
            elif claim.has_source:
                corrected_text = _apply_correction(
                    corrected_text, claim, claim.best_source.text_excerpt
                )
        
        elif intervention.intervention_type == InterventionType.REMOVAL:
            # Remove claims with low confidence
            if claim.confidence_score < 0.3:
                corrected_text = _remove_claim(corrected_text, claim)
    
    return corrected_text


def _add_uncertainty_qualifier(
    text: str, 
    claim: Claim,
    conservative: bool = True
) -> str:
    """
    Add an uncertainty qualifier to a claim in the text.
    
    Args:
        text: The text to modify
        claim: The claim to add uncertainty qualifier to
        conservative: Whether to use conservative (weaker) qualifiers
        
    Returns:
        Modified text with uncertainty qualifier
    """
    # Ensure the claim text exists in the current text
    if claim.text not in text[claim.start_idx:claim.end_idx + 10]:
        # Claim text doesn't match expected position, try to find it
        match_pos = text.find(claim.text)
        if match_pos == -1:
            # Can't find the claim text, don't modify
            return text
        
        # Update indices based on found position
        claim.start_idx = match_pos
        claim.end_idx = match_pos + len(claim.text)
    
    # Select appropriate uncertainty qualifier based on conservativeness
    if conservative:
        # Conservative qualifiers
        qualifiers = [
            "may", "might", "could", "reportedly", "according to sources",
            "seems to", "appears to"
        ]
    else:
        # Stronger qualifiers
        qualifiers = [
            "uncertain if", "limited evidence suggests", "not clearly supported",
            "sources partially indicate", "questionable whether", 
            "unverified claim that", "limited support for the claim that"
        ]
    
    # Different claim types might use different qualifiers
    qualifier = qualifiers[hash(claim.text) % len(qualifiers)]
    
    # Extract the part of the claim to qualify
    claim_text = text[claim.start_idx:claim.end_idx]
    
    # Check if the claim starts with a capital letter
    starts_with_capital = claim_text[0].isupper() if claim_text else False
    
    # Different insertion strategies based on claim structure
    if re.match(r'^[A-Z][a-z]+ (is|are|was|were) ', claim_text):
        # For "X is Y" type claims
        pattern = r'^([A-Z][a-z]+ )(is|are|was|were) '
        qualified_text = re.sub(pattern, r'\1' + qualifier + r' \2 ', claim_text)
    elif re.match(r'^The [a-z]+ (is|are|was|were) ', claim_text):
        # For "The X is Y" type claims
        pattern = r'^(The [a-z]+ )(is|are|was|were) '
        qualified_text = re.sub(pattern, r'\1' + qualifier + r' \2 ', claim_text)
    else:
        # Default approach: insert at beginning
        if starts_with_capital:
            # Capitalize the qualifier if the claim starts with a capital
            qualifier = qualifier[0].upper() + qualifier[1:]
            qualified_text = f"{qualifier} {claim_text}"
        else:
            qualified_text = f"{qualifier} {claim_text}"
    
    # Replace the original claim with the qualified version
    return text[:claim.start_idx] + qualified_text + text[claim.end_idx:]


def _apply_correction(
    text: str, 
    claim: Claim,
    correction: str
) -> str:
    """
    Replace a claim with its correction in the text.
    
    Args:
        text: The text to modify
        claim: The claim to correct
        correction: The corrected text to insert
        
    Returns:
        Modified text with correction applied
    """
    # Ensure the claim text exists in the current text
    if claim.text not in text[claim.start_idx:claim.end_idx + 10]:
        # Claim text doesn't match expected position, try to find it
        match_pos = text.find(claim.text)
        if match_pos == -1:
            # Can't find the claim text, don't modify
            return text
        
        # Update indices based on found position
        claim.start_idx = match_pos
        claim.end_idx = match_pos + len(claim.text)
    
    # Check if the claim starts with a capital letter
    starts_with_capital = text[claim.start_idx].isupper() if claim.start_idx < len(text) else False
    
    # Check if the correction needs capitalization adjustment
    if starts_with_capital and not correction[0].isupper():
        correction = correction[0].upper() + correction[1:]
    elif not starts_with_capital and correction[0].isupper():
        correction = correction[0].lower() + correction[1:]
    
    # Replace the original claim with the correction
    return text[:claim.start_idx] + correction + text[claim.end_idx:]


def _remove_claim(text: str, claim: Claim) -> str:
    """
    Remove a claim from the text.
    
    Args:
        text: The text to modify
        claim: The claim to remove
        
    Returns:
        Modified text with claim removed
    """
    # Ensure the claim text exists in the current text
    if claim.text not in text[claim.start_idx:claim.end_idx + 10]:
        # Claim text doesn't match expected position, try to find it
        match_pos = text.find(claim.text)
        if match_pos == -1:
            # Can't find the claim text, don't modify
            return text
        
        # Update indices based on found position
        claim.start_idx = match_pos
        claim.end_idx = match_pos + len(claim.text)
    
    # Check if the claim is a complete sentence
    is_complete_sentence = False
    
    # Look for sentence-ending punctuation
    if claim.end_idx < len(text) and text[claim.end_idx - 1] in '.!?':
        is_complete_sentence = True
    
    # Determine how to remove the claim
    if is_complete_sentence:
        # Remove the entire sentence including any trailing space
        end = claim.end_idx
        while end < len(text) and text[end].isspace():
            end += 1
        
        return text[:claim.start_idx] + text[end:]
    else:
        # Remove just the claim text
        return text[:claim.start_idx] + text[claim.end_idx:]