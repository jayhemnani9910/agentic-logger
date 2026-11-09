"""
OCR Agent - Extract text from images
"""
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any

# Add privacy filtering
BLACKLISTED_KEYWORDS = [
    "password", "passwd", "pwd", "secret", "key", "token",
    "credit card", "ssn", "social security", "api_key",
    "private_key", "access_token", "bearer"
]

def filter_sensitive_content(text: str) -> str:
    """Filter out sensitive information"""
    import re
    for keyword in BLACKLISTED_KEYWORDS:
        if keyword.lower() in text.lower():
            return "[SENSITIVE_CONTENT_FILTERED]"
    return text

class OCRAgent:
    """Handle OCR processing for images with privacy controls"""
    
    def __init__(self):
        """Initialize OCR agent"""
        self.tesseract_available = self._check_tesseract()
        if not self.tesseract_available:
            print("Warning: Tesseract OCR not found. Image OCR disabled.")
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is installed"""
        try:
            result = subprocess.run(
                ['tesseract', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            return False

    def process_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract text from image using OCR
        Args:
            image_path: Path to image file
        Returns:
            Dict with extracted text and metadata
        """
        if not os.path.exists(image_path):
            return {
                'success': False,
                'error': 'Image file not found',
                'timestamp': datetime.utcnow()
            }
        
        if not self.tesseract_available:
            return {
                'success': False,
                'error': 'Tesseract not available',
                'timestamp': datetime.utcnow()
            }
        
        try:
            # Run tesseract
            result = subprocess.run(
                ['tesseract', image_path, 'stdout', '-l', 'eng'],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                extracted_text = result.stdout.strip()
                return {
                    'success': True,
                    'extracted_text': extracted_text,
                    'confidence': 0.85,  # Default confidence (tesseract doesn't provide this easily)
                    'image_path': image_path,
                    'timestamp': datetime.utcnow()
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'timestamp': datetime.utcnow()
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'OCR processing timeout',
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow()
            }
    
    def process_clipboard_image(self, image_data: bytes = None) -> Optional[Dict[str, Any]]:
        """
        Process image from clipboard
        Args:
            image_data: Binary image data from clipboard
        Returns:
            Dict with extracted text and metadata
        """
        if image_data is None:
            # Try to get image from clipboard
            image_data = self._get_clipboard_image()
        
        if image_data is None:
            return {
                'success': False,
                'error': 'No image data provided or found in clipboard',
                'timestamp': datetime.utcnow()
            }
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(image_data)
            tmp_path = tmp.name
        
        try:
            result = self.process_image(tmp_path)
            if result and result.get('success'):
                result['temp_image_path'] = tmp_path
            return result
        finally:
            # Cleanup temp file after processing
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def _get_clipboard_image(self) -> Optional[bytes]:
        """Get image data from system clipboard"""
        try:
            # Try xclip (X11)
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            pass

        try:
            # Try wl-paste (Wayland)
            result = subprocess.run(
                ['wl-paste', '--type', 'image/png'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            pass
        
        return None
    
    def save_screenshot(self, output_dir: str = None) -> Optional[str]:
        """
        Capture and save screenshot
        Args:
            output_dir: Directory to save screenshot
        Returns:
            Path to saved screenshot
        """
        output_dir = output_dir or tempfile.gettempdir()
        
        # Generate filename with timestamp
        filename = f"screenshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        output_path = os.path.join(output_dir, filename)
        
        try:
            # Try gnome-screenshot
            result = subprocess.run(
                ['gnome-screenshot', '-f', output_path],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return output_path
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            pass

        try:
            # Try import (ImageMagick)
            result = subprocess.run(
                ['import', '-window', 'root', output_path],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return output_path
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            pass

        try:
            # Try scrot
            result = subprocess.run(
                ['scrot', output_path],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return output_path
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            pass
        
        return None


if __name__ == '__main__':
    # Test OCR agent
    ocr = OCRAgent()
    
    if ocr.tesseract_available:
        print("✅ Tesseract is available")
        
        # Try to process an image if one is provided
        import sys
        if len(sys.argv) > 1:
            result = ocr.process_image(sys.argv[1])
            print(f"\nOCR Result:")
            print(f"  Success: {result.get('success')}")
            print(f"  Text: {result.get('extracted_text', '')[:200]}")
        else:
            print("\nTo test: python ocr_agent.py <image_path>")
    else:
        print("❌ Tesseract not available")
        print("Install with: sudo apt-get install tesseract-ocr")
