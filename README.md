# HalluciNOT

![HalluciNOT Logo](docs/assets/hallucinot_logo.png)

[![PyPI version](https://img.shields.io/pypi/v/hallucinot.svg)](https://pypi.org/project/hallucinot/)
[![Python Versions](https://img.shields.io/pypi/pyversions/hallucinot.svg)](https://pypi.org/project/hallucinot/)
[![License](https://img.shields.io/pypi/l/hallucinot.svg)](https://github.com/username/hallucinot/blob/main/LICENSE)

## Document-Grounded Verification for Large Language Models

HalluciNOT is a modular toolkit for detecting, measuring, and mitigating hallucinations in LLM outputs when working with document-based content. It leverages rich document structure and metadata to efficiently verify LLM-generated content against source materials, ensuring factual consistency and appropriate uncertainty communication.

```python
from hallucinot import VerificationProcessor

# Create verification processor
verifier = VerificationProcessor()

# Verify LLM response against document sources
verification_result = verifier.verify(
    llm_response="The company reported revenue of $12.5M in Q2 2023.", 
    document_store=document_collection
)

# Get verification report
report = verification_result.generate_report()
print(f"Overall confidence score: {report.confidence_score}")
print(f"Verified claims: {report.verified_claims_count}/{report.total_claims_count}")
```

## Why HalluciNOT?

LLMs are powerful but prone to hallucinations - generating content that seems plausible but is factually incorrect or unsupported by source documents. In document-grounded applications like RAG systems, these hallucinations undermine trust and reliability.

HalluciNOT addresses this challenge by:

- **Tracing claims back to source**: Mapping LLM assertions to specific document locations
- **Measuring factual alignment**: Quantifying how well claims match their source material
- **Detecting unsupported content**: Identifying claims without sufficient grounding
- **Managing hallucinations**: Providing strategies to handle detected inaccuracies

## Core Features

### 🔍 Claim Detection and Source Mapping
- Extract discrete factual assertions from LLM outputs
- Map claims back to specific document chunks using metadata
- Calculate semantic alignment between claims and sources
- Identify unsupported or misaligned claims

### 📊 Confidence Scoring System
- Quantify alignment between claims and source material
- Provide multi-dimensional confidence metrics for different claim types
- Generate consolidated trustworthiness assessments for responses
- Calibrate confidence scores based on evidence strength

### 🛠️ Hallucination Management
- Select appropriate interventions for detected inaccuracies
- Generate corrections grounded in source material
- Implement standardized uncertainty communication patterns
- Maintain conversation flow while addressing factual issues

### 📈 Visualization and Reporting
- Highlight confidence levels within responses
- Create clear source attributions and citations
- Generate detailed verification reports
- Monitor hallucination patterns over time

## Integration with ByteMeSumAI

HalluciNOT is designed to work seamlessly with [ByteMeSumAI](https://github.com/username/ByteMeSumAI), leveraging its document processing pipeline:

1. ByteMeSumAI handles document ingestion, processing, and metadata enrichment
2. HalluciNOT defines additional metadata requirements for verification purposes
3. Together they create a robust pipeline for accurate, verifiable document-based AI interactions

```python
from bytemesumai import Document, ChunkingProcessor
from hallucinot import VerificationProcessor, VerificationMetadataEnricher

# Process document with ByteMeSumAI
doc = Document.from_file("complex_document.pdf")
chunker = ChunkingProcessor()
chunks = chunker.chunk_text_boundary_aware(doc.content)

# Enrich chunks with verification metadata
enricher = VerificationMetadataEnricher()
verification_ready_chunks = enricher.enrich_chunks(chunks)

# Later, verify LLM response against these chunks
verifier = VerificationProcessor()
verification_result = verifier.verify(llm_response, verification_ready_chunks)
```

## Getting Started

### Installation

```bash
pip install hallucinot
```

### Basic Usage

```python
from hallucinot import ClaimExtractor, SourceMapper, ConfidenceScorer

# Extract claims from LLM response
extractor = ClaimExtractor()
claims = extractor.extract_claims("The report indicates a 15% increase in Q3 sales.")

# Map claims to document sources
mapper = SourceMapper()
mapped_claims = mapper.map_to_sources(claims, document_store)

# Score claim confidence
scorer = ConfidenceScorer()
scored_claims = scorer.score_claims(mapped_claims)

# Generate verification report
for claim in scored_claims:
    print(f"Claim: {claim.text}")
    print(f"Confidence: {claim.confidence_score}")
    print(f"Source: {claim.source_reference}")
```

### Advanced Usage

See our [documentation](https://hallucinot.readthedocs.io/) for advanced usage scenarios, integration examples, and customization options.

## File Structure

```
hallucinot/
├── __init__.py
├── claim_extraction/
│   ├── __init__.py
│   ├── extractor.py       # Core claim extraction logic
│   └── models.py          # Claim data structures
├── source_mapping/
│   ├── __init__.py
│   ├── mapper.py          # Source mapping algorithms
│   └── scoring.py         # Alignment scoring functions
├── confidence/
│   ├── __init__.py
│   ├── scorer.py          # Confidence scoring system
│   └── calibration.py     # Confidence calibration utilities
├── visualization/
│   ├── __init__.py
│   ├── highlighter.py     # Text highlighting utilities
│   └── reporting.py       # Report generation
├── handlers/
│   ├── __init__.py
│   ├── strategies.py      # Intervention strategy selection
│   └── corrections.py     # Correction generation utilities
├── integration/
│   ├── __init__.py
│   ├── bytemesumai.py     # ByteMeSumAI integration
│   └── metadata.py        # Metadata enrichment utilities
├── utils/
│   ├── __init__.py
│   └── common.py          # Shared utilities
└── processor.py           # Main verification processor
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

HalluciNOT is developed as a companion to [ByteMeSumAI](https://github.com/username/ByteMeSumAI) to create a more robust ecosystem for document-grounded AI applications.