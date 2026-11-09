"""
Orchestrator Agent - The one event pipeline: capture, analyse, save
"""
import hashlib
import json
import os
import platform
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import numpy as np
import psutil

from agents.clipboard_watcher import ClipboardWatcher, ClipboardEventExtractor
from agents.ocr_agent import OCRAgent, filter_sensitive_content, SENSITIVE_PLACEHOLDER
from agents.activity_watcher import ActivityWatcher
from agents.command_logger import CommandLogger
from agents.llm_processor import LLMProcessor
from models_extended import ActivityEvent, ClipboardEvent, CommandEvent, OCRResult


class EventOrchestrator:
    """Orchestrate event processing pipeline"""

    def __init__(self, app, db, on_event_callback=None):
        """
        Initialize orchestrator
        Args:
            app: Flask app, used to give watcher threads an app context
            db: Flask-SQLAlchemy instance bound to app
            on_event_callback: Called as (event_type, event_dict) after each save
        """
        self.app = app
        self.db = db
        self.on_event_callback = on_event_callback

        self.clipboard_watcher = ClipboardWatcher(
            on_change_callback=self._on_clipboard_event
        )
        self.activity_watcher = ActivityWatcher(
            on_change_callback=self._on_activity_event
        )
        self.ocr_agent = OCRAgent()
        self.llm_processor = LLMProcessor()
        self.command_logger = CommandLogger()

        self.running = False

    def _emit(self, event_type: str, event):
        if self.on_event_callback:
            self.on_event_callback(event_type, event.to_dict())

    @staticmethod
    def _system_info() -> Dict[str, Any]:
        return {
            'hostname': os.getenv('HOSTNAME', 'unknown'),
            'user': os.getenv('USER', 'unknown'),
            'os': platform.system(),
            'os_version': platform.release(),
            'machine': platform.machine(),
            'python_version': platform.python_version(),
        }

    @staticmethod
    def _system_state() -> Dict[str, Any]:
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'process_count': len(psutil.pids()),
            }
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def _is_valid_json(content: str) -> bool:
        try:
            json.loads(content)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    def _content_metadata(self, content: str) -> Dict[str, Any]:
        return {
            'content_length': len(content),
            'content_hash': hashlib.sha256(content.encode()).hexdigest(),
            'is_url': content.strip().startswith(('http://', 'https://', 'ftp://')),
            'is_code': any(keyword in content.lower() for keyword in ['def ', 'class ', 'function ', 'import ', '<?php']),
            'is_json': self._is_valid_json(content),
            'line_count': len(content.split('\n')),
            'word_count': len(content.split()),
            'has_code_patterns': any(char in content for char in '{}()[]'),
        }

    def _analyse(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[list]]:
        """Return (summary, comma separated tags, embedding) for text"""
        if not text or text == SENSITIVE_PLACEHOLDER:
            return None, None, None

        summary = tags = None
        try:
            processed = self.llm_processor.process_text_event(text).get('processed', {})
            summary = processed.get('summary')
            tag_list = processed.get('tags')
            if isinstance(tag_list, list):
                tags = ','.join(str(tag).strip() for tag in tag_list)[:1000] or None
        except Exception as e:
            print(f"   LLM processing failed: {e}")

        return summary, tags, self.llm_processor.generate_embedding(text)

    def _clipboard_event(self, content: str, content_type: str, activity: Optional[Dict[str, Any]],
                         image_path: Optional[str] = None) -> ClipboardEvent:
        summary, tags, embedding = self._analyse(content)
        return ClipboardEvent(
            content_type=content_type,
            raw_content=content,
            source_app=activity.get('application') if activity else None,
            source_url=activity.get('url') if activity else None,
            image_path=image_path,
            processed_summary=summary,
            tags=tags,
            embedding=embedding,
            event_metadata={
                'content': self._content_metadata(content),
                'system': self._system_state(),
                'system_info': self._system_info(),
                'activity': {
                    'app': activity.get('application') if activity else None,
                    'window': activity.get('window_title') if activity else None,
                },
            },
        )

    def _on_clipboard_event(self, clipboard_data: Dict[str, Any]):
        """Handle clipboard change event"""
        print(f"\n📋 Clipboard Event: {clipboard_data['type']}")

        if clipboard_data['type'] == 'text':
            self._process_text_event(clipboard_data['content'])
        elif clipboard_data['type'] == 'image':
            self._process_image_event(clipboard_data['content'])

    def _process_text_event(self, content: str):
        """Process text clipboard event"""
        content = filter_sensitive_content(content)
        activity = self.activity_watcher.get_current()
        content_type = ClipboardEventExtractor.get_content_type(content)
        event = self._clipboard_event(content, content_type, activity)

        with self.app.app_context():
            self.db.session.add(event)
            self.db.session.commit()
            print(f"   Saved {content_type}, {len(content)} chars, summary: {bool(event.processed_summary)}")
            self._emit('clipboard_text', event)

    def _process_image_event(self, image_data: bytes):
        """Process image clipboard event"""
        activity = self.activity_watcher.get_current()
        ocr_result = self.ocr_agent.process_clipboard_image(image_data)

        if not ocr_result or not ocr_result.get('success'):
            print(f"   OCR failed: {ocr_result.get('error') if ocr_result else 'Unknown'}")
            return

        extracted_text = ocr_result.get('extracted_text', '')
        event = self._clipboard_event(extracted_text, 'image', activity, ocr_result.get('image_path'))

        with self.app.app_context():
            self.db.session.add(event)
            self.db.session.flush()
            self.db.session.add(OCRResult(
                clipboard_event_id=event.id,
                extracted_text=extracted_text,
                confidence=ocr_result.get('confidence', 0.0)
            ))
            self.db.session.commit()
            print(f"   Saved image, {len(extracted_text)} chars of OCR text")
            self._emit('clipboard_image', event)

    def _on_activity_event(self, activity_data: Dict[str, Any]):
        """Handle activity change event"""
        print(f"\n🪟 Activity: {activity_data['application']}")

        with self.app.app_context():
            event = ActivityEvent(
                window_title=activity_data['window_title'],
                application=activity_data['application'],
                url=activity_data.get('url'),
                event_metadata=json.dumps({
                    'timestamp': activity_data['timestamp'].isoformat(),
                    'system': self._system_state(),
                    'system_info': self._system_info(),
                })
            )
            self.db.session.add(event)
            self.db.session.commit()
            self._emit('activity', event)

    def _on_command_event(self, command_data: Dict[str, Any]):
        """Handle command execution event"""
        command = filter_sensitive_content(command_data['command'])
        print(f"\n💻 Command: {command[:100]}")

        with self.app.app_context():
            event = CommandEvent(
                command=command,
                user_name=command_data.get('user'),
                working_directory=command_data.get('cwd'),
                exit_code=command_data.get('exit_code'),
                event_metadata=json.dumps({
                    'shell': command_data.get('shell'),
                    'timestamp': command_data['timestamp'].isoformat(),
                    'system': self._system_state(),
                    'system_info': self._system_info(),
                    'duration': command_data.get('duration'),
                })
            )
            self.db.session.add(event)
            self.db.session.commit()
            self._emit('command', event)

    def start(self):
        """Start orchestrator"""
        if self.running:
            return

        self.running = True
        print("🚀 Event Orchestrator started")

        self.clipboard_watcher.start()
        self.activity_watcher.start()
        self.command_logger.monitor_commands(
            on_command_callback=self._on_command_event,
            check_interval=5
        )

    def stop(self):
        """Stop orchestrator"""
        self.running = False
        self.clipboard_watcher.stop()
        self.activity_watcher.stop()
        self.command_logger.stop()
        print("🛑 Event Orchestrator stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            'running': self.running,
            'clipboard_watcher': self.clipboard_watcher.running,
            'activity_watcher': self.activity_watcher.running,
            'llm_available': self.llm_processor.available,
            'ocr_available': self.ocr_agent.tesseract_available,
            'timestamp': datetime.utcnow().isoformat()
        }

    def semantic_search(self, query: str, limit: int = 20):
        """Rank saved clipboard events by cosine similarity to the query"""
        try:
            query_embedding = self.llm_processor.generate_embedding(query)
            if not query_embedding:
                return []

            events = ClipboardEvent.query.filter(
                ClipboardEvent.embedding.isnot(None)
            ).order_by(ClipboardEvent.timestamp.desc()).limit(1000).all()

            query_vector = np.array(query_embedding)
            results = []
            for event in events:
                vector = np.array(event.embedding)
                if vector.shape != query_vector.shape:
                    continue
                similarity = np.dot(query_vector, vector) / (np.linalg.norm(query_vector) * np.linalg.norm(vector))
                results.append({'event': event.to_dict(), 'similarity': float(similarity)})

            results.sort(key=lambda result: result['similarity'], reverse=True)
            return results[:limit]
        except Exception as e:
            print(f"Semantic search error: {e}")
            return []
