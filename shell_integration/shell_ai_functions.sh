#!/bin/bash
# Shell Integration for AI Assistant
# Add this to your ~/.bashrc or ~/.zshrc

# Configuration - This will be updated by setup.sh
AI_ASSISTANT_PATH="/path/to/shell-ai-assistant/shell_ai/main.py"

# Main AI function
ai() {
    if [ $# -eq 0 ]; then
        # No arguments - start interactive mode
        python3 "$AI_ASSISTANT_PATH"
    else
        # Arguments provided - single query mode
        python3 "$AI_ASSISTANT_PATH" "$@"
    fi
}

# Quick aliases for common patterns
alias ai-install='ai "install"'
alias ai-find='ai "find"'
alias ai-fix='ai "fix the error:"'
alias ai-help='ai-usage'

# Function to automatically suggest command when a command fails
suggest_fix() {
    local exit_code=$?
    local last_command=$(history | tail -1 | sed 's/^[ ]*[0-9]*[ ]*//')
    
    if [ $exit_code -ne 0 ] && [ "$last_command" != "suggest_fix" ]; then
        echo ""
        echo "🤖 Command failed with exit code $exit_code"
        echo "💡 Would you like AI assistance? Type: ai \"fix: $last_command\""
        echo ""
    fi
    
    return $exit_code
}

# Optional: Auto-suggest on command failure
# Uncomment the next line to enable automatic suggestions when commands fail
# trap 'suggest_fix' ERR

# Function to add context-aware AI assistance
ai-here() {
    local context="Current directory: $(pwd)"
    context="$context\nFiles in directory: $(ls -la | head -10)"
    context="$context\nDisk usage: $(df -h . | tail -1)"
    
    if [ $# -eq 0 ]; then
        ai "Context: $context. What can I do here?"
    else
        ai "Context: $context. $*"
    fi
}

# Function for system information queries
ai-sys() {
    local system_info="OS: $(uname -s)"
    system_info="$system_info\nDistribution: $(lsb_release -d 2>/dev/null | cut -f2 | head -1 || echo 'Unknown')"
    system_info="$system_info\nKernel: $(uname -r)"
    system_info="$system_info\nMemory: $(free -h 2>/dev/null | grep '^Mem:' | awk '{print $3 "/" $2}' || echo 'Unknown')"
    system_info="$system_info\nCPU: $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 'Unknown') cores"
    
    if [ $# -eq 0 ]; then
        ai "System info: $system_info. What would you like to know about the system?"
    else
        ai "System info: $system_info. $*"
    fi
}

# Function for package management queries
ai-pkg() {
    local pkg_manager=""
    
    if command -v apt &> /dev/null; then
        pkg_manager="apt"
    elif command -v yum &> /dev/null; then
        pkg_manager="yum"
    elif command -v dnf &> /dev/null; then
        pkg_manager="dnf"
    elif command -v pacman &> /dev/null; then
        pkg_manager="pacman"
    elif command -v brew &> /dev/null; then
        pkg_manager="brew"
    elif command -v apk &> /dev/null; then
        pkg_manager="apk"
    fi
    
    if [ -z "$pkg_manager" ]; then
        ai "$*"
    else
        ai "Package manager: $pkg_manager. $*"
    fi
}

# Function for git-related queries
ai-git() {
    local git_info=""
    if git rev-parse --git-dir > /dev/null 2>&1; then
        git_info="In git repository: $(basename $(git rev-parse --show-toplevel 2>/dev/null || echo 'unknown'))"
        git_info="$git_info\nCurrent branch: $(git branch --show-current 2>/dev/null || echo 'detached HEAD')"
        git_info="$git_info\nStatus: $(git status --porcelain 2>/dev/null | wc -l) modified files"
    else
        git_info="Not in a git repository"
    fi
    
    ai "Git context: $git_info. $*"
}

# Function for docker queries
ai-docker() {
    local docker_info=""
    if command -v docker &> /dev/null; then
        docker_info="Docker installed: $(docker --version 2>/dev/null | head -1)"
        docker_info="$docker_info\nContainers running: $(docker ps -q 2>/dev/null | wc -l)"
        docker_info="$docker_info\nImages: $(docker images -q 2>/dev/null | wc -l)"
    else
        docker_info="Docker not installed"
    fi
    
    ai "Docker context: $docker_info. $*"
}

# Function for network queries
ai-net() {
    local net_info="Hostname: $(hostname)"
    net_info="$net_info\nIP addresses: $(ip addr show 2>/dev/null | grep 'inet ' | awk '{print $2}' | head -3 | tr '\n' ' ' || ifconfig 2>/dev/null | grep 'inet ' | awk '{print $2}' | head -3 | tr '\n' ' ')"
    net_info="$net_info\nDefault gateway: $(ip route 2>/dev/null | grep default | awk '{print $3}' | head -1 || netstat -rn 2>/dev/null | grep '^0.0.0.0' | awk '{print $2}' | head -1)"
    
    ai "Network context: $net_info. $*"
}

# Function to analyze files
ai-analyze() {
    if [ $# -eq 0 ]; then
        echo "Usage: ai-analyze <file>"
        return 1
    fi
    
    local file="$1"
    if [ ! -f "$file" ]; then
        echo "File not found: $file"
        return 1
    fi
    
    local file_info="File: $file"
    file_info="$file_info\nSize: $(du -h "$file" 2>/dev/null | cut -f1)"
    file_info="$file_info\nType: $(file -b "$file" 2>/dev/null | head -1)"
    file_info="$file_info\nLines: $(wc -l < "$file" 2>/dev/null)"
    
    # Get first few lines for context
    local preview=$(head -n 10 "$file" 2>/dev/null | sed 's/^/  /')
    
    ai "Analyze this file. $file_info\n\nFirst 10 lines:\n$preview"
}

# Help function
ai-usage() {
    cat << 'EOF'
🤖 Shell AI Assistant Help

BASIC USAGE:
  ai "natural language request"     - Single query mode
  ai                               - Interactive mode
  ai "/command"                    - Execute command directly (bypass AI)

SPECIALIZED FUNCTIONS:
  ai-here "query"                  - Include current directory context
  ai-sys "query"                   - Include system information
  ai-pkg "install something"       - Package management assistance
  ai-git "git operation"           - Git repository assistance
  ai-docker "container task"       - Docker assistance
  ai-net "network query"           - Network configuration help
  ai-analyze <file>                - Analyze a file

EXAMPLES:
  ai "create a backup of this folder"
  ai "install docker on ubuntu"
  ai "find all python files larger than 1MB"
  ai "kill the process using port 3000"
  ai "/ls -la"                     - Direct command execution
  ai-here "what files can I clean up?"
  ai-sys "why is my system slow?"
  ai-pkg "update all packages"
  ai-git "create a new branch"
  ai-docker "list running containers"
  ai-net "check open ports"

DIRECT COMMANDS:
  Use "/" prefix to run commands directly without AI processing:
  ai "/ls -la"        - List files
  ai "/df -h"         - Check disk space
  ai "/ps aux"        - Show processes
  
  Direct commands show output immediately and offer AI help if they fail.

CONFIGURATION:
  Edit ~/.shell_ai_config to change:
  - AI provider (OpenAI/Ollama)
  - Model selection
  - API keys
  - Other settings

TIPS:
  • Be specific in your requests for better results
  • Use direct commands (/) for simple operations
  • The AI learns from context - provide details when needed
  • For complex tasks, break them into steps

The assistant provides:
  ✅ Shell commands with explanations
  ⚠️  Risk warnings for dangerous operations  
  🔄 Alternative approaches
  💡 Automatic error analysis and fixes
  🚀 Direct command execution with "/" prefix
EOF
}

# Completion function for bash/zsh
if [ -n "$BASH_VERSION" ]; then
    # Bash completion
    _ai_complete() {
        local cur="${COMP_WORDS[COMP_CWORD]}"
        local commands="help quit clear history"
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
    }
    complete -F _ai_complete ai
elif [ -n "$ZSH_VERSION" ]; then
    # Zsh completion
    _ai_complete() {
        local commands=("help:Show help" "quit:Exit AI assistant" "clear:Clear screen" "history:Show history")
        _describe 'ai commands' commands
    }
    compdef _ai_complete ai
fi

# Quick shortcut function for last command fix
fix-last() {
    local last_cmd=$(fc -ln -1 | sed 's/^[ \t]*//')
    ai "fix this error: Command '$last_cmd' failed"
}

# Function to save useful commands
ai-save() {
    local cmd="$1"
    local desc="$2"
    local save_file="$HOME/.ai_saved_commands"
    
    if [ -z "$cmd" ]; then
        echo "Usage: ai-save \"command\" \"description\""
        echo "Saved commands:"
        if [ -f "$save_file" ]; then
            cat "$save_file" | nl
        else
            echo "No saved commands yet."
        fi
        return
    fi
    
    echo "[$desc] $cmd" >> "$save_file"
    echo "✅ Command saved!"
}

# Model switching shortcuts
ai-gpt4() {
    export OPENAI_MODEL="gpt-4"
    echo "✅ Switched to GPT-4"
}

ai-gpt35() {
    export OPENAI_MODEL="gpt-3.5-turbo"
    echo "✅ Switched to GPT-3.5 Turbo"
}

ai-deepseek() {
    export SHELL_AI_PROVIDER="ollama"
    export OLLAMA_MODEL="deepseek-r1:8b"
    echo "✅ Switched to DeepSeek R1 8B (Ollama)"
}

ai-qwen() {
    export SHELL_AI_PROVIDER="ollama"
    export OLLAMA_MODEL="qwen2.5:7b"
    echo "✅ Switched to Qwen 2.5 7B (Ollama)"
}

# Show current configuration
ai-config() {
    echo "🤖 Shell AI Configuration:"
    echo "Provider: ${SHELL_AI_PROVIDER:-openai}"
    if [ "$SHELL_AI_PROVIDER" = "ollama" ]; then
        echo "Model: ${OLLAMA_MODEL:-deepseek-r1:8b}"
        echo "Host: ${OLLAMA_HOST:-http://localhost:11434}"
    else
        echo "Model: ${OPENAI_MODEL:-gpt-4}"
        echo "API Key: ${OPENAI_API_KEY:+[SET]}"
    fi
}

echo "🤖 Shell AI Assistant loaded! Type 'ai-usage' for help."