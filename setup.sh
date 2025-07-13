#!/bin/bash

# Shell AI Assistant Setup Script
# This script sets up the Shell AI Assistant with either OpenAI or Ollama

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}       🤖 Shell AI Assistant Setup 🤖${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect shell
detect_shell() {
    if [ -n "$BASH_VERSION" ]; then
        echo "bash"
    elif [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    else
        echo "unknown"
    fi
}

# Function to get shell config file
get_shell_config() {
    local shell_type=$(detect_shell)
    case $shell_type in
        bash)
            if [ -f "$HOME/.bashrc" ]; then
                echo "$HOME/.bashrc"
            else
                echo "$HOME/.bash_profile"
            fi
            ;;
        zsh)
            echo "$HOME/.zshrc"
            ;;
        *)
            echo "$HOME/.profile"
            ;;
    esac
}

# Check Python installation
echo -e "${YELLOW}Checking Python installation...${NC}"
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
    echo -e "${YELLOW}Please install Python 3 and run this script again.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Install Python dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip3 install -r "$SCRIPT_DIR/requirements.txt" --user
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Choose AI provider
echo -e "\n${YELLOW}Choose your AI provider:${NC}"
echo "1) OpenAI (requires API key)"
echo "2) Ollama (local models)"
read -p "Enter choice (1 or 2): " provider_choice

CONFIG_FILE="$HOME/.shell_ai_config"

case $provider_choice in
    1)
        echo -e "\n${YELLOW}Setting up OpenAI...${NC}"
        
        # Check for existing API key
        if [ -n "$OPENAI_API_KEY" ]; then
            echo -e "${GREEN}✅ Found existing OpenAI API key${NC}"
            read -p "Use existing key? (y/n): " use_existing
            if [ "$use_existing" != "y" ]; then
                read -p "Enter your OpenAI API key: " api_key
                OPENAI_API_KEY=$api_key
            fi
        else
            read -p "Enter your OpenAI API key: " api_key
            OPENAI_API_KEY=$api_key
        fi
        
        # Save configuration
        cat > "$CONFIG_FILE" << EOF
# Shell AI Assistant Configuration
export SHELL_AI_PROVIDER="openai"
export OPENAI_API_KEY="$OPENAI_API_KEY"
export OPENAI_MODEL="gpt-4"
EOF
        
        echo -e "${GREEN}✅ OpenAI configured${NC}"
        ;;
        
    2)
        echo -e "\n${YELLOW}Setting up Ollama...${NC}"
        
        # Check if Ollama is installed
        if ! command_exists ollama; then
            echo -e "${YELLOW}Ollama not found. Would you like to install it?${NC}"
            read -p "Install Ollama? (y/n): " install_ollama
            
            if [ "$install_ollama" = "y" ]; then
                echo -e "${YELLOW}Installing Ollama...${NC}"
                curl -fsSL https://ollama.ai/install.sh | sh
                echo -e "${GREEN}✅ Ollama installed${NC}"
            else
                echo -e "${RED}❌ Ollama is required for local models${NC}"
                exit 1
            fi
        else
            echo -e "${GREEN}✅ Ollama is already installed${NC}"
        fi
        
        # List available models
        echo -e "\n${YELLOW}Available models:${NC}"
        echo "1) deepseek-r1:32b (Most capable, ~19GB)"
        echo "2) deepseek-r1:8b (Efficient, ~4.7GB)"
        echo "3) qwen2.5:32b (Large, excellent performance, ~19GB)"
        echo "4) qwen2.5:7b (Balanced, ~4.5GB)"
        echo "5) qwen3:8b (Latest Qwen, ~4.7GB)"
        echo "6) llama3.1:8b (Meta's model, ~4.7GB)"
        
        read -p "Choose model (1-6): " model_choice
        
        case $model_choice in
            1) OLLAMA_MODEL="deepseek-r1:32b" ;;
            2) OLLAMA_MODEL="deepseek-r1:8b" ;;
            3) OLLAMA_MODEL="qwen2.5:32b" ;;
            4) OLLAMA_MODEL="qwen2.5:7b" ;;
            5) OLLAMA_MODEL="qwen3:8b" ;;
            6) OLLAMA_MODEL="llama3.1:8b" ;;
            *) OLLAMA_MODEL="deepseek-r1:8b" ;;
        esac
        
        echo -e "${YELLOW}Pulling $OLLAMA_MODEL model...${NC}"
        ollama pull "$OLLAMA_MODEL"
        echo -e "${GREEN}✅ Model downloaded${NC}"
        
        # Save configuration
        cat > "$CONFIG_FILE" << EOF
# Shell AI Assistant Configuration
export SHELL_AI_PROVIDER="ollama"
export OLLAMA_MODEL="$OLLAMA_MODEL"
export OLLAMA_HOST="http://localhost:11434"
EOF
        
        echo -e "${GREEN}✅ Ollama configured${NC}"
        ;;
        
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

# Setup shell integration
echo -e "\n${YELLOW}Setting up shell integration...${NC}"

SHELL_CONFIG=$(get_shell_config)
SHELL_FUNCTIONS="$SCRIPT_DIR/shell_integration/shell_ai_functions.sh"

# Update paths in shell functions file
sed -i.bak "s|AI_ASSISTANT_PATH=.*|AI_ASSISTANT_PATH=\"$SCRIPT_DIR/shell_ai/main.py\"|" "$SHELL_FUNCTIONS"
rm -f "$SHELL_FUNCTIONS.bak"

# Add to shell configuration
if ! grep -q "shell_ai_functions.sh" "$SHELL_CONFIG" 2>/dev/null; then
    echo -e "\n# Shell AI Assistant" >> "$SHELL_CONFIG"
    echo "source $CONFIG_FILE" >> "$SHELL_CONFIG"
    echo "source $SHELL_FUNCTIONS" >> "$SHELL_CONFIG"
    echo -e "${GREEN}✅ Added to $SHELL_CONFIG${NC}"
else
    echo -e "${YELLOW}⚠️  Shell AI already configured in $SHELL_CONFIG${NC}"
fi

# Create symlink for easy access
echo -e "\n${YELLOW}Creating command symlink...${NC}"
if [ -d "$HOME/.local/bin" ]; then
    ln -sf "$SCRIPT_DIR/shell_ai/main.py" "$HOME/.local/bin/shell-ai"
    echo -e "${GREEN}✅ Created symlink at ~/.local/bin/shell-ai${NC}"
fi

# Final instructions
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo
echo -e "${YELLOW}To start using Shell AI Assistant:${NC}"
echo -e "1. Reload your shell configuration:"
echo -e "   ${BLUE}source $SHELL_CONFIG${NC}"
echo
echo -e "2. Test the installation:"
echo -e "   ${BLUE}ai \"hello\"${NC}"
echo
echo -e "3. Get help:"
echo -e "   ${BLUE}ai-usage${NC}"
echo
echo -e "${YELLOW}Configuration saved to: ${BLUE}$CONFIG_FILE${NC}"
echo -e "${YELLOW}You can edit this file to change settings.${NC}"
echo
echo -e "${GREEN}Enjoy your AI-powered shell! 🚀${NC}"