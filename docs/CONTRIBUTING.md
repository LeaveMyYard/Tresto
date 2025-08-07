# Contributing to Tresto

Thank you for your interest in contributing to Tresto! We welcome contributions from the community.

## 🛠️ Development Setup

### Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) for dependency management
- Node.js (for Playwright browser installation)

### Setup Steps

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Tresto.git
   cd Tresto
   ```

2. **Install dependencies**
   ```bash
   uv sync --dev
   ```

3. **Install Playwright browsers**
   ```bash
   uv run playwright install
   ```

4. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

5. **Set up environment variables**
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

## 🧪 Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_example.py

# Run with coverage
uv run pytest --cov=src/tresto
```

## 📋 Code Quality

We use several tools to maintain code quality:

### Linting and Formatting

```bash
# Run ruff for linting
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Format code with black
uv run black .

# Type checking with mypy
uv run mypy .
```

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:
- Black (code formatting)
- Ruff (linting)
- MyPy (type checking)
- Pytest (basic tests)

## 🚀 Making Changes

### Branch Strategy

1. Create a feature branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

3. Push to your fork and create a pull request
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### Code Style Guidelines

1. **Python Code Style**
   - Follow PEP 8
   - Use type hints for all functions
   - Maximum line length: 120 characters
   - Use descriptive variable and function names

2. **Documentation**
   - Add docstrings to all public functions and classes
   - Use Google-style docstrings
   - Update README.md if adding new features

3. **Testing**
   - Write tests for new features
   - Maintain test coverage above 80%
   - Use descriptive test names

## 📝 Pull Request Process

1. **Ensure your PR**:
   - Has a clear title and description
   - References any related issues
   - Includes tests for new functionality
   - Updates documentation if needed
   - Passes all CI checks

2. **PR Template**:
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement

   ## Testing
   - [ ] Tests pass locally
   - [ ] New tests added for new functionality

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   ```

## 🐛 Reporting Issues

When reporting issues, please include:

1. **Environment details**:
   - OS and version
   - Python version
   - Tresto version

2. **Steps to reproduce**:
   - Clear, numbered steps
   - Expected vs actual behavior
   - Error messages or logs

3. **Additional context**:
   - Screenshots if applicable
   - Configuration files
   - Sample test cases

## 💡 Feature Requests

We welcome feature requests! Please:

1. Search existing issues first
2. Provide a clear use case
3. Explain the expected behavior
4. Consider implementation complexity

## 🎯 Areas for Contribution

### High Priority
- Additional AI model support (GPT-4, Gemini)
- Better error handling and recovery
- Test code optimization algorithms
- More selector strategies

### Medium Priority
- TypeScript test generation
- Visual regression testing
- API test recording
- Browser extension for recording

### Documentation
- More usage examples
- Video tutorials
- Best practices guide
- Performance optimization tips

## 🤝 Community

- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Use GitHub Issues for bugs and feature requests
- **Code Review**: All contributors can review PRs

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for helping make Tresto better! 🚀
