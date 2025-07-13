# Shell AI Assistant 🤖

A powerful natural language to shell command translator that integrates AI into your terminal workflow. Supports both OpenAI and Ollama models for flexible, local or cloud-based AI assistance.

## Features ✨

- **Natural Language to Command Translation**: Describe what you want in plain English
- **Multi-Model Support**: Use OpenAI GPT-4 or local Ollama models
- **Error Analysis & Auto-Fix**: Automatically suggests fixes when commands fail
- **Direct Command Execution**: Run commands directly with `/` prefix
- **Context-Aware Assistance**: Understands your current directory, system, and git status
- **Safe Execution**: Warns about potentially dangerous commands
- **Interactive & Single Query Modes**: Use as needed

## Supported Ollama Models 🦙

- `deepseek-r1:32b` - Most capable model for complex tasks
- `deepseek-r1:8b` - Efficient DeepSeek model
- `qwen2.5:32b` - Large Qwen model with excellent performance
- `qwen2.5:7b` - Balanced performance and speed
- `qwen3:8b` - Latest Qwen 3 model
- `llama3.1:8b` - Meta's Llama 3.1 model

## Installation 🚀

### Prerequisites

- Python 3.7+
- Ollama (for local models) or OpenAI API key
- Linux/macOS/WSL

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/shell-ai-assistant.git
cd shell-ai-assistant

# Run the setup script
chmod +x setup.sh
./setup.sh
```

### Manual Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your AI provider:

**For OpenAI:**
```bash
export OPENAI_API_KEY='your-api-key-here'
```

**For Ollama:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull your preferred model
ollama pull deepseek-r1:8b
```

3. Add to your shell configuration:
```bash
echo "source /path/to/shell-ai-assistant/shell_integration/shell_ai_functions.sh" >> ~/.bashrc
source ~/.bashrc
```

## Usage 💡

### Basic Commands

```bash
# Interactive mode
ai

# Single query
ai "create a backup of my home directory"

# Direct command execution (bypass AI)
ai "/ls -la"
```

### Specialized Functions

```bash
# Context-aware assistance
ai-here "what large files can I delete?"

# System information queries
ai-sys "check memory usage"

# Package management
ai-pkg "install docker"

# Git operations
ai-git "create feature branch"
```

### Examples

```bash
# File operations
ai "find all PDF files modified in the last week"
ai "compress all images in this folder"

# System management
ai "kill the process using port 3000"
ai "show disk usage by directory"

# Development
ai "create a Python virtual environment"
ai "run this script in the background"

# Error fixing
ai "fix: python3 script.py"  # After a failed command
```

## Configuration ⚙️

### Switching AI Providers

Edit `~/.shell_ai_config` or use environment variables:

```bash
# Use OpenAI
export SHELL_AI_PROVIDER="openai"
export OPENAI_API_KEY="your-key"

# Use Ollama
export SHELL_AI_PROVIDER="ollama"
export OLLAMA_MODEL="deepseek-r1:8b"
```

### Model Selection

**OpenAI Models:**
- `gpt-4` (default)
- `gpt-4-turbo`
- `gpt-3.5-turbo`

**Ollama Models:**
- See supported models list above
- Change with: `export OLLAMA_MODEL="model-name"`

## Architecture 🏗️

```
shell_ai/
├── main.py           # Entry point and CLI interface
├── assistant.py      # AI assistant core logic
├── command_executor.py # Command execution and safety checks
├── system_info.py    # System information gathering
├── config.py         # Configuration management
└── prompts.py        # AI prompt templates
```

## Safety Features 🛡️

- **Command Risk Assessment**: Warns about destructive operations
- **Confirmation Required**: For sudo, rm -rf, and other dangerous commands
- **Explanation First**: Always shows what a command will do
- **Alternative Suggestions**: Provides safer alternatives when available

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments 🙏

- OpenAI for GPT models
- Ollama team for local model support
- DeepSeek, Alibaba (Qwen), and Meta (Llama) for their excellent models

## Troubleshooting 🔧

### Common Issues

**"API key not found"**
- Ensure your API key is exported: `echo $OPENAI_API_KEY`
- Add to ~/.bashrc for persistence

**"Ollama not responding"**
- Check Ollama is running: `ollama list`
- Ensure model is pulled: `ollama pull model-name`

**"Command not found: ai"**
- Source shell functions: `source ~/.bashrc`
- Check installation path in shell_ai_functions.sh

For more help, open an issue on GitHub!
