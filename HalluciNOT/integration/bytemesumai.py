# Copyright (c) 2025 Kris Naleszkiewicz
# Licensed under the MIT License - see LICENSE file for details
"""
ByteMeSumAI Integration Example

This example demonstrates how to integrate HalluciNOT with ByteMeSumAI
for verifying LLM responses against document chunks processed by ByteMeSumAI.
"""

import sys
import os
import logging
from typing import List, Dict, Any, Optional

# Add the parent directory to the path to access the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hallucinot import (
    VerificationProcessor,
    ByteMeSumAIAdapter,
    VerificationMetadataEnricher,
    ByteMeSumAIDocumentStore,
    highlight_verification_result
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Mock ByteMeSumAI classes for demonstration purposes
# In a real application, you would import these from the ByteMeSumAI package
class MockByteMeSumAIChunk:
    """Mock class representing a ByteMeSumAI chunk."""
    
    def __init__(self, id, text, document_id, metadata=None, entities=None):
        self.id = id
        self.text = text
        self.document_id = document_id
        self.start_idx = 0  # Simplified for demo
        self.end_idx = len(text)  # Simplified for demo
        self.metadata = metadata or {}
        self.entities = entities or []

class MockByteMeSumAIDocument:
    """Mock class representing a ByteMeSumAI document."""
    
    def __init__(self, id, title, chunks=None):
        self.id = id
        self.title = title
        self.chunks = chunks or []
    
    def get_chunks(self):
        return self.chunks

# Create a sample ByteMeSumAI document
def create_sample_bytemesumai_document():
    """Create a sample ByteMeSumAI document for demonstration."""
    
    # Create sample chunks
    chunks = [
        MockByteMeSumAIChunk(
            id="chunk1",
            text="Apple Inc. was founded on April 1, 1976, by Steve Jobs, Steve Wozniak, and Ronald Wayne. The company was established to develop and sell Wozniak's Apple I personal computer.",
            document_id="company_history.txt",
            metadata={
                "boundary_type": "paragraph",
                "parent_section": "company_founding"
            },
            entities=[
                {"text": "Apple Inc.", "type": "organization"},
                {"text": "April 1, 1976", "type": "date"},
                {"text": "Steve Jobs", "type": "person"},
                {"text": "Steve Wozniak", "type": "person"},
                {"text": "Ronald Wayne", "type": "person"},
                {"text": "Apple I", "type": "product"}
            ]
        ),
        MockByteMeSumAIChunk(
            id="chunk2",
            text="In 2021, Apple's revenue was $365.8 billion, making it one of the world's most valuable companies. The company employs over 147,000 people worldwide.",
            document_id="company_financials.txt",
            metadata={
                "boundary_type": "paragraph",
                "parent_section": "financial_performance"
            },
            entities=[
                {"text": "Apple", "type": "organization"},
                {"text": "2021", "type": "date"},
                {"text": "$365.8 billion", "type": "money"}
            ]
        ),
        MockByteMeSumAIChunk(
            id="chunk3",
            text="The iPhone was first announced by Steve Jobs on January 9, 2007. It was released on June 29, 2007, and multiple revisions have been released since then.",
            document_id="product_history.txt",
            metadata={
                "boundary_type": "paragraph",
                "parent_section": "iphone_development"
            },
            entities=[
                {"text": "iPhone", "type": "product"},
                {"text": "Steve Jobs", "type": "person"},
                {"text": "January 9, 2007", "type": "date"},
                {"text": "June 29, 2007", "type": "date"}
            ]
        ),
        MockByteMeSumAIChunk(
            id="chunk4",
            text="Apple's headquarters, Apple Park, is a circular building in Cupertino, California. It was opened in 2017 and cost approximately $5 billion to build.",
            document_id="company_facilities.txt",
            metadata={
                "boundary_type": "paragraph",
                "parent_section": "headquarters"
            },
            entities=[
                {"text": "Apple", "type": "organization"},
                {"text": "Apple Park", "type": "location"},
                {"text": "Cupertino, California", "type": "location"},
                {"text": "2017", "type": "date"},
                {"text": "$5 billion", "type": "money"}
            ]
        )
    ]
    
    # Create the document
    document = MockByteMeSumAIDocument(
        id="apple_company_profile",
        title="Apple Inc. Company Profile",
        chunks=chunks
    )
    
    return document

def main():
    # Create a sample ByteMeSumAI document
    bytemesumai_document = create_sample_bytemesumai_document()
    print(f"Created ByteMeSumAI document with {len(bytemesumai_document.chunks)} chunks")
    
    # Sample LLM response to verify
    llm_response = """
    Apple Inc. was founded on April 1, 1976, by Steve Jobs, Steve Wozniak, and Ronald Wayne.
    In 2022, Apple's revenue was $378 billion, showing continued growth from previous years.
    The iPhone was first announced in January 2007 and released in June of the same year.
    The Apple Park headquarters in Cupertino cost about $4 billion to construct and was completed in 2017.
    The company has over 150,000 employees worldwide as of 2023.
    """
    
    print("\nSample LLM response to verify:")
    print(llm_response)
    
    # Method 1: Using ByteMeSumAIAdapter
    print("\nMethod 1: Using ByteMeSumAIAdapter")
    adapter = ByteMeSumAIAdapter()
    hallucinot_chunks = adapter.convert_chunks(bytemesumai_document.chunks)
    document_store = ByteMeSumAIDocumentStore(bytemesumai_chunks=bytemesumai_document.chunks)
    
    # Create a verification processor
    verifier = VerificationProcessor()
    
    # Verify the LLM response
    print("Verifying response...")
    verification_result = verifier.verify(llm_response, document_store)
    
    # Print verification summary
    print("\nVerification Summary:")
    print(f"Overall confidence score: {verification_result.confidence_score:.2f}")
    print(f"Hallucination score: {verification_result.hallucination_score:.2f}")
    print(f"Claims verified: {sum(1 for c in verification_result.claims if c.has_source)}/{len(verification_result.claims)}")
    
    # Method 2: Using VerificationMetadataEnricher for enhanced verification
    print("\nMethod 2: Using VerificationMetadataEnricher")
    enricher = VerificationMetadataEnricher(config={
        "add_claim_type_hints": True,
        "add_source_reliability": True,
        "add_cross_references": True
    })
    
    # Enrich the chunks with verification metadata
    enriched_chunks = enricher.enrich_chunks(bytemesumai_document.chunks)
    enriched_document_store = ByteMeSumAIDocumentStore(bytemesumai_document=bytemesumai_document)
    
    # Create a verification processor with custom configuration
    enhanced_verifier = VerificationProcessor(
        config={
            "auto_generate_report": True
        }
    )
    
    # Verify the LLM response with enhanced metadata
    print("Verifying response with enhanced metadata...")
    enhanced_verification_result = enhanced_verifier.verify(llm_response, enriched_document_store)
    
    # Print enhanced verification summary
    print("\nEnhanced Verification Summary:")
    print(f"Overall confidence score: {enhanced_verification_result.confidence_score:.2f}")
    print(f"Hallucination score: {enhanced_verification_result.hallucination_score:.2f}")
    print(f"Claims verified: {sum(1 for c in enhanced_verification_result.claims if c.has_source)}/{len(enhanced_verification_result.claims)}")
    
    # Print detailed claim information for enhanced verification
    print("\nDetailed Claim Analysis (Enhanced):")
    for i, claim in enumerate(enhanced_verification_result.claims):
        print(f"\nClaim {i+1}: \"{claim.text}\"")
        print(f"  Type: {claim.type.value}")
        print(f"  Confidence: {claim.confidence_score:.2f}")
        
        if claim.has_source:
            print(f"  Source: {claim.best_source.document_id}")
            print(f"  Excerpt: \"{claim.best_source.text_excerpt}\"")
            
            # Print any additional metadata from enrichment
            if claim.best_source.context:
                print(f"  Additional context: {claim.best_source.context}")
        else:
            print("  Source: No direct source found")
    
    # Generate a highlighted version of the response
    print("\nHighlighted Response (text format):")
    highlighted = highlight_verification_result(enhanced_verification_result, format="text")
    print(highlighted)
    
    # Generate a corrected response
    from hallucinot.handlers.corrections import generate_corrected_response
    corrected = generate_corrected_response(enhanced_verification_result, strategy="explanatory")
    print("\nCorrected Response:")
    print(corrected)
    
    # Generate HTML report
    from hallucinot.visualization.reporting import ReportGenerator
    report_generator = ReportGenerator()
    html_report = report_generator.generate_html_report(enhanced_verification_result)
    
    # Save the HTML report to a file
    with open("enhanced_verification_report.html", "w") as f:
        f.write(html_report)
    
    print("\nSaved HTML verification report to enhanced_verification_report.html")

if __name__ == "__main__":
    main()