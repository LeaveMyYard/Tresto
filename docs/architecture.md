# Project Architecture

This document provides an overview of Tresto's architecture and design decisions.

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Tresto CLI                          │
├─────────────────────────────────────────────────────────────┤
│  Commands Layer                                             │
│  ├── init.py (Project setup)                               │
│  ├── record.py (Recording & AI generation)                 │
│  └── run.py (Test execution) [Future]                      │
├─────────────────────────────────────────────────────────────┤
│  Core Layer                                                 │
│  ├── config.py (Configuration management)                  │
│  ├── recorder.py (Browser recording)                       │
│  └── templates.py (Test templates) [Future]                │
├─────────────────────────────────────────────────────────────┤
│  AI Layer                                                   │
│  ├── agent.py (Test generation agent)                      │
│  ├── models.py (AI model adapters) [Future]                │
│  └── prompts.py (Prompt templates) [Future]                │
├─────────────────────────────────────────────────────────────┤
│  External Dependencies                                      │
│  ├── Playwright (Browser automation)                       │
│  ├── Anthropic Claude (AI generation)                      │
│  ├── Typer (CLI framework)                                 │
│  └── Rich (Terminal UI)                                    │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Package Structure

```
src/tresto/
├── __init__.py              # Package version and metadata
├── cli.py                   # Main CLI application entry point
├── commands/                # CLI command implementations
│   ├── __init__.py
│   ├── init.py             # Project initialization
│   └── record.py           # Recording and generation
├── core/                    # Core functionality
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   └── recorder.py         # Browser recording logic
└── ai/                      # AI-related functionality
    ├── __init__.py
    ├── agent.py            # Test generation agent
    └── models.py           # AI model abstractions [Future]
```

## 🔄 Data Flow

### Recording Session Flow

1. **Initialization**
   ```
   User runs `tresto record`
   ↓
   Load configuration from .trestorc
   ↓
   Validate API keys and dependencies
   ↓
   Prompt user for test details
   ```

2. **Recording Phase**
   ```
   Launch Playwright browser
   ↓
   Inject JavaScript event listeners
   ↓
   User performs actions in browser
   ↓
   Capture clicks, inputs, navigation
   ↓
   Store action data with timestamps
   ```

3. **AI Generation Phase**
   ```
   Process recorded actions
   ↓
   Generate Claude API prompt
   ↓
   Call Claude for initial code generation
   ↓
   Iterate with analysis and improvements
   ↓
   Return final test code
   ```

4. **Finalization**
   ```
   Save generated test to file
   ↓
   Optionally run test validation
   ↓
   Display results to user
   ```

## 🎯 Design Principles

### 1. **Modularity**
- Each component has a single responsibility
- Clear interfaces between layers
- Easy to test and maintain individual components

### 2. **Extensibility**
- Plugin architecture for AI models (future)
- Configurable templates and strategies
- Support for multiple programming languages (future)

### 3. **User Experience**
- Rich terminal UI with clear feedback
- Intuitive CLI commands
- Helpful error messages and guidance

### 4. **Reliability**
- Robust error handling
- Graceful degradation
- Input validation and sanitization

## 🔧 Key Components

### Configuration System (`core/config.py`)

```python
class TrestoConfig(BaseModel):
    project: ProjectConfig
    browser: BrowserConfig  
    ai: AIConfig
    recording: RecordingConfig
```

**Responsibilities:**
- Load/save configuration from `.trestorc`
- Validate configuration values
- Provide defaults for missing values
- Environment variable integration

### Browser Recorder (`core/recorder.py`)

```python
class BrowserRecorder:
    async def start_recording(url: str) -> Dict[str, Any]
    async def _setup_event_listeners() -> None
    async def _wait_for_user_completion() -> None
```

**Responsibilities:**
- Launch and configure Playwright browser
- Inject JavaScript for action capture
- Process and normalize recorded actions
- Handle browser lifecycle

### AI Agent (`ai/agent.py`)

```python
class TestGenerationAgent:
    async def generate_test(...) -> str
    def _create_generation_prompt(...) -> str
    def _create_analysis_prompt(...) -> str
    def _create_improvement_prompt(...) -> str
```

**Responsibilities:**
- Generate initial test code from actions
- Analyze and improve generated code
- Manage API calls to Claude
- Handle prompt engineering

## 🔌 Extension Points

### 1. **AI Model Support**
```python
# Future: ai/models/base.py
class AIModel(ABC):
    @abstractmethod
    async def generate_code(prompt: str) -> str
    
# ai/models/claude.py
class ClaudeModel(AIModel): ...

# ai/models/gpt.py  
class GPTModel(AIModel): ...
```

### 2. **Language Templates**
```python
# Future: core/templates/
class TestTemplate(ABC):
    @abstractmethod
    def generate_test(actions: List[Action]) -> str

class PythonPlaywrightTemplate(TestTemplate): ...
class TypeScriptPlaywrightTemplate(TestTemplate): ...
```

### 3. **Selector Strategies**
```python
# Future: core/selectors/
class SelectorStrategy(ABC):
    @abstractmethod
    def get_selector(element_data: Dict) -> str

class DataTestIdStrategy(SelectorStrategy): ...
class XPathStrategy(SelectorStrategy): ...
```

## 📊 Performance Considerations

### 1. **Browser Recording**
- Minimal JavaScript injection
- Efficient event handling
- Asynchronous action processing

### 2. **AI Generation**
- Batch API calls when possible
- Token usage optimization
- Caching for repeated patterns

### 3. **File I/O**
- Atomic writes for configuration
- Efficient test file generation
- Temporary file cleanup

## 🔒 Security Considerations

### 1. **API Keys**
- Environment variable storage only
- No key logging or persistence
- Secure transmission to AI services

### 2. **Browser Security**
- Sandboxed browser instances
- No persistent data storage
- Controlled JavaScript injection

### 3. **File System**
- Validate file paths
- Restrict write permissions
- Clean up temporary files

## 🚀 Future Architecture Enhancements

### 1. **Plugin System**
```python
class TrestoPlugin(ABC):
    @abstractmethod
    def register(app: TrestoApp) -> None
```

### 2. **Distributed Recording**
- Remote browser support
- Cloud-based AI processing
- Team collaboration features

### 3. **Advanced AI Features**
- Visual element recognition
- Test maintenance suggestions
- Performance optimization hints

### 4. **Integration Platform**
- CI/CD pipeline integration
- IDE extensions
- Test reporting dashboard

## 🔍 Monitoring and Observability

### 1. **Logging Strategy**
- Structured logging with rich
- Configurable log levels
- Error tracking and reporting

### 2. **Metrics Collection**
- Recording session statistics
- AI generation performance
- User interaction patterns

### 3. **Error Handling**
- Graceful error recovery
- User-friendly error messages
- Debug information collection
