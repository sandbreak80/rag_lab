# Contributing to Ollama Local AI

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)

## 📜 Code of Conduct

This project follows a Code of Conduct that all contributors are expected to adhere to. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## 🤝 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- System information (Mac model, macOS version, RAM)
- Error messages and logs
- Screenshots if applicable

Use the **Bug Report** template when creating issues.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- Use a clear, descriptive title
- Provide detailed description of the proposed feature
- Explain why this enhancement would be useful
- Include examples of how it would be used

Use the **Feature Request** template when creating issues.

### Pull Requests

1. **Fork the repository**
2. **Create a branch** for your feature (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages** (`git commit -m 'Add amazing feature'`)
6. **Push to your branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

## 💻 Development Setup

### Prerequisites

- Mac with Apple Silicon (M1/M2/M3)
- Homebrew
- VS Code (recommended)

### Initial Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ollama-local-ai.git
cd ollama-local-ai

# Install dependencies
pip3 install -r requirements.txt

# Run the setup (optional, for full testing)
./setup.sh
```

### VS Code Setup

Open the workspace file for recommended settings:

```bash
code ollama-local-ai.code-workspace
```

Install recommended extensions when prompted.

## 📝 Submitting Changes

### Commit Messages

Use clear, descriptive commit messages following this format:

```
type: brief description

Longer description if needed.

Fixes #issue_number
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat: add support for additional AI models

docs: update installation instructions for macOS 15

fix: resolve Docker container startup issue on M3 chips
```

### Pull Request Process

1. **Update documentation** if you're changing functionality
2. **Add/update tests** if applicable
3. **Ensure all scripts run** without errors
4. **Update README.md** if adding features
5. **Describe your changes** in the PR description
6. **Link related issues**
7. **Request review** from maintainers

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Tested on Apple Silicon
- [ ] All scripts run successfully
- [ ] Documentation updated
- [ ] No breaking changes

## Related Issues
Fixes #(issue_number)

## Screenshots (if applicable)
```

## 🎨 Style Guidelines

### Python

- Follow **PEP 8**
- Use **black** for formatting (88 char line length)
- Use **type hints** where appropriate
- Add **docstrings** to functions
- Use **meaningful variable names**

```python
def generate_text(prompt: str, model: str = "llama3.1:8b") -> str:
    """
    Generate text using the specified AI model.
    
    Args:
        prompt: The input prompt
        model: The model name (default: llama3.1:8b)
    
    Returns:
        Generated text response
    """
    # Implementation
```

### Shell Scripts

- Use **shellcheck** for linting
- Add comments for complex logic
- Use **set -e** for error handling
- Follow **Google Shell Style Guide**
- Use **descriptive variable names**

```bash
#!/bin/bash
set -e

# Install required dependencies
install_dependencies() {
    local package_name="$1"
    brew install "$package_name"
}
```

### Markdown

- Use **markdownlint** for consistency
- Use **headings** hierarchically
- Add **table of contents** for long documents
- Use **code blocks** with language specification
- Add **alt text** to images

### Documentation

- Keep documentation **up-to-date**
- Use **clear, simple language**
- Include **examples** where helpful
- Add **screenshots** for UI elements
- Maintain **consistent formatting**

## 🧪 Testing

### Before Submitting

Test your changes thoroughly:

```bash
# Test shell scripts
shellcheck *.sh

# Test Python scripts
python3 -m pylint examples/*.py

# Test installation (if modifying setup.sh)
./setup.sh

# Test specific examples
python3 examples/chatbot.py --demo
python3 examples/obsidian_chat.py
```

### Test Checklist

- [ ] Scripts run without errors
- [ ] Documentation is accurate
- [ ] Examples work as described
- [ ] No breaking changes (or documented)
- [ ] Error messages are helpful
- [ ] Code is properly formatted

## 📚 Documentation Guidelines

### What to Document

- **New Features**: Add usage examples
- **API Changes**: Update API_GUIDE.md
- **Setup Changes**: Update SETUP.md
- **Examples**: Add to examples/README.md
- **Configuration**: Document new settings

### Where to Document

| Change Type | Document |
|-------------|----------|
| Installation steps | SETUP.md |
| API usage | API_GUIDE.md |
| Examples | examples/README.md |
| Integration | OBSIDIAN_INTEGRATION.md |
| Project overview | README.md |

## 🏷️ Versioning

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

## 🎁 Recognition

Contributors will be:
- Listed in the project README
- Credited in release notes
- Appreciated in the community!

## ❓ Questions?

- Open an issue with the "question" label
- Check existing documentation first
- Be specific about what you need help with

## 📬 Contact

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Security**: See SECURITY.md

---

Thank you for contributing to Ollama Local AI! 🎉

Your contributions help make local AI accessible to everyone.

