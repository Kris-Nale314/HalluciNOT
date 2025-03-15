"""
HalluciNOT Basic Usage Example

This example demonstrates the core functionality of HalluciNOT for
verifying LLM responses against document chunks.
"""
import sys
import os
import logging
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import HalluciNOT
from hallucinot import (
    VerificationProcessor,
    DocumentStore,
    DocumentChunk,
    Claim,
    ClaimType,
    highlight_verification_result
)


def create_sample_documents() -> List[DocumentChunk]:
    """Create sample document chunks for testing."""
    chunks = [
        DocumentChunk(
            id="doc1-chunk1",
            text="The first artificial neural network was developed by Warren McCulloch and Walter Pitts in 1943. Their paper, titled 'A Logical Calculus of the Ideas Immanent in Nervous Activity', proposed a computational model for neural networks based on mathematics and algorithms.",
            source_document="ai_history.txt",
            entities=[
                {"text": "Warren McCulloch", "label": "PERSON"},
                {"text": "Walter Pitts", "label": "PERSON"},
                {"text": "1943", "label": "DATE"}
            ]
        ),
        DocumentChunk(
            id="doc1-chunk2",
            text="Frank Rosenblatt created the perceptron in 1958, which was the first implementation of a trainable artificial neural network. The perceptron was initially implemented as a machine called the Mark 1 Perceptron.",
            source_document="ai_history.txt",
            entities=[
                {"text": "Frank Rosenblatt", "label": "PERSON"},
                {"text": "perceptron", "label": "CONCEPT"},
                {"text": "1958", "label": "DATE"},
                {"text": "Mark 1 Perceptron", "label": "PRODUCT"}
            ]
        ),
        DocumentChunk(
            id="doc2-chunk1",
            text="Transformers were introduced in the paper 'Attention Is All You Need' by Vaswani et al. in 2017. This architecture revolutionized natural language processing and forms the basis for models like GPT and BERT.",
            source_document="transformer_models.txt",
            entities=[
                {"text": "Transformers", "label": "CONCEPT"},
                {"text": "Attention Is All You Need", "label": "WORK_OF_ART"},
                {"text": "Vaswani", "label": "PERSON"},
                {"text": "2017", "label": "DATE"},
                {"text": "GPT", "label": "PRODUCT"},
                {"text": "BERT", "label": "PRODUCT"}
            ]
        ),
        DocumentChunk(
            id="doc2-chunk2",
            text="BERT (Bidirectional Encoder Representations from Transformers) was developed by Google in 2018. It was a significant breakthrough in NLP that allowed models to consider context from both directions in text.",
            source_document="transformer_models.txt",
            entities=[
                {"text": "BERT", "label": "PRODUCT"},
                {"text": "Google", "label": "ORG"},
                {"text": "2018", "label": "DATE"}
            ]
        )
    ]
    
    return chunks


def main():
    # Create sample document chunks
    chunks = create_sample_documents()
    print(f"Created {len(chunks)} sample document chunks")
    
    # Create a document store
    document_store = DocumentStore(chunks)
    
    # Sample LLM response to verify
    llm_response = """
    The history of artificial neural networks began with Warren McCulloch and Walter Pitts in 1943.
    They developed the first computational model based on mathematical algorithms that mimicked neural networks.
    In 1957, Frank Rosenblatt invented the perceptron, which was the first trainable neural network model.
    Later developments include transformers, which were introduced in the paper "Attention Is All You Need" in 2017.
    Google developed BERT in 2019, which was a major breakthrough in bidirectional language understanding.
    Today, neural networks power most advanced AI systems including self-driving cars and medical diagnostics.
    """
    
    print("\nSample LLM response to verify:")
    print(llm_response)
    
    # Create a verification processor
    config = {
        "extractor": {
            "use_spacy": True,  # Set to False if spaCy is not installed
            "enable_entity_extraction": True
        },
        "mapper": {
            "min_alignment_score": 0.5,
            "max_sources_per_claim": 2
        },
        "scorer": {
            "unsupported_claim_score": 0.1
        },
        "intervention": {
            "hallucination_threshold": 0.3,
            "uncertain_threshold": 0.7
        },
        "enable_claim_merging": True
    }
    
    verifier = VerificationProcessor(config)
    
    # Verify the response
    print("\nVerifying response...")
    result = verifier.verify(llm_response, document_store)
    
    # Print verification summary
    print("\nVerification Result:")
    print(f"Overall confidence score: {result.confidence_score:.2f}")
    print(f"Hallucination score: {result.hallucination_score:.2f}")
    print(f"Claims verified: {sum(1 for c in result.claims if c.has_source)}/{len(result.claims)}")
    
    # Print claim details
    print("\nDetailed Claim Analysis:")
    for i, claim in enumerate(result.claims):
        print(f"\nClaim {i+1}: \"{claim.text}\"")
        print(f"  Type: {claim.type.value}")
        print(f"  Confidence: {claim.confidence_score:.2f}")
        
        if claim.has_source:
            print(f"  Source: {claim.best_source.document_id}")
            print(f"  Excerpt: \"{claim.best_source.text_excerpt}\"")
            print(f"  Alignment: {claim.best_source.alignment_score:.2f}")
        else:
            print("  Source: No direct source found")
    
    # Print intervention recommendations
    if result.interventions:
        print("\nRecommended Interventions:")
        for i, intervention in enumerate(result.interventions):
            claim = result.get_claim_by_id(intervention.claim_id)
            print(f"\nIntervention {i+1} for claim: \"{claim.text}\"")
            print(f"  Type: {intervention.intervention_type.value}")
            print(f"  Confidence: {intervention.confidence:.2f}")
            print(f"  Recommendation: {intervention.recommendation}")
    
    # Generate highlighted text
    highlighted = highlight_verification_result(result, format="text")
    print("\nHighlighted Text Output:")
    print(highlighted)
    
    # Generate corrected response
    corrected = verifier.generate_corrected_response(result, strategy="balanced")
    print("\nCorrected Response:")
    print(corrected)
    
    # Generate HTML report
    html_report = verifier.generate_report(result, format="html")
    
    # Save the HTML report to a file
    with open("verification_report.html", "w") as f:
        f.write(html_report)
    
    print("\nSaved HTML verification report to verification_report.html")


if __name__ == "__main__":
    main()