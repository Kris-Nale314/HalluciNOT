# HalluciNOT Installation Guide

This guide will help you install and set up HalluciNOT for verifying LLM responses against document sources.

## System Requirements

- Python 3.8 or higher
- 2GB+ RAM (4GB+ recommended for processing larger documents)
- Operating Systems: Windows, macOS, or Linux

## Installation Methods

### Method 1: Install from PyPI (Recommended)

The simplest way to install HalluciNOT is using pip:

```bash
pip install hallucinot
```

For enhanced claim extraction capabilities, install spaCy and its English model:

```bash
pip install hallucinot[nlp]  # Installs HalluciNOT with spaCy dependencies
python -m spacy download en_core_web_sm
```

### Method 2: Install from Source

If you prefer to install from source or want the latest development version:

```bash
git clone https://github.com/Kris-Nale314/hallucinot.git
cd hallucinot
pip install -e .
```

For development with additional tools:

```bash
pip install -e .[dev]  # Includes testing and development tools
```

## Optional Dependencies

HalluciNOT has several optional dependency groups that enable additional functionality:

### NLP Features
```bash
pip install hallucinot[nlp]
```
- Enables enhanced claim extraction using spaCy
- Improves entity recognition and claim type classification

### Visualization
```bash
pip install hallucinot[visualizations]
```
- Adds advanced data visualization capabilities
- Enables custom report generation

### ByteMeSumAI Integration
```bash
pip install hallucinot[bytemesumai]
```
- Adds integration with ByteMeSumAI for document processing
- Enables metadata enrichment for verification

### All Features
```bash
pip install hallucinot[all]
```
- Installs all optional dependencies

## Verifying Installation

You can verify your installation by running the following Python code:

```python
import hallucinot

# Print the version
print(f"HalluciNOT version: {hallucinot.__version__}")

# Check if NLP features are available
if hasattr(hallucinot, "__has_spacy__"):
    print("NLP features: Available")
else:
    print("NLP features: Not available (install with pip install hallucinot[nlp])")

# Check if ByteMeSumAI integration is available
if hasattr(hallucinot, "__has_bytemesumai__"):
    print("ByteMeSumAI integration: Available")
else:
    print("ByteMeSumAI integration: Not available (install with pip install hallucinot[bytemesumai])")
```

## Troubleshooting

### Common Installation Issues

#### Missing NLP Models

If you see an error like:
```
[E050] Can't find model 'en_core_web_sm'. It doesn't seem to be a Python package or a valid path to a data directory.
```

Install the spaCy model:
```bash
python -m spacy download en_core_web_sm
```

#### ImportError for Optional Dependencies

If you see an error like:
```
ImportError: No module named 'spacy'
```

Install the missing dependency:
```bash
pip install hallucinot[nlp]
```

#### Version Conflicts

If you encounter package version conflicts, try using a virtual environment:

```bash
python -m venv hallucinot-env
source hallucinot-env/bin/activate  # On Windows: hallucinot-env\Scripts\activate
pip install hallucinot
```

## Next Steps

After installing HalluciNOT, see the [Quick Start Guide](quickstart.md) for instructions on how to start verifying LLM responses.

## Getting Help

If you encounter any issues that aren't covered in this guide:
- Check the [GitHub Issues](https://github.com/Kris-Nale314/hallucinot/issues) for known problems
