#!/usr/bin/env python3
"""
Local Agent Runner - Runs monitoring agents locally and saves to Docker database

This script:
1. Runs clipboard/activity/command monitoring locally
2. Saves raw data to PostgreSQL database (running in Docker)
3. Processes data with LLM (if available)
4. Works with existing Docker setup

Usage:
    python local_agent_runner.py
"""

import os
import sys
import time
import json
import platform
import psutil
from datetime import datetime
from typing import Optional, Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from agents.clipboard_watcher import ClipboardWatcher
    from agents.activity_watcher import ActivityWatcher
    from agents.command_logger import CommandLogger
    from agents.llm_processor import LLMProcessor
    from agents.ocr_agent import OCRAgent
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the agentic_logger directory")
    sys.exit(1)

# Database setup
try:
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from models_extended import ClipboardEvent, ActivityEvent, CommandEvent, OCRResult
except ImportError:
    print("❌ Cannot import database models")
    sys.exit(1)

class LocalAgentRunner:
    """Run agents locally with database connection to Docker"""
    
    def __init__(self):
        self.running = False
        self.db_app = None
        self.db = None
        
        # Initialize database connection
        self._setup_database()
        
        # Initialize agents
        self.clipboard_watcher = ClipboardWatcher(on_change_callback=self._on_clipboard_event)
        self.activity_watcher = ActivityWatcher(on_change_callback=self._on_activity_event)
        self.command_logger = CommandLogger()
        self.llm_processor = LLMProcessor()
        self.ocr_agent = OCRAgent()
        
        print("🚀 Local Agent Runner initialized")
        print(f"📋 Clipboard platform: {self.clipboard_watcher.platform}")
        print(f"🗄️  Database: PostgreSQL (Docker)")
        print(f"💻 OS: {platform.system()} {platform.release()}")
        print(f"👤 User: {os.getenv('USER', 'unknown')}\n")
    
    def _get_system_metadata(self) -> Dict[str, Any]:
        """Capture system metadata"""
        try:
            return {
                'hostname': os.getenv('HOSTNAME', 'unknown'),
                'user': os.getenv('USER', 'unknown'),
                'os': platform.system(),
                'os_version': platform.release(),
                'machine': platform.machine(),
                'python_version': platform.python_version(),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_system_state(self) -> Dict[str, Any]:
        """Capture system state at event time"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'process_count': len(psutil.pids()),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_clipboard_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from clipboard content"""
        metadata = {
            'content_length': len(content),
            'content_hash': hash(content) % ((2**31) - 1),  # Positive hash
            'is_url': content.strip().startswith(('http://', 'https://', 'ftp://')),
            'is_code': any(keyword in content.lower() for keyword in ['def ', 'class ', 'function ', 'import ', '<?php']),
            'is_json': self._is_valid_json(content),
            'line_count': len(content.split('\n')),
            'word_count': len(content.split()),
            'has_code_patterns': bool(any(char in content for char in ['{', '}', '(', ')', '[', ']'])),
        }
        return metadata
    
    @staticmethod
    def _is_valid_json(content: str) -> bool:
        """Check if content is valid JSON"""
        try:
            json.loads(content)
            return True
        except (json.JSONDecodeError, ValueError):
            return False
    
    def _setup_database(self):
        """Setup Flask app and database connection"""
        self.db_app = Flask(__name__)
        
        # Connect to Docker database
        postgres_url = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/agentic_logger')
        self.db_app.config['SQLALCHEMY_DATABASE_URI'] = postgres_url
        self.db_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        self.db = SQLAlchemy(self.db_app)
        
        with self.db_app.app_context():
            self.db.create_all()
    
    def _on_clipboard_event(self, clipboard_data: Dict[str, Any]):
        """Handle clipboard change event"""
        print(f"\n📋 Clipboard Event: {clipboard_data['type']}")
        
        if clipboard_data['type'] == 'text':
            self._process_text_event(clipboard_data['content'])
        elif clipboard_data['type'] == 'image':
            self._process_image_event(clipboard_data)
    
    def _on_activity_event(self, activity_data: Dict[str, Any]):
        """Handle activity change event"""
        print(f"\n🪟 Activity: {activity_data['application']}")
        
        with self.db_app.app_context():
            from models_extended import ActivityEvent
            
            event = ActivityEvent(
                window_title=activity_data['window_title'],
                application=activity_data['application'],
                url=activity_data.get('url'),
                event_metadata=json.dumps({
                    'timestamp': activity_data['timestamp'].isoformat(),
                    'system': self._get_system_metadata(),
                    'state': self._get_system_state(),
                })
            )
            self.db.session.add(event)
            self.db.session.commit()
            print(f"   ✅ Activity saved with system metadata")
    
    def _on_command_event(self, command_data: Dict[str, Any]):
        """Handle command execution event"""
        command = command_data['command'][:100]
        print(f"\n💻 Command: {command}")
        
        with self.db_app.app_context():
            from models_extended import CommandEvent
            
            event = CommandEvent(
                command=command_data['command'],
                user_name=command_data.get('user'),
                working_directory=command_data.get('cwd'),
                exit_code=command_data.get('exit_code'),
                event_metadata=json.dumps({
                    'shell': command_data.get('shell'),
                    'timestamp': command_data['timestamp'].isoformat(),
                    'system': self._get_system_metadata(),
                    'state': self._get_system_state(),
                    'duration': command_data.get('duration'),
                })
            )
            self.db.session.add(event)
            self.db.session.commit()
            print(f"   ✅ Command saved with metadata")
    
    def _process_text_event(self, content: str):
        """Process text clipboard event"""
        # Get context
        activity_info = self.activity_watcher.get_current()
        
        # Extract content metadata
        content_metadata = self._get_clipboard_metadata(content)
        system_state = self._get_system_state()
        
        # Process with LLM if available
        processed_summary = None
        tags = None
        try:
            llm_result = self.llm_processor.process_text_event(content)
            processed_summary = llm_result.get('processed', {}).get('summary')
            tags = llm_result.get('processed', {}).get('tags')
        except Exception as e:
            print(f"   ⚠️  LLM processing failed: {e}")
        
        # Save to database
        with self.db_app.app_context():
            from models_extended import ClipboardEvent
            
            event = ClipboardEvent(
                content_type='text',
                raw_content=content,
                source_app=activity_info.get('application') if activity_info else None,
                source_url=activity_info.get('url') if activity_info else None,
                processed_summary=processed_summary,
                tags=str(tags) if tags else None,
                event_metadata=json.dumps({
                    'content': content_metadata,
                    'system': system_state,
                    'activity': {
                        'app': activity_info.get('application') if activity_info else None,
                        'window': activity_info.get('window_title') if activity_info else None,
                    }
                })
            )
            self.db.session.add(event)
            self.db.session.commit()
            
            print(f"   Type: text")
            print(f"   Length: {content_metadata['content_length']} chars")
            print(f"   Kind: {'🔗 URL' if content_metadata['is_url'] else '💻 Code' if content_metadata['is_code'] else '📝 Text'}")
            print(f"   Summary: {processed_summary[:50] if processed_summary else 'None'}...")
            print(f"   Tags: {tags}")
            print(f"   ✅ Clipboard saved with rich metadata")
    
    def _process_image_event(self, clipboard_data: Dict[str, Any]):
        """Process image clipboard event"""
        # Get context
        activity_info = self.activity_watcher.get_current()
        
        # Run OCR
        ocr_result = self.ocr_agent.process_clipboard_image()
        
        if not ocr_result or not ocr_result.get('success'):
            print(f"   ❌ OCR failed: {ocr_result.get('error') if ocr_result else 'Unknown'}")
            return
        
        extracted_text = ocr_result.get('extracted_text', '')
        
        # Process OCR text with LLM
        processed_summary = None
        tags = None
        try:
            llm_result = self.llm_processor.process_text_event(extracted_text)
            processed_summary = llm_result.get('processed', {}).get('summary')
            tags = llm_result.get('processed', {}).get('tags')
        except Exception as e:
            print(f"   ⚠️  LLM processing failed: {e}")
        
        # Save to database
        with self.db_app.app_context():
            from models_extended import ClipboardEvent, OCRResult
            
            event = ClipboardEvent(
                content_type='image',
                raw_content=extracted_text,
                source_app=activity_info.get('application') if activity_info else None,
                source_url=activity_info.get('url') if activity_info else None,
                image_path=ocr_result.get('image_path'),
                processed_summary=processed_summary,
                tags=tags
            )
            self.db.session.add(event)
            self.db.session.flush()
            
            # Save OCR result
            ocr_entry = OCRResult(
                clipboard_event_id=event.id,
                extracted_text=extracted_text,
                confidence=ocr_result.get('confidence', 0.0)
            )
            self.db.session.add(ocr_entry)
            self.db.session.commit()
            
            print(f"   OCR: {extracted_text[:100]}")
            print(f"   Summary: {processed_summary}")
            print(f"   Tags: {tags}")
            print(f"   ✅ Image clipboard saved to database")
    
    def start(self):
        """Start all monitoring agents"""
        if self.running:
            print("⚠️  Agents already running")
            return
        
        print("\n🚀 Starting Local Agent Runner...")
        
        # Start clipboard watcher
        if self.clipboard_watcher.platform != 'none':
            self.clipboard_watcher.start()
            print("✅ Clipboard watcher started")
        else:
            print("❌ Clipboard watcher not available (no xclip/xdotool)")
        
        # Start activity watcher
        self.activity_watcher.start()
        print("✅ Activity watcher started")
        
        # Start command monitoring
        self.command_logger.monitor_commands(
            on_command_callback=self._on_command_event,
            check_interval=5
        )
        print("✅ Command logger started")
        
        self.running = True
        print("\n🎯 Local agents are monitoring...")
        print("📊 Data will be saved to PostgreSQL database (Docker)")
        print("🌐 Frontend at http://localhost:3000 will show the data")
        print("\nPress Ctrl+C to stop")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping agents...")
            self.stop()
    
    def stop(self):
        """Stop all monitoring agents"""
        self.running = False
        
        if self.clipboard_watcher:
            self.clipboard_watcher.stop()
        if self.activity_watcher:
            self.activity_watcher.stop()
        
        print("✅ All agents stopped")

def main():
    """Main entry point"""
    print("🎯 Local Agent Runner for Agentic Logger")
    print("=" * 50)
    
    # Check if Docker database is running
    try:
        import psycopg2
        conn = psycopg2.connect(
            "postgresql://postgres:postgres@localhost:5432/agentic_logger"
        )
        conn.close()
        print("✅ Docker database connection verified")
    except Exception as e:
        print(f"❌ Cannot connect to Docker database: {e}")
        print("Make sure Docker containers are running:")
        print("   docker compose up -d postgres redis")
        sys.exit(1)
    
    # Start agent runner
    runner = LocalAgentRunner()
    runner.start()

if __name__ == '__main__':
    main()