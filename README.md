<div align="center">
    <img src="docs/images/logo.svg" alt="HalluciNOT Logo" width="200"/>
</div>

[![PyPI version](https://img.shields.io/pypi/v/hallucinot.svg)](https://pypi.org/project/hallucinot/)
[![Python versions](https://img.shields.io/pypi/pyversions/hallucinot.svg)](https://pypi.org/project/hallucinot/)
[![License](https://img.shields.io/github/license/Kris-Nale314/hallucinot)](LICENSE)

# HalluciNOT

## Why HalluciNOT?

**The Trust Problem in AI:** Large Language Models (LLMs) have revolutionized how we interact with information, but they come with a critical flaw - hallucinations. When an LLM confidently presents incorrect information as fact, it undermines trust in AI systems and can lead to serious consequences in high-stakes domains.

**The RAG Gap:** Retrieval-Augmented Generation (RAG) systems attempt to ground LLM outputs in reliable sources, but they often lack rigorous verification mechanisms. The source material is retrieved, but how do we ensure the LLM's claims actually align with it?

**HalluciNOT bridges this gap.**

HalluciNOT is a modular toolkit that systematically verifies LLM outputs against source documents, providing:

- **Precise verification** that maps specific claims to document evidence
- **Quantified confidence scores** for each factual assertion
- **Actionable intervention strategies** when hallucinations are detected
- **Transparent reporting** that builds trust through visibility

Unlike general hallucination detection systems, HalluciNOT is specifically designed for document-grounded applications where source material is available as the ground truth.

## Key Features

<div align="center">
    <img src="docs/images/workflow.svg" alt="HalluciNOT Workflow" width="800"/>
</div>

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

## Quick Start

### Installation

```bash
pip install hallucinot

# Optional: Install spaCy for enhanced claim extraction
pip install spacy
python -m spacy download en_core_web_sm
```

### Basic Usage

```python
from hallucinot import VerificationProcessor, DocumentStore, DocumentChunk

# Create document chunks
chunks = [
    DocumentChunk(
        id="doc1-chunk1",
        text="The Earth orbits the Sun at an average distance of 93 million miles.",
        source_document="astronomy_facts.txt"
    ),
    # Add more document chunks...
]

# Create document store
document_store = DocumentStore(chunks)

# Create verifier
verifier = VerificationProcessor()

# Verify an LLM response
llm_response = "The Earth orbits the Sun at a distance of 90 million miles, completing one orbit every 365.25 days."
result = verifier.verify(llm_response, document_store)

# Print results
print(f"Overall confidence: {result.confidence_score:.2f}")
print(f"Hallucination score: {result.hallucination_score:.2f}")

# Generate highlighted output
highlighted = verifier.highlight_verification_result(result, format="html")

# Generate corrected response
corrected = verifier.generate_corrected_response(result, strategy="balanced")
```

## Business Value

### Risk Mitigation
- Reduce the risk of propagating false information in customer-facing AI applications
- Protect your organization's reputation through verifiable AI claims
- Create audit trails of verification for regulated industries

### Enhanced User Trust
- Provide transparency into the reliability of AI-generated content 
- Allow users to distinguish between verified and unverified information
- Build confidence in your AI systems' outputs

### Operational Efficiency
- Automate the fact-checking process that would otherwise require human review
- Focus reviewer attention only on claims that need human verification
- Reduce the time and cost of manually validating AI outputs

### Competitive Advantage
- Differentiate your AI offerings with superior factual reliability
- Address a key concern that limits enterprise adoption of generative AI
- Demonstrate responsible AI practices to stakeholders

## Integration with RAG Systems

HalluciNOT works seamlessly with [ByteMeSumAI](https://github.com/username/ByteMeSumAI) and other RAG frameworks to create a complete document processing and verification pipeline:

1. Document ingestion and chunking (RAG system)
2. Metadata enrichment and embeddings (RAG system)
3. LLM response generation (RAG system)
4. Claim extraction and verification (HalluciNOT)
5. Confidence scoring and reporting (HalluciNOT)
6. Hallucination correction (HalluciNOT)

## Technical Approach

HalluciNOT uses a modular architecture with specialized components:

1. **Claim Extraction**: Identifies discrete factual assertions in text
2. **Source Mapping**: Maps claims to supporting document chunks
3. **Confidence Scoring**: Calculates alignment scores and confidence metrics
4. **Intervention Selection**: Recommends strategies for handling hallucinations
5. **Visualization**: Generates reports and highlighted outputs

Each component can be configured independently, allowing for customization to specific use cases.

## Status and Roadmap

**Current Status**: Alpha release (v0.1.0)

### Roadmap

1. **Alpha Phase** (Current)
   - Core verification functionality
   - Basic integration capabilities
   - Rule-based and NLP-based claim extraction

2. **Beta Phase** (Q2 2025)
   - Performance optimization
   - Enhanced visualization options
   - Integration with popular RAG frameworks
   - Benchmarking suite

3. **Production Release** (Q3 2025)
   - Full test coverage
   - Comprehensive documentation
   - Pre-trained models for claim extraction
   - Real-world case studies

## Use Cases

- **Enterprise Knowledge Bases**: Verify information extracted from company documents
- **Customer Support**: Ensure accurate responses based on product documentation
- **Legal & Compliance**: Verify claims against regulatory documents
- **Research Analysis**: Ground scientific claims in research papers
- **Educational Content**: Ensure factual accuracy in learning materials
- **Content Creation**: Validate auto-generated content against style guides

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- **Project Link**: [https://github.com/Kris-Nale314/hallucinot](https://github.com/Kris-Nale314/hallucinot)

## Acknowledgments

HalluciNOT is developed as a companion to [ByteMeSumAI](https://github.com/username/ByteMeSumAI) to create a more robust ecosystem for document-grounded AI applications.