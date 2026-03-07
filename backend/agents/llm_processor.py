"""
LLM Processing Agent - Process clipboard content with local LLM
"""
import subprocess
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any

class LLMProcessor:
    """Process content with local LLM via Ollama"""
    
    def __init__(self, model: str = "qwen2.5:3b", ollama_url: str = "http://localhost:11434"):
        """
        Initialize LLM processor
        Args:
            model: Model to use (default: qwen2.5:3b)
            ollama_url: URL to Ollama server
        """
        self.model = model
        self.ollama_url = ollama_url
        self.available = self._check_ollama()
        self.embedding_model = None
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
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
            except:
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
            import numpy as np
            
            # Use Sentence Transformers for embedding generation
            try:
                from sentence_transformers import SentenceTransformer
                
                if not self.embedding_model:
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                
                embedding = self.embedding_model.encode([text])
                return embedding[0].tolist()
            except ImportError:
                # Fallback to simple hash-based embedding
                import hashlib
                hash_obj = hashlib.md5(text.encode())
                return [int(b) for b in hash_obj.digest()]
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
                return json.loads(result)
            except:
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
    


class OllamaManager:
    """Manage Ollama service"""
    
    @staticmethod
    def is_running() -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def start_ollama() -> bool:
        """Try to start Ollama service"""
        try:
            # Try common installation locations
            paths = [
                '/usr/local/bin/ollama',
                '/opt/ollama/bin/ollama',
                'ollama'
            ]
            
            for path in paths:
                try:
                    subprocess.Popen(
                        [path, 'serve'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return True
                except:
                    continue
        except:
            pass
        
        return False
    
    @staticmethod
    def pull_model(model: str = "qwen:3b") -> bool:
        """Pull a model from Ollama library"""
        try:
            result = subprocess.run(
                ['ollama', 'pull', model],
                timeout=300  # 5 minutes
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def list_models() -> list[str]:
        """List available models"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return [m['name'] for m in data.get('models', [])]
        except:
            pass
        
        return []


if __name__ == '__main__':
    # Test LLM processor
    print("🤖 LLM Processor Test")
    
    # Check Ollama
    if not OllamaManager.is_running():
        print("❌ Ollama not running")
        print("   Starting Ollama...")
        if OllamaManager.start_ollama():
            print("   ✅ Ollama started")
            import time
            time.sleep(5)
        else:
            print("   ❌ Failed to start Ollama")
            print("   Install from: https://ollama.ai")
            exit(1)
    else:
        print("✅ Ollama is running")
    
    # Check models
    models = OllamaManager.list_models()
    print(f"📦 Available models: {models}")
    
    if not models:
        print("   Pulling Qwen 3B...")
        if OllamaManager.pull_model("qwen:3b"):
            print("   ✅ Model pulled")
        else:
            print("   ❌ Failed to pull model")
    
    # Test processing
    processor = LLMProcessor()
    
    if processor.available:
        print("\n📝 Testing content processing...")
        test_content = "sudo apt update && apt install nginx"
        
        print(f"Input: {test_content}")
        
        # Classify
        classification = processor.classify_content(test_content)
        print(f"Classification: {classification}")
        
        # Summarize
        summary = processor.summarize_content(test_content)
        print(f"Summary: {summary}")
        
        # Tags
        tags = processor.extract_tags(test_content)
        print(f"Tags: {tags}")
    else:
        print("❌ LLM not available")
