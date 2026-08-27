# Contributing to SpeechScribe

First off, thank you for considering contributing to SpeechScribe! It's people like you that make SpeechScribe such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps to reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed and what behavior you expected**
* **Include error messages if applicable**
* **Include system information** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a detailed description of the suggested enhancement**
* **Explain why this enhancement would be useful**
* **List some examples of how this enhancement would be used**

### Pull Requests

* Fill in the required template
* Follow the Python style guide (PEP 8)
* Include tests for new features
* Update documentation as needed
* Add an entry to the CHANGELOG.md

## Development Setup

### Prerequisites

* Python 3.8 or higher
* pip package manager
* Git

### Setting Up Your Development Environment

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then:
   git clone https://github.com/slam-prog/SpeechScribe.git
   cd SpeechScribe
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Activate on Linux/Mac
   source venv/bin/activate
   
   # Activate on Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

4. **Run tests**
   ```bash
   pytest tests/ -v
   ```

## Coding Guidelines

### Python Style

* Follow [PEP 8](https://pep8.org/)
* Use type hints
* Write docstrings for all public functions
* Keep functions small and focused
* Use meaningful variable names

### Example Function

```python
def calculate_similarity(
    segment_a: np.ndarray,
    segment_b: np.ndarray,
) -> float:
    """
    Calculate similarity between two audio segments.
    
    Args:
        segment_a: First audio segment
        segment_b: Second audio segment
        
    Returns:
        Similarity score between 0 and 1
    """
    # Implementation here
    pass
```

### Testing

* Write tests for all new features
* Maintain or improve code coverage
* Run tests before submitting PR
* Use descriptive test names

```python
def test_segment_extraction():
    """Test that segments are extracted correctly."""
    # Test implementation
    pass
```

### Documentation

* Update README.md if behavior changes
* Add docstrings to new functions
* Update API documentation
* Include examples for new features

## Pull Request Process

1. **Create a branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes**
   - Write code
   - Write tests
   - Update documentation

3. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

5. **Open a Pull Request**
   - Use the PR template
   - Describe your changes
   - Link related issues

6. **Review process**
   - Maintainers will review your PR
   - Address feedback
   - Once approved, it will be merged

## Questions?

Feel free to open an issue for any questions or concerns.

Thank you for contributing! 🎉