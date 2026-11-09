"""
Clipboard Watcher Agent
Monitors clipboard for copy/paste events with event-driven architecture
"""
import os
import shutil
import sys
import threading
import time
from datetime import datetime
import subprocess
import hashlib
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# A copy that offers any of these is treated as text, even if it also has an image
TEXT_TARGETS = ('UTF8_STRING', 'STRING', 'TEXT', 'text/plain', 'text/plain;charset=utf-8')

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
        
        self.fallback_polling = self.platform == 'pyperclip' or self.platform == 'none'
    
    def _detect_platform(self) -> str:
        """Detect clipboard manager available on system"""
        # xclip exits non-zero on an empty clipboard too, so only a display error rules it out
        if os.environ.get('DISPLAY') and shutil.which('xclip'):
            try:
                result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'],
                                        capture_output=True, timeout=1, text=True, errors='ignore')
                if 'open display' not in result.stderr:
                    return 'xclip'
            except (subprocess.SubprocessError, OSError):
                pass

        if os.environ.get('WAYLAND_DISPLAY') and shutil.which('wl-paste'):
            return 'wl-clipboard'

        if sys.platform != 'linux':
            try:
                import pyperclip
                return 'pyperclip'
            except ImportError:
                pass

        return 'none'

    def _read_clipboard_image(self) -> Optional[bytes]:
        """Return PNG bytes when the clipboard holds an image and no text"""
        if self.platform == 'xclip':
            list_targets = ['xclip', '-selection', 'clipboard', '-t', 'TARGETS', '-o']
            read_image = ['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o']
        elif self.platform == 'wl-clipboard':
            list_targets = ['wl-paste', '--list-types']
            read_image = ['wl-paste', '--type', 'image/png']
        else:
            return None

        targets = subprocess.run(list_targets, capture_output=True, timeout=2, text=True)
        if targets.returncode != 0:
            return None

        available = targets.stdout.split()
        if 'image/png' not in available or any(target in available for target in TEXT_TARGETS):
            return None

        image = subprocess.run(read_image, capture_output=True, timeout=5)
        return image.stdout if image.returncode == 0 and image.stdout else None

    def _get_clipboard_content(self) -> Optional[Dict[str, Any]]:
        """Get current clipboard content"""
        try:
            image = self._read_clipboard_image()
            if image:
                return {
                    'type': 'image',
                    'content': image,
                    'timestamp': datetime.utcnow()
                }

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
        if not content:
            return

        content_bytes = content if isinstance(content, bytes) else content.encode()
        content_hash = hashlib.md5(content_bytes).hexdigest()

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
        if self.xclip_process:
            self.xclip_process.terminate()
            self.xclip_process = None
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
        is_text = data['type'] == 'text'
        content_type = ClipboardEventExtractor.get_content_type(data['content']) if is_text else 'image'
        window_info = ClipboardEventExtractor.get_active_window()
        print(f"\n📋 Clipboard Event:")
        print(f"   Type: {content_type}")
        preview = data['content'][:100] if is_text else f"{len(data['content'])} bytes"
        print(f"   Content: {preview}")
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
