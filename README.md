# SSMIS - Local LLM Chat Interface

A powerful local LLM chat application with support for Ollama and LM Studio models, featuring a modern PyQt5 interface, TTS integration, and GPU acceleration.

## Features

- 🤖 **Multi-Model Support**: Seamlessly switch between Ollama and LM Studio models without restart
- 💬 **Chat Interface**: Modern dark-themed chat window with message history
- 🔊 **TTS Integration**: OpenAI-compatible Text-to-Speech for voice output
- 💾 **Persistent Context**: MCP memory server connector for maintaining conversation context
- 🖥️ **System Tray**: Minimize to system tray for background operation
- ⚡ **GPU Acceleration**: CUDA 12.1/12.8 support for faster inference
- 🔧 **Configurable**: Comprehensive settings for ports, models, and preferences
- 📁 **Chat History**: Save and browse previous conversations

## Requirements

- Python 3.11+
- PyQt5
- aiohttp
- Optional: NVIDIA GPU with CUDA 12.1 or 12.8 for GPU acceleration

## Installation

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/tevasauksinis1-ctrl/SSMIS.git
cd SSMIS

# Run the setup script (creates isolated Python 3.11 environment)
chmod +x setup_env.sh
./setup_env.sh
```

### Manual Installation

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For CUDA 12.1 support
pip install torch --index-url https://download.pytorch.org/whl/cu121

# For CUDA 12.8 support
pip install torch --index-url https://download.pytorch.org/whl/cu128
```

## Usage

### Starting the Application

```bash
# Using the launcher
~/.llm_chat/run.sh

# Or manually
python -m llm_chat

# Start minimized to system tray
python -m llm_chat --minimized

# Enable debug logging
python -m llm_chat --debug

# Use custom config file
python -m llm_chat --config /path/to/config.json
```

### Prerequisites

Before using LLM Chat, ensure you have one of the following running:

1. **Ollama** (default port 11434):
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Pull a model
   ollama pull llama2
   
   # Start Ollama
   ollama serve
   ```

2. **LM Studio** (default port 1234):
   - Download from [lmstudio.ai](https://lmstudio.ai)
   - Load a model and start the local server

### Optional: TTS Service

For text-to-speech functionality, you need an OpenAI-compatible TTS server:

```bash
# Example using xtts-api-server
pip install xtts-api-server
xtts-api-server --port 8000
```

## Configuration

Configuration is stored at `~/.llm_chat/config.json`. You can also access settings through the application's Settings dialog (Edit → Settings).

### Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `ports.ollama` | 11434 | Ollama API port |
| `ports.lm_studio` | 1234 | LM Studio API port |
| `ports.tts` | 8000 | TTS service port |
| `ports.mcp_memory` | 3100 | MCP memory server port |
| `model.default_provider` | ollama | Default model provider |
| `model.temperature` | 0.7 | Sampling temperature |
| `model.max_tokens` | 2048 | Maximum response tokens |
| `tts.enabled` | false | Enable TTS |
| `tts.voice` | alloy | TTS voice |
| `mcp.enabled` | true | Enable MCP memory |
| `cuda.enabled` | true | Enable CUDA |
| `cuda.cuda_version` | 12.1 | CUDA version |

## Architecture

```
llm_chat/
├── __init__.py          # Package initialization
├── __main__.py          # Application entry point
├── core/
│   ├── chat_client.py   # Main chat client
│   ├── model_manager.py # Model switching
│   └── history_manager.py # Chat history
├── gui/
│   ├── main_window.py   # Main application window
│   ├── chat_widget.py   # Chat display widget
│   ├── system_tray.py   # System tray manager
│   └── dialogs/         # Settings, model, about dialogs
├── services/
│   ├── ollama_client.py # Ollama API client
│   ├── lm_studio_client.py # LM Studio client
│   ├── tts_service.py   # TTS integration
│   └── mcp_connector.py # MCP memory connector
├── config/
│   └── settings.py      # Application settings
└── utils/
    ├── config_manager.py # Configuration management
    └── logger.py        # Logging utilities
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Chat |
| Ctrl+L | Clear Chat |
| Ctrl+E | Export Chat |
| Ctrl+M | Select Model |
| Ctrl+H | Toggle History Panel |
| F5 | Refresh Models |
| Ctrl+, | Settings |

## Development

```bash
# Install development dependencies
pip install pytest pytest-asyncio black mypy

# Run tests
pytest

# Format code
black llm_chat/

# Type checking
mypy llm_chat/
```

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.