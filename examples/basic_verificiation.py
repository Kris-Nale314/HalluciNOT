"""
Basic Verification Example

This example demonstrates how to use HalluciNOT for verifying
an LLM response against a simple document store.
"""

import sys
import os
import logging

# Add the parent directory to the path to access the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hallucinot import (
    VerificationProcessor,
    DocumentChunk,
    DocumentStore,
    BoundaryType,
    highlight_verification_result
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a sample document store
def create_sample_document_store():
    """Create a sample document store for demonstration."""
    chunks = [
        DocumentChunk(
            id="chunk1",
            text="Apple Inc. was founded on April 1, 1976, by Steve Jobs, Steve Wozniak, and Ronald Wayne. The company was established to develop and sell Wozniak's Apple I personal computer.",
            source_document="company_history.txt",
            boundary_type=BoundaryType.PARAGRAPH,
            entities=[
                {"text": "Apple Inc.", "type": "organization"},
                {"text": "April 1, 1976", "type": "date"},
                {"text": "Steve Jobs", "type": "person"},
                {"text": "Steve Wozniak", "type": "person"},
                {"text": "Ronald Wayne", "type": "person"},
                {"text": "Apple I", "type": "product"}
            ]
        ),
        DocumentChunk(
            id="chunk2",
            text="In 2021, Apple's revenue was $365.8 billion, making it one of the world's most valuable companies. The company employs over 147,000 people worldwide.",
            source_document="company_financials.txt",
            boundary_type=BoundaryType.PARAGRAPH,
            entities=[
                {"text": "Apple", "type": "organization"},
                {"text": "2021", "type": "date"},
                {"text": "$365.8 billion", "type": "money"}
            ]
        ),
        DocumentChunk(
            id="chunk3",
            text="The iPhone was first announced by Steve Jobs on January 9, 2007. It was released on June 29, 2007, and multiple revisions have been released since then.",
            source_document="product_history.txt",
            boundary_type=BoundaryType.PARAGRAPH,
            entities=[
                {"text": "iPhone", "type": "product"},
                {"text": "Steve Jobs", "type": "person"},
                {"text": "January 9, 2007", "type": "date"},
                {"text": "June 29, 2007", "type": "date"}
            ]
        ),
        DocumentChunk(
            id="chunk4",
            text="Apple's headquarters, Apple Park, is a circular building in Cupertino, California. It was opened in 2017 and cost approximately $5 billion to build.",
            source_document="company_facilities.txt",
            boundary_type=BoundaryType.PARAGRAPH,
            entities=[
                {"text": "Apple", "type": "organization"},
                {"text": "Apple Park", "type": "location"},
                {"text": "Cupertino, California", "type": "location"},
                {"text": "2017", "type": "date"},
                {"text": "$5 billion", "type": "money"}
            ]
        )
    ]
    
    return DocumentStore(chunks)

def main():
    # Create a sample document store
    document_store = create_sample_document_store()
    print(f"Created document store with {document_store.count} chunks")
    
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
    
    # Create a verification processor
    verifier = VerificationProcessor()
    
    # Verify the LLM response
    print("\nVerifying response...")
    verification_result = verifier.verify(llm_response, document_store)
    
    # Print verification summary
    print("\nVerification Summary:")
    print(f"Overall confidence score: {verification_result.confidence_score:.2f}")
    print(f"Hallucination score: {verification_result.hallucination_score:.2f}")
    print(f"Claims verified: {sum(1 for c in verification_result.claims if c.has_source)}/{len(verification_result.claims)}")
    
    # Print detailed claim information
    print("\nDetailed Claim Analysis:")
    for i, claim in enumerate(verification_result.claims):
        print(f"\nClaim {i+1}: \"{claim.text}\"")
        print(f"  Type: {claim.type.value}")
        print(f"  Confidence: {claim.confidence_score:.2f}")
        
        if claim.has_source:
            print(f"  Source: {claim.best_source.document_id}")
            print(f"  Excerpt: \"{claim.best_source.text_excerpt}\"")
        else:
            print("  Source: No direct source found")
    
    # Generate a highlighted version of the response
    print("\nHighlighted Response (text format):")
    highlighted = highlight_verification_result(verification_result, format="text")
    print(highlighted)
    
    # Generate a corrected response if needed
    if verification_result.hallucination_score > 0.2:
        print("\nGenerating corrected response...")
        from hallucinot.handlers.corrections import generate_corrected_response
        corrected = generate_corrected_response(verification_result, strategy="explanatory")
        print("\nCorrected Response:")
        print(corrected)
    
    # Generate HTML report (typically saved to a file)
    from hallucinot.visualization.reporting import ReportGenerator
    report_generator = ReportGenerator()
    html_report = report_generator.generate_html_report(verification_result)
    
    # Save the HTML report to a file
    with open("verification_report.html", "w") as f:
        f.write(html_report)
    
    print("\nSaved HTML verification report to verification_report.html")

if __name__ == "__main__":
    main()