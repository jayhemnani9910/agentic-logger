"""
Command Logger Agent - Track shell commands executed
"""
import os
import subprocess
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any

class CommandLogger:
    """Log shell commands executed"""
    
    def __init__(self):
        """Initialize command logger"""
        self.bash_history_file = os.path.expanduser('~/.bash_history')
        self.zsh_history_file = os.path.expanduser('~/.zsh_history')
        self.last_position = 0
        self.commands_cache = []
    
    def _get_active_shell_history(self) -> tuple[Optional[str], int]:
        """Get the active shell history file and current position"""
        # Try bash first
        if os.path.exists(self.bash_history_file):
            try:
                with open(self.bash_history_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, 2)  # Seek to end
                    return self.bash_history_file, f.tell()
            except OSError:
                pass

        # Try zsh
        if os.path.exists(self.zsh_history_file):
            try:
                with open(self.zsh_history_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, 2)
                    return self.zsh_history_file, f.tell()
            except OSError:
                pass
        
        return None, 0
    
    def _parse_bash_history(self, lines: list[str]) -> list[Dict[str, Any]]:
        """Parse bash history lines"""
        commands = []
        for line in lines:
            if line.strip():
                commands.append({
                    'command': line.strip(),
                    'shell': 'bash',
                    'timestamp': datetime.utcnow()
                })
        return commands
    
    def _parse_zsh_history(self, lines: list[str]) -> list[Dict[str, Any]]:
        """Parse zsh history lines (extended format)"""
        commands = []
        for line in lines:
            if not line.strip():
                continue
            
            # Zsh history format: ": timestamp:0;command"
            if line.startswith(':'):
                parts = line.split(';', 1)
                if len(parts) == 2:
                    try:
                        timestamp_str = parts[0].split(':')[1]
                        timestamp = datetime.fromtimestamp(int(timestamp_str))
                        command = parts[1].strip()
                        commands.append({
                            'command': command,
                            'shell': 'zsh',
                            'timestamp': timestamp
                        })
                    except (ValueError, IndexError):
                        pass
            else:
                commands.append({
                    'command': line.strip(),
                    'shell': 'zsh',
                    'timestamp': datetime.utcnow()
                })
        
        return commands
    
    def get_recent_commands(self, limit: int = 100) -> list[Dict[str, Any]]:
        """Get recent shell commands"""
        history_file, current_pos = self._get_active_shell_history()
        
        if not history_file:
            return []
        
        try:
            with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Read from last position to end
                if self.last_position > 0:
                    f.seek(self.last_position)
                else:
                    f.seek(max(0, current_pos - 10000))  # Read last ~10KB
                
                lines = f.readlines()
                self.last_position = f.tell()
            
            # Parse based on shell type
            if 'zsh' in history_file:
                commands = self._parse_zsh_history(lines)
            else:
                commands = self._parse_bash_history(lines)
            
            return sorted(commands, key=lambda x: x['timestamp'], reverse=True)[:limit]
        
        except Exception as e:
            print(f"Error reading command history: {e}")
            return []
    
    def monitor_commands(self, on_command_callback=None, check_interval: int = 5):
        """Monitor for new commands in real-time"""
        def monitor_loop():
            last_command = None
            while True:
                try:
                    recent = self.get_recent_commands(limit=1)

                    if recent and recent[0]['command'] != last_command:
                        last_command = recent[0]['command']
                        if on_command_callback:
                            on_command_callback(recent[0])

                    time.sleep(check_interval)
                except Exception as e:
                    print(f"Error in command monitor: {e}")
                    time.sleep(check_interval)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        return thread


class SnoopyCommandLogger:
    """Alternative: Use Snoopy system library for command logging"""
    
    @staticmethod
    def is_available() -> bool:
        """Check if Snoopy is installed"""
        try:
            result = subprocess.run(
                ['snoopy', '-h'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            return False

    @staticmethod
    def get_snoopy_log_path() -> Optional[str]:
        """Get Snoopy log file path"""
        # Common locations
        paths = [
            '/var/log/snoopy.log',
            '/var/log/auth.log',
            '/var/log/messages'
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        return None
    
    @staticmethod
    def read_snoopy_logs(limit: int = 100) -> list[Dict[str, Any]]:
        """Read Snoopy logs"""
        log_path = SnoopyCommandLogger.get_snoopy_log_path()
        
        if not log_path:
            return []
        
        commands = []
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-limit:]
            
            for line in lines:
                if 'snoopy' in line.lower():
                    # Parse snoopy log format
                    # Example: ... snoopy[PID]: username:command
                    if 'username' in line or 'command' in line:
                        commands.append({
                            'command': line.strip(),
                            'source': 'snoopy',
                            'timestamp': datetime.utcnow()
                        })
        except OSError:
            pass

        return commands


if __name__ == '__main__':
    # Test command logger
    logger = CommandLogger()
    
    print("📝 Recent Commands:")
    recent = logger.get_recent_commands(limit=10)
    for cmd in recent:
        print(f"  {cmd['timestamp']}: {cmd['command']}")
    
    # Check Snoopy
    if SnoopyCommandLogger.is_available():
        print("\n✅ Snoopy available")
    else:
        print("\n❌ Snoopy not available")
        print("   Install with: sudo apt-get install snoopy")
