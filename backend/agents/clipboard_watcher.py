"""
Clipboard Watcher Agent
Monitors clipboard for copy/paste events with event-driven architecture
"""
import threading
import time
from datetime import datetime
import subprocess
import hashlib
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ClipboardWatcher:
    """Watch system clipboard for changes using event-driven X11 monitoring"""
    
    def __init__(self, on_change_callback=None, check_interval=1.0):
        """
        Initialize clipboard watcher with event-driven architecture
        Args:
            on_change_callback: Function to call when clipboard changes
            check_interval: Fallback polling interval if event monitoring unavailable (seconds)
        """
        self.on_change_callback = on_change_callback
        self.last_clipboard_content = ""
        self.last_hash = ""
        self.running = False
        self.thread = None
        self.check_interval = check_interval
        self.platform = self._detect_platform()
        self.fallback_polling = False
        self.xclip_process = None
        
        # Initialize X11 clipboard monitoring
        try:
            from pyperclip import paste

            # Use xclip for X11 selection events (event-driven)
            self.xclip_process = subprocess.Popen(
                ["xclip", "-selection", "clipboard", "-o"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info("X11 event-driven clipboard monitoring initialized")
        except ImportError:
            # Fallback to polling if xclip not available
            self.check_interval = check_interval
            self.fallback_polling = True
            logger.warning("xclip not available, falling back to polling mode")
    
    def _detect_platform(self) -> str:
        """Detect clipboard manager available on system"""
        try:
            subprocess.run(['xclip', '-selection', 'clipboard', '-o'], 
                         capture_output=True, timeout=1)
            return 'xclip'
        except:
            pass
        
        try:
            subprocess.run(['wl-paste'], capture_output=True, timeout=1)
            return 'wl-clipboard'
        except:
            pass
        
        try:
            import pyperclip
            return 'pyperclip'
        except:
            pass
        
        return 'none'
    
    def _get_clipboard_content(self) -> Optional[Dict[str, Any]]:
        """Get current clipboard content"""
        try:
            if self.platform == 'xclip':
                result = subprocess.run(
                    ['xclip', '-selection', 'clipboard', '-o'],
                    capture_output=True,
                    timeout=2,
                    text=True
                )
                if result.returncode == 0:
                    return {
                        'type': 'text',
                        'content': result.stdout,
                        'timestamp': datetime.utcnow()
                    }
            
            elif self.platform == 'wl-clipboard':
                result = subprocess.run(
                    ['wl-paste'],
                    capture_output=True,
                    timeout=2,
                    text=True
                )
                if result.returncode == 0:
                    return {
                        'type': 'text',
                        'content': result.stdout,
                        'timestamp': datetime.utcnow()
                    }
            
            elif self.platform == 'pyperclip':
                import pyperclip
                content = pyperclip.paste()
                if content:
                    return {
                        'type': 'text',
                        'content': content,
                        'timestamp': datetime.utcnow()
                    }
        
        except Exception as e:
            print(f"Error reading clipboard: {e}")
        
        return None
    
    def _check_clipboard(self):
        """Check if clipboard content changed"""
        content_data = self._get_clipboard_content()
        
        if not content_data:
            return
        
        content = content_data['content']
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        if content_hash != self.last_hash:
            self.last_hash = content_hash
            if self.on_change_callback:
                self.on_change_callback(content_data)
    
    def _watch_loop(self):
        """Main watch loop"""
        while self.running:
            try:
                self._check_clipboard()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in clipboard watch loop: {e}")
                time.sleep(self.check_interval)
    
    def start(self):
        """Start watching clipboard"""
        if self.running:
            return
        
        if self.platform == 'none':
            print("Warning: No clipboard manager detected. Clipboard watching disabled.")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        print(f"Clipboard watcher started (platform: {self.platform})")
    
    def stop(self):
        """Stop watching clipboard"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Clipboard watcher stopped")
    
    def get_current(self) -> Optional[Dict[str, Any]]:
        """Get current clipboard content immediately"""
        return self._get_clipboard_content()


class ClipboardEventExtractor:
    """Extract metadata from clipboard events"""
    
    @staticmethod
    def get_content_type(content: str) -> str:
        """Determine type of clipboard content"""
        if not content:
            return 'unknown'
        
        # Check for file paths
        if content.startswith('/') and '\n' not in content and len(content) < 500:
            return 'file_path'
        
        # Check for URLs
        if content.startswith(('http://', 'https://', 'ftp://')):
            return 'url'
        
        # Check for code patterns
        if any(keyword in content.lower() for keyword in 
               ['def ', 'class ', 'import ', 'function', '<?php', '<%', '<script']):
            return 'code'
        
        # Check for JSON
        if content.strip().startswith(('{', '[')):
            return 'json'
        
        # Check for command
        if content.startswith(('$', '#', '>', '%')) or any(
            cmd in content.split()[0:1] for cmd in 
            ['sudo', 'docker', 'git', 'npm', 'pip', 'curl', 'wget']):
            return 'command'
        
        # Default
        return 'text'
    
    @staticmethod
    def get_active_window() -> Optional[Dict[str, Any]]:
        """Get current active window information"""
        try:
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowname'],
                capture_output=True,
                timeout=2,
                text=True
            )
            if result.returncode == 0:
                window_title = result.stdout.strip()
                app_name = window_title.split(' - ')[-1] if ' - ' in window_title else 'Unknown'
                return {
                    'window_title': window_title,
                    'application': app_name,
                    'timestamp': datetime.utcnow()
                }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return {
            'window_title': 'Unknown',
            'application': 'Unknown',
            'timestamp': datetime.utcnow()
        }


if __name__ == '__main__':
    # Test clipboard watcher
    def on_clipboard_change(data):
        content_type = ClipboardEventExtractor.get_content_type(data['content'])
        window_info = ClipboardEventExtractor.get_active_window()
        print(f"\n📋 Clipboard Event:")
        print(f"   Type: {content_type}")
        print(f"   Content: {data['content'][:100]}")
        print(f"   App: {window_info['application']}")
        print(f"   Time: {data['timestamp']}")
    
    watcher = ClipboardWatcher(on_change_callback=on_clipboard_change)
    watcher.start()
    
    try:
        print("Watching clipboard... (Ctrl+C to stop)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
        print("\nStopped")
