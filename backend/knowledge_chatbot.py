#!/usr/bin/env python3
"""
AI Knowledge Base Chatbot with Learning, Personality, and Voice - Complete Application
Combines document processing with chat interface, learning system, personality customization, and voice output
Enhanced with LLM Failover System to handle API quota issues - CLAUDE
"""

import os
import sys
import logging
import time

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import json
from datetime import datetime
import uuid
import sqlite3
from collections import defaultdict, Counter

import gradio as gr
import chromadb
import fitz  # PyMuPDF
import numpy as np
import argparse

# Configure logging FIRST - before using logger anywhere
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Now we can use logger for everything below
try:
    from dotenv import load_dotenv  # type: ignore
    DOTENV_AVAILABLE = True
except Exception:
    DOTENV_AVAILABLE = False
    def load_dotenv():
        return None

import threading
import base64
import contextlib
import io

from concurrent.futures import ThreadPoolExecutor, as_completed

# Automatically load the .env file from the current directory or parent directories
if DOTENV_AVAILABLE:
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
else:
    logger.warning("dotenv not available - install with: pip install python-dotenv")

# Third-party imports (guarded)
try:
    import gradio as gr  # type: ignore
    GRADIO_AVAILABLE = True
except Exception:
    GRADIO_AVAILABLE = False
    gr = None

try:
    import fitz  # PyMuPDF  # type: ignore
    PYMuPDF_AVAILABLE = True
except Exception:
    PYMuPDF_AVAILABLE = False
    fitz = None

try:
    import chromadb  # type: ignore
    CHROMADB_AVAILABLE = True
except Exception:
    CHROMADB_AVAILABLE = False
    chromadb = None

try:
    import numpy as np  # type: ignore
    NUMPY_AVAILABLE = True
except Exception:
    NUMPY_AVAILABLE = False
    np = None

try:
    import openai  # type: ignore
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False
    openai = None

# NEW IMPORTS - Add failover system
try:
    from llm_failover_system import LLMFailoverManager  # type: ignore
except Exception as e:
    logger.warning(f"LLM Failover system not available: {e}")
    class LLMFailoverManager:  # minimal stub
        def get_status(self):
            return {
                "current_embedding_provider": None,
                "current_llm_provider": None,
                "failure_counts": {}
            }
        def reset_providers(self):
            return None

# Voice synthesis imports
VOICE_AVAILABLE = False
try:
    import pyttsx3
    VOICE_AVAILABLE = True
    # Suppress pyttsx3 debug logs
    _pyttsx3_logger = logging.getLogger('pyttsx3')
    _pyttsx3_logger.setLevel(logging.WARNING)
    for _name in ['pyttsx3.driver', 'pyttsx3.drivers', 'pyttsx3.engine']:
        _log = logging.getLogger(_name)
        _log.setLevel(logging.WARNING)
        _log.propagate = False
except ImportError:
    logger.warning("pyttsx3 not available. Voice features will be disabled.")
    VOICE_AVAILABLE = False


# Initialize OpenAI client
if OPENAI_AVAILABLE and (openai is not None):
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        openai.api_key = openai_key
        logger.info("OpenAI API key loaded successfully")
    else:
        logger.warning("OPENAI_API_KEY not found in environment")

try:
    # Optional client import
    if OPENAI_AVAILABLE:
        from openai import OpenAI  # type: ignore
    else:
        OpenAI = None  # type: ignore
except Exception:
    OpenAI = None  # type: ignore

def get_embeddings(texts):
    """
    DEPRECATED - This function is now handled by the failover system
    Kept for backward compatibility but will be replaced by failover manager calls
    """
    print("Warning: Direct get_embeddings() call detected. This should be handled by failover system.")
    if isinstance(texts, str):
        texts = [texts]

    # Guard against missing OpenAI dependency
    if not (OPENAI_AVAILABLE and (openai is not None)):
        print("OpenAI is not available. Returning None from get_embeddings().")
        return None

    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",  # Fast and cost-effective
            input=texts
        )

        # Extract embeddings from response
        embeddings = [item.embedding for item in response.data]
        return embeddings[0] if len(texts) == 1 else embeddings

    except Exception as e:
        print(f"OpenAI embedding error: {e}")
        return None

class VoiceSystem:
    """Handles text-to-speech with personality-based voice characteristics - IMPROVED"""

    def __init__(self):
        self.voice_enabled = VOICE_AVAILABLE
        self.engine = None
        self.voice_lock = threading.Lock()  # NEW - Thread safety
        self.voice_settings = {
            'enabled': True,
            'speed': 180,
            'volume': 0.8
        }
        self.female_voices = []
        self.male_voices = []

        if self.voice_enabled:
            self.init_voice_engine()

    def init_voice_engine(self):
        """Initialize TTS engine with improved Windows compatibility"""
        try:
            # Initialize COM for Windows
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except:
                pass  # Not on Windows or COM already initialized

            self.engine = pyttsx3.init()

            # Get voices
            voices = self.engine.getProperty('voices')
            logger.info(f"Found {len(voices)} voices:")

            # List all available voices for debugging
            for i, voice in enumerate(voices):
                logger.info(f"  Voice {i}: {voice.name}")

                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'index': i
                }

                # Improved gender detection
                voice_name_lower = voice.name.lower()
                if any(keyword in voice_name_lower for keyword in
                      ['female', 'woman', 'zira', 'hazel', 'susan', 'samantha', 'heather']):
                    self.female_voices.append(voice_info)
                    logger.info(f"    -> Detected as FEMALE voice")
                else:
                    self.male_voices.append(voice_info)

            # Set default voice
            if self.female_voices:
                selected_voice = self.female_voices[0]
                self.engine.setProperty('voice', selected_voice['id'])
                logger.info(f"Selected female voice: {selected_voice['name']}")
            elif voices:
                self.engine.setProperty('voice', voices[0].id)
                logger.info(f"No female voice found, using: {voices[0].name}")

            # Set default properties
            self.engine.setProperty('rate', self.voice_settings['speed'])
            self.engine.setProperty('volume', self.voice_settings['volume'])

            # TEST VOICE immediately on startup
            logger.info("Testing voice output at startup...")
            self.engine.say("Voice system initialized")
            self.engine.runAndWait()
            logger.info("Voice test completed!")

        except Exception as e:
            logger.error(f"Voice system initialization failed: {e}", exc_info=True)
            self.voice_enabled = False

    def speak_text(self, text: str, personality: str = 'assistant', background: bool = True):
        """Convert text to speech - IMPROVED VERSION"""
        if not self.voice_enabled:
            logger.warning("Voice system disabled")
            return

        if not self.voice_settings['enabled']:
            logger.warning("Voice output disabled by user")
            return

        if not self.engine:
            logger.error("Voice engine not initialized!")
            return

        def speak():
            try:
                # Initialize COM for this thread
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except:
                    pass

                # Acquire lock for thread safety
                with self.voice_lock:
                    # Clean text
                    clean_text = self.clean_text_for_speech(text)
                    if not clean_text:
                        logger.warning("No text to speak after cleaning")
                        return

                    logger.info(f"Speaking text: {clean_text[:50]}...")

                    # Apply personality settings
                    voice_settings = self.get_personality_voice_settings(personality)

                    self.engine.setProperty('rate', voice_settings['rate'])
                    self.engine.setProperty('volume', voice_settings['volume'])

                    # Use female voice if available
                    if self.female_voices:
                        self.engine.setProperty('voice', self.female_voices[0]['id'])

                    # Speak the text
                    self.engine.say(clean_text)
                    self.engine.runAndWait()

                    logger.info("Speech completed successfully")

            except Exception as e:
                logger.error(f"Text-to-speech error: {e}", exc_info=True)

        if background:
            thread = threading.Thread(target=speak, daemon=True)
            thread.start()
            logger.info("Started background voice thread")
        else:
            speak()

    def test_voice(self):
        """Test voice output immediately"""
        if not self.voice_enabled:
            return "Voice system disabled - pyttsx3 not available"

        if not self.engine:
            return "Voice engine not initialized"

        try:
            logger.info("Testing voice with direct call...")
            self.engine.say("This is Athena. Voice system test. If you can hear this, voice is working correctly.")
            self.engine.runAndWait()
            return "Voice test completed - Did you hear it?"
        except Exception as e:
            logger.error(f"Voice test failed: {e}", exc_info=True)
            return f"Voice test failed: {e}"

    def clean_text_for_speech(self, text: str) -> str:
        """Clean and prepare text for speech synthesis"""
        if not text:
            return ""

        import re

        # Remove citations and source references
        text = re.sub(r'\[Source \d+:.*?\]', '', text)
        text = re.sub(r'\(Relevance:.*?\)', '', text)

        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)

        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)

        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

        # Remove emojis and special symbols
        text = re.sub(r'[📚📊🎯📋⭐🎭💡🚀]', '', text)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Limit length
        if len(text) > 500:
            text = text[:500] + "..."

        return text

    def get_personality_voice_settings(self, personality: str) -> dict:
        """Get voice settings based on personality"""
        personality_voices = {
            'sage': {'rate': 160, 'volume': 0.8, 'pitch_preference': 'medium-low'},
            'mentor': {'rate': 170, 'volume': 0.9, 'pitch_preference': 'medium'},
            'explorer': {'rate': 190, 'volume': 0.9, 'pitch_preference': 'medium-high'},
            'assistant': {'rate': 180, 'volume': 0.8, 'pitch_preference': 'medium'},
            'specialist': {'rate': 165, 'volume': 0.7, 'pitch_preference': 'medium-low'}
        }
        return personality_voices.get(personality, personality_voices['assistant'])

    def get_voice_status(self) -> dict:
        """Get current voice system status"""
        return {
            'enabled': self.voice_enabled,
            'settings': self.voice_settings,
            'female_voices_available': len(self.female_voices) if self.voice_enabled else 0,
            'current_voice': self.female_voices[0]['name'] if self.voice_enabled and self.female_voices else None
        }

    def update_voice_settings(self, enabled=None, speed=None, volume=None):
        """Update voice settings"""
        if enabled is not None:
            self.voice_settings['enabled'] = enabled
        if speed is not None:
            self.voice_settings['speed'] = speed
        if volume is not None:
            self.voice_settings['volume'] = volume

class PersonalitySystem:
    """Manages AI personality, voice, and identity characteristics"""

    def __init__(self, db_path: str = "./data/personality.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.current_personality = "sage"  # Default personality
        self.custom_name = "Athena"  # Default AI name
        self.init_database()
        self.load_personality_profiles()

    def init_database(self):
        """Initialize personality preferences database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personality_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personality_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personality_used TEXT NOT NULL,
                user_rating INTEGER NOT NULL,
                response_style TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Set defaults if not exists
        cursor.execute('''
            INSERT OR IGNORE INTO personality_settings (setting_name, setting_value)
            VALUES ('ai_name', 'Athena'), ('current_personality', 'sage'), ('formality_level', '0.7')
        ''')

        conn.commit()
        conn.close()

    def load_personality_profiles(self):
        """Define different personality profiles"""
        self.personality_profiles = {
            'sage': {
                'name_suggestions': ['Athena', 'Minerva', 'Sophia', 'Aristotle'],
                'greeting_style': "I've carefully reviewed your document collection and found some insights that might help.",
                'uncertainty_phrase': "Based on the available sources, it appears that",
                'confidence_phrase': "Your documents clearly indicate that",
                'tone_description': "Scholarly but accessible, thoughtful and precise",
                'voice_characteristics': "Calm, measured pace with thoughtful pauses",
                'response_style': {
                    'formality': 0.8,
                    'detail_level': 0.9,
                    'citation_style': 'academic',
                    'explanation_depth': 'comprehensive'
                }
            },
            'mentor': {
                'name_suggestions': ['Professor', 'Guide', 'Mentor', 'Sage'],
                'greeting_style': "Let me help you understand this topic by drawing from your personal library.",
                'uncertainty_phrase': "From what I can see in your materials",
                'confidence_phrase': "Your collection provides strong evidence that",
                'tone_description': "Encouraging teacher, patient and explanatory",
                'voice_characteristics': "Warm, encouraging tone with clear articulation",
                'response_style': {
                    'formality': 0.7,
                    'detail_level': 0.8,
                    'citation_style': 'educational',
                    'explanation_depth': 'step_by_step'
                }
            },
            'explorer': {
                'name_suggestions': ['Scout', 'Navigator', 'Discovery', 'Quest'],
                'greeting_style': "Great question! Let me dive into your documents to uncover what we can find.",
                'uncertainty_phrase': "Interesting - the sources suggest",
                'confidence_phrase': "I've discovered something fascinating in your books:",
                'tone_description': "Enthusiastic researcher, curious and discovering",
                'voice_characteristics': "Energetic, faster pace with excitement in discoveries",
                'response_style': {
                    'formality': 0.5,
                    'detail_level': 0.7,
                    'citation_style': 'conversational',
                    'explanation_depth': 'exploratory'
                }
            },
            'assistant': {
                'name_suggestions': ['Helper', 'Companion', 'Partner', 'Ally'],
                'greeting_style': "I'm here to help! Let me check your documents for the information you need.",
                'uncertainty_phrase': "I'm not completely certain, but your documents suggest",
                'confidence_phrase': "I found exactly what you're looking for:",
                'tone_description': "Friendly and helpful, like a capable research assistant",
                'voice_characteristics': "Natural, conversational pace with friendly warmth",
                'response_style': {
                    'formality': 0.4,
                    'detail_level': 0.6,
                    'citation_style': 'friendly',
                    'explanation_depth': 'practical'
                }
            },
            'specialist': {
                'name_suggestions': ['Expert', 'Specialist', 'Authority', 'Master'],
                'greeting_style': "Drawing from your specialized collection, I can provide detailed insights.",
                'uncertainty_phrase': "The technical literature suggests",
                'confidence_phrase': "Your specialized sources confirm that",
                'tone_description': "Domain expert, technical and authoritative",
                'voice_characteristics': "Professional, precise delivery with authoritative confidence",
                'response_style': {
                    'formality': 0.9,
                    'detail_level': 1.0,
                    'citation_style': 'technical',
                    'explanation_depth': 'expert'
                }
            }
        }

    def get_personality_settings(self):
        """Get current personality settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT setting_name, setting_value FROM personality_settings')
        settings = dict(cursor.fetchall())

        conn.close()

        self.custom_name = settings.get('ai_name', 'Athena')
        self.current_personality = settings.get('current_personality', 'sage')

        return settings

    def update_personality_setting(self, setting_name: str, setting_value: str):
        """Update personality setting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO personality_settings (setting_name, setting_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (setting_name, setting_value))

        conn.commit()
        conn.close()

        # Update local settings
        if setting_name == 'ai_name':
            self.custom_name = setting_value
        elif setting_name == 'current_personality':
            self.current_personality = setting_value

    def get_subject_adapted_personality(self, detected_subjects: List[str]) -> str:
        """Adapt personality based on detected subjects"""
        subject_personality_map = {
            'mathematics': 'specialist',
            'programming': 'specialist',
            'science': 'specialist',
            'engineering': 'specialist',
            'medicine': 'specialist',
            'history': 'sage',
            'literature': 'sage',
            'philosophy': 'sage',
            'psychology': 'mentor',
            'business': 'mentor'
        }

        # Check if any detected subjects suggest a specific personality
        for subject in detected_subjects:
            if subject.lower() in subject_personality_map:
                adapted_personality = subject_personality_map[subject.lower()]
                logger.info(f"Adapting personality to '{adapted_personality}' for subject: {subject}")
                return adapted_personality

        return self.current_personality

    def generate_enhanced_system_message(self, context: str, detected_subjects: List[str],
                                       base_system_message: str) -> str:
        """Generate personality-enhanced system message"""

        # Get current settings
        settings = self.get_personality_settings()

        # Adapt personality based on subjects if enabled
        adaptive_enabled = settings.get('adaptive_personality', 'true').lower() == 'true'
        if adaptive_enabled:
            active_personality = self.get_subject_adapted_personality(detected_subjects)
        else:
            active_personality = self.current_personality

        profile = self.personality_profiles.get(active_personality, self.personality_profiles['sage'])

        # Build personality context
        personality_context = f"""
Your name is {self.custom_name} and you embody the '{active_personality}' personality profile.

Personality Characteristics:
- Tone: {profile['tone_description']}
- Voice Style: {profile['voice_characteristics']}
- Greeting Style: "{profile['greeting_style']}"
- When uncertain: "{profile['uncertainty_phrase']}"
- When confident: "{profile['confidence_phrase']}"
- Response Style: {profile['response_style']['citation_style']} citations, {profile['response_style']['explanation_depth']} explanations

Adapt your language and approach to match this personality while maintaining helpfulness and accuracy.
"""

        # Combine with base system message
        enhanced_message = f"{base_system_message}\n\n{personality_context}"

        return enhanced_message, active_personality

    def record_personality_feedback(self, personality_used: str, rating: int, response_style: str):
        """Record feedback for personality adaptation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO personality_feedback (personality_used, user_rating, response_style)
            VALUES (?, ?, ?)
        ''', (personality_used, rating, response_style))

        conn.commit()
        conn.close()

    def get_personality_stats(self):
        """Get personality usage and feedback statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Personality usage stats
        cursor.execute('''
            SELECT personality_used, AVG(user_rating) as avg_rating, COUNT(*) as usage_count
            FROM personality_feedback
            GROUP BY personality_used
            ORDER BY avg_rating DESC, usage_count DESC
        ''')

        stats = {
            'personality_ratings': [
                {
                    'personality': row[0],
                    'average_rating': round(row[1], 2),
                    'usage_count': row[2]
                } for row in cursor.fetchall()
            ],
            'current_name': self.custom_name,
            'current_personality': self.current_personality,
            'available_personalities': list(self.personality_profiles.keys())
        }

        conn.close()
        return stats

    def get_personality_customization_options(self):
        """Get options for personality customization"""
        return {
            'personalities': {
                name: {
                    'description': profile['tone_description'],
                    'voice_characteristics': profile['voice_characteristics'],
                    'suggested_names': profile['name_suggestions'],
                    'sample_greeting': profile['greeting_style']
                } for name, profile in self.personality_profiles.items()
            },
            'current_settings': self.get_personality_settings()
        }

class LearningSystem:
    """Simplified learning system integrated into the chatbot"""

    def __init__(self, db_path: str = "./data/learning.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.document_scores = defaultdict(float)
        self.init_database()

    def init_database(self):
        """Initialize learning database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                response_preview TEXT NOT NULL,
                rating INTEGER NOT NULL,
                sources_used TEXT NOT NULL,
                feedback_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_query TEXT NOT NULL,
                sources_found TEXT NOT NULL,
                user_rating INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def record_feedback(self, query: str, response: str, rating: int, sources: List[str], feedback_text: str = ""):
        """Record user feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        response_preview = response[:200] + "..." if len(response) > 200 else response

        cursor.execute('''
            INSERT INTO user_feedback (query, response_preview, rating, sources_used, feedback_text)
            VALUES (?, ?, ?, ?, ?)
        ''', (query, response_preview, rating, json.dumps(sources), feedback_text))

        conn.commit()
        conn.close()

        # Update document popularity scores
        rating_weight = rating / 5.0  # Convert 1-5 to 0-1
        for source in sources:
            self.document_scores[source] += rating_weight

        logger.info(f"Recorded feedback: {rating}/5 for sources {sources}")

    def get_document_boost_scores(self) -> Dict[str, float]:
        """Get learned boost scores for documents"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT sources_used, AVG(CAST(rating AS FLOAT)) as avg_rating, COUNT(*) as count
            FROM user_feedback
            WHERE rating >= 3
            GROUP BY sources_used
        ''')

        boost_scores = {}
        for row in cursor.fetchall():
            sources = json.loads(row[0])
            avg_rating = row[1]
            count = row[2]

            # Calculate boost: (average_rating - 3) * log(count + 1) * 0.1
            boost = (avg_rating - 3.0) * (count ** 0.5) * 0.1

            for source in sources:
                if source not in boost_scores:
                    boost_scores[source] = 0
                boost_scores[source] += boost

        conn.close()
        return boost_scores

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total feedback count
        cursor.execute("SELECT COUNT(*) FROM user_feedback")
        stats['total_feedback'] = cursor.fetchone()[0]

        # Average rating
        cursor.execute("SELECT AVG(CAST(rating AS FLOAT)) FROM user_feedback")
        result = cursor.fetchone()[0]
        stats['average_rating'] = round(result, 2) if result else 0

        # Most helpful documents
        cursor.execute('''
            SELECT sources_used, AVG(CAST(rating AS FLOAT)) as avg_rating, COUNT(*) as usage_count
            FROM user_feedback
            GROUP BY sources_used
            ORDER BY avg_rating DESC, usage_count DESC
            LIMIT 3
        ''')

        top_docs = []
        for row in cursor.fetchall():
            sources = json.loads(row[0])
            top_docs.append({
                'documents': sources,
                'rating': round(row[1], 2),
                'usage': row[2]
            })
        stats['top_documents'] = top_docs

        conn.close()
        return stats

class DocumentProcessor:
    """Handles document processing and text extraction with folder awareness"""

    def __init__(self, books_directory: str = "D:/Books"):
        self.books_directory = Path(books_directory)
        self.supported_formats = ['.pdf', '.epub']
        self.folder_subjects = {}  # Cache for folder subject mapping
        # Internal flags
        self._pdf_extractor_warned = False

    def extract_subject_from_path(self, file_path: Path) -> Tuple[str, str]:
        """Extract subject/category from folder structure
        Always returns a tuple: (primary_subject, subject_hierarchy)
        """
        relative_path = file_path.relative_to(self.books_directory)
        path_parts = relative_path.parts[:-1]  # Exclude filename

        if not path_parts:
            # No folder structure; default to general for both fields
            return "general", "general"

        # Use the deepest folder as primary subject
        primary_subject = path_parts[-1].lower()

        # Create hierarchical subject path
        subject_hierarchy = " > ".join(path_parts)

        return primary_subject, subject_hierarchy

    def find_documents_with_structure(self, limit: int = None) -> List[Dict[str, Any]]:
        """Find all documents with folder structure information - optimized for large collections"""
        logger.info(f"Scanning {self.books_directory} for documents with folder structure...")

        if not self.books_directory.exists():
            logger.error(f"Directory {self.books_directory} does not exist!")
            return []

        documents = []
        subject_counts = defaultdict(int)

        # Get all files first - DON'T limit discovery!
        all_files = []
        for ext in self.supported_formats:
            files = list(self.books_directory.glob(f"**/*{ext}"))
            all_files.extend(files)

        total_files = len(all_files)
        logger.info(f"Found {total_files} total documents in collection")

        # Process ALL files for metadata (this is fast!)
        for file_path in all_files:
            primary_subject, subject_hierarchy = self.extract_subject_from_path(file_path)

            doc_info = {
                'path': file_path,
                'primary_subject': primary_subject,
                'subject_hierarchy': subject_hierarchy,
                'filename': file_path.name,
                'relative_path': str(file_path.relative_to(self.books_directory)),
                'file_size': file_path.stat().st_size if file_path.exists() else 0
            }

            documents.append(doc_info)
            subject_counts[primary_subject] += 1

        # Log comprehensive folder structure discovered
        logger.info(f"Discovered {len(documents)} documents from {len(subject_counts)} subjects:")

        # Sort subjects by count for better logging
        for subject, count in sorted(subject_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  Subject {subject}: {count} documents")

        self.folder_subjects = dict(subject_counts)

        # Store collection metadata
        self.collection_stats = {
            'total_files_found': total_files,
            'files_discovered': len(documents),
            'subjects_detected': len(subject_counts),
            'largest_subject': max(subject_counts.items(), key=lambda x: x[1]) if subject_counts else None
        }

        return documents  # Return ALL documents, let initialize_system handle batching

    def extract_text_from_pdf(self, pdf_path: Path, max_pages: int = 10) -> str:
        """Extract text from PDF file"""
        # Guard missing PDF extractor
        if not (PYMuPDF_AVAILABLE and (fitz is not None)):
            if not self._pdf_extractor_warned:
                logger.warning("PDF extraction is unavailable (PyMuPDF/fitz not installed). Install 'pymupdf' to enable processing.")
                self._pdf_extractor_warned = True
            return ""
        try:
            doc = fitz.open(str(pdf_path))
            text = ""

            # Limit pages for faster processing
            page_count = min(max_pages, doc.page_count)
            for page_num in range(page_count):
                page = doc[page_num]
                text += page.get_text()

            doc.close()

            # Basic cleanup
            text = text.replace('\n\n', ' ').replace('\n', ' ').strip()
            return text

        except Exception as e:
            logger.error(f"Error extracting from {pdf_path.name}: {e}")
            return ""

    def create_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Create overlapping text chunks"""
        if not text.strip():
            return []

        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            if chunk_words:
                chunks.append(' '.join(chunk_words))

        return chunks if chunks else [text]

class VectorDatabase:
    """Handles vector database operations with FAILOVER embeddings"""

    def __init__(self, collection_name: str = "knowledge_base", db_path: str = "./data/vector_db"):
        self.collection_name = collection_name
        self.db_path = Path(db_path)
        self.client = None
        self.collection = None
        self.document_count = 0
        # NEW - Initialize failover manager for embeddings
        self.failover_manager = None
        self.embedding_dim = None  # will be set on first use

        # Create database directory if it doesn't exist
        self.db_path.mkdir(parents=True, exist_ok=True)

    def initialize(self, failover_manager=None):
        """Initialize the vector database with failover embedding support"""
        logger.info(f"Initializing persistent vector database at: {self.db_path.absolute()}")

        # Store failover manager reference
        self.failover_manager = failover_manager

        try:
            # Initialize ChromaDB with persistent storage
            self.client = chromadb.PersistentClient(path=str(self.db_path))

            # Create or get collection
            try:
                self.collection = self.client.create_collection(self.collection_name)
                logger.info(f"Created new collection: {self.collection_name}")
            except:
                self.collection = self.client.get_collection(self.collection_name)
                existing_count = self.collection.count()
                logger.info(f"Using existing collection: {self.collection_name} with {existing_count} documents")
                self.document_count = existing_count

            logger.info("Vector database initialized successfully with failover embeddings")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            return False

    def document_exists(self, doc_info: Dict[str, Any]) -> bool:
        """Check if document is already in the database using the document's relative path.
        Using only the filename (stem) can cause false positives across different folders.
        """
        try:
            rel_path = doc_info.get('relative_path')
            if not rel_path:
                # Fallback to doc_name if relative path missing
                doc_name = doc_info['path'].stem
                results = self.collection.get(where={"doc_name": doc_name})
                return len(results.get('ids', [])) > 0
            results = self.collection.get(where={"relative_path": rel_path})
            return len(results.get('ids', [])) > 0
        except Exception as e:
            logger.warning(f"document_exists check failed, assuming not present: {e}")
            return False

    def _local_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Deterministic local embedding fallback (no external deps)."""
        try:
            import hashlib, random
            h = hashlib.sha256(text.encode('utf-8')).digest()
            seed = int.from_bytes(h[:8], 'big')
            rnd = random.Random(seed)
            return [rnd.uniform(-1.0, 1.0) for _ in range(dim)]
        except Exception:
            # Last-resort fixed vector
            return [0.0] * dim

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Route embedding generation with safe fallbacks."""
        # Prefer failover manager if it provides get_embeddings
        try:
            if self.failover_manager and hasattr(self.failover_manager, 'get_embeddings') and callable(getattr(self.failover_manager, 'get_embeddings')):
                emb = self.failover_manager.get_embeddings(text)
                if emb is not None:
                    if self.embedding_dim is None:
                        self.embedding_dim = len(emb)
                    return emb
        except Exception as e:
            logger.warning(f"Failover embedding error, falling back: {e}")
        # Fallback to direct OpenAI helper if available
        try:
            emb = get_embeddings(text)
            if emb is not None:
                if self.embedding_dim is None:
                    self.embedding_dim = len(emb)
                return emb
        except Exception as e:
            logger.warning(f"OpenAI embedding error, falling back: {e}")
        # Local deterministic embedding fallback
        if self.embedding_dim is None:
            self.embedding_dim = 384
        return self._local_embedding(text, dim=self.embedding_dim)

    def add_document_with_structure(self, doc_info: Dict[str, Any], chunks: List[str]):
        """Add document chunks with folder structure information using FAILOVER embeddings"""
        if not chunks:
            return

        try:
            doc_path = doc_info['path']

            # Use safe embedding router with fallbacks
            embeddings = []
            for chunk in chunks:
                embedding = self._get_embedding(chunk)
                if embedding is None:
                    logger.error(f"Failed to generate embedding for chunk in {doc_path.name}")
                    return
                embeddings.append(embedding)

            if not embeddings:
                logger.error(f"No embeddings generated for {doc_path.name}")
                return

            # Create unique IDs based on relative path to avoid collisions across folders
            doc_name = doc_path.stem
            rel_path_for_id = doc_info.get('relative_path', str(doc_path))
            try:
                import hashlib
                path_hash = hashlib.sha1(rel_path_for_id.encode('utf-8')).hexdigest()[:10]
            except Exception:
                path_hash = "nohash"
            chunk_ids = [f"{doc_name}_{path_hash}_{i}" for i in range(len(chunks))]

            # Create enhanced metadata with folder structure
            metadatas = [{
                'source': str(doc_path),
                'doc_name': doc_name,
                'primary_subject': doc_info['primary_subject'],
                'subject_hierarchy': doc_info['subject_hierarchy'],
                'filename': doc_info['filename'],
                'relative_path': doc_info['relative_path'],
                'chunk_index': i,
                'timestamp': datetime.now().isoformat()
            } for i in range(len(chunks))]

            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=chunks,
                ids=chunk_ids,
                metadatas=metadatas
            )

            self.document_count += 1
            logger.info(f"Added {len(chunks)} chunks from {doc_name} ({doc_info['primary_subject']}) to database")

        except Exception as e:
            logger.error(f"Error adding document {doc_path.name}: {e}")

    def search_with_subject_boost(self, query: str, preferred_subjects: List[str] = None,
                                 n_results: int = 5) -> List[Dict[str, Any]]:
        """Search with subject-based boosting using FAILOVER embeddings"""
        try:
            # Use safe embedding router
            query_embedding = self._get_embedding(query)
            if query_embedding is None:
                logger.error("Failed to generate query embedding")
                return []

            # Get more results for subject filtering and boosting
            search_results = n_results * 3

            # Search database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=search_results
            )

            # Format and boost results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    base_relevance = 1 - distance

                    # Apply subject boost
                    subject_boost = 0
                    if preferred_subjects:
                        primary_subject = metadata.get('primary_subject', '').lower()
                        subject_hierarchy = metadata.get('subject_hierarchy', '').lower()

                        for pref_subject in preferred_subjects:
                            if pref_subject.lower() in primary_subject:
                                subject_boost += 0.15  # Primary subject match
                            elif pref_subject.lower() in subject_hierarchy:
                                subject_boost += 0.1   # Hierarchy match

                    final_relevance = min(1.0, base_relevance + subject_boost)

                    formatted_results.append({
                        'content': doc,
                        'source': metadata.get('doc_name', 'Unknown'),
                        'primary_subject': metadata.get('primary_subject', 'general'),
                        'subject_hierarchy': metadata.get('subject_hierarchy', ''),
                        'filename': metadata.get('filename', ''),
                        'relative_path': metadata.get('relative_path', ''),
                        'relevance': final_relevance,
                        'base_relevance': base_relevance,
                        'subject_boost': subject_boost,
                        'metadata': metadata
                    })

            # Sort by boosted relevance and return top results
            formatted_results.sort(key=lambda x: x['relevance'], reverse=True)
            return formatted_results[:n_results]

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_available_subjects(self) -> Dict[str, int]:
        """Get all available subjects and their document counts"""
        try:
            # If collection is not initialized yet, return empty without logging an error
            if not getattr(self, 'collection', None):
                return {}

            # Get all documents from collection
            all_docs = self.collection.get()

            subject_counts = defaultdict(int)
            if all_docs and all_docs.get('metadatas'):
                for metadata in all_docs['metadatas']:
                    subject = metadata.get('primary_subject', 'general')
                    subject_counts[subject] += 1

            return dict(subject_counts)

        except Exception as e:
            logger.warning(f"Error getting subjects: {e}")
            return {}

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant chunks using FAILOVER embeddings"""
        try:
            # Use safe embedding router
            query_embedding = self._get_embedding(query)
            if query_embedding is None:
                logger.error("Failed to generate query embedding")
                return []

            # Search database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )

            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    formatted_results.append({
                        'content': doc,
                        'source': metadata.get('doc_name', 'Unknown'),
                        'relevance': 1 - distance,  # Convert distance to relevance
                        'metadata': metadata
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def cleanup_deleted_documents(self):
        """Remove database entries for files that no longer exist on disk"""
        try:
            if not self.collection:
                logger.warning("Collection not initialized, skipping cleanup")
                return 0

            # Get all documents from collection
            all_docs = self.collection.get()

            if not all_docs or not all_docs.get('metadatas'):
                logger.info("No documents in collection to clean up")
                return 0

            deleted_count = 0
            ids_to_delete = []

            # Check each document to see if file still exists
            for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas']):
                source_path = metadata.get('source', '')

                if source_path:
                    file_path = Path(source_path)

                    # Check if file still exists
                    if not file_path.exists():
                        ids_to_delete.append(doc_id)
                        logger.info(f"Marking for deletion: {file_path.name} (file no longer exists)")

            # Delete all marked documents
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                deleted_count = len(ids_to_delete)
                logger.info(f"Cleaned up {deleted_count} document chunks from deleted files")
            else:
                logger.info("No deleted files found - database is clean")

            return deleted_count

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0

class KnowledgeBaseChatbot:
    """Main chatbot class with learning capabilities, subject awareness, personality system, voice, and LLM FAILOVER"""

    def __init__(self, skip_scan=False):
        self.skip_scan = skip_scan  # Store the flag
        self.doc_processor = DocumentProcessor()
        self.vector_db = VectorDatabase()
        self.learning_system = LearningSystem()
        self.personality_system = PersonalitySystem()
        self.voice_system = VoiceSystem()

        # NEW - Initialize failover manager
        self.failover_manager = LLMFailoverManager()
        logger.info("Failover system initialized")

        self.client = None
        self.processing_status = "Not initialized"
        self.documents_processed = 0
        self.session_id = str(uuid.uuid4())
        self.last_query = ""
        self.last_response = ""
        self.last_sources = []
        self.last_personality = "assistant"
        self.available_subjects = {}

        # Subject detection keywords
        self.subject_keywords = {
            'mathematics': ['math', 'mathematics', 'algebra', 'calculus', 'geometry', 'statistics', 'probability'],
            'programming': ['programming', 'code', 'coding', 'python', 'java', 'javascript', 'algorithm'],
            'science': ['science', 'physics', 'chemistry', 'biology', 'scientific'],
            'history': ['history', 'historical', 'ancient', 'medieval', 'war', 'civilization'],
            'literature': ['literature', 'novel', 'poetry', 'writing', 'author', 'book'],
            'business': ['business', 'management', 'finance', 'economics', 'marketing', 'strategy'],
            'philosophy': ['philosophy', 'philosophical', 'ethics', 'logic', 'metaphysics'],
            'psychology': ['psychology', 'psychological', 'behavior', 'mental', 'cognitive'],
            'engineering': ['engineering', 'mechanical', 'electrical', 'civil', 'technical'],
            'medicine': ['medicine', 'medical', 'health', 'anatomy', 'disease', 'treatment']
        }

    def detect_query_subjects(self, query: str) -> List[str]:
        """Detect relevant subjects from user query"""
        query_lower = query.lower()
        detected_subjects = []

        # Check against known subjects in the database
        for subject in self.available_subjects.keys():
            if subject.lower() in query_lower:
                detected_subjects.append(subject)

        # Check against keyword mappings
        for subject, keywords in self.subject_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                if subject not in detected_subjects and subject in self.available_subjects:
                    detected_subjects.append(subject)

        # Fallback: find partial matches with folder names
        if not detected_subjects:
            for subject in self.available_subjects.keys():
                if any(word in subject.lower() for word in query_lower.split()):
                    detected_subjects.append(subject)

        logger.info(f"Detected subjects for '{query}': {detected_subjects}")
        return detected_subjects

    def initialize_system(self, progress_callback=None, batch_size: int = 200, parallel_workers: Optional[int] = None):
        """Initialize the entire system with folder structure awareness and FAILOVER support.
        Adds parallelized PDF extraction to better utilize CPU on multi-core systems.
        """
        try:
            start_time = time.time()
            self.processing_status = "Initializing vector database with failover support..."
            if progress_callback:
                progress_callback(0.05, self.processing_status)

            # Pass failover manager to vector database
            if not self.vector_db.initialize(self.failover_manager):
                return False, "Failed to initialize vector database"

            # NEW - Cleanup deleted documents first
            self.processing_status = "Cleaning up deleted documents..."
            if progress_callback:
                progress_callback(0.08, self.processing_status)

            deleted_count = self.vector_db.cleanup_deleted_documents()
            if deleted_count > 0:
                logger.info(f"Removed {deleted_count} chunks from {deleted_count // 10} deleted files (approx)")

            # Get available subjects from existing database
            self.available_subjects = self.vector_db.get_available_subjects()
            existing_count = self.vector_db.document_count

            # Check if we should skip scanning
            if self.skip_scan:
                logger.info("Skipping document scan (--skip-scan flag set)")
                self.processing_status = f"Ready! Using existing {existing_count} documents in database"
                if progress_callback:
                    progress_callback(1.0, self.processing_status)
                return True, self.processing_status

            self.processing_status = "Scanning large collection folder structure..."
            if progress_callback:
                progress_callback(0.1, self.processing_status)

            # Use larger batch size for large collections
            documents = self.doc_processor.find_documents_with_structure(limit=batch_size)
            if not documents:
                return False, "No documents found in D:/Books directory"

            # Report collection statistics
            collection_stats = getattr(self.doc_processor, 'collection_stats', {})
            total_files = collection_stats.get('total_files_found', len(documents))

            if total_files > batch_size:
                logger.info("Large Collection Detected:")
                logger.info(f"   Total files in collection: {total_files}")
                logger.info(f"   Processing batch size: {batch_size}")
                logger.info(f"   Existing processed documents: {existing_count}")

            total_docs = len(documents)
            self.processing_status = f"Processing batch of {total_docs} documents with failover embeddings..."

            # Determine parallelism - OPTIMIZED FOR HIGH-PERFORMANCE SYSTEMS
            max_cpu = os.cpu_count() or 4
            # For Ryzen 9 with 96GB RAM, use more aggressive parallelism
            if parallel_workers and parallel_workers > 0:
                workers = parallel_workers
            else:
                # At 3s per file, CPU is I/O bound - can use more workers!
                if max_cpu >= 16:  # Ryzen 9 5950X/7950X
                    workers = 16  # Use almost all cores - 3s/file is slow enough
                    logger.info(f"High-core CPU with I/O-bound workload - using {workers} workers")
                elif max_cpu >= 12:
                    workers = 12
                else:
                    workers = min(8, max(2, max_cpu // 2))

            # Filter out already processed documents first to avoid wasted work
            to_process = []
            skipped_existing = 0
            for i, doc_info in enumerate(documents):
                if self.vector_db.document_exists(doc_info):
                    skipped_existing += 1
                    if i % 25 == 0:
                        logger.info(f"Skipped {skipped_existing} already processed documents...")
                    continue
                to_process.append(doc_info)

            newly_processed = 0
            completed = 0
            total_to_process = len(to_process)

            def _extract_task(doc_info):
                try:
                    if doc_info['path'].suffix.lower() == '.pdf':
                        text = self.doc_processor.extract_text_from_pdf(doc_info['path'])
                        if text:
                            chunks = self.doc_processor.create_chunks(text)
                            return doc_info, chunks
                    return None
                except Exception as e:
                    logger.warning(f"Extraction failed for {doc_info.get('filename')}: {e}")
                    return None

            # Parallelize only the extraction+chunking. We keep DB writes on the main thread.
            if total_to_process > 0:
                if progress_callback:
                    progress_callback(0.12, f"Extracting text in parallel using {workers} workers...")

                # If PDF extractor is unavailable, skip actual extraction while informing the user
                extractor_available = (PYMuPDF_AVAILABLE and (fitz is not None))
                if not extractor_available:
                    logger.warning("Skipping extraction: PyMuPDF (fitz) is not installed.")
                else:
                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        future_map = {executor.submit(_extract_task, di): di for di in to_process}
                        for idx, future in enumerate(as_completed(future_map)):
                            result = future.result()
                            completed += 1

                            # Update progress smoothly between 12% and 90%
                            if progress_callback and total_to_process:
                                progress = 0.12 + (0.78 * completed / total_to_process)
                                subject = future_map[future]['primary_subject'][:15]
                                fn = future_map[future]['filename'][:30]
                                progress_callback(progress, f"Processing: {fn}... ({subject})")

                            if not result:
                                continue
                            doc_info, chunks = result
                            if chunks:
                                self.vector_db.add_document_with_structure(doc_info, chunks)
                                newly_processed += 1

            # Update available subjects
            self.available_subjects = self.vector_db.get_available_subjects()
            self.documents_processed = newly_processed

            # Final status with comprehensive information
            total_in_db = self.vector_db.document_count
            subjects_list = list(self.available_subjects.keys())[:5]  # Show first 5 subjects
            subjects_preview = ', '.join(subjects_list)
            if len(self.available_subjects) > 5:
                subjects_preview += f" (+{len(self.available_subjects) - 5} more)"

            # Build comprehensive status message with failover info
            failover_status = self.failover_manager.get_status()
            elapsed = time.time() - start_time
            status_parts = [
                f"Ready with failover system! Database contains {total_in_db} documents",
                f"({newly_processed} newly processed, {skipped_existing} already existed)",
                f"Using {failover_status['current_embedding_provider']} for embeddings",
                f"Parallel workers: {workers}",
                f"Elapsed: {elapsed:.1f}s"
            ]

            # If nothing was processed and extractor is missing, surface a clear hint
            if newly_processed == 0 and total_to_process > 0 and not (PYMuPDF_AVAILABLE and (fitz is not None)):
                status_parts.append("Note: 0 processed because PDF extractor is unavailable. Install 'pymupdf' and re-run Process Document Batch.")

            if total_files > batch_size:
                remaining = total_files - batch_size
                status_parts.append(f"Large collection: {remaining} files remaining for future batches")

            status_parts.append(f"Subjects: {subjects_preview}")

            self.processing_status = " | ".join(status_parts)

            if progress_callback:
                progress_callback(1.0, self.processing_status)

            # Log final statistics
            logger.info("Initialization Complete:")
            logger.info(f"   Total documents in database: {total_in_db}")
            logger.info(f"   Newly processed this session: {newly_processed}")
            logger.info(f"   Skipped (already processed): {skipped_existing}")
            logger.info(f"   Subjects detected: {len(self.available_subjects)}")
            logger.info(f"   Current embedding provider: {failover_status['current_embedding_provider']}")
            logger.info(f"   Parallel workers used: {workers} (CPU count: {os.cpu_count()})")
            logger.info(f"   Elapsed: {elapsed:.2f}s")

            return True, self.processing_status

        except Exception as e:
            error_msg = f"Initialization failed: {e}"
            logger.exception(error_msg)
            return False, error_msg

    def debug_database_status(self):
        """Enhanced debug function to check database and failover status"""
        debug_info = []
        try:
            # Check vector database
            if getattr(self, 'vector_db', None) and getattr(self.vector_db, 'collection', None):
                count = self.vector_db.collection.count()
                debug_info.append(f"Vector database contains {count} document chunks")

                if count > 0:
                    # Get sample documents
                    sample = self.vector_db.collection.get(limit=5)
                    if sample.get('metadatas'):
                        debug_info.append("Sample documents in database:")
                        for i, metadata in enumerate(sample['metadatas'][:3]):
                            debug_info.append(f"  {i+1}. {metadata.get('filename', 'Unknown')} ({metadata.get('primary_subject', 'No subject')})")
                    else:
                        debug_info.append("No metadata found in sample")
                else:
                    debug_info.append("Vector database is empty - no documents processed")
            else:
                debug_info.append("Vector database not initialized")

            # Check available subjects
            subjects = self.vector_db.get_available_subjects() if getattr(self, 'vector_db', None) else {}
            if isinstance(subjects, dict):
                debug_info.append(f"\nAvailable subjects ({len(subjects)}): {list(subjects.keys())[:10]}")
            else:
                debug_info.append(f"\nAvailable subjects: {subjects}")

            # Test embedding search for a specific query
            if getattr(self, 'vector_db', None) and getattr(self.vector_db, 'collection', None) and self.vector_db.collection.count() > 0:
                try:
                    test_results = self.enhanced_search_with_subjects("AI Agents with MCP Kyle Stratis", n_results=3)
                    if test_results:
                        debug_info.append(f"\nEmbedding search found {len(test_results)} results:")
                        for result in test_results[:2]:
                            src = result.get('source', 'Unknown')
                            rel = result.get('relevance', 0.0)
                            debug_info.append(f"  - {src} (relevance: {rel:.3f})")
                    else:
                        debug_info.append("\nEmbedding search found NO results for 'AI Agents with MCP'")
                except Exception as e:
                    debug_info.append(f"Embedding search test error: {e}")

            # Add failover status
            if getattr(self, 'failover_manager', None):
                try:
                    failover_status = self.failover_manager.get_status()
                    debug_info.append(f"Current embedding provider: {failover_status.get('current_embedding_provider')}")
                    debug_info.append(f"Current LLM provider: {failover_status.get('current_llm_provider')}")
                    debug_info.append(f"Provider failures: {failover_status.get('failure_counts')}")
                except Exception as e:
                    debug_info.append(f"Failover status error: {e}")
        except Exception as e:
            debug_info.append(f"Debug error: {e}")

        return "\n".join(debug_info)

    def enhanced_search_with_subjects(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search with both learning and subject-based boosting using failover embeddings"""
        # Detect relevant subjects from query
        preferred_subjects = self.detect_query_subjects(query)

        # Get subject-aware search results (now using failover embeddings)
        search_results = self.vector_db.search_with_subject_boost(
            query, preferred_subjects, n_results + 2
        )

        if not search_results:
            return []

        # Apply additional learning boosts
        boost_scores = self.learning_system.get_document_boost_scores()

        for result in search_results:
            source = result['source']
            original_relevance = result['relevance']

            # Apply learned boost (from user feedback)
            learning_boost = boost_scores.get(source, 0)
            result['relevance'] = min(1.0, original_relevance + learning_boost * 0.5)  # Reduce learning boost slightly
            result['learning_boost'] = learning_boost

            # Add combined boost indicator
            if learning_boost > 0.05 or result.get('subject_boost', 0) > 0.05:
                result['is_boosted'] = True

        # Final sort and limit
        search_results.sort(key=lambda x: x['relevance'], reverse=True)
        return search_results[:n_results]

    def chat_with_documents(self, message: str, history: List[Tuple[str, str]],
                          api_key: str, max_tokens: int = 2048,
                          temperature: float = 0.7, n_context_docs: int = 3,
                          enable_voice: bool = False):
        """Main chat function with learning, personality, subject awareness, voice output, and LLM FAILOVER"""

        # FIXED - Add LLM failover option
        use_failover_llm = not api_key.strip()  # Use failover if no API key provided

        # Get OpenRouter key from environment if not provided in GUI
        if not use_failover_llm and not api_key.strip():
            api_key = os.getenv('OPENROUTER_API_KEY', '')
            if not api_key:
                logger.warning("No OpenRouter API key provided, switching to failover LLM")
                use_failover_llm = True

        if self.vector_db.document_count == 0:
            yield "No documents have been processed yet. Please wait for initialization to complete."
            return

        try:
            # Use enhanced search with subject detection (now with failover embeddings)
            search_results = self.enhanced_search_with_subjects(message, n_results=n_context_docs)

            if not search_results:
                yield "No relevant information found in your documents. Try rephrasing your question."
                return

            # Build context with subject and learning indicators
            context_parts = []
            sources_used = []

            for i, result in enumerate(search_results, 1):
                relevance = result['relevance']
                source = result['source']
                content = result['content'][:500]
                subject = result.get('primary_subject', 'general')
                subject_hierarchy = result.get('subject_hierarchy', '')

                # Create boost indicators
                indicators = []
                if result.get('learning_boost', 0) > 0.05:
                    indicators.append("STAR")  # Learning boost
                if result.get('subject_boost', 0) > 0.05:
                    indicators.append("BOOK")  # Subject boost

                boost_indicator = "".join(indicators)
                subject_info = f" ({subject})" if subject != 'general' else ""

                sources_used.append(source)

                context_parts.append(
                    f"[Source {i}: {source}{subject_info}{boost_indicator} (Relevance: {relevance:.2f})]\nPath: {subject_hierarchy}\n{content}\n"
                )

            context = "\n".join(context_parts)

            # Enhanced system message with subject context
            detected_subjects = self.detect_query_subjects(message)
            subject_context = f"\nThe user is asking about: {', '.join(detected_subjects)}" if detected_subjects else ""

            base_system_message = f"""You are a helpful AI assistant that answers questions based on the user's personal document collection organized by subject folders.

Use the following context from their documents to answer the question. Pay attention to the subject organization:
- Documents marked with STAR have been highly rated by the user
- Documents marked with BOOK are from subject folders relevant to this query{subject_context}

Context from documents:
{context}

Instructions:
1. Answer based primarily on the provided context
2. Always mention which document(s) and subject areas you're referencing
3. If context doesn't contain enough information, suggest checking specific subject folders
4. Be concise but comprehensive
5. Use a helpful and friendly tone
6. Pay special attention to documents marked with STAR or BOOK as they're most relevant"""

            # Generate personality-enhanced system message
            enhanced_system_message, active_personality = self.personality_system.generate_enhanced_system_message(
                context, detected_subjects, base_system_message
            )

            self.last_personality = active_personality

            # Store query info for learning
            self.last_query = message
            self.last_sources = sources_used

            # Build conversation history
            messages = [{"role": "system", "content": enhanced_system_message}]

            for user_msg, assistant_msg in history:
                if user_msg:
                    messages.append({"role": "user", "content": user_msg})
                if assistant_msg:
                    messages.append({"role": "assistant", "content": assistant_msg})

            messages.append({"role": "user", "content": message})

            # MODIFIED - Use failover system or OpenRouter based on availability
            response = ""
            if use_failover_llm or not api_key:
                # Use failover LLM system
                logger.info("Using LLM failover system for response generation")
                full_prompt = f"Context: {context}\n\nQuestion: {message}\n\nAnswer:"

                response = self.failover_manager.generate_response(
                    prompt=message,
                    context=context,
                    max_tokens=max_tokens
                )

                if response:
                    # Show provider info
                    failover_status = self.failover_manager.get_status()
                    provider_info = f"\n\n*Using {failover_status['current_llm_provider']} via failover system*"
                    response += provider_info
                    yield response
                else:
                    yield "I apologize, but all LLM providers are currently unavailable. Please try again later."

            else:
                # Use OpenRouter as before
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key,
                )

                # Stream response
                for chunk in client.chat.completions.create(
                    model="google/gemini-2.0-flash-lite-preview-02-05:free",
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                ):
                    if chunk.choices[0].delta.content:
                        response += chunk.choices[0].delta.content
                        yield response

            # Store complete response for learning
            self.last_response = response

            # Generate voice output if enabled
            if enable_voice and self.voice_system.voice_enabled:
                self.voice_system.speak_text(response, active_personality, background=True)

        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"Error: {str(e)}"

    def get_subject_summary(self) -> Dict[str, Any]:
        """Get summary of available subjects and their document counts - enhanced for large collections"""
        summary = {
            'available_subjects': self.available_subjects,
            'total_subjects': len(self.available_subjects),
            'folder_structure_detected': len(self.doc_processor.folder_subjects) > 0,
            'documents_in_database': self.vector_db.document_count
        }

        # Add failover system info
        if self.failover_manager:
            failover_status = self.failover_manager.get_status()
            summary['failover_status'] = {
                'current_embedding_provider': failover_status['current_embedding_provider'],
                'current_llm_provider': failover_status['current_llm_provider'],
                'available_providers': failover_status.get('available_providers', [])
            }

        # Add collection statistics if available
        if hasattr(self.doc_processor, 'collection_stats'):
            stats = self.doc_processor.collection_stats
            summary.update({
                'collection_total_files': stats.get('total_files_found', 0),
                'files_processed_this_batch': stats.get('files_in_this_batch', 0),
                'largest_subject': stats.get('largest_subject', None),
                'is_large_collection': stats.get('total_files_found', 0) > 1000
            })

        return summary

    def submit_feedback(self, rating: int, feedback_text: str = "") -> str:
        """Submit user feedback on the last response"""
        if not self.last_query or not self.last_response:
            return "No recent conversation to rate"

        self.learning_system.record_feedback(
            self.last_query,
            self.last_response,
            rating,
            self.last_sources,
            feedback_text
        )

        # Record personality-specific feedback
        try:
            current_personality = self.personality_system.current_personality
            self.personality_system.record_personality_feedback(
                current_personality, rating, "user_interaction"
            )
        except Exception as e:
            logger.error(f"Error recording personality feedback: {e}")

        return f"Thank you! Feedback recorded ({rating}/5 stars)"

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get learning system insights"""
        return self.learning_system.get_learning_stats()

    def update_personality(self, personality_type: str, ai_name: str = None):
        """Update AI personality and name"""
        self.personality_system.update_personality_setting('current_personality', personality_type)
        if ai_name:
            self.personality_system.update_personality_setting('ai_name', ai_name)
        return f"Personality updated to '{personality_type}'" + (f" with name '{ai_name}'" if ai_name else "")

    def get_personality_options(self):
        """Get personality customization options"""
        return self.personality_system.get_personality_customization_options()

    def get_personality_insights(self):
        """Get personality usage statistics"""
        return self.personality_system.get_personality_stats()

    def get_voice_status(self):
        """Get voice system status"""
        return self.voice_system.get_voice_status()

    def update_voice_settings(self, enabled: bool = None, speed: int = None, volume: float = None):
        """Update voice settings"""
        self.voice_system.update_voice_settings(enabled, speed, volume)
        return "Voice settings updated"

    # NEW - Add failover management methods
    def get_failover_status(self):
        """Get failover system status"""
        if self.failover_manager:
            return self.failover_manager.get_status()
        return {"status": "Failover manager not initialized"}

    def reset_failover_providers(self):
        """Reset failover providers to primary"""
        if self.failover_manager:
            self.failover_manager.reset_providers()
            return "Failover providers reset to primary"
        return "Failover manager not available"

    def test_embeddings(self):
        """Test embedding generation with failover"""
        try:
            test_text = "This is a test embedding"
            embedding = self.vector_db._get_embedding(test_text)
            if embedding:
                return f"✓ Embedding generated successfully! Dimension: {len(embedding)}, Provider: {self.failover_manager.get_status()['current_embedding_provider']}"
            else:
                return "✗ Failed to generate embedding"
        except Exception as e:
            return f"✗ Embedding test failed: {e}"

def create_interface(skip_scan=False):
    """Create the enhanced Gradio interface with learning, personality, voice, and FAILOVER"""

    # Initialize chatbot
    chatbot = KnowledgeBaseChatbot(skip_scan=skip_scan)

    def initialize_chatbot(batch_size, progress=gr.Progress()):
        """Initialize chatbot with progress tracking and batch size"""
        def update_progress(value, status):
            progress(value, desc=status)

        success, message = chatbot.initialize_system(update_progress, int(batch_size))
        return message

    def submit_user_feedback(rating_str, feedback_text):
        """Handle user feedback submission"""
        if not rating_str:
            return "Please select a rating first!"

        # Convert rating string to number
        rating_map = {"Poor (1)": 1, "Fair (2)": 2, "Good (3)": 3,
                     "Great (4)": 4, "Excellent (5)": 5}
        rating = rating_map.get(rating_str, 3)

        return chatbot.submit_feedback(rating, feedback_text)

    def refresh_insights():
        """Refresh learning insights"""
        return chatbot.get_learning_insights()

    def get_subject_browser():
        """Get subject browser information with failover status"""
        return chatbot.get_subject_summary()

    def update_ai_personality(personality_type, ai_name, formality, detail, adaptive):
        """Update AI personality settings"""
        try:
            # Update personality
            status = chatbot.update_personality(personality_type, ai_name)

            # Update advanced settings if needed
            chatbot.personality_system.update_personality_setting('formality_level', str(formality))
            chatbot.personality_system.update_personality_setting('detail_level', str(detail))
            chatbot.personality_system.update_personality_setting('adaptive_personality', str(adaptive))

            # Get personality preview
            preview = chatbot.get_personality_options()
            current_profile = preview['personalities'].get(personality_type, {})

            preview_data = {
                'name': ai_name,
                'personality': personality_type,
                'description': current_profile.get('description', ''),
                'voice_characteristics': current_profile.get('voice_characteristics', ''),
                'sample_greeting': current_profile.get('sample_greeting', ''),
                'formality_level': formality,
                'detail_level': detail,
                'adaptive_mode': adaptive
            }

            return status, preview_data

        except Exception as e:
            return f"Error updating personality: {e}", {}

    def get_personality_preview(personality_type):
        """Get preview of selected personality"""
        try:
            options = chatbot.get_personality_options()
            if personality_type in options['personalities']:
                profile = options['personalities'][personality_type]
                return {
                    'description': profile['description'],
                    'voice_characteristics': profile['voice_characteristics'],
                    'sample_greeting': profile['sample_greeting'],
                    'suggested_names': profile['suggested_names']
                }
            return {}
        except:
            return {}

    def refresh_personality_statistics():
        """Refresh personality usage statistics"""
        try:
            return chatbot.get_personality_insights()
        except:
            return {}

    def debug_database():
        """Debug database status with failover info"""
        return chatbot.debug_database_status()

    def test_embeddings():
        """Test failover embeddings"""
        return chatbot.test_embeddings()

    def get_voice_status():
        """Get voice system status"""
        return chatbot.get_voice_status()

    def update_voice_settings(enabled, speed, volume):
        """Update voice settings"""
        return chatbot.update_voice_settings(enabled, speed, volume)

    # NEW - Failover management functions
    def get_failover_system_status():
        """Get detailed failover system status"""
        return chatbot.get_failover_status()

    def reset_failover_providers():
        """Reset failover providers"""
        return chatbot.reset_failover_providers()

    def chat_function(message, history, api_key, max_tokens, temperature, n_docs, voice_enabled):
        """Handle chat interaction with voice and failover support"""
        if not message.strip():
            return history, ""

        # Convert messages format to tuples
        history_tuples = []
        if history:
            for msg in history:
                if isinstance(msg, dict) and 'role' in msg:
                    if msg['role'] == 'user':
                        history_tuples.append((msg['content'], None))
                    elif msg['role'] == 'assistant' and history_tuples:
                        history_tuples[-1] = (history_tuples[-1][0], msg['content'])
                elif isinstance(msg, (list, tuple)) and len(msg) == 2:
                    history_tuples.append((msg[0], msg[1]))

        # DEBUG - Log voice status
        logger.info(f"Voice checkbox state: {voice_enabled}")
        logger.info(f"Voice system enabled: {chatbot.voice_system.voice_enabled}")
        logger.info(f"Voice settings: {chatbot.voice_system.voice_settings}")

        # CRITICAL FIX - Update voice settings from checkbox
        if voice_enabled:
            chatbot.voice_system.voice_settings['enabled'] = True
            logger.info("Voice output ENABLED for this response")
        else:
            chatbot.voice_system.voice_settings['enabled'] = False
            logger.info("Voice output DISABLED for this response")

        # Get streaming response with failover support
        full_response = ""
        for response_chunk in chatbot.chat_with_documents(
            message, history_tuples, api_key, max_tokens, temperature, n_docs, voice_enabled
        ):
            full_response = response_chunk

        # Update history
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": full_response}
        ]

        return new_history, ""

    def clear_chat():
        """Clear chat history"""
        return [], ""

    # Custom CSS for better styling
    css = """
    .gradio-container {
        max-width: 1400px !important;
    }
    .status-box {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .header-text {
        text-align: center;
        color: #2d3748;
        margin-bottom: 20px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
    }
    .voice-indicator {
        background: linear-gradient(45deg, #ff9a9e 0%, #fecfef 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .failover-indicator {
        background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    """

    # Create interface with learning, personality, voice, and FAILOVER capabilities
    with gr.Blocks(css=css, title="AI Knowledge Base Chatbot - Enhanced with Failover") as demo:
        gr.HTML("""
        <div class="header-text">
            <h1>AI Knowledge Base Chatbot with Voice & Failover System</h1>
            <p>Advanced AI assistant with personality-based voice output and automatic provider failover</p>
            <p><strong>Learning:</strong> Adapts from feedback | <strong>Subject-Aware:</strong> Folder intelligence | <strong>Personality:</strong> Customizable character | <strong>Voice:</strong> Text-to-speech | <strong>FAILOVER:</strong> Automatic provider switching</p>
        </div>
        """)

        # Initialization section
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Row():
                    init_button = gr.Button("Process Document Batch", variant="primary", scale=2)
                    batch_size_slider = gr.Slider(
                        minimum=50,
                        maximum=1000,
                        value=200,
                        step=50,
                        label="Batch Size",
                        scale=1
                    )

                status_text = gr.Textbox(
                    label="System Status",
                    value="Click 'Process Document Batch' to start processing your large collection with failover support",
                    interactive=False,
                    lines=3
                )

            with gr.Column(scale=1):
                # Failover status section
                with gr.Group():
                    gr.HTML('<div class="failover-indicator"><h3>Failover System Active</h3><p>Automatic switching between OpenAI, Local, Ollama, and Gemini providers</p></div>')
                    failover_status_display = gr.JSON(label="Failover System Status", value={})
                    with gr.Row():
                        refresh_failover_btn = gr.Button("Refresh Failover Status", variant="secondary", scale=1)
                        reset_failover_btn = gr.Button("Reset to Primary", variant="secondary", scale=1)

                # Debug section
                with gr.Group():
                    gr.Markdown("#### System Debug Tools")
                    with gr.Row():
                        debug_db_btn = gr.Button("Debug Database", variant="secondary", scale=1)
                        test_embed_btn = gr.Button("Test Embeddings", variant="secondary", scale=1)
                    debug_output = gr.Textbox(label="Debug Output", lines=3, interactive=False)

        gr.Markdown("---")

        # Main content with tabs
        with gr.Tabs():
            # Enhanced Chat Tab with failover info
            with gr.TabItem("Chat", id=0):
                with gr.Row():
                    with gr.Column(scale=3):
                        # Chat interface
                        with gr.Group():
                            chatbot_display = gr.Chatbot(
                                height=400,
                                show_copy_button=True,
                                type='messages',
                                label="AI Knowledge Base Chat with Failover"
                            )

                            msg_input = gr.Textbox(
                                placeholder="Ask questions about your documents... (Failover system will automatically handle provider issues)",
                                lines=2,
                                label="Your Question",
                                interactive=True
                            )

                            with gr.Row():
                                submit_btn = gr.Button("Ask Question", variant="primary", scale=2)
                                clear_btn = gr.Button("Clear Chat", scale=1)

                        # Enhanced Settings with failover options
                        with gr.Accordion("Chat Settings", open=False):
                            gr.Markdown("**Failover System:** Leave API key empty to use automatic LLM failover (Ollama → OpenAI → Gemini)")
                            api_key_input = gr.Textbox(
                                label="OpenRouter API Key (Optional)",
                                type="password",
                                placeholder="Leave empty to use LLM failover system",
                                info="Empty = Use failover LLMs | Provided = Use OpenRouter"
                            )

                            with gr.Row():
                                max_tokens_slider = gr.Slider(
                                    minimum=512,
                                    maximum=4096,
                                    value=2048,
                                    step=256,
                                    label="Max Response Length"
                                )
                                temperature_slider = gr.Slider(
                                    minimum=0.1,
                                    maximum=1.0,
                                    value=0.7,
                                    step=0.1,
                                    label="Creativity"
                                )
                                n_docs_slider = gr.Slider(
                                    minimum=1,
                                    maximum=10,
                                    value=3,
                                    step=1,
                                    label="Documents to Search"
                                )

                            # Voice Settings
                            gr.Markdown("#### Voice Output Settings")
                            with gr.Row():
                                voice_enabled = gr.Checkbox(
                                    label="Enable Voice Output",
                                    value=False,
                                    info="Speak responses aloud with personality-based voice"
                                )
                                voice_speed = gr.Slider(
                                    minimum=100,
                                    maximum=250,
                                    value=180,
                                    step=10,
                                    label="Voice Speed"
                                )
                                voice_volume = gr.Slider(
                                    minimum=0.1,
                                    maximum=1.0,
                                    value=0.8,
                                    step=0.1,
                                    label="Voice Volume"
                                )

                        # Feedback Section
                        gr.Markdown("### Rate the Last Response")
                        with gr.Row():
                            with gr.Column(scale=2):
                                feedback_rating = gr.Radio(
                                    choices=["Poor (1)", "Fair (2)", "Good (3)",
                                            "Great (4)", "Excellent (5)"],
                                    label="How helpful was the response?",
                                    value=None
                                )
                                feedback_text = gr.Textbox(
                                    label="Additional feedback (optional)",
                                    placeholder="What could be improved? What was particularly helpful?",
                                    lines=2
                                )

                            with gr.Column(scale=1):
                                submit_feedback_btn = gr.Button("Submit Feedback", variant="secondary")
                                feedback_status = gr.Textbox(
                                    label="Feedback Status",
                                    value="Rate the response above to help the AI learn!",
                                    interactive=False,
                                    lines=1
                                )

                    with gr.Column(scale=1):
                        # Failover System Info
                        gr.HTML("""
                        <div class="failover-indicator">
                            <h3>Failover System Features:</h3>
                            <ul>
                                <li><strong>Embedding Failover:</strong> OpenAI → Local → Ollama</li>
                                <li><strong>LLM Failover:</strong> Ollama → OpenAI → Gemini</li>
                                <li><strong>Automatic Switching:</strong> No manual intervention needed</li>
                                <li><strong>Cost Tracking:</strong> Monitor API usage across providers</li>
                                <li><strong>Quota Handling:</strong> Bypasses OpenAI limits automatically</li>
                            </ul>
                        </div>
                        """)

                        # Voice Status Display
                        gr.HTML("""
                        <div class="voice-indicator">
                            <h3>Voice Features:</h3>
                            <ul>
                                <li><strong>Personality-Based:</strong> Voice adapts to AI personality</li>
                                <li><strong>Female Voice:</strong> Uses female TTS when available</li>
                                <li><strong>Background Processing:</strong> Non-blocking speech synthesis</li>
                                <li><strong>Smart Text Cleanup:</strong> Removes formatting for natural speech</li>
                            </ul>
                        </div>
                        """)

                        gr.HTML("""
                        <div style="padding: 20px; background: #edf2f7; border-radius: 10px; margin-top: 10px;">
                            <h3>Smart Search Tips:</h3>
                            <ul>
                                <li><strong>Subject Detection:</strong> Mention subjects like "mathematics", "programming"</li>
                                <li><strong>STAR = Highly Rated:</strong> Documents you've rated 4-5 stars</li>
                                <li><strong>BOOK = Subject Match:</strong> Documents from relevant folders</li>
                                <li><strong>Path Context:</strong> Responses show document organization</li>
                            </ul>
                        </div>
                        """)

            # Enhanced AI Personality Tab
            with gr.TabItem("AI Personality & Voice"):
                gr.Markdown("### Customize Your AI Assistant's Personality & Voice")
                gr.Markdown("Choose how your AI assistant communicates, interacts, and speaks.")

                with gr.Row():
                    with gr.Column(scale=2):
                        # AI Name Customization
                        with gr.Group():
                            gr.Markdown("#### Name Your AI Assistant")
                            ai_name_input = gr.Textbox(
                                label="AI Assistant Name",
                                placeholder="Enter a name for your AI assistant",
                                value="Athena"
                            )

                            # Personality Selection
                            gr.Markdown("#### Choose Personality Style")
                            personality_radio = gr.Radio(
                                choices=[
                                    ("Sage - Scholarly and thoughtful", "sage"),
                                    ("Mentor - Encouraging teacher", "mentor"),
                                    ("Explorer - Enthusiastic researcher", "explorer"),
                                    ("Assistant - Friendly helper", "assistant"),
                                    ("Specialist - Technical expert", "specialist")
                                ],
                                label="Personality Type",
                                value="sage"
                            )

                            # Update button
                            update_personality_btn = gr.Button("Update AI Personality", variant="primary")
                            personality_status = gr.Textbox(
                                label="Status",
                                value="Ready to customize your AI assistant",
                                interactive=False
                            )

                    with gr.Column(scale=1):
                        # Enhanced Personality Preview
                        personality_preview = gr.JSON(
                            label="Personality & Voice Preview",
                            value={}
                        )

                        # Voice characteristics info
                        gr.HTML("""
                        <div style="padding: 20px; background: #f7fafc; border-radius: 10px;">
                            <h3>Voice Characteristics by Personality:</h3>
                            <ul>
                                <li><strong>Sage:</strong> Calm, measured pace with thoughtful pauses</li>
                                <li><strong>Mentor:</strong> Warm, encouraging tone with clear articulation</li>
                                <li><strong>Explorer:</strong> Energetic, faster pace with excitement</li>
                                <li><strong>Assistant:</strong> Natural, conversational with friendly warmth</li>
                                <li><strong>Specialist:</strong> Professional, precise with authority</li>
                            </ul>
                        </div>
                        """)

                # Advanced Settings
                with gr.Accordion("Advanced Personality & Voice Settings", open=False):
                    with gr.Row():
                        formality_slider = gr.Slider(
                            minimum=0.1,
                            maximum=1.0,
                            value=0.7,
                            step=0.1,
                            label="Formality Level"
                        )
                        detail_slider = gr.Slider(
                            minimum=0.1,
                            maximum=1.0,
                            value=0.8,
                            step=0.1,
                            label="Detail Level"
                        )

                    adaptive_personality_checkbox = gr.Checkbox(
                        label="Auto-adapt personality based on subject",
                        value=True,
                        info="Automatically switch to specialist mode for technical subjects"
                    )

                # Personality Statistics
                gr.Markdown("### Personality Usage Statistics")
                with gr.Row():
                    personality_stats_display = gr.JSON(
                        label="Personality Performance",
                        value={}
                    )
                    refresh_personality_stats_btn = gr.Button("Refresh Statistics")

            # Enhanced Subject Browser Tab with failover info
            with gr.TabItem("Subject Browser"):
                gr.Markdown("### Browse Your Document Collection by Subject")
                gr.Markdown("Explore the folder structure and subjects detected in your D:/Books directory with failover system support.")

                with gr.Row():
                    with gr.Column():
                        subject_summary_display = gr.JSON(
                            label="Subject Summary with Failover Status",
                            value={}
                        )

                        refresh_subjects_btn = gr.Button("Refresh Subject Information", variant="primary")

                    with gr.Column():
                        gr.HTML("""
                        <div style="padding: 20px; background: #f7fafc; border-radius: 10px;">
                            <h3>How Subject Detection Works:</h3>
                            <ul>
                                <li><strong>Folder Names:</strong> Primary subject = deepest folder name</li>
                                <li><strong>Hierarchy:</strong> Full path preserved for context</li>
                                <li><strong>Smart Matching:</strong> Query keywords → folder names</li>
                                <li><strong>Boost Priority:</strong> Subject folders → Learning feedback</li>
                                <li><strong>Failover Embeddings:</strong> Always works even with API issues</li>
                            </ul>
                        </div>
                        """)

            # Enhanced Learning Insights Tab
            with gr.TabItem("Learning Insights"):
                gr.Markdown("### AI Learning Dashboard")
                gr.Markdown("See how the AI is learning from your interactions and improving over time.")

                with gr.Row():
                    with gr.Column():
                        insights_display = gr.JSON(
                            label="Learning Statistics",
                            value={}
                        )

                        refresh_insights_btn = gr.Button("Refresh Insights", variant="primary")

                    with gr.Column():
                        gr.HTML("""
                        <div style="padding: 20px; background: #fff5f5; border-radius: 10px;">
                            <h3>What This Shows:</h3>
                            <ul>
                                <li><strong>Total Feedback:</strong> Number of ratings you've given</li>
                                <li><strong>Average Rating:</strong> Overall satisfaction score</li>
                                <li><strong>Top Documents:</strong> Your most helpful sources</li>
                            </ul>
                        </div>
                        """)

            # NEW - Failover System Tab
            with gr.TabItem("Failover System"):
                gr.Markdown("### LLM Failover System Control Panel")
                gr.Markdown("Monitor and manage the automatic provider switching system.")

                with gr.Row():
                    with gr.Column():
                        failover_detailed_status = gr.JSON(
                            label="Detailed Failover Status",
                            value={}
                        )

                        with gr.Row():
                            refresh_detailed_failover_btn = gr.Button("Refresh Status", variant="primary")
                            reset_detailed_failover_btn = gr.Button("Reset All Providers", variant="secondary")

                        failover_action_status = gr.Textbox(
                            label="Action Status",
                            value="Failover system ready",
                            interactive=False
                        )

                    with gr.Column():
                        gr.HTML("""
                        <div style="padding: 20px; background: #e6fffa; border-radius: 10px;">
                            <h3>Failover System Details:</h3>
                            <ul>
                                <li><strong>Embedding Priority:</strong> OpenAI → Local SentenceTransformers → Ollama</li>
                                <li><strong>LLM Priority:</strong> Qwen 2.5 → Mistral 7B → OpenAI → Gemini</li>
                                <li><strong>Automatic Detection:</strong> Quota limits, timeouts, service errors</li>
                                <li><strong>Transparent Switching:</strong> No interruption to user experience</li>
                                <li><strong>Cost Optimization:</strong> Uses free providers first</li>
                                <li><strong>Health Monitoring:</strong> Tracks provider reliability</li>
                            </ul>
                        </div>
                        """)

        # Event handlers
        init_button.click(
            fn=initialize_chatbot,
            inputs=[batch_size_slider],
            outputs=status_text
        )

        # Debug event handlers
        debug_db_btn.click(
            fn=debug_database,
            outputs=debug_output
        )

        test_embed_btn.click(
            fn=test_embeddings,
            outputs=debug_output
        )

        # Failover event handlers
        refresh_failover_btn.click(
            fn=get_failover_system_status,
            outputs=failover_status_display
        )

        reset_failover_btn.click(
            fn=reset_failover_providers,
            outputs=debug_output
        )

        refresh_detailed_failover_btn.click(
            fn=get_failover_system_status,
            outputs=failover_detailed_status
        )

        reset_detailed_failover_btn.click(
            fn=reset_failover_providers,
            outputs=failover_action_status
        )

        # Chat event handlers with voice and failover support
        submit_btn.click(
            fn=chat_function,
            inputs=[msg_input, chatbot_display, api_key_input, max_tokens_slider, temperature_slider, n_docs_slider, voice_enabled],
            outputs=[chatbot_display, msg_input]
        )

        msg_input.submit(
            fn=chat_function,
            inputs=[msg_input, chatbot_display, api_key_input, max_tokens_slider, temperature_slider, n_docs_slider, voice_enabled],
            outputs=[chatbot_display, msg_input]
        )

        clear_btn.click(
            fn=clear_chat,
            outputs=[chatbot_display, msg_input]
        )

        submit_feedback_btn.click(
            fn=submit_user_feedback,
            inputs=[feedback_rating, feedback_text],
            outputs=feedback_status
        )

        refresh_insights_btn.click(
            fn=refresh_insights,
            outputs=insights_display
        )

        refresh_subjects_btn.click(
            fn=get_subject_browser,
            outputs=subject_summary_display
        )

        # Personality event handlers
        update_personality_btn.click(
            fn=update_ai_personality,
            inputs=[personality_radio, ai_name_input, formality_slider, detail_slider, adaptive_personality_checkbox],
            outputs=[personality_status, personality_preview]
        )

        personality_radio.change(
            fn=get_personality_preview,
            inputs=[personality_radio],
            outputs=[personality_preview]
        )

        refresh_personality_stats_btn.click(
            fn=refresh_personality_statistics,
            outputs=personality_stats_display
        )

        # Footer
        gr.HTML("""
        <div style="text-align: center; margin-top: 20px; color: #666; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; color: white;">
            <p><strong>AI Knowledge Base Chatbot - Enhanced Edition with Failover</strong></p>
            <p>Complete AI assistant with Learning, Subject Intelligence, Personality, Voice Output & LLM Failover System</p>
            <p><small>Batch Processing | Learning System | Subject-Aware | Personality | Voice Synthesis | AUTOMATIC FAILOVER</small></p>
        </div>
        """)

    return demo

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Knowledge Base Chatbot')
    parser.add_argument('--skip-scan', action='store_true',
                        help='Skip scanning for new documents on startup')
    args = parser.parse_args()

    logger.info("Starting Enhanced AI Knowledge Base Chatbot with Voice and Failover System...")

    # Install voice dependencies message
    if not VOICE_AVAILABLE:
        print("\n" + "="*60)
        print("VOICE FEATURES DISABLED")
        print("To enable voice output, install: pip install pyttsx3")
        print("="*60 + "\n")

     # Create and launch interface
    demo = create_interface(skip_scan=args.skip_scan)

    demo.queue().launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False,
        inbrowser=True
    )
