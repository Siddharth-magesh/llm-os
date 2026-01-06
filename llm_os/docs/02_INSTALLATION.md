# Installation Guide

## Requirements

### System Requirements
- Linux (Ubuntu 24.04 LTS recommended)
- Python 3.11 or higher
- 4GB+ RAM (8GB+ recommended for local models)
- GPU optional but recommended for local LLMs

### For Local LLMs (Ollama)
- Ollama installed and running
- At least one model pulled (e.g., `llama3.2:3b`)

### For Cloud LLMs
- Anthropic API key (for Claude)
- OpenAI API key (for GPT models)

## Installation Steps

### 1. Clone or Copy the Project

```bash
# If using git
git clone <repository> llm_os
cd llm_os

# Or copy the folder to your machine
```

### 2. Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install LLM-OS

```bash
# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### 4. Set Up Ollama (for local models)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2:3b

# Pull reasoning model (optional)
ollama pull deepseek-r1:1.5b

# Verify Ollama is running
ollama list
```

### 5. Configure API Keys (for cloud models)

```bash
# Option 1: Environment variables
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"

# Option 2: Add to ~/.bashrc or ~/.zshrc
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc

# Option 3: Create config file
mkdir -p ~/.llm-os
cat > ~/.llm-os/config.yaml << EOF
anthropic:
  api_key: "your-key-here"
openai:
  api_key: "your-key-here"
EOF
```

### 6. Verify Installation

```bash
# Check installation
llm-os --version

# Run in demo mode
llm-os --no-ui

# Start the TUI
llm-os
```

## Quick Configuration

### Use Local Models Only

```bash
llm-os --local-only
```

### Use Specific Provider

```bash
llm-os --provider anthropic
llm-os --provider openai
llm-os --provider ollama
```

### Use Specific Model

```bash
llm-os --provider ollama --model llama3.2:1b
llm-os --provider anthropic --model claude-3-5-haiku-latest
```

## Troubleshooting

### Ollama Not Connecting

```bash
# Check if Ollama is running
systemctl status ollama

# Start Ollama service
systemctl start ollama

# Or run manually
ollama serve
```

### Permission Errors

```bash
# Ensure user has access to necessary directories
sudo usermod -aG docker $USER  # If using Docker
```

### Missing Dependencies

```bash
# Install system dependencies
sudo apt update
sudo apt install python3-dev python3-pip git

# Reinstall Python packages
pip install --upgrade pip
pip install -e ".[dev]"
```

## Next Steps

1. Read the [Architecture](./03_ARCHITECTURE.md) guide
2. Configure your [settings](./07_CONFIGURATION.md)
3. Try some [example commands](./01_OVERVIEW.md#example-usage)
