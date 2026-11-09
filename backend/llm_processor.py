"""
Background Processing Queue for LLM-based content analysis using Ollama
"""
import json
import logging
import time
from typing import Dict, Any, Optional
import requests

try:
    from models_extended import ClipboardEvent, ActivityEvent, CommandEvent, db
except ImportError:
    from .models_extended import ClipboardEvent, ActivityEvent, CommandEvent, db

logger = logging.getLogger(__name__)


class OllamaProcessor:
    """Process events with Ollama LLM for summarization and tagging"""
    
    def __init__(self, ollama_url: str = 'http://localhost:11434', model: str = 'mistral'):
        """
        Initialize Ollama processor
        
        Args:
            ollama_url: URL to Ollama service
            model: Model to use for processing (default: mistral)
        """
        self.ollama_url = ollama_url
        self.model = model
        self.timeout = 30
    
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f'{self.ollama_url}/api/tags', timeout=5)
            return response.status_code == 200
        except (requests.RequestException, OSError):
            logger.warning('Ollama service not available')
            return False
    
    def get_available_models(self) -> list:
        """Get list of available models in Ollama"""
        try:
            response = requests.get(f'{self.ollama_url}/api/tags', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m.get('name') for m in data.get('models', [])]
            return []
        except Exception as e:
            logger.error(f'Failed to get Ollama models: {e}')
            return []
    
    def generate_summary(self, content: str, content_type: str = 'text', max_length: int = 200) -> str:
        """
        Generate a summary of content using Ollama
        
        Args:
            content: Content to summarize
            content_type: Type of content (text, code, json, url)
            max_length: Maximum length of summary
            
        Returns:
            Summary text
        """
        if not self.is_available():
            logger.warning('Ollama not available, skipping summarization')
            return ''
        
        if len(content) < 50:
            return content  # Don't summarize short content
        
        # Truncate very long content
        if len(content) > 2000:
            content = content[:2000] + '...'
        
        prompt = self._build_summary_prompt(content, content_type, max_length)
        
        try:
            response = requests.post(
                f'{self.ollama_url}/api/generate',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False,
                    'temperature': 0.3,  # Lower temperature for consistency
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('response', '').strip()
                return summary[:max_length]  # Ensure max length
            else:
                logger.error(f'Ollama returned status {response.status_code}')
                return ''
        except requests.Timeout:
            logger.warning('Ollama processing timeout')
            return ''
        except Exception as e:
            logger.error(f'Failed to generate summary: {e}')
            return ''
    
    def extract_tags(self, content: str, summary: str = '', max_tags: int = 5) -> list:
        """
        Extract tags from content using Ollama
        
        Args:
            content: Content to extract tags from
            summary: Optional summary for context
            max_tags: Maximum number of tags to extract
            
        Returns:
            List of tags
        """
        if not self.is_available():
            return []
        
        # Truncate for tagging
        if len(content) > 1000:
            content = content[:1000]
        
        prompt = self._build_tagging_prompt(content, summary, max_tags)
        
        try:
            response = requests.post(
                f'{self.ollama_url}/api/generate',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False,
                    'temperature': 0.2,
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                tags = self._parse_tags(response_text)
                return tags[:max_tags]
            return []
        except Exception as e:
            logger.error(f'Failed to extract tags: {e}')
            return []
    
    def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """
        Analyze sentiment of content using Ollama
        
        Args:
            content: Content to analyze
            
        Returns:
            Dict with sentiment info
        """
        if not self.is_available():
            return {}
        
        if len(content) < 20:
            return {}
        
        # Truncate for analysis
        if len(content) > 500:
            content = content[:500]
        
        prompt = f"Analyze the sentiment of this text in one word (positive/neutral/negative): {content}"
        
        try:
            response = requests.post(
                f'{self.ollama_url}/api/generate',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False,
                    'temperature': 0.1,
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                sentiment = result.get('response', '').strip().lower()
                
                # Normalize sentiment
                if 'positive' in sentiment:
                    return {'sentiment': 'positive', 'confidence': 0.8}
                elif 'negative' in sentiment:
                    return {'sentiment': 'negative', 'confidence': 0.8}
                else:
                    return {'sentiment': 'neutral', 'confidence': 0.6}
            return {}
        except Exception as e:
            logger.error(f'Failed sentiment analysis: {e}')
            return {}
    
    def _build_summary_prompt(self, content: str, content_type: str, max_length: int) -> str:
        """Build a prompt for summarization"""
        if content_type == 'code':
            return f"Briefly summarize what this code does in {max_length} characters:\n{content}\n\nSummary:"
        elif content_type == 'json':
            return f"Describe the structure and purpose of this JSON in {max_length} characters:\n{content}\n\nDescription:"
        elif content_type == 'url':
            return f"If this is a URL, describe what it likely points to in {max_length} characters. If not a URL, summarize it:\n{content}\n\nDescription:"
        else:
            return f"Summarize this text in {max_length} characters:\n{content}\n\nSummary:"
    
    def _build_tagging_prompt(self, content: str, summary: str, max_tags: int) -> str:
        """Build a prompt for tag extraction"""
        context = f"{summary}\n\n" if summary else ""
        return f"Extract {max_tags} relevant tags (comma-separated) from this content:\n\n{context}{content}\n\nTags:"
    
    def _parse_tags(self, response: str) -> list:
        """Parse tags from Ollama response"""
        # Split by comma and clean up
        tags = [t.strip().lower() for t in response.split(',')]
        # Remove empty tags and limit length
        tags = [t for t in tags if t and len(t) < 30]
        return tags


class ProcessingQueue:
    """Manage processing queue for events"""
    
    def __init__(self, db, ollama_url: str = 'http://localhost:11434'):
        """Initialize processing queue"""
        self.db = db
        self.processor = OllamaProcessor(ollama_url=ollama_url)
        self.logger = logging.getLogger(__name__)
    
    def process_clipboard_event(self, event_id: int) -> bool:
        """
        Process a clipboard event with LLM
        
        Args:
            event_id: ID of clipboard event to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            event = ClipboardEvent.query.get(event_id)
            if not event:
                self.logger.error(f'Clipboard event {event_id} not found')
                return False
            
            if not event.raw_content:
                return False
            
            # Skip if already processed
            if event.processed_summary:
                return True
            
            # Detect content type
            metadata = {}
            if event.event_metadata:
                try:
                    metadata = json.loads(event.event_metadata) if isinstance(event.event_metadata, str) else event.event_metadata
                except (json.JSONDecodeError, TypeError):
                    pass

            content_analysis = metadata.get('content', {})
            content_type = 'text'
            if content_analysis.get('is_url'):
                content_type = 'url'
            elif content_analysis.get('is_code'):
                content_type = 'code'
            elif content_analysis.get('is_json'):
                content_type = 'json'
            
            # Generate summary
            summary = self.processor.generate_summary(event.raw_content, content_type)
            
            # Extract tags
            tags = self.processor.extract_tags(event.raw_content, summary)
            
            # Analyze sentiment
            sentiment = self.processor.analyze_sentiment(event.raw_content)
            
            # Update event
            event.processed_summary = summary
            event.tags = ','.join(tags) if tags else ''
            
            # Add sentiment to metadata
            if sentiment:
                if not metadata:
                    metadata = {}
                metadata['sentiment'] = sentiment
                event.event_metadata = json.dumps(metadata)
            
            self.db.session.commit()
            self.logger.info(f'Processed clipboard event {event_id}: {len(summary)} char summary, {len(tags)} tags')
            return True
            
        except Exception as e:
            self.logger.error(f'Failed to process clipboard event {event_id}: {e}')
            return False
    
    def process_command_event(self, event_id: int) -> bool:
        """
        Process a command event with LLM
        
        Args:
            event_id: ID of command event to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            event = CommandEvent.query.get(event_id)
            if not event:
                self.logger.error(f'Command event {event_id} not found')
                return False
            
            if not event.command:
                return False
            
            # Generate analysis/tags for command
            tags = self.processor.extract_tags(event.command, max_tags=3)
            
            # Build command info
            metadata = {}
            if event.event_metadata:
                try:
                    metadata = json.loads(event.event_metadata) if isinstance(event.event_metadata, str) else event.event_metadata
                except (json.JSONDecodeError, TypeError):
                    pass
            
            if tags:
                metadata['command_tags'] = tags
                event.event_metadata = json.dumps(metadata)
            
            self.db.session.commit()
            self.logger.info(f'Processed command event {event_id}: extracted {len(tags)} tags')
            return True
            
        except Exception as e:
            self.logger.error(f'Failed to process command event {event_id}: {e}')
            return False
    
    def process_unprocessed_events(self, limit: int = 10, event_type: str = 'clipboard') -> Dict[str, int]:
        """
        Process unprocessed events in batch
        
        Args:
            limit: Maximum number of events to process
            event_type: Type of events to process ('clipboard', 'command', 'all')
            
        Returns:
            Stats dict with processed/failed counts
        """
        stats = {'processed': 0, 'failed': 0, 'skipped': 0}
        
        try:
            if event_type in ('clipboard', 'all'):
                # Find unprocessed clipboard events
                unprocessed = ClipboardEvent.query.filter(
                    (ClipboardEvent.processed_summary == None) |
                    (ClipboardEvent.processed_summary == '')
                ).limit(limit).all()
                
                for event in unprocessed:
                    if self.process_clipboard_event(event.id):
                        stats['processed'] += 1
                    else:
                        stats['failed'] += 1
            
            if event_type in ('command', 'all'):
                # Find command events without tags
                unprocessed = CommandEvent.query.limit(limit).all()
                
                for event in unprocessed:
                    if self.process_command_event(event.id):
                        stats['processed'] += 1
                    else:
                        stats['failed'] += 1
        
        except Exception as e:
            self.logger.error(f'Batch processing error: {e}')
        
        return stats


def start_background_processor(app, db, ollama_url: str = 'http://localhost:11434', interval: int = 30):
    """
    Start background processor in a separate thread
    
    Args:
        app: Flask app instance
        db: Database instance
        ollama_url: URL to Ollama service
        interval: Processing interval in seconds
    """
    import threading
    
    def processor_loop():
        logger.info('Background processor started')
        
        with app.app_context():
            queue = ProcessingQueue(db, ollama_url)
            
            while True:
                try:
                    # Check if Ollama is available
                    if not queue.processor.is_available():
                        logger.debug('Ollama not available, waiting...')
                        time.sleep(interval)
                        continue
                    
                    # Process unprocessed events
                    stats = queue.process_unprocessed_events(limit=5, event_type='clipboard')
                    if stats['processed'] > 0 or stats['failed'] > 0:
                        logger.info(f'Processing cycle: {stats["processed"]} processed, {stats["failed"]} failed')
                    
                    time.sleep(interval)
                
                except Exception as e:
                    logger.error(f'Background processor error: {e}')
                    time.sleep(interval)
    
    # Start processor thread
    thread = threading.Thread(target=processor_loop, daemon=True)
    thread.start()
    logger.info('Background processor thread started')


# API endpoints for processing
def register_processing_routes(app, db):
    """Register API endpoints for processing"""
    from flask import jsonify, request
    
    queue = ProcessingQueue(db)
    
    @app.route('/api/processing/status', methods=['GET'])
    def processing_status():
        """Get processing status"""
        try:
            ollama_available = queue.processor.is_available()
            models = queue.processor.get_available_models() if ollama_available else []
            
            # Count unprocessed events
            unprocessed_clipboard = ClipboardEvent.query.filter(
                (ClipboardEvent.processed_summary == None) |
                (ClipboardEvent.processed_summary == '')
            ).count()
            
            return jsonify({
                'success': True,
                'status': {
                    'ollama_available': ollama_available,
                    'ollama_models': models,
                    'current_model': queue.processor.model,
                    'unprocessed_clipboard': unprocessed_clipboard
                }
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/processing/process/<int:event_id>', methods=['POST'])
    def process_event(event_id):
        """Process a specific event"""
        try:
            event_type = request.args.get('type', 'clipboard')
            
            if event_type == 'clipboard':
                success = queue.process_clipboard_event(event_id)
            elif event_type == 'command':
                success = queue.process_command_event(event_id)
            else:
                return jsonify({'success': False, 'error': 'Unknown event type'}), 400
            
            return jsonify({
                'success': success,
                'message': 'Event processed successfully' if success else 'Failed to process event'
            }), 200 if success else 500
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/processing/batch', methods=['POST'])
    def batch_process():
        """Process batch of unprocessed events"""
        try:
            data = request.get_json() or {}
            limit = data.get('limit', 10)
            event_type = data.get('type', 'clipboard')
            
            stats = queue.process_unprocessed_events(limit=limit, event_type=event_type)
            
            return jsonify({
                'success': True,
                'stats': stats
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
