"""
Activity Watcher Agent - Track active window/application
"""
import threading
import time
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any

class ActivityWatcher:
    """Watch active window and application"""
    
    def __init__(self, on_change_callback=None, check_interval=5.0):
        """
        Initialize activity watcher
        Args:
            on_change_callback: Function to call when active window changes
            check_interval: How often to check (seconds)
        """
        self.on_change_callback = on_change_callback
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.last_window = None
        self.last_app = None
    
    def _get_active_window(self) -> Optional[Dict[str, Any]]:
        """Get current active window information"""
        try:
            # Try xdotool (X11)
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowname'],
                capture_output=True,
                timeout=2,
                text=True
            )
            
            if result.returncode == 0:
                window_title = result.stdout.strip()
                
                # Try to extract application name
                if ' - ' in window_title:
                    app_name = window_title.split(' - ')[-1]
                elif ':' in window_title:
                    app_name = window_title.split(':')[0]
                else:
                    app_name = window_title
                
                # Extract URL if browser
                url = None
                if any(browser in app_name.lower() for browser in
                       ['firefox', 'chrome', 'chromium', 'safari', 'edge']):
                    url = self._extract_browser_url(window_title)
                
                return {
                    'window_title': window_title,
                    'application': app_name,
                    'url': url,
                    'timestamp': datetime.utcnow()
                }
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            pass
        
        return None
    
    def _extract_browser_url(self, window_title: str) -> Optional[str]:
        """Extract URL from browser window title"""
        try:
            if " - " in window_title:
                potential_url = window_title.split(" - ")[-1]
                if potential_url.startswith(("http://", "https://")):
                    return potential_url
            return None
        except Exception:
            return None
    
    def _check_activity(self):
        """Check if active window changed"""
        window_info = self._get_active_window()
        
        if not window_info:
            return
        
        current_window = window_info['window_title']
        current_app = window_info['application']
        
        # Check if changed
        if (current_window != self.last_window or current_app != self.last_app):
            self.last_window = current_window
            self.last_app = current_app
            
            if self.on_change_callback:
                self.on_change_callback(window_info)
    
    def _watch_loop(self):
        """Main watch loop"""
        while self.running:
            try:
                self._check_activity()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in activity watch loop: {e}")
                time.sleep(self.check_interval)
    
    def start(self):
        """Start watching activity"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        print(f"Activity watcher started (check interval: {self.check_interval}s)")
    
    def stop(self):
        """Stop watching activity"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Activity watcher stopped")
    
    def get_current(self) -> Optional[Dict[str, Any]]:
        """Get current window activity"""
        return self._get_active_window()


if __name__ == '__main__':
    # Test activity watcher
    def on_activity_change(info):
        print(f"\n🪟 Activity Changed:")
        print(f"   App: {info['application']}")
        print(f"   Window: {info['window_title']}")
        if info.get('url'):
            print(f"   URL: {info['url']}")
        print(f"   Time: {info['timestamp']}")
    
    watcher = ActivityWatcher(on_change_callback=on_activity_change, check_interval=2)
    watcher.start()
    
    try:
        print("Watching activity... (Ctrl+C to stop)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
        print("\nStopped")
