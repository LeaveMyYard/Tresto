# Tresto 🎭🤖
## Warning: Still in development

**Test + Presto = Tresto**

An AI-powered E2E testing CLI that revolutionizes how you create and maintain automated tests. Inspired by Playwright's codegen but enhanced with intelligent AI agents that don't just record your actions—they understand, analyze, and write robust test code for you.

## ✨ Features

- **🎯 Smart Test Generation**: AI agents that understand your testing intent, not just your clicks
- **🎭 Playwright Integration**: Built on the robust Playwright testing framework
- **🤖 AI-Powered Code Writing**: Intelligent agents that write, run, and iterate on test code
- **🚀 Simple CLI Interface**: Easy-to-use commands for rapid test development
- **📝 Multiple AI Models**: Currently supports Claude-4, with more models coming soon
- **⚙️ Configurable**: Flexible configuration system for different project needs
- **🐍 Python-First**: Generates clean, maintainable Python test code

## 🚀 Quick Start

### Installation

```bash
# Install via pip (coming soon)
pip install tresto

# Or install from source
git clone https://github.com/LeaveMyYard/Tresto.git
cd Tresto
uv sync
```

### Setup Your Project

```bash
# Initialize Tresto in your project
tresto init

# This creates:
# - tests/ directory structure
# - .trestorc configuration file
# - Basic test templates
```

### Record Your First Test

```bash
# Start an interactive test recording session
tresto record

# The CLI will:
# 1. Ask what you want to test and how to name it
# 2. Launch a browser and record your actions
# 3. Have an AI agent write optimized test code
# 4. Run and iterate on the code until it works perfectly
```

## 📋 Requirements

- Python 3.9+
- A modern web browser (Chrome, Firefox, Safari, or Edge)
- Claude API key (set as `ANTHROPIC_API_KEY` environment variable)

## 🛠️ Configuration

After running `tresto init`, edit your `.trestorc` file:

```toml
[project]
name = "my-awesome-app"
base_url = "http://localhost:3000"
test_directory = "./tests"

[browser]
headless = false
timeout = 30000
viewport = { width = 1280, height = 720 }

[ai]
model = "claude-3-5-sonnet-20241022"
max_iterations = 5
temperature = 0.1

[recording]
auto_wait = true
capture_screenshots = true
generate_selectors = "smart"
```

## 📖 Commands

### `tresto init`
Initializes a new Tresto project in the current directory.

**Options:**
- `--force`: Overwrite existing configuration
- `--template`: Use a specific template (default, react, vue, etc.)

### `tresto record`
Starts an interactive test recording session.

**Options:**
- `--name`: Pre-specify the test name
- `--description`: Pre-specify what the test should do
- `--headless`: Run browser in headless mode
- `--iterations`: Maximum AI iterations for code improvement

### `tresto run`
Run existing tests (coming soon).

### `tresto validate`
Validate test code and configuration (coming soon).

## 🏗️ How It Works

1. **Recording Phase**: Tresto launches a Playwright browser and records your interactions
2. **Analysis Phase**: AI agents analyze your actions and understand the testing intent
3. **Code Generation**: AI writes initial test code based on recorded actions and intent
4. **Validation Phase**: The code is executed and analyzed for correctness
5. **Iteration Phase**: AI iteratively improves the code based on execution results
6. **Finalization**: Clean, documented test code is saved to your test directory

## 🎯 Example Generated Test

```python
import pytest
from playwright.async_api import Page, expect

class TestUserLogin:
    """Test user authentication flow"""
    
    async def test_successful_login_redirects_to_dashboard(self, page: Page) -> None:
        """Test that a valid user can log in and is redirected to dashboard"""
        # Navigate to login page
        await page.goto("/login")
        
        # Fill in credentials
        await page.fill('[data-testid="email-input"]', "user@example.com")
        await page.fill('[data-testid="password-input"]', "password123")
        
        # Submit form
        await page.click('[data-testid="login-button"]')
        
        # Verify successful login
        await expect(page).to_have_url("/dashboard")
        await expect(page.locator('[data-testid="welcome-message"]')).to_be_visible()
        await expect(page.locator('[data-testid="user-name"]')).to_contain_text("Welcome")
```

## 🔮 Roadmap

- **Multi-Model Support**: Add support for GPT-4, Gemini, and other AI models
- **Language Support**: Generate tests in TypeScript, JavaScript, and other languages
- **Visual Testing**: AI-powered visual regression testing
- **API Testing**: Extend beyond E2E to API test generation
- **CI/CD Integration**: Built-in support for popular CI/CD platforms
- **Team Features**: Collaborative test development and sharing
- **Premium Features**: Advanced AI models and priority support via subscription

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./docs/CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/LeaveMyYard/Tresto.git
cd Tresto

# Install dependencies with uv
uv sync --dev

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check .
mypy .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Playwright Team**: For creating an amazing browser automation framework
- **Anthropic**: For Claude, the AI that powers our intelligent test generation
- **FastAPI & Typer**: For inspiration on creating developer-friendly CLI tools

## 📞 Support

- 📖 [Documentation](./docs/)
- 🐛 [Issue Tracker](https://github.com/LeaveMyYard/Tresto/issues)
- 💬 [Discussions](https://github.com/LeaveMyYard/Tresto/discussions)

---

**Made with ❤️ by developers, for developers**

*Tresto: Because testing should be as fast as your ideas* ⚡
