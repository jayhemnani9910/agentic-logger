"""
LLM Processing Agent - Process clipboard content with local LLM
"""
import json
import os
import time
import requests
from datetime import datetime
from typing import Optional, Dict, Any

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3.5:4b')
AVAILABILITY_CHECK_SECONDS = 30

class LLMProcessor:
    """Process content with local LLM via Ollama"""
    
    def __init__(self, model: str = OLLAMA_MODEL, ollama_url: str = OLLAMA_URL):
        """
        Initialize LLM processor
        Args:
            model: Model to use
            ollama_url: URL to Ollama server
        """
        self.model = model
        self.ollama_url = ollama_url
        self.embedding_model = None
        self._available = False
        self._next_availability_check = 0.0
    
    @property
    def available(self) -> bool:
        """Whether Ollama is reachable, rechecked every AVAILABILITY_CHECK_SECONDS"""
        now = time.monotonic()
        if now >= self._next_availability_check:
            self._available = self._check_ollama()
            self._next_availability_check = now + AVAILABILITY_CHECK_SECONDS
        return self._available
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            return response.status_code == 200
        except (requests.RequestException, OSError):
            return False

    def _call_ollama(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """Call Ollama API"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
        except Exception as e:
            print(f"Error calling Ollama: {e}")
        
        return None
    
    def classify_content(self, content: str) -> Optional[Dict[str, Any]]:
        """Classify clipboard content"""
        if not self.available:
            return None
        
        prompt = f"""Classify this text and provide a brief description.

Text: {content[:500]}

Respond ONLY in JSON format:
{{"category": "string", "description": "brief description", "confidence": 0.0-1.0}}"""
        
        result = self._call_ollama(prompt, temperature=0.3)
        
        if result:
            try:
                return json.loads(result)
            except (json.JSONDecodeError, ValueError):
                return {
                    'category': 'text',
                    'description': result[:100],
                    'confidence': 0.5
                }
        
        return None
    
    def summarize_content(self, content: str, max_length: int = 150) -> Optional[str]:
        """Summarize clipboard content"""
        if not self.available:
            return None
        
        prompt = f"""Summarize the following text in {max_length} characters or less:

{content}

Summary:"""
        
        result = self._call_ollama(prompt, temperature=0.5)
        return result[:max_length] if result else None
    
    def generate_embedding(self, text: str) -> Optional[list]:
        """Generate vector embeddings for semantic search"""
        try:
            from sentence_transformers import SentenceTransformer
            
            if not self.embedding_model:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            return self.embedding_model.encode([text])[0].tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def extract_tags(self, content: str) -> Optional[list]:
        """Extract relevant tags from content"""
        if not self.available:
            return None
        
        prompt = f"""Extract 3-5 relevant tags for this text.

Text: {content[:500]}

Respond ONLY with a JSON array of tags:
["tag1", "tag2", "tag3"]"""
        
        result = self._call_ollama(prompt, temperature=0.3)
        
        if result:
            try:
                tags = json.loads(result)
                if isinstance(tags, list):
                    return tags
            except (json.JSONDecodeError, ValueError):
                pass
            return [tag.strip() for tag in result.split(',')[:5]]
        
        return None
    
    def process_text_event(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a clipboard text event"""
        result = {
            'raw_content': content,
            'timestamp': datetime.utcnow(),
            'processed': {}
        }
        
        if not self.available:
            return result
        
        # Classify
        classification = self.classify_content(content)
        if classification:
            result['processed']['classification'] = classification
        
        # Summarize
        summary = self.summarize_content(content)
        if summary:
            result['processed']['summary'] = summary
        
        # Extract tags
        tags = self.extract_tags(content)
        if tags:
            result['processed']['tags'] = tags
        
        return result
