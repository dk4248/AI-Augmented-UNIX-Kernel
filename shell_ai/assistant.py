"""
Core AI Assistant for Shell AI
Handles communication with OpenAI and Ollama models
"""

import os
import json
import requests
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from colorama import Fore, Style, init

from .config import Config
from .prompts import PromptBuilder
from .system_info import SystemInfo
from .command_executor import CommandExecutor

# Initialize colorama
init(autoreset=True)

class ShellAIAssistant:
    """Main AI Assistant class"""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the AI assistant"""
        self.config = config or Config()
        self.conversation_history: List[Dict[str, str]] = []
        self.executor = CommandExecutor()
        self.prompt_builder = PromptBuilder()
        
        # Initialize AI client based on provider
        if self.config.is_openai:
            self.client = OpenAI(api_key=self.config.api_key)
        else:
            self.client = None  # Ollama uses REST API directly
        
        # Get system context
        self.system_context = SystemInfo.get_full_context()
        self.system_context['provider'] = self.config.provider
        
        # Build system prompt
        self.system_prompt = self.prompt_builder.get_system_prompt(self.system_context)
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        
        # Keep only last N exchanges based on config
        max_entries = self.config.get('history.max_entries', 20)
        if len(self.conversation_history) > max_entries:
            self.conversation_history = self.conversation_history[-max_entries:]
    
    def get_command_suggestion(self, user_input: str) -> Dict:
        """Get command suggestion from AI"""
        try:
            if self.config.is_openai:
                return self._get_openai_suggestion(user_input)
            else:
                return self._get_ollama_suggestion(user_input)
        except Exception as e:
            return self._error_response(str(e))
    
    def _get_openai_suggestion(self, user_input: str) -> Dict:
        """Get suggestion from OpenAI"""
        try:
            # Add user input to history
            self.add_to_history("user", user_input)
            
            # Prepare messages
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.conversation_history)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.config.get('openai.model', 'gpt-4'),
                messages=messages,
                temperature=self.config.get('openai.temperature', 0.1),
                max_tokens=self.config.get('openai.max_tokens', 1000)
            )
            
            # Parse response
            ai_response = response.choices[0].message.content
            self.add_to_history("assistant", ai_response)
            
            # Validate and parse JSON
            return self.prompt_builder.validate_json_response(ai_response)
            
        except Exception as e:
            return self._error_response(f"OpenAI API error: {str(e)}")
    
    def _get_ollama_suggestion(self, user_input: str) -> Dict:
        """Get suggestion from Ollama"""
        try:
            # Format prompt for Ollama
            model = self.config.get('ollama.model')
            prompt = self.prompt_builder.format_ollama_messages(
                self.system_prompt, user_input, model
            )
            
            # Call Ollama API
            url = f"{self.config.ollama_host}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": self.config.get('ollama.temperature', 0.1),
                "max_tokens": self.config.get('ollama.max_tokens', 1000)
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code != 200:
                return self._error_response(f"Ollama API error: {response.text}")
            
            # Parse response
            result = response.json()
            ai_response = result.get('response', '')
            
            # Add to history
            self.add_to_history("user", user_input)
            self.add_to_history("assistant", ai_response)
            
            # Validate and parse JSON
            return self.prompt_builder.validate_json_response(ai_response)
            
        except requests.exceptions.ConnectionError:
            return self._error_response(
                "Cannot connect to Ollama. Make sure it's running: 'ollama serve'"
            )
        except Exception as e:
            return self._error_response(f"Ollama error: {str(e)}")
    
    def _error_response(self, error_msg: str) -> Dict:
        """Create an error response"""
        return {
            "command": "# Error occurred",
            "explanation": error_msg,
            "risks": ["Check configuration and try again"],
            "alternatives": [],
            "safe_to_auto_execute": False
        }
    
    def display_suggestion(self, suggestion: Dict) -> None:
        """Display the command suggestion in a nice format"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}🤖 AI COMMAND SUGGESTION")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Command
        print(f"\n{Fore.GREEN}💻 Command:")
        print(f"   {Fore.WHITE}{suggestion['command']}")
        
        # Explanation
        print(f"\n{Fore.BLUE}📝 Explanation:")
        print(f"   {Fore.WHITE}{suggestion['explanation']}")
        
        # Risks
        if suggestion.get('risks'):
            print(f"\n{Fore.YELLOW}⚠️  Potential Issues:")
            for risk in suggestion['risks']:
                print(f"   {Fore.YELLOW}• {risk}")
        
        # Alternatives
        if suggestion.get('alternatives'):
            print(f"\n{Fore.MAGENTA}🔄 Alternatives:")
            for i, alt in enumerate(suggestion['alternatives'], 1):
                print(f"   {Fore.WHITE}{i}. {alt}")
        
        # Safety indicator
        if suggestion.get('safe_to_auto_execute', False):
            safety = f"{Fore.GREEN}✅ SAFE"
        else:
            safety = f"{Fore.RED}🚨 REQUIRES CAUTION"
        
        print(f"\n{Fore.CYAN}🛡️  Safety: {safety}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    def get_user_choice(self, suggestion: Dict) -> str:
        """Get user's choice on what to do with the suggestion"""
        safe = suggestion.get('safe_to_auto_execute', False)
        
        while True:
            if safe:
                prompt = f"\n{Fore.CYAN}Choose: [y]es, [n]o, [e]dit, [a]lternatives, [q]uit: {Style.RESET_ALL}"
            else:
                prompt = f"\n{Fore.YELLOW}⚠️  CAUTION REQUIRED ⚠️\nChoose: [y]es (I understand risks), [n]o, [e]dit, [a]lternatives, [q]uit: {Style.RESET_ALL}"
            
            choice = input(prompt).lower().strip()
            
            if choice in ['y', 'yes']:
                return 'execute'
            elif choice in ['n', 'no']:
                return 'cancel'
            elif choice in ['e', 'edit']:
                return 'edit'
            elif choice in ['a', 'alternatives']:
                return 'alternatives'
            elif choice in ['q', 'quit']:
                return 'quit'
            else:
                print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
    
    def execute_command(self, command: str, safe: bool = False) -> bool:
        """Execute the command using the executor"""
        result = self.executor.execute_with_confirmation(command, auto_confirm=safe)
        self.executor.format_output(result)
        
        # If command failed, offer to help fix it
        if not result['success'] and result['returncode'] != -1:
            print(f"\n{Fore.YELLOW}💡 Would you like AI help to fix this error? [y/n]: {Style.RESET_ALL}", end="")
            try:
                choice = input().strip().lower()
                if choice in ['y', 'yes']:
                    error_context = self.prompt_builder.get_error_fix_prompt(
                        command=result['command'],
                        error=result['stderr'],
                        stdout=result['stdout'],
                        exit_code=result['returncode']
                    )
                    
                    print(f"\n{Fore.CYAN}🤔 Analyzing error...{Style.RESET_ALL}")
                    suggestion = self.get_command_suggestion(error_context)
                    self.display_suggestion(suggestion)
                    
                    fix_choice = self.get_user_choice(suggestion)
                    if fix_choice == 'execute':
                        print(f"\n{Fore.CYAN}🔄 Executing fix: {suggestion['command']}{Style.RESET_ALL}")
                        return self.execute_command(suggestion['command'])
            except KeyboardInterrupt:
                print("\n")
                pass
        
        return result['success']
    
    def execute_direct_command(self, command: str) -> None:
        """Execute a command directly without AI processing"""
        result = self.executor.execute(command)
        self.executor.format_output(result)
        
        # Auto-suggest fix for errors
        if not result['success'] and result['returncode'] != -1:
            suggestions = self.executor.suggest_fix(result)
            if suggestions:
                print(f"\n{Fore.YELLOW}💡 Suggestions:{Style.RESET_ALL}")
                for sugg in suggestions:
                    print(f"   • {sugg}")
            
            print(f"\n{Fore.YELLOW}💡 Would you like AI help with this error? [y/n]: {Style.RESET_ALL}", end="")
            choice = input().strip().lower()
            if choice in ['y', 'yes']:
                error_context = self.prompt_builder.get_error_fix_prompt(
                    command=result['command'],
                    error=result['stderr'],
                    stdout=result['stdout'],
                    exit_code=result['returncode']
                )
                
                print(f"\n{Fore.CYAN}🤔 Analyzing error...{Style.RESET_ALL}")
                suggestion = self.get_command_suggestion(error_context)
                self.display_suggestion(suggestion)
                
                fix_choice = self.get_user_choice(suggestion)
                if fix_choice == 'execute':
                    self.execute_command(suggestion['command'])
    
    def handle_alternatives(self, alternatives: List[str]) -> Optional[str]:
        """Handle alternative command selection"""
        if not alternatives:
            print(f"{Fore.YELLOW}No alternatives available.{Style.RESET_ALL}")
            return None
        
        print(f"\n{Fore.CYAN}🔄 Available alternatives:{Style.RESET_ALL}")
        for i, alt in enumerate(alternatives, 1):
            print(f"   {i}. {alt}")
        
        try:
            choice = input(f"\n{Fore.CYAN}Select alternative (number) or [c]ancel: {Style.RESET_ALL}")
            if choice.lower() == 'c':
                return None
            
            alt_index = int(choice) - 1
            if 0 <= alt_index < len(alternatives):
                return alternatives[alt_index]
            else:
                print(f"{Fore.RED}❌ Invalid selection{Style.RESET_ALL}")
                return None
        except ValueError:
            print(f"{Fore.RED}❌ Invalid input{Style.RESET_ALL}")
            return None
    
    def process_request(self, user_input: str) -> None:
        """Process a single user request"""
        # Check for direct command execution
        if user_input.startswith('/'):
            direct_command = user_input[1:].strip()
            if direct_command:
                self.execute_direct_command(direct_command)
            else:
                print(f"{Fore.RED}❌ Empty command after '/'{Style.RESET_ALL}")
            return
        
        # Get AI suggestion
        print(f"\n{Fore.CYAN}🤔 Thinking...{Style.RESET_ALL}")
        suggestion = self.get_command_suggestion(user_input)
        
        # Display suggestion
        self.display_suggestion(suggestion)
        
        # Get user choice
        choice = self.get_user_choice(suggestion)
        
        if choice == 'execute':
            self.execute_command(
                suggestion['command'], 
                safe=suggestion.get('safe_to_auto_execute', False)
            )
        
        elif choice == 'edit':
            new_command = input(f"\n{Fore.CYAN}✏️  Edit command [{suggestion['command']}]: {Style.RESET_ALL}")
            if new_command.strip():
                self.execute_command(new_command)
        
        elif choice == 'alternatives':
            alt_command = self.handle_alternatives(suggestion.get('alternatives', []))
            if alt_command:
                self.execute_command(alt_command)
        
        elif choice == 'cancel':
            print(f"{Fore.YELLOW}❌ Command cancelled.{Style.RESET_ALL}")
        
        elif choice == 'quit':
            raise KeyboardInterrupt()