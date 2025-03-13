"""
Visualization Module - Verification Highlighting

This module provides functionality for highlighting verified claims in
LLM responses, showing confidence levels and source references.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import re
import html

from ..utils.common import VerificationResult, Claim, ClaimType

# Set up logging
logger = logging.getLogger(__name__)


def highlight_verification_result(
    verification_result: VerificationResult,
    format: str = "html"
) -> str:
    """
    Generate a highlighted version of the response showing confidence levels.
    
    Args:
        verification_result: The verification result to visualize
        format: Output format ('html', 'markdown', or 'text')
        
    Returns:
        Highlighted response with confidence indicators
    """
    logger.debug("Generating highlighted response in %s format", format)
    
    if format == "html":
        return _highlight_html(verification_result)
    elif format == "markdown":
        return _highlight_markdown(verification_result)
    else:  # text is the default
        return _highlight_text(verification_result)


def _highlight_html(verification_result: VerificationResult) -> str:
    """
    Generate an HTML-highlighted version of the response.
    
    This is the most visually rich format, with color coding,
    tooltips, and interactive elements.
    """
    # Start with the original response text
    response_text = verification_result.original_response
    highlighted_text = ""
    
    # Sort claims by their position in the text
    sorted_claims = sorted(verification_result.claims, key=lambda c: c.start_idx)
    
    # Track the current position in the text
    current_pos = 0
    
    # Add CSS styles
    styles = """
    <style>
        .verified-claim { display: inline; position: relative; }
        .verified-claim span { position: relative; }
        .verified-high { background-color: rgba(0, 255, 0, 0.2); border-bottom: 2px solid #0c0; }
        .verified-medium { background-color: rgba(255, 255, 0, 0.2); border-bottom: 2px solid #cc0; }
        .verified-low { background-color: rgba(255, 0, 0, 0.2); border-bottom: 2px solid #c00; }
        .verified-claim .tooltip {
            visibility: hidden;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            width: 300px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .verified-claim:hover .tooltip {
            visibility: visible;
            opacity: 1;
        }
        .source-excerpt {
            background-color: #f9f9f9;
            border-left: 3px solid #ddd;
            padding: 5px;
            margin: 5px 0;
        }
        .confidence {
            font-weight: bold;
        }
        .confidence-high { color: #0c0; }
        .confidence-medium { color: #cc0; }
        .confidence-low { color: #c00; }
    </style>
    """
    
    # Process each claim and add highlighting
    for i, claim in enumerate(sorted_claims):
        # Add any text between the last claim and this one
        highlighted_text += html.escape(response_text[current_pos:claim.start_idx])
        
        # Get the claim text
        claim_text = response_text[claim.start_idx:claim.end_idx]
        
        # Determine confidence class
        if claim.confidence_score >= 0.7:
            confidence_class = "high"
        elif claim.confidence_score >= 0.3:
            confidence_class = "medium"
        else:
            confidence_class = "low"
        
        # Create the tooltip content
        tooltip = f"""
        <div class="tooltip">
            <div><strong>Claim Type:</strong> {claim.type.value}</div>
            <div class="confidence">
                <strong>Confidence:</strong> 
                <span class="confidence-{confidence_class}">{claim.confidence_score:.2f}</span>
            </div>
        """
        
        # Add source information if available
        if claim.has_source:
            best_source = claim.best_source
            tooltip += f"""
            <div><strong>Source:</strong> {html.escape(best_source.document_id)}</div>
            <div class="source-excerpt">{html.escape(best_source.text_excerpt)}</div>
            """
        else:
            tooltip += f"""
            <div class="source-excerpt">No direct source found for this claim.</div>
            """
        
        # Add verification notes
        if claim.verification_notes:
            tooltip += f"""
            <div><strong>Notes:</strong> {html.escape(claim.verification_notes)}</div>
            """
        
        tooltip += "</div>"
        
        # Create the highlighted claim HTML
        highlighted_claim = f"""
        <span class="verified-claim">
            <span class="verified-{confidence_class}">{html.escape(claim_text)}</span>
            {tooltip}
        </span>
        """
        
        highlighted_text += highlighted_claim
        
        # Update current position
        current_pos = claim.end_idx
    
    # Add any remaining text after the last claim
    highlighted_text += html.escape(response_text[current_pos:])
    
    # Wrap in a div with styles
    return f"{styles}<div class='verification-result'>{highlighted_text}</div>"


def _highlight_markdown(verification_result: VerificationResult) -> str:
    """
    Generate a Markdown-highlighted version of the response.
    
    This uses Markdown formatting for highlighting, which works
    in environments that support Markdown but not HTML.
    """
    # Start with the original response text
    response_text = verification_result.original_response
    highlighted_text = ""
    
    # Sort claims by their position in the text
    sorted_claims = sorted(verification_result.claims, key=lambda c: c.start_idx)
    
    # Track the current position in the text
    current_pos = 0
    
    # Process each claim and add highlighting
    for i, claim in enumerate(sorted_claims):
        # Add any text between the last claim and this one
        highlighted_text += response_text[current_pos:claim.start_idx]
        
        # Get the claim text
        claim_text = response_text[claim.start_idx:claim.end_idx]
        
        # Determine confidence marker
        if claim.confidence_score >= 0.7:
            marker = "✓"  # High confidence
        elif claim.confidence_score >= 0.3:
            marker = "⚠️"  # Medium confidence
        else:
            marker = "❌"  # Low confidence
        
        # Create a reference for footnotes
        ref_num = i + 1
        
        # Add the highlighted claim with footnote reference
        highlighted_claim = f"{claim_text}[{marker}^{ref_num}]"
        highlighted_text += highlighted_claim
        
        # Update current position
        current_pos = claim.end_idx
    
    # Add any remaining text after the last claim
    highlighted_text += response_text[current_pos:]
    
    # Add footnotes at the end
    highlighted_text += "\n\n---\n\n"
    
    for i, claim in enumerate(sorted_claims):
        ref_num = i + 1
        footnote = f"^{ref_num}: "
        
        # Add confidence information
        footnote += f"Confidence: {claim.confidence_score:.2f} | Type: {claim.type.value}"
        
        # Add source information if available
        if claim.has_source:
            best_source = claim.best_source
            footnote += f"\n\nSource: {best_source.document_id}\n\n> {best_source.text_excerpt}"
        else:
            footnote += "\n\n> No direct source found for this claim."
        
        # Add verification notes
        if claim.verification_notes:
            footnote += f"\n\nNotes: {claim.verification_notes}"
        
        highlighted_text += f"{footnote}\n\n"
    
    return highlighted_text


def _highlight_text(verification_result: VerificationResult) -> str:
    """
    Generate a plain text highlighted version of the response.
    
    This uses simple text markers for highlighting, suitable for
    environments that don't support HTML or Markdown.
    """
    # Start with the original response text
    response_text = verification_result.original_response
    highlighted_text = ""
    
    # Sort claims by their position in the text
    sorted_claims = sorted(verification_result.claims, key=lambda c: c.start_idx)
    
    # Track the current position in the text
    current_pos = 0
    
    # Process each claim and add highlighting
    for i, claim in enumerate(sorted_claims):
        # Add any text between the last claim and this one
        highlighted_text += response_text[current_pos:claim.start_idx]
        
        # Get the claim text
        claim_text = response_text[claim.start_idx:claim.end_idx]
        
        # Determine confidence marker
        if claim.confidence_score >= 0.7:
            marker = "✓"  # High confidence
        elif claim.confidence_score >= 0.3:
            marker = "!"  # Medium confidence
        else:
            marker = "X"  # Low confidence
        
        # Create a reference for annotations
        ref_num = i + 1
        
        # Add the highlighted claim with reference
        highlighted_claim = f"{claim_text} [{marker}{ref_num}]"
        highlighted_text += highlighted_claim
        
        # Update current position
        current_pos = claim.end_idx
    
    # Add any remaining text after the last claim
    highlighted_text += response_text[current_pos:]
    
    # Add annotations at the end
    highlighted_text += "\n\n---\n\n"
    
    for i, claim in enumerate(sorted_claims):
        ref_num = i + 1
        
        # Determine confidence marker
        if claim.confidence_score >= 0.7:
            confidence_text = "HIGH"
        elif claim.confidence_score >= 0.3:
            confidence_text = "MEDIUM"
        else:
            confidence_text = "LOW"
        
        annotation = f"[{ref_num}] Confidence: {confidence_text} ({claim.confidence_score:.2f}) | Type: {claim.type.value}"
        
        # Add source information if available
        if claim.has_source:
            best_source = claim.best_source
            annotation += f"\nSource: {best_source.document_id}\n\n\"{best_source.text_excerpt}\""
        else:
            annotation += "\nNo direct source found for this claim."
        
        # Add verification notes
        if claim.verification_notes:
            annotation += f"\nNotes: {claim.verification_notes}"
        
        highlighted_text += f"{annotation}\n\n"
    
    return highlighted_text


def create_confidence_legend() -> str:
    """
    Create an HTML legend explaining the confidence indicators.
    
    Returns:
        HTML string with the confidence legend
    """
    return """
    <div class="confidence-legend">
        <h3>Confidence Indicators</h3>
        <ul>
            <li><span class="verified-high">High confidence</span> - Claim is well-supported by sources</li>
            <li><span class="verified-medium">Medium confidence</span> - Claim has partial support</li>
            <li><span class="verified-low">Low confidence</span> - Claim has little or no support</li>
        </ul>
    </div>
    """