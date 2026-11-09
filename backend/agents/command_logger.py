"""
Command Logger Agent - Track shell commands executed
"""
import os
import threading
from datetime import datetime
from typing import Optional, Dict, Any

class CommandLogger:
    """Log shell commands executed"""
    
    def __init__(self):
        """Initialize command logger"""
        self.bash_history_file = os.path.expanduser('~/.bash_history')
        self.zsh_history_file = os.path.expanduser('~/.zsh_history')
        self.last_position = 0
        self.active_history = None
        self.commands_cache = []
        self._stop_event = threading.Event()

    def _get_active_shell_history(self) -> tuple[Optional[str], int]:
        """Get the most recently written shell history file and its end position"""
        existing = [path for path in (self.bash_history_file, self.zsh_history_file) if os.path.exists(path)]

        for history_file in sorted(existing, key=os.path.getmtime, reverse=True):
            try:
                with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, 2)  # Seek to end
                    return history_file, f.tell()
            except OSError:
                continue

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

        # File was trimmed, or another shell took over: carry on from its end
        if self.last_position > current_pos or (self.active_history and history_file != self.active_history):
            self.last_position = current_pos
        self.active_history = history_file

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
        """Log every command written to the history after this call"""
        self._stop_event.clear()
        self.active_history, self.last_position = self._get_active_shell_history()

        def monitor_loop():
            while not self._stop_event.wait(check_interval):
                try:
                    for command in reversed(self.get_recent_commands(limit=1000)):
                        if on_command_callback:
                            on_command_callback(command)
                except Exception as e:
                    print(f"Error in command monitor: {e}")

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        return thread

    def stop(self):
        """Stop monitoring commands"""
        self._stop_event.set()


if __name__ == '__main__':
    # Test command logger
    logger = CommandLogger()
    
    print("📝 Recent Commands:")
    recent = logger.get_recent_commands(limit=10)
    for cmd in recent:
        print(f"  {cmd['timestamp']}: {cmd['command']}")
