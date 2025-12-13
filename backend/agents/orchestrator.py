"""
Orchestrator Agent - Route events between processors
"""
from datetime import datetime
from typing import Optional, Dict, Any
import json

from agents.clipboard_watcher import ClipboardWatcher, ClipboardEventExtractor
from agents.ocr_agent import OCRAgent
from agents.activity_watcher import ActivityWatcher
from agents.command_logger import CommandLogger
from agents.llm_processor import LLMProcessor


class EventOrchestrator:
    """Orchestrate event processing pipeline"""
    
    def __init__(self, db_session=None, on_event_callback=None):
        """
        Initialize orchestrator
        Args:
            db_session: SQLAlchemy database session
            on_event_callback: Callback when event is processed
        """
        self.db_session = db_session
        self.on_event_callback = on_event_callback
        
        # Initialize agents
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
        
        if self.db_session:
            from models_extended import ActivityEvent
            
            event = ActivityEvent(
                window_title=activity_data['window_title'],
                application=activity_data['application'],
                url=activity_data.get('url'),
                metadata={'timestamp': activity_data['timestamp'].isoformat()}
            )
            self.db_session.add(event)
            self.db_session.commit()
            
            if self.on_event_callback:
                self.on_event_callback('activity', event.to_dict())
    
    def _process_text_event(self, content: str):
        """Process text clipboard event"""
        # Get context
        activity_info = self.activity_watcher.get_current()
        content_type = ClipboardEventExtractor.get_content_type(content)
        
        # Process with LLM
        llm_result = self.llm_processor.process_text_event(content)
        
        # Save to database
        if self.db_session:
            from models_extended import ClipboardEvent
            
            event = ClipboardEvent(
                content_type=content_type,
                raw_content=content,
                source_app=activity_info.get('application') if activity_info else None,
                source_url=activity_info.get('url') if activity_info else None,
                processed_summary=llm_result.get('processed', {}).get('summary'),
                tags=llm_result.get('processed', {}).get('tags')
            )
            self.db_session.add(event)
            self.db_session.commit()
            
            print(f"   Type: {content_type}")
            print(f"   Summary: {event.processed_summary}")
            print(f"   Tags: {event.tags}")
            
            if self.on_event_callback:
                self.on_event_callback('clipboard_text', event.to_dict())
    
    def _process_image_event(self, clipboard_data: Dict[str, Any]):
        """Process image clipboard event"""
        # Get context
        activity_info = self.activity_watcher.get_current()
        
        # Run OCR
        ocr_result = self.ocr_agent.process_clipboard_image()
        
        if not ocr_result or not ocr_result.get('success'):
            print(f"   OCR failed: {ocr_result.get('error') if ocr_result else 'Unknown'}")
            return
        
        extracted_text = ocr_result.get('extracted_text', '')
        
        # Process OCR text with LLM
        llm_result = self.llm_processor.process_text_event(extracted_text)
        
        # Save to database
        if self.db_session:
            from models_extended import ClipboardEvent, OCRResult
            
            event = ClipboardEvent(
                content_type='image',
                raw_content=extracted_text,
                source_app=activity_info.get('application') if activity_info else None,
                source_url=activity_info.get('url') if activity_info else None,
                image_path=ocr_result.get('image_path'),
                processed_summary=llm_result.get('processed', {}).get('summary'),
                tags=llm_result.get('processed', {}).get('tags')
            )
            self.db_session.add(event)
            self.db_session.flush()
            
            # Save OCR result
            ocr_entry = OCRResult(
                clipboard_event_id=event.id,
                extracted_text=extracted_text,
                confidence=ocr_result.get('confidence', 0.0)
            )
            self.db_session.add(ocr_entry)
            self.db_session.commit()
            
            print(f"   OCR: {extracted_text[:100]}")
            print(f"   Summary: {event.processed_summary}")
            print(f"   Tags: {event.tags}")
            
            if self.on_event_callback:
                self.on_event_callback('clipboard_image', event.to_dict())
    
    def start(self):
        """Start orchestrator"""
        if self.running:
            return
        
        self.running = True
        print("🚀 Event Orchestrator started")
        
        # Start all watchers
        self.clipboard_watcher.start()
        self.activity_watcher.start()
        
        # Start command monitoring if db available
        if self.db_session:
            self.command_logger.monitor_commands(
                on_command_callback=self._on_command_event,
                check_interval=5
            )
    
    def stop(self):
        """Stop orchestrator"""
        self.running = False
        self.clipboard_watcher.stop()
        self.activity_watcher.stop()
        print("🛑 Event Orchestrator stopped")
    
    def _on_command_event(self, command_data: Dict[str, Any]):
        """Handle command execution event"""
        print(f"\n💻 Command: {command_data['command'][:100]}")
        
        if self.db_session:
            from models_extended import CommandEvent
            
            event = CommandEvent(
                command=command_data['command'],
                user_name=command_data.get('user'),
                metadata={
                    'shell': command_data.get('shell'),
                    'timestamp': command_data['timestamp'].isoformat()
                }
            )
            self.db_session.add(event)
            self.db_session.commit()
            
            if self.on_event_callback:
                self.on_event_callback('command', event.to_dict())
    
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
        """RAG-style semantic search across clipboard events"""
        try:
            from models_extended import ClipboardEvent
            
            # Generate query embedding
            query_embedding = self.llm_processor.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Get all events with embeddings
            all_events = self.db_session.query(ClipboardEvent).filter(
                ClipboardEvent.embedding.isnot(None)
            ).order_by(ClipboardEvent.timestamp.desc()).limit(1000).all()
            
            if not all_events:
                return []
            
            # Calculate similarities using cosine similarity
            try:
                from sklearn.metrics.pairwise import cosine_similarity
                import numpy as np
                
                similarities = []
                for event in all_events:
                    if event.embedding:
                        similarity = cosine_similarity(
                            [query_embedding], 
                            [event.embedding]
                        )[0][0]
                        similarities.append({
                            'event': event.to_dict() if hasattr(event, 'to_dict') else {
                                'id': event.id,
                                'content': event.raw_content[:500],
                                'timestamp': event.timestamp.isoformat(),
                                'app': event.source_app
                            },
                            'similarity': float(similarity)
                        })
                
                # Sort by similarity and return top results
                similarities.sort(key=lambda x: x['similarity'], reverse=True)
                return similarities[:limit]
            except ImportError:
                # Fallback: simple keyword matching
                results = []
                for event in all_events[:limit]:
                    if query.lower() in event.raw_content.lower():
                        results.append({
                            'event': event.to_dict() if hasattr(event, 'to_dict') else {
                                'id': event.id,
                                'content': event.raw_content[:500],
                                'timestamp': event.timestamp.isoformat(),
                                'app': event.source_app
                            },
                            'similarity': 0.5
                        })
                return results
        except Exception as e:
            print(f"Semantic search error: {e}")
            import traceback
            traceback.print_exc()
            return []
