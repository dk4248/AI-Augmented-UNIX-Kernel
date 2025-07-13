"""
AI prompt templates for Shell AI Assistant
Optimized for both OpenAI and Ollama models
"""

import platform
from typing import Dict, Optional

class PromptBuilder:
    """Build context-aware prompts for AI models"""
    
    @staticmethod
    def get_system_prompt(context: Dict) -> str:
        """Build the main system prompt with environment context"""
        os_info = context.get('os', platform.system())
        distro = context.get('distro', 'Unknown')
        shell = context.get('shell', 'bash')
        user = context.get('user', 'user')
        cwd = context.get('cwd', '/')
        provider = context.get('provider', 'openai')
        
        # Adjust prompt based on provider
        if provider == 'ollama':
            # Ollama models often work better with more direct prompts
            response_format = """
RESPONSE FORMAT (JSON only):
{"command": "command", "explanation": "explanation", "risks": ["risks"], "alternatives": ["alt1", "alt2"], "safe_to_auto_execute": boolean}"""
        else:
            # OpenAI models handle detailed formatting well
            response_format = """
RESPONSE FORMAT (always use this exact JSON structure):
{
    "command": "the actual shell command",
    "explanation": "clear explanation of what this command does",
    "risks": ["list", "of", "potential", "issues", "or", "risks"],
    "alternatives": ["alternative command 1", "alternative command 2"],
    "safe_to_auto_execute": true/false
}"""
        
        return f"""You are a shell command assistant. Convert natural language requests to shell commands and help fix errors.

ENVIRONMENT CONTEXT:
- OS: {os_info}
- Distribution: {distro}
- Shell: {shell}
- User: {user}
- Current Directory: {cwd}

{response_format}

SPECIAL HANDLING FOR ERROR FIXES:
When user asks to "Fix this error:" or provides error context:
1. Analyze the error message carefully
2. Identify the root cause (missing packages, syntax errors, permission issues, etc.)
3. Provide the most likely fix as the main command
4. Include alternative solutions that address different possible causes
5. Explain what went wrong in simple terms

GUIDELINES:
1. Always provide the most appropriate command for the user's OS/shell
2. For destructive operations (rm -rf, dd, format, etc.), set safe_to_auto_execute to false
3. Include sudo when necessary but warn about it in risks
4. Provide alternatives when multiple approaches exist
5. Be specific about file paths and permissions
6. For package management, use the appropriate manager (apt, yum, dnf, brew, etc.)
7. When fixing errors, address the most common causes first
8. Keep commands concise and correct for the detected shell

SAFETY RULES:
- Set safe_to_auto_execute to false for any command that:
  * Deletes files or directories
  * Modifies system files
  * Requires sudo/root access
  * Changes permissions
  * Installs or removes software
  * Could cause data loss
  * Involves network operations with unknown endpoints"""
    
    @staticmethod
    def get_error_fix_prompt(command: str, error: str, stdout: str = "", exit_code: int = 1) -> str:
        """Build prompt for error fixing"""
        return f"""Fix this error:

Command executed: {command}
Exit code: {exit_code}
Error output: {error}
Standard output: {stdout}

Analyze this error and provide:
1. The most likely fix command
2. Clear explanation of what went wrong
3. Alternative solutions for different possible causes
4. Any necessary prerequisites or checks"""
    
    @staticmethod
    def get_context_aware_prompt(base_query: str, context: Dict) -> str:
        """Build context-aware prompt with additional information"""
        prompt_parts = [base_query]
        
        if 'git_info' in context:
            prompt_parts.append(f"\nGit context: {context['git_info']}")
        
        if 'system_info' in context:
            prompt_parts.append(f"\nSystem info: {context['system_info']}")
        
        if 'directory_info' in context:
            prompt_parts.append(f"\nDirectory context: {context['directory_info']}")
        
        if 'package_manager' in context:
            prompt_parts.append(f"\nPackage manager: {context['package_manager']}")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def get_ollama_optimized_prompt(prompt: str, model: str) -> str:
        """Optimize prompts for specific Ollama models"""
        # Model-specific optimizations
        if 'deepseek' in model.lower():
            # DeepSeek models work well with structured thinking
            return f"""<thinking>
Let me analyze this request step by step.
</thinking>

{prompt}

Remember to respond with valid JSON only."""
        
        elif 'qwen' in model.lower():
            # Qwen models are good with direct instructions
            return f"""{prompt}

Output only valid JSON matching the specified format."""
        
        elif 'llama' in model.lower():
            # Llama models benefit from examples
            return f"""{prompt}

Example response:
{{"command": "ls -la", "explanation": "Lists all files with details", "risks": [], "alternatives": ["ls -l", "ls -a"], "safe_to_auto_execute": true}}"""
        
        return prompt
    
    @staticmethod
    def format_ollama_messages(system_prompt: str, user_prompt: str, model: str) -> str:
        """Format messages for Ollama API"""
        # Ollama expects a simple prompt format
        optimized_user = PromptBuilder.get_ollama_optimized_prompt(user_prompt, model)
        
        # Combine system and user prompts
        full_prompt = f"""{system_prompt}

USER REQUEST: {optimized_user}

ASSISTANT RESPONSE (JSON only):"""
        
        return full_prompt
    
    @staticmethod
    def validate_json_response(response: str) -> Dict:
        """Validate and clean JSON response from AI"""
        import json
        import re
        
        # Clean common issues
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith('```'):
            response = re.sub(r'^```[a-z]*\n', '', response)
            response = re.sub(r'\n```$', '', response)
        
        # Extract JSON if wrapped in text
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Return safe fallback
            return {
                "command": "echo 'Error parsing AI response'",
                "explanation": f"AI response was not valid JSON: {str(e)}",
                "risks": ["Response parsing failed"],
                "alternatives": [],
                "safe_to_auto_execute": False
            }