# HalluciNOT Quick Start Guide

This guide will help you get started with HalluciNOT for verifying LLM responses against document sources.

<div align="center">
  <img src="hallucinot/docs/images/workflow.svg" alt="HalluciNOT Workflow" width="800"/>
</div>

## Basic Usage

Here's a simple example to verify an LLM response against document sources:

```python
from hallucinot import VerificationProcessor, DocumentStore, DocumentChunk

# 1. Create document chunks
chunks = [
    DocumentChunk(
        id="doc1-para1",
        text="The first artificial neural network was developed by Warren McCulloch and Walter Pitts in 1943.",
        source_document="ai_history.txt"
    ),
    DocumentChunk(
        id="doc1-para2",
        text="Frank Rosenblatt created the perceptron in 1958, which was the first implementation of a trainable neural network.",
        source_document="ai_history.txt"
    )
]

# 2. Create document store
document_store = DocumentStore(chunks)

# 3. Create verifier
verifier = VerificationProcessor()

# 4. Verify an LLM response
llm_response = """
The history of neural networks began with Warren McCulloch and Walter Pitts in 1943.
Frank Rosenblatt developed the perceptron in 1957, the first trainable neural network.
"""

# 5. Run verification
result = verifier.verify(llm_response, document_store)

# 6. Print results
print(f"Overall confidence: {result.confidence_score:.2f}")
print(f"Hallucination score: {result.hallucination_score:.2f}")
print(f"Claims verified: {sum(1 for c in result.claims if c.has_source)}/{len(result.claims)}")

# 7. Generate highlighted output
highlighted = verifier.highlight_verification_result(result, format="text")
print("\nHighlighted Output:")
print(highlighted)

# 8. Generate corrected response
corrected = verifier.generate_corrected_response(result, strategy="balanced")
print("\nCorrected Response:")
print(corrected)
```

## Step-by-Step Walkthrough

### 1. Prepare Your Document Chunks

Document chunks represent the source material that will be used to verify LLM responses. Each chunk should contain:
- A unique ID
- The text content
- Source document identifier
- Optional metadata and entities

```python
from hallucinot import DocumentChunk

chunk = DocumentChunk(
    id="unique-id",
    text="Chunk text content",
    source_document="source-document-name",
    # Optional attributes
    metadata={"key": "value"},
    entities=[{"text": "Entity Name", "label": "PERSON"}]
)
```

### 2. Create a Document Store

The `DocumentStore` holds all your document chunks and provides retrieval functionality:

```python
from hallucinot import DocumentStore

document_store = DocumentStore(chunks)
```

### 3. Configure the Verification Processor

The `VerificationProcessor` is the main interface for verification. You can customize its behavior:

```python
from hallucinot import VerificationProcessor

# Default configuration
verifier = VerificationProcessor()

# With custom configuration
config = {
    "extractor": {
        "use_spacy": True,
        "enable_entity_extraction": True
    },
    "mapper": {
        "min_alignment_score": 0.6,
        "max_sources_per_claim": 3
    },
    "scorer": {
        "unsupported_claim_score": 0.1
    },
    "intervention": {
        "hallucination_threshold": 0.3
    },
    "enable_claim_merging": True
}

custom_verifier = VerificationProcessor(config)
```

### 4. Verify LLM Responses

Call the `verify` method to check an LLM response against your document store:

```python
result = verifier.verify(llm_response, document_store)
```

### 5. Analyze Results

The verification result contains detailed information about the claims, sources, and confidence scores:

```python
# Print overall metrics
print(f"Overall confidence: {result.confidence_score:.2f}")
print(f"Hallucination score: {result.hallucination_score:.2f}")

# Examine individual claims
for claim in result.claims:
    print(f"Claim: {claim.text}")
    print(f"  Type: {claim.type.value}")
    print(f"  Confidence: {claim.confidence_score:.2f}")
    
    if claim.has_source:
        print(f"  Source: {claim.best_source.document_id}")
        print(f"  Excerpt: {claim.best_source.text_excerpt}")
    else:
        print("  No source found")
```

### 6. Generate Outputs

HalluciNOT provides several ways to visualize and utilize verification results:

```python
# Generate highlighted text (format can be "text", "html", or "markdown")
highlighted = verifier.highlight_verification_result(result, format="html")

# Generate a corrected version (strategy can be "conservative", "balanced", or "aggressive")
corrected = verifier.generate_corrected_response(result, strategy="balanced")

# Generate a detailed report (format can be "html", "json", or "object")
report = verifier.generate_report(result, format="html")

# Save outputs to files
with open("highlighted.html", "w") as f:
    f.write(highlighted)

with open("report.html", "w") as f:
    f.write(report)
```

## Using the Command Line Interface

HalluciNOT includes a command-line interface for quick verification tasks:

```bash
# Basic usage
hallucinot response.txt documents.json --format text

# With correction
hallucinot response.txt documents.json --correction --format text

# Generate HTML report
hallucinot response.txt documents.json --report --format html --output report.html

# With custom configuration
hallucinot response.txt documents.json --config config.json --format html
```

## ByteMeSumAI Integration

If you have ByteMeSumAI installed, you can use the integration features:

```python
from hallucinot import (
    ByteMeSumAIAdapter, 
    ByteMeSumAIDocumentStore, 
    VerificationProcessor
)

# Using ByteMeSumAI document chunks
adapter = ByteMeSumAIAdapter()
bytemesumai_chunks = [...]  # Your ByteMeSumAI chunks
hallucinot_chunks = adapter.convert_chunks(bytemesumai_chunks)

# Or create a document store directly
document_store = ByteMeSumAIDocumentStore(bytemesumai_chunks=bytemesumai_chunks)

# Verify as usual
verifier = VerificationProcessor()
result = verifier.verify(llm_response, document_store)
```

## Next Steps

For more detailed information, see:
- [Configuration Guide](configuration.md)
- [API Reference](api-reference.md)
- [Advanced Usage](advanced-usage.md)
- [Examples](examples.md)