"""
System information gathering for Shell AI Assistant
Provides context about the current environment
"""

import os
import platform
import subprocess
import socket
from typing import Dict, Optional, List
from pathlib import Path

class SystemInfo:
    """Gather system and environment information"""
    
    @staticmethod
    def get_os_info() -> Dict[str, str]:
        """Get operating system information"""
        info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': socket.gethostname()
        }
        
        # Get Linux distribution info
        if platform.system() == 'Linux':
            info['distro'] = SystemInfo._get_linux_distro()
        elif platform.system() == 'Darwin':
            info['distro'] = 'macOS'
        else:
            info['distro'] = platform.system()
        
        return info
    
    @staticmethod
    def _get_linux_distro() -> str:
        """Get Linux distribution name"""
        try:
            # Try modern method first
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            return line.split('=')[1].strip().strip('"')
                        elif line.startswith('NAME='):
                            distro_name = line.split('=')[1].strip().strip('"')
            
            # Fallback methods
            if os.path.exists('/etc/lsb-release'):
                result = subprocess.run(['lsb_release', '-d'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.split(':')[1].strip()
            
            # Check specific distro files
            distro_files = {
                '/etc/debian_version': 'Debian',
                '/etc/redhat-release': 'Red Hat',
                '/etc/fedora-release': 'Fedora',
                '/etc/arch-release': 'Arch Linux',
                '/etc/gentoo-release': 'Gentoo',
                '/etc/SuSE-release': 'openSUSE'
            }
            
            for file, distro in distro_files.items():
                if os.path.exists(file):
                    return distro
            
            return 'Unknown Linux'
            
        except Exception:
            return 'Linux'
    
    @staticmethod
    def get_shell_info() -> Dict[str, str]:
        """Get shell information"""
        info = {
            'shell': os.getenv('SHELL', 'unknown').split('/')[-1],
            'term': os.getenv('TERM', 'unknown'),
            'user': os.getenv('USER', 'unknown'),
            'home': os.getenv('HOME', 'unknown'),
            'path': os.getenv('PATH', ''),
            'pwd': os.getcwd()
        }
        
        # Get shell version if possible
        shell_name = info['shell']
        if shell_name in ['bash', 'zsh', 'fish']:
            try:
                result = subprocess.run([shell_name, '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    info['shell_version'] = result.stdout.split('\n')[0]
            except Exception:
                pass
        
        return info
    
    @staticmethod
    def get_package_manager() -> Optional[str]:
        """Detect the system package manager"""
        # Common package managers in order of preference
        managers = [
            ('apt', ['apt', '--version']),         # Debian/Ubuntu
            ('dnf', ['dnf', '--version']),         # Fedora/RHEL 8+
            ('yum', ['yum', '--version']),         # RHEL/CentOS
            ('pacman', ['pacman', '--version']),   # Arch
            ('zypper', ['zypper', '--version']),   # openSUSE
            ('brew', ['brew', '--version']),       # macOS/Linux
            ('apk', ['apk', '--version']),         # Alpine
            ('emerge', ['emerge', '--version']),   # Gentoo
            ('pkg', ['pkg', '--version']),         # FreeBSD
        ]
        
        for name, cmd in managers:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return name
            except FileNotFoundError:
                continue
        
        return None
    
    @staticmethod
    def get_git_info() -> Optional[Dict[str, str]]:
        """Get git repository information if in a git directory"""
        try:
            # Check if we're in a git repository
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return None
            
            info = {}
            
            # Get repository name
            result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                info['repo'] = os.path.basename(result.stdout.strip())
                info['repo_path'] = result.stdout.strip()
            
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                info['branch'] = result.stdout.strip() or 'detached HEAD'
            
            # Get status summary
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                modified = len([l for l in lines if l.strip()])
                info['modified_files'] = modified
                info['clean'] = modified == 0
            
            # Get remote info
            result = subprocess.run(['git', 'remote', '-v'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                info['has_remote'] = True
            else:
                info['has_remote'] = False
            
            return info
            
        except Exception:
            return None
    
    @staticmethod
    def get_directory_info(path: str = '.') -> Dict[str, any]:
        """Get information about a directory"""
        try:
            path_obj = Path(path).resolve()
            
            info = {
                'path': str(path_obj),
                'exists': path_obj.exists(),
                'is_writable': os.access(str(path_obj), os.W_OK),
                'is_readable': os.access(str(path_obj), os.R_OK)
            }
            
            if path_obj.exists() and path_obj.is_dir():
                # Count files and directories
                items = list(path_obj.iterdir())
                info['total_items'] = len(items)
                info['files'] = len([i for i in items if i.is_file()])
                info['directories'] = len([i for i in items if i.is_dir()])
                
                # Get size (simplified)
                try:
                    result = subprocess.run(['du', '-sh', str(path_obj)], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        info['size'] = result.stdout.split('\t')[0]
                except Exception:
                    pass
                
                # Check for common files
                common_files = ['.git', '.env', 'package.json', 'requirements.txt', 
                               'Makefile', 'Dockerfile', 'docker-compose.yml']
                info['special_files'] = [f for f in common_files 
                                       if (path_obj / f).exists()]
            
            return info
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_system_resources() -> Dict[str, str]:
        """Get system resource information"""
        info = {}
        
        # Memory info
        try:
            if platform.system() == 'Linux':
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            total = int(line.split()[1]) // 1024  # Convert to MB
                            info['memory_total'] = f"{total} MB"
                        elif line.startswith('MemAvailable:'):
                            avail = int(line.split()[1]) // 1024
                            info['memory_available'] = f"{avail} MB"
            elif platform.system() == 'Darwin':  # macOS
                result = subprocess.run(['sysctl', 'hw.memsize'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    bytes_val = int(result.stdout.split(':')[1].strip())
                    info['memory_total'] = f"{bytes_val // (1024**2)} MB"
        except Exception:
            pass
        
        # CPU info
        try:
            info['cpu_count'] = os.cpu_count()
            
            if platform.system() == 'Linux':
                result = subprocess.run(['nproc'], capture_output=True, text=True)
                if result.returncode == 0:
                    info['cpu_cores'] = result.stdout.strip()
        except Exception:
            pass
        
        # Disk info
        try:
            result = subprocess.run(['df', '-h', '.'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        info['disk_used'] = parts[2]
                        info['disk_available'] = parts[3]
                        info['disk_usage'] = parts[4]
        except Exception:
            pass
        
        return info
    
    @staticmethod
    def get_full_context() -> Dict[str, any]:
        """Get complete system context"""
        context = {
            'os': platform.system(),
            'distro': SystemInfo._get_linux_distro() if platform.system() == 'Linux' else platform.system(),
            'shell': os.getenv('SHELL', 'bash').split('/')[-1],
            'user': os.getenv('USER', 'user'),
            'cwd': os.getcwd(),
            'package_manager': SystemInfo.get_package_manager()
        }
        
        # Add optional context
        git_info = SystemInfo.get_git_info()
        if git_info:
            context['git_info'] = git_info
        
        return context