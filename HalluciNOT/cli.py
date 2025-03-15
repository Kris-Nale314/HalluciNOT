# Copyright (c) 2025 Kris Naleszkiewicz
# Licensed under the MIT License - see LICENSE file for details
"""
HalluciNOT Command Line Interface

This module provides a command-line interface for using HalluciNOT
to verify LLM responses against document sources.
"""

import argparse
import json
import logging
import sys
import os
from typing import List, Dict, Any

from .processor import VerificationProcessor
from .utils.common import DocumentStore, DocumentChunk


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)


def load_documents(docs_path: str) -> List[DocumentChunk]:
    """
    Load document chunks from a JSON file.
    
    The file should contain a list of document chunk objects
    with the required fields (id, text, source_document).
    
    Args:
        docs_path: Path to the documents file
        
    Returns:
        List of DocumentChunk objects
    """
    if not os.path.exists(docs_path):
        print(f"Error: Documents file not found: {docs_path}")
        sys.exit(1)
    
    try:
        with open(docs_path, 'r') as f:
            data = json.load(f)
            
        chunks = []
        for item in data:
            # Convert each JSON object to a DocumentChunk
            chunk = DocumentChunk(
                id=item["id"],
                text=item["text"],
                source_document=item["source_document"],
                start_idx=item.get("start_idx", 0),
                end_idx=item.get("end_idx", len(item["text"])),
                metadata=item.get("metadata", {}),
                entities=item.get("entities", [])
            )
            chunks.append(chunk)
        
        return chunks
    except Exception as e:
        print(f"Error loading documents: {e}")
        sys.exit(1)


def load_text(text_path: str) -> str:
    """
    Load text from a file.
    
    Args:
        text_path: Path to the text file
        
    Returns:
        Text content
    """
    if not os.path.exists(text_path):
        print(f"Error: Text file not found: {text_path}")
        sys.exit(1)
    
    try:
        with open(text_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading text: {e}")
        sys.exit(1)


def save_output(output: str, output_path: str):
    """
    Save output to a file.
    
    Args:
        output: Output content
        output_path: Path to save the output
    """
    try:
        with open(output_path, 'w') as f:
            f.write(output)
        print(f"Output saved to {output_path}")
    except Exception as e:
        print(f"Error saving output: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="HalluciNOT: Document-Grounded Verification for LLMs")
    
    parser.add_argument(
        "text",
        help="Path to the text file containing the LLM response to verify"
    )
    
    parser.add_argument(
        "documents",
        help="Path to the JSON file containing document chunks for verification"
    )
    
    parser.add_argument(
        "--config",
        help="Path to the configuration JSON file",
        default=None
    )
    
    parser.add_argument(
        "--output",
        help="Path to save the verification results",
        default=None
    )
    
    parser.add_argument(
        "--format",
        help="Output format (text, html, json)",
        choices=["text", "html", "json"],
        default="text"
    )
    
    parser.add_argument(
        "--correction",
        help="Generate a corrected version of the text",
        action="store_true"
    )
    
    parser.add_argument(
        "--correction-strategy",
        help="Strategy for corrections (conservative, balanced, aggressive)",
        choices=["conservative", "balanced", "aggressive"],
        default="balanced"
    )
    
    parser.add_argument(
        "--report",
        help="Generate a detailed verification report",
        action="store_true"
    )
    
    parser.add_argument(
        "--verbose",
        help="Enable verbose logging",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Load configuration if provided
    config = load_config(args.config) if args.config else {}
    
    # Load documents
    documents = load_documents(args.documents)
    document_store = DocumentStore(documents)
    print(f"Loaded {len(documents)} document chunks")
    
    # Load text to verify
    text = load_text(args.text)
    print(f"Loaded text to verify ({len(text)} characters)")
    
    # Create verifier and run verification
    verifier = VerificationProcessor(config)
    result = verifier.verify(text, document_store)
    
    # Generate output based on format
    if args.format == "text":
        if args.correction:
            # Generate corrected text
            output = verifier.generate_corrected_response(result, args.correction_strategy)
        else:
            # Generate highlighted text
            output = verifier.highlight_verification_result(result, "text")
    
    elif args.format == "html":
        if args.report:
            # Generate HTML report
            output = verifier.generate_report(result, "html")
        else:
            # Generate highlighted HTML
            output = verifier.highlight_verification_result(result, "html")
    
    elif args.format == "json":
        if args.report:
            # Generate JSON report
            output = verifier.generate_report(result, "json")
        else:
            # Generate JSON of the verification result
            output = json.dumps({
                "confidence_score": result.confidence_score,
                "hallucination_score": result.hallucination_score,
                "claims": [
                    {
                        "text": claim.text,
                        "type": claim.type.value,
                        "confidence": claim.confidence_score,
                        "has_source": claim.has_source,
                        "sources": [
                            {
                                "document_id": src.document_id,
                                "chunk_id": src.chunk_id,
                                "alignment": src.alignment_score,
                                "excerpt": src.text_excerpt
                            } for src in claim.sources
                        ] if claim.has_source else []
                    } for claim in result.claims
                ],
                "interventions": [
                    {
                        "claim_id": intervention.claim_id,
                        "type": intervention.intervention_type.value,
                        "confidence": intervention.confidence,
                        "recommendation": intervention.recommendation,
                        "corrected_text": intervention.corrected_text
                    } for intervention in result.interventions
                ]
            }, indent=2)
    
    # Print summary to console
    print("\nVerification Summary:")
    print(f"Overall confidence score: {result.confidence_score:.2f}")
    print(f"Hallucination score: {result.hallucination_score:.2f}")
    print(f"Claims verified: {sum(1 for c in result.claims if c.has_source)}/{len(result.claims)}")
    print(f"Interventions recommended: {len(result.interventions)}")
    
    # Save or print output
    if args.output:
        save_output(output, args.output)
    else:
        print("\nOutput:")
        print(output)


if __name__ == "__main__":
    main()