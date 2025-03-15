# Copyright (c) 2025 Kris Naleszkiewicz
# Licensed under the MIT License - see LICENSE file for details
"""
Visualization Module - Verification Reporting

This module provides functionality for generating detailed reports on
verification results, including summary statistics and visualization.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import json

from ..utils.common import VerificationResult, VerificationReport, Claim, ClaimType

# Set up logging
logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates detailed reports on verification results.
    
    The reports include summary statistics, claim-by-claim analysis,
    and recommendations for addressing potential hallucinations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the report generator with configuration options.
        
        Args:
            config: Configuration options for report generation
        """
        self.config = config or {}
        
        # Default configuration values
        self.include_source_excerpts = self.config.get("include_source_excerpts", True)
        self.detailed_claim_analysis = self.config.get("detailed_claim_analysis", True)
        self.include_suggestions = self.config.get("include_suggestions", True)
        
        logger.debug("ReportGenerator initialized with config: %s", self.config)
    
    def generate_report(self, verification_result: VerificationResult) -> VerificationReport:
        """
        Generate a detailed verification report.
        
        Args:
            verification_result: The verification result to report on
            
        Returns:
            VerificationReport with detailed analysis
        """
        logger.debug("Generating verification report")
        
        # Calculate overall summary metrics
        verified_claims_count = sum(1 for c in verification_result.claims if c.has_source)
        total_claims_count = len(verification_result.claims)
        
        # Generate detailed claim information
        detailed_claims = self._generate_detailed_claims(verification_result) if self.detailed_claim_analysis else []
        
        # Generate verification summary
        verification_summary = self._generate_summary(verification_result)
        
        # Create the report
        report = VerificationReport(
            overall_confidence=verification_result.confidence_score,
            verified_claims_count=verified_claims_count,
            total_claims_count=total_claims_count,
            hallucination_score=verification_result.hallucination_score,
            verification_summary=verification_summary,
            detailed_claims=detailed_claims,
            generation_timestamp=datetime.now()
        )
        
        logger.info("Generated verification report with overall confidence: %.2f", 
                   report.overall_confidence)
        
        return report
    
    def _generate_detailed_claims(self, verification_result: VerificationResult) -> List[Dict[str, Any]]:
        """
        Generate detailed information for each claim.
        
        This includes confidence scores, sources, and other analysis.
        """
        detailed_claims = []
        
        for claim in verification_result.claims:
            claim_info = {
                "id": claim.id,
                "text": claim.text,
                "type": claim.type.value,
                "confidence_score": claim.confidence_score,
                "has_source": claim.has_source,
                "verification_notes": claim.verification_notes,
                "position": {
                    "start_idx": claim.start_idx,
                    "end_idx": claim.end_idx
                }
            }
            
            # Add source information if available
            if claim.has_source and self.include_source_excerpts:
                sources_info = []
                for source in claim.sources:
                    source_info = {
                        "document_id": source.document_id,
                        "chunk_id": source.chunk_id,
                        "alignment_score": source.alignment_score,
                    }
                    
                    # Include excerpt if requested
                    if self.include_source_excerpts:
                        source_info["text_excerpt"] = source.text_excerpt
                    
                    sources_info.append(source_info)
                
                claim_info["sources"] = sources_info
            
            # Add intervention information if available
            for intervention in verification_result.interventions:
                if intervention.claim_id == claim.id:
                    claim_info["intervention"] = {
                        "type": intervention.intervention_type.value,
                        "confidence": intervention.confidence,
                        "recommendation": intervention.recommendation,
                        "explanation": intervention.explanation
                    }
                    break
            
            detailed_claims.append(claim_info)
        
        return detailed_claims
    
    def _generate_summary(self, verification_result: VerificationResult) -> str:
        """
        Generate a human-readable summary of the verification results.
        
        This includes overall confidence, hallucination assessment,
        and recommendations.
        """
        claims = verification_result.claims
        verified_count = sum(1 for c in claims if c.has_source)
        total_count = len(claims)
        
        if total_count == 0:
            return "No verifiable claims were found in this response."
        
        # Overall confidence assessment
        confidence_score = verification_result.confidence_score
        
        if confidence_score >= 0.8:
            confidence_desc = "high"
            summary = f"The response has high factual accuracy, with {verified_count}/{total_count} claims supported by source material."
        elif confidence_score >= 0.5:
            confidence_desc = "moderate"
            summary = f"The response has moderate factual accuracy, with {verified_count}/{total_count} claims supported by source material."
        else:
            confidence_desc = "low"
            summary = f"The response has low factual accuracy, with only {verified_count}/{total_count} claims supported by source material."
        
        # Hallucination assessment
        hallucination_score = verification_result.hallucination_score
        
        if hallucination_score <= 0.1:
            summary += " No significant hallucinations were detected."
        elif hallucination_score <= 0.3:
            summary += f" Minor hallucinations were detected ({int(hallucination_score * 100)}% of claims)."
        else:
            summary += f" Significant hallucinations were detected ({int(hallucination_score * 100)}% of claims)."
        
        # Add recommendations if requested
        if self.include_suggestions and verification_result.interventions:
            intervention_count = len(verification_result.interventions)
            correction_count = sum(1 for i in verification_result.interventions if i.intervention_type.value == "correction")
            uncertainty_count = sum(1 for i in verification_result.interventions if i.intervention_type.value == "uncertainty")
            removal_count = sum(1 for i in verification_result.interventions if i.intervention_type.value == "removal")
            
            summary += f"\n\nRecommended interventions: {intervention_count} total"
            
            if correction_count > 0:
                summary += f", {correction_count} corrections"
            
            if uncertainty_count > 0:
                summary += f", {uncertainty_count} uncertainty qualifications"
            
            if removal_count > 0:
                summary += f", {removal_count} removals"
            
            summary += "."
        
        return summary
    
    def generate_html_report(self, verification_result: VerificationResult) -> str:
        """
        Generate an HTML report for the verification result.
        
        Args:
            verification_result: The verification result to report on
            
        Returns:
            HTML string with the formatted report
        """
        report = self.generate_report(verification_result)
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Verification Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                .report-container {{ max-width: 800px; margin: 0 auto; }}
                .report-header {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; }}
                .report-summary {{ margin-top: 20px; padding: 15px; background-color: #e9f7fe; border-radius: 5px; }}
                .confidence-high {{ color: #0c0; }}
                .confidence-medium {{ color: #cc0; }}
                .confidence-low {{ color: #c00; }}
                .claim-card {{ border: 1px solid #ddd; border-radius: 5px; margin-bottom: 15px; padding: 15px; }}
                .claim-high {{ border-left: 5px solid #0c0; }}
                .claim-medium {{ border-left: 5px solid #cc0; }}
                .claim-low {{ border-left: 5px solid #c00; }}
                .source-excerpt {{ background-color: #f9f9f9; border-left: 3px solid #ddd; padding: 10px; margin: 10px 0; }}
                .intervention {{ background-color: #fff8e1; padding: 10px; border-radius: 5px; margin-top: 10px; }}
                .metrics {{ display: flex; justify-content: space-between; margin: 20px 0; }}
                .metric-card {{ text-align: center; padding: 15px; background-color: #f4f4f4; border-radius: 5px; width: 30%; }}
                .metric-value {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
                .footer {{ margin-top: 30px; font-size: 0.8em; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <div class="report-header">
                    <h1>Verification Report</h1>
                    <p>Generated on: {report.generation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="metrics">
                    <div class="metric-card">
                        <h3>Overall Confidence</h3>
                        <div class="metric-value confidence-{self._get_confidence_class(report.overall_confidence)}">
                            {report.overall_confidence:.2f}
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <h3>Verified Claims</h3>
                        <div class="metric-value">
                            {report.verified_claims_count}/{report.total_claims_count}
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <h3>Hallucination Score</h3>
                        <div class="metric-value confidence-{self._get_confidence_class(1 - report.hallucination_score)}">
                            {report.hallucination_score:.2f}
                        </div>
                    </div>
                </div>
                
                <div class="report-summary">
                    <h2>Summary</h2>
                    <p>{report.verification_summary}</p>
                </div>
        """
        
        if report.detailed_claims:
            html_content += """
                <h2>Claim Analysis</h2>
            """
            
            for claim_info in report.detailed_claims:
                confidence = claim_info["confidence_score"]
                confidence_class = self._get_confidence_class(confidence)
                
                html_content += f"""
                <div class="claim-card claim-{confidence_class}">
                    <h3>Claim: "{claim_info["text"]}"</h3>
                    <p><strong>Type:</strong> {claim_info["type"]}</p>
                    <p><strong>Confidence:</strong> <span class="confidence-{confidence_class}">{confidence:.2f}</span></p>
                """
                
                if "sources" in claim_info and claim_info["sources"]:
                    html_content += f"""
                    <h4>Sources:</h4>
                    """
                    
                    for source in claim_info["sources"]:
                        html_content += f"""
                        <div>
                            <p><strong>Document:</strong> {source["document_id"]}</p>
                            <p><strong>Alignment:</strong> {source["alignment_score"]:.2f}</p>
                            <div class="source-excerpt">
                                {source.get("text_excerpt", "No excerpt available")}
                            </div>
                        </div>
                        """
                else:
                    html_content += """
                    <p><strong>Sources:</strong> No supporting sources found</p>
                    """
                
                if "intervention" in claim_info:
                    intervention = claim_info["intervention"]
                    html_content += f"""
                    <div class="intervention">
                        <h4>Recommended Intervention: {intervention["type"]}</h4>
                        <p><strong>Recommendation:</strong> {intervention["recommendation"]}</p>
                        {"<p><strong>Explanation:</strong> " + intervention["explanation"] + "</p>" if "explanation" in intervention and intervention["explanation"] else ""}
                    </div>
                    """
                
                html_content += """
                </div>
                """
        
        html_content += """
                <div class="footer">
                    <p>Generated by HalluciNOT Verification System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _get_confidence_class(self, score: float) -> str:
        """Get the CSS class for a confidence score."""
        if score >= 0.7:
            return "high"
        elif score >= 0.3:
            return "medium"
        else:
            return "low"
    
    def generate_json_report(self, verification_result: VerificationResult) -> str:
        """
        Generate a JSON representation of the verification report.
        
        Args:
            verification_result: The verification result to report on
            
        Returns:
            JSON string with the report data
        """
        report = self.generate_report(verification_result)
        
        # Convert to a dictionary
        report_dict = {
            "overall_confidence": report.overall_confidence,
            "verified_claims_count": report.verified_claims_count,
            "total_claims_count": report.total_claims_count,
            "hallucination_score": report.hallucination_score,
            "verification_summary": report.verification_summary,
            "detailed_claims": report.detailed_claims,
            "generation_timestamp": report.generation_timestamp.isoformat()
        }
        
        # Convert to JSON
        return json.dumps(report_dict, indent=2)