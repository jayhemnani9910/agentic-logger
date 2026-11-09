"""
Activity Watcher Agent - Track active window/application
"""
import ast
import json
import os
import re
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
    
    @staticmethod
    def _call_window_calls(method: str, *args: str) -> Optional[str]:
        """Call the GNOME Window Calls extension and return its string result"""
        result = subprocess.run(
            ['gdbus', 'call', '--session',
             '--dest', 'org.gnome.Shell',
             '--object-path', '/org/gnome/Shell/Extensions/Windows',
             '--method', f'org.gnome.Shell.Extensions.Windows.{method}', *args],
            capture_output=True,
            timeout=2,
            text=True
        )
        if result.returncode != 0:
            return None
        return ast.literal_eval(result.stdout.strip())[0]

    def _read_gnome_window(self) -> Optional[tuple[str, Optional[str]]]:
        """Return (title, app name) of the focused window on GNOME Wayland"""
        listing = self._call_window_calls('List')
        if not listing:
            return None

        focused = next((window for window in json.loads(listing) if window.get('focus')), None)
        if not focused:
            return None

        title = focused.get('title') or self._call_window_calls('GetTitle', str(focused['id']))
        return (title, focused.get('wm_class')) if title else None

    def _read_x11_window(self) -> Optional[tuple[str, Optional[str]]]:
        """Return (title, no app name) of the focused window through xdotool"""
        result = subprocess.run(
            ['xdotool', 'getactivewindow', 'getwindowname'],
            capture_output=True,
            timeout=2,
            text=True
        )
        return (result.stdout.strip(), None) if result.returncode == 0 else None

    @staticmethod
    def _is_gnome_wayland() -> bool:
        return (os.environ.get('XDG_SESSION_TYPE') == 'wayland'
                and 'GNOME' in os.environ.get('XDG_CURRENT_DESKTOP', ''))

    def _get_active_window(self) -> Optional[Dict[str, Any]]:
        """Get current active window information"""
        read_window = self._read_gnome_window if self._is_gnome_wayland() else self._read_x11_window
        try:
            window = read_window()
        except (FileNotFoundError, subprocess.SubprocessError, OSError, ValueError, SyntaxError):
            return None

        if not window:
            return None

        window_title, app_name = window

        # Without a reported app name, fall back to parsing the title
        if not app_name:
            if ' - ' in window_title:
                app_name = window_title.split(' - ')[-1]
            elif ':' in window_title:
                app_name = window_title.split(':')[0]
            else:
                app_name = window_title

        url = None
        if any(browser in app_name.lower() for browser in
               ['firefox', 'chrome', 'chromium', 'safari', 'edge']):
            url = self._extract_browser_url(window_title)

        return {
            'window_title': window_title[:500],
            'application': app_name[:255],
            'url': url[:500] if url else None,
            'timestamp': datetime.utcnow()
        }

    @staticmethod
    def _extract_browser_url(window_title: str) -> Optional[str]:
        """Return a URL shown in a browser window title, if there is one"""
        match = re.search(r'https?://\S+', window_title)
        return match.group(0) if match else None

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

        if self._get_active_window() is None:
            if self._is_gnome_wayland():
                print("Warning: activity tracking needs the 'Window Calls' GNOME extension. No window data will be saved.")
            else:
                print("Warning: cannot read the active window (is xdotool installed?). No window data will be saved.")

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
        print("\n🪟 Activity Changed:")
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
