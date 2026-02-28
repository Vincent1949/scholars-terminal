#!/usr/bin/env python3
"""
LLM Failover System - Windows-Compatible Version
Handles automatic provider switching for embeddings and LLM responses
"""

import os
import logging
import time
from typing import List, Optional, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class LLMFailoverManager:
    """Manages failover between different LLM and embedding providers"""
    
    def __init__(self):
        self.embedding_providers = []
        self.llm_providers = []
        self.current_embedding_idx = 0
        self.current_llm_idx = 0
        
        # Track failures for each provider
        self.failure_counts = defaultdict(int)
        self.last_failure_time = defaultdict(float)
        self.cooldown_period = 300  # 5 minutes
        
        # Cost tracking
        self.cost_tracking = defaultdict(float)
        
        self._init_embedding_providers()
        self._init_llm_providers()
        logger.info("Failover system initialized")
    
    def _init_embedding_providers(self):
        """Initialize embedding providers in priority order"""
        
        # 1. OpenAI Embeddings (if available)
        try:
            import openai
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.embedding_providers.append({
                    'name': 'openai_embeddings',
                    'func': self._openai_embeddings,
                    'cost_per_1k': 0.0001  # $0.0001 per 1K tokens
                })
                logger.info("[OK] OpenAI embeddings available")
        except Exception as e:
            logger.warning(f"OpenAI embeddings not available: {e}")
        
        # 2. Local SentenceTransformers (always available, free)
        try:
            from sentence_transformers import SentenceTransformer
            self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_providers.append({
                'name': 'local_embeddings',
                'func': self._local_embeddings,
                'cost_per_1k': 0.0  # Free
            })
            logger.info("[OK] Local SentenceTransformers available")
        except Exception as e:
            logger.warning(f"Local embeddings not available: {e}")
        
        # 3. Ollama Embeddings (if server available)
        if self._check_ollama_available():
            try:
                import ollama
                # Check if nomic-embed-text is available
                models_response = ollama.list()
                
                # Handle both old and new Ollama API formats
                if isinstance(models_response, dict) and 'models' in models_response:
                    model_list = models_response['models']
                else:
                    model_list = models_response
                
                # Extract model names from various possible formats
                model_names = []
                for model in model_list:
                    if isinstance(model, dict):
                        # Try different possible keys
                        name = model.get('name') or model.get('model') or model.get('id', '')
                    else:
                        name = str(model)
                    model_names.append(name)
                
                if any('nomic-embed-text' in name for name in model_names):
                    self.embedding_providers.append({
                        'name': 'ollama_embeddings',
                        'func': self._ollama_embeddings,
                        'cost_per_1k': 0.0  # Free, local
                    })
                    logger.info("[OK] Ollama nomic-embed-text available")
            except Exception as e:
                logger.warning(f"Ollama embeddings not available: {e}")
        
        # 4. Deterministic Fallback (always works, no ML)
        self.embedding_providers.append({
            'name': 'deterministic_fallback',
            'func': self._deterministic_embeddings,
            'cost_per_1k': 0.0
        })
        
        logger.info(f"[INIT] Initialized {len(self.embedding_providers)} embedding providers")
        logger.info(f"[LIST] Embedding Priority: {[p['name'] for p in self.embedding_providers]}")
    
    def _init_llm_providers(self):
        """Initialize LLM providers in priority order"""
        
        # 1. Ollama Models (free, local - highest priority)
        ollama_available = self._check_ollama_available()
        logger.info(f"Ollama availability check: {ollama_available}")
        
        if ollama_available:
            try:
                import ollama
                models_response = ollama.list()
                
                # Handle both old and new Ollama API formats
                if isinstance(models_response, dict) and 'models' in models_response:
                    model_list = models_response['models']
                else:
                    model_list = models_response
                
                # Extract model names from various possible formats
                available_models = []
                for model in model_list:
                    if isinstance(model, dict):
                        # Try different possible keys
                        name = model.get('name') or model.get('model') or model.get('id', '')
                    else:
                        name = str(model)
                    available_models.append(name)
                
                logger.info(f"Available Ollama models: {available_models}")
                
                providers = []
                
                # Llama 3 (best overall)
                if any('llama3' in m for m in available_models):
                    providers.append({
                        'name': 'ollama_llama3',
                        'func': lambda prompt: self._ollama_generate(prompt, 'llama3:latest'),
                        'cost_per_1k': 0.0
                    })
                    logger.info("[OK] Llama 3 added")
                
                # CodeLlama (good for technical content)
                if any('codellama' in m for m in available_models):
                    providers.append({
                        'name': 'ollama_codellama',
                        'func': lambda prompt: self._ollama_generate(prompt, 'codellama:latest'),
                        'cost_per_1k': 0.0
                    })
                    logger.info("[OK] CodeLlama added")
                
                # GPT-OSS
                if any('gpt-oss' in m for m in available_models):
                    providers.append({
                        'name': 'ollama_gptoss',
                        'func': lambda prompt: self._ollama_generate(prompt, 'gpt-oss:latest'),
                        'cost_per_1k': 0.0
                    })
                    logger.info("[OK] GPT-OSS added")
                
                self.llm_providers.extend(providers)
                logger.info(f"[OK] {len(providers)} Ollama LLM(s) added to provider list")
                
            except Exception as e:
                logger.warning(f"Could not initialize Ollama LLMs: {e}")
        
        # 2. OpenAI GPT (paid, but reliable)
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.llm_providers.append({
                'name': 'openai_gpt',
                'func': self._openai_chat,
                'cost_per_1k': 0.002  # GPT-3.5-turbo pricing
            })
            logger.info("[OK] OpenAI LLM added (but may have quota limits)")
        
        # 3. Google Gemini (free tier available)
        google_key = os.getenv('GOOGLE_API_KEY')
        if google_key:
            self.llm_providers.append({
                'name': 'gemini',
                'func': self._gemini_chat,
                'cost_per_1k': 0.0  # Free tier
            })
            logger.info("[OK] Gemini LLM added")
        
        logger.info(f"[INIT] Total LLM providers initialized: {len(self.llm_providers)}")
        if self.llm_providers:
            logger.info(f"[LIST] LLM Priority Order: {[p['name'] for p in self.llm_providers]}")
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama server is running"""
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.status_code == 200:
                logger.info("[OK] Ollama server detected on localhost:11434")
                return True
        except Exception:
            pass
        return False
    
    def _should_retry_provider(self, provider_name: str) -> bool:
        """Check if provider is out of cooldown period"""
        if provider_name not in self.last_failure_time:
            return True
        
        time_since_failure = time.time() - self.last_failure_time[provider_name]
        return time_since_failure > self.cooldown_period
    
    def get_embeddings(self, text: str) -> Optional[List[float]]:
        """Get embeddings with automatic failover"""
        for provider_idx, provider in enumerate(self.embedding_providers):
            
            # Skip if in cooldown
            if not self._should_retry_provider(provider['name']):
                continue
            
            try:
                logger.info(f"[TRY] Attempting embeddings with {provider['name']}")
                embedding = provider['func'](text)
                
                if embedding is not None:
                    self.current_embedding_idx = provider_idx
                    logger.info(f"[SUCCESS] Successfully got embeddings from {provider['name']}")
                    return embedding
                    
            except Exception as e:
                logger.warning(f"[FAIL] Provider {provider['name']} failed: {e}")
                self.failure_counts[provider['name']] += 1
                self.last_failure_time[provider['name']] = time.time()
        
        # All providers failed - use deterministic fallback
        logger.warning("[FALLBACK] All embedding providers failed, using deterministic fallback")
        return self._deterministic_embeddings(text)
    
    def get_response(self, prompt: str, context: str = None, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Optional[str]:
        """Get LLM response with automatic failover
        
        Args:
            prompt: The user's question/prompt
            context: Optional context from retrieved documents
            max_tokens: Maximum tokens in response (default 1000)
            temperature: Temperature for response generation (default 0.7)
            **kwargs: Additional parameters (for compatibility)
        """
        # Combine context with prompt if provided
        if context:
            full_prompt = f"Context information:\n{context}\n\nQuestion: {prompt}\n\nAnswer:"
        else:
            full_prompt = prompt
            
        for provider_idx, provider in enumerate(self.llm_providers):
            
            # Skip if in cooldown
            if not self._should_retry_provider(provider['name']):
                continue
            
            try:
                logger.info(f"[TRY] Attempting response generation with {provider['name']}")
                response = provider['func'](full_prompt)
                
                if response:
                    self.current_llm_idx = provider_idx
                    logger.info(f"[SUCCESS] Successfully got response from {provider['name']}")
                    return response
                    
            except Exception as e:
                logger.warning(f"[FAIL] Provider {provider['name']} failed: {e}")
                self.failure_counts[provider['name']] += 1
                self.last_failure_time[provider['name']] = time.time()
        
        return None
    
    # Alias method for backward compatibility
    def generate_response(self, prompt: str, context: str = None, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Optional[str]:
        """Alias for get_response() - for backward compatibility
        
        Args:
            prompt: The user's question/prompt
            context: Optional context from retrieved documents
            max_tokens: Maximum tokens in response (default 1000)
            temperature: Temperature for response generation (default 0.7)
            **kwargs: Additional parameters (for compatibility)
        """
        return self.get_response(prompt, context, max_tokens, temperature, **kwargs)
    
    # ============================================
    # Embedding Provider Implementations
    # ============================================
    
    def _openai_embeddings(self, text: str) -> List[float]:
        """OpenAI embeddings"""
        import openai
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    
    def _local_embeddings(self, text: str) -> List[float]:
        """Local SentenceTransformers embeddings"""
        embedding = self.local_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def _ollama_embeddings(self, text: str) -> List[float]:
        """Ollama embeddings using nomic-embed-text"""
        import ollama
        response = ollama.embeddings(
            model='nomic-embed-text:latest',
            prompt=text
        )
        return response['embedding']
    
    def _deterministic_embeddings(self, text: str) -> List[float]:
        """Deterministic fallback embeddings (always works, no ML)"""
        import hashlib
        
        # Create a deterministic hash-based embedding
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to list of floats normalized to [-1, 1]
        embedding = [(b - 128) / 128.0 for b in hash_bytes]
        
        # Pad to 384 dimensions to match typical embedding sizes
        while len(embedding) < 384:
            embedding.extend(embedding[:min(384-len(embedding), len(embedding))])
        
        return embedding[:384]
    
    # ============================================
    # LLM Provider Implementations
    # ============================================
    
    def _ollama_generate(self, prompt: str, model: str) -> str:
        """Generate response using Ollama"""
        import ollama
        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
    
    def _openai_chat(self, prompt: str) -> str:
        """Generate response using OpenAI"""
        import openai
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def _gemini_chat(self, prompt: str) -> str:
        """Generate response using Google Gemini"""
        import google.generativeai as genai
        
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of failover system"""
        return {
            'current_embedding_provider': self.embedding_providers[self.current_embedding_idx]['name'],
            'current_llm_provider': self.llm_providers[self.current_llm_idx]['name'] if self.llm_providers else 'none',
            'failure_counts': dict(self.failure_counts),
            'cost_tracking': dict(self.cost_tracking),
            'available_providers': {
                'embeddings': [p['name'] for p in self.embedding_providers],
                'llm': [p['name'] for p in self.llm_providers]
            }
        }
    
    def reset_providers(self):
        """Reset to primary providers (useful after quota resets)"""
        self.current_embedding_idx = 0
        self.current_llm_idx = 0
        logger.info("Reset to primary providers")