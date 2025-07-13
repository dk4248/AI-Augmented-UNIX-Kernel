#!/usr/bin/env python3
"""
Shell AI Assistant - Natural Language to Command Translation
Main entry point for the application
"""

import sys
import os
from colorama import Fore, Style, init
import click

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shell_ai.config import Config
from shell_ai.assistant import ShellAIAssistant
from shell_ai.system_info import SystemInfo

# Initialize colorama
init(autoreset=True)

def print_banner():
    """Print welcome banner"""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║                  🤖 Shell AI Assistant 🤖                  ║
║           Natural Language → Shell Commands               ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def print_help():
    """Print help information"""
    help_text = f"""
{Fore.CYAN}💡 Usage Tips:{Style.RESET_ALL}
• Type requests in natural language (e.g., "create a backup of my home directory")
• Start with '/' to run commands directly (e.g., '/ls -la')
• Type 'quit', 'exit', or press Ctrl+C to exit

{Fore.CYAN}🔧 Examples:{Style.RESET_ALL}
• "install docker on ubuntu"
• "find all PDF files modified today"
• "check what's using port 3000"
• "compress all images in this folder"
• "/df -h" (direct command execution)

{Fore.CYAN}⚡ Quick Commands:{Style.RESET_ALL}
• ai-here "query"  - Include current directory context
• ai-sys "query"   - Include system information
• ai-pkg "query"   - Package management help
• ai-git "query"   - Git repository assistance
"""
    print(help_text)

def run_interactive_session(assistant: ShellAIAssistant):
    """Run the main interactive loop"""
    print_banner()
    
    # Show current configuration
    provider = assistant.config.provider
    model = assistant.config.model
    print(f"{Fore.GREEN}✅ Using {provider} with model: {model}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Type 'help' for usage tips, or 'quit' to exit.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Tip: Start with '/' to run commands directly (e.g., '/ls -la'){Style.RESET_ALL}")
    
    while True:
        try:
            # Get user input
            user_input = input(f"\n{Fore.GREEN}🗣️  You: {Style.RESET_ALL}").strip()
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print(f"{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}")
                break
            
            elif user_input.lower() in ['help', '?']:
                print_help()
                continue
            
            elif user_input.lower() == 'clear':
                os.system('clear' if os.name != 'nt' else 'cls')
                print_banner()
                continue
            
            elif user_input.lower() == 'history':
                if assistant.conversation_history:
                    print(f"\n{Fore.CYAN}📜 Conversation History:{Style.RESET_ALL}")
                    for i, msg in enumerate(assistant.conversation_history[-10:], 1):
                        role_color = Fore.GREEN if msg['role'] == 'user' else Fore.BLUE
                        print(f"{i}. {role_color}{msg['role']}: {msg['content'][:80]}...")
                else:
                    print(f"{Fore.YELLOW}No conversation history yet.{Style.RESET_ALL}")
                continue
            
            elif not user_input:
                continue
            
            # Process the request
            assistant.process_request(user_input)
            
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"\n{Fore.RED}❌ Unexpected error: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please try again or report this issue.{Style.RESET_ALL}")

def process_single_query(assistant: ShellAIAssistant, query: str):
    """Process a single query and exit"""
    try:
        assistant.process_request(query)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}❌ Cancelled{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

@click.command()
@click.argument('query', nargs=-1)
@click.option('--provider', '-p', type=click.Choice(['openai', 'ollama']), 
              help='AI provider to use')
@click.option('--model', '-m', help='Model to use (e.g., gpt-4, deepseek-r1:8b)')
@click.option('--config', '-c', help='Path to config file')
@click.option('--version', '-v', is_flag=True, help='Show version')
def main(query, provider, model, config, version):
    """Shell AI Assistant - Natural Language to Command Translation"""
    
    if version:
        print("Shell AI Assistant v1.0.0")
        return
    
    # Load configuration
    config_obj = Config(config_file=config)
    
    # Override provider/model if specified
    if provider:
        config_obj.set('provider', provider)
    if model:
        if provider == 'openai' or config_obj.is_openai:
            config_obj.set('openai.model', model)
        else:
            config_obj.set('ollama.model', model)
    
    # Validate configuration
    if not config_obj.validate():
        sys.exit(1)
    
    # Create assistant
    try:
        assistant = ShellAIAssistant(config_obj)
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to initialize AI assistant: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Process query or run interactive mode
    if query:
        # Join all arguments as a single query
        query_str = ' '.join(query)
        process_single_query(assistant, query_str)
    else:
        # Interactive mode
        run_interactive_session(assistant)

if __name__ == "__main__":
    main()