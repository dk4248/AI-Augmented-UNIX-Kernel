"""
Command execution module for Shell AI Assistant
Handles safe command execution with proper error handling
"""

import os
import subprocess
import re
from typing import Dict, Tuple, Optional, List
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class CommandExecutor:
    """Execute shell commands safely with proper validation"""
    
    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',           # rm -rf /
        r'rm\s+-rf\s+\*',          # rm -rf *
        r'dd\s+if=.*of=/dev/',     # dd to device
        r'mkfs',                   # Format filesystem
        r'>\s*/dev/',              # Write to device
        r'chmod\s+-R\s+777',       # Dangerous permissions
        r'chown\s+-R\s+root',      # Change to root ownership
        r'curl.*\|\s*bash',        # Curl pipe to bash
        r'wget.*\|\s*sh',          # Wget pipe to shell
        r':\(\)\s*\{.*\}',         # Fork bomb
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize executor with optional configuration"""
        self.config = config or {}
        self.history = []
        
    def is_dangerous(self, command: str) -> Tuple[bool, List[str]]:
        """Check if command matches dangerous patterns"""
        risks = []
        
        # Check against dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                risks.append(f"Matches dangerous pattern: {pattern}")
        
        # Check for sudo
        if command.strip().startswith('sudo'):
            risks.append("Requires root/admin privileges")
        
        # Check for redirects that might overwrite files
        if '>' in command and not '>>' in command:
            risks.append("May overwrite existing files")
        
        # Check for pipe to shell
        if '|' in command and any(shell in command for shell in ['bash', 'sh', 'zsh']):
            risks.append("Pipes to shell - could execute arbitrary code")
        
        return len(risks) > 0, risks
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """Validate command before execution"""
        if not command or not command.strip():
            return False, "Empty command"
        
        # Check for shell injection attempts
        dangerous_chars = ['`', '$(...)', '${...}']
        for char in dangerous_chars:
            if char in command:
                return False, f"Potential shell injection: contains {char}"
        
        return True, "Valid"
    
    def execute(self, command: str, dry_run: bool = False) -> Dict[str, any]:
        """Execute a command and return results"""
        # Validate command
        valid, reason = self.validate_command(command)
        if not valid:
            return {
                'success': False,
                'command': command,
                'error': f"Invalid command: {reason}",
                'stdout': '',
                'stderr': '',
                'returncode': -1
            }
        
        # Check if dangerous
        is_dangerous, risks = self.is_dangerous(command)
        
        result = {
            'command': command,
            'is_dangerous': is_dangerous,
            'risks': risks,
            'dry_run': dry_run
        }
        
        if dry_run:
            result['success'] = True
            result['stdout'] = f"[DRY RUN] Would execute: {command}"
            result['stderr'] = ''
            result['returncode'] = 0
            return result
        
        try:
            # Execute command
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                timeout=30  # 30 second timeout
            )
            
            result.update({
                'success': process.returncode == 0,
                'stdout': process.stdout,
                'stderr': process.stderr,
                'returncode': process.returncode
            })
            
            # Add to history
            self.history.append(result)
            
        except subprocess.TimeoutExpired:
            result.update({
                'success': False,
                'stdout': '',
                'stderr': 'Command timed out after 30 seconds',
                'returncode': -1
            })
        except Exception as e:
            result.update({
                'success': False,
                'stdout': '',
                'stderr': f"Execution failed: {str(e)}",
                'returncode': -1
            })
        
        return result
    
    def execute_with_confirmation(self, command: str, auto_confirm: bool = False) -> Dict[str, any]:
        """Execute command with user confirmation for dangerous operations"""
        # Check if dangerous
        is_dangerous, risks = self.is_dangerous(command)
        
        if is_dangerous and not auto_confirm:
            print(f"\n{Fore.YELLOW}⚠️  WARNING: This command may be dangerous!")
            print(f"{Fore.YELLOW}Command: {Fore.WHITE}{command}")
            print(f"{Fore.YELLOW}Risks:")
            for risk in risks:
                print(f"{Fore.YELLOW}  • {risk}")
            
            response = input(f"\n{Fore.YELLOW}Are you sure you want to execute this? [y/N]: {Style.RESET_ALL}")
            if response.lower() != 'y':
                return {
                    'success': False,
                    'command': command,
                    'error': 'Execution cancelled by user',
                    'stdout': '',
                    'stderr': '',
                    'returncode': -1
                }
        
        return self.execute(command)
    
    def format_output(self, result: Dict[str, any]) -> None:
        """Pretty print command execution results"""
        if result.get('dry_run'):
            print(f"{Fore.BLUE}🔍 DRY RUN")
            print(f"{Fore.WHITE}{result['stdout']}")
            return
        
        # Command
        print(f"\n{Fore.CYAN}🔄 Executing: {Fore.WHITE}{result['command']}")
        
        # Warnings
        if result.get('risks'):
            for risk in result['risks']:
                print(f"{Fore.YELLOW}⚠️  {risk}")
        
        # Output
        if result['stdout']:
            print(f"\n{Fore.GREEN}📤 Output:")
            print(result['stdout'])
        
        # Errors
        if result['stderr']:
            print(f"\n{Fore.RED}❌ Error:")
            print(result['stderr'])
        
        # Status
        if result['success']:
            print(f"\n{Fore.GREEN}✅ Command completed successfully")
        else:
            print(f"\n{Fore.RED}❌ Command failed with exit code: {result['returncode']}")
    
    def get_last_error(self) -> Optional[Dict[str, any]]:
        """Get the last command that failed"""
        for cmd in reversed(self.history):
            if not cmd['success']:
                return cmd
        return None
    
    def suggest_fix(self, error_result: Dict[str, any]) -> List[str]:
        """Suggest potential fixes for common errors"""
        suggestions = []
        error_text = error_result.get('stderr', '').lower()
        command = error_result.get('command', '')
        
        # Command not found
        if 'command not found' in error_text:
            cmd_name = command.split()[0]
            suggestions.append(f"Install {cmd_name} using your package manager")
            suggestions.append(f"Check if {cmd_name} is in your PATH")
            suggestions.append("Check for typos in the command name")
        
        # Permission denied
        elif 'permission denied' in error_text:
            suggestions.append(f"Try with sudo: sudo {command}")
            suggestions.append("Check file permissions with ls -l")
            suggestions.append("Ensure you have access to the file/directory")
        
        # No such file or directory
        elif 'no such file or directory' in error_text:
            suggestions.append("Check if the file/directory exists")
            suggestions.append("Verify the path is correct")
            suggestions.append("Use tab completion to verify paths")
        
        # Package management errors
        elif any(pkg in error_text for pkg in ['apt', 'yum', 'dnf', 'brew']):
            if 'lock' in error_text:
                suggestions.append("Another package manager is running")
                suggestions.append("Wait for it to finish or kill the process")
            elif 'not found' in error_text:
                suggestions.append("Update package lists first")
                suggestions.append("Check package name spelling")
        
        # Git errors
        elif 'git' in command:
            if 'not a git repository' in error_text:
                suggestions.append("Initialize a git repository: git init")
                suggestions.append("Clone an existing repository")
            elif 'merge conflict' in error_text:
                suggestions.append("Resolve conflicts manually")
                suggestions.append("Use git status to see conflicted files")
        
        # Python errors
        elif 'python' in command or 'pip' in command:
            if 'modulenotfounderror' in error_text:
                module = re.search(r"No module named '([^']+)'", error_result.get('stderr', ''))
                if module:
                    suggestions.append(f"Install missing module: pip install {module.group(1)}")
            elif 'syntaxerror' in error_text:
                suggestions.append("Check Python syntax")
                suggestions.append("Verify Python version compatibility")
        
        return suggestions
    
    @staticmethod
    def clean_command(command: str) -> str:
        """Clean and normalize command string"""
        # Remove leading/trailing whitespace
        command = command.strip()
        
        # Remove multiple spaces
        command = ' '.join(command.split())
        
        # Handle common typos
        replacements = {
            'ls-la': 'ls -la',
            'cd~': 'cd ~',
            'cd..': 'cd ..',
            'rm-rf': 'rm -rf',
        }
        
        for typo, correct in replacements.items():
            command = command.replace(typo, correct)
        
        return command