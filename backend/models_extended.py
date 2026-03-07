"""
Extended SQLAlchemy Models for Activity Logger
"""
try:
    from models import db
except ImportError:
    from .models import db

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, JSON


class ClipboardEvent(db.Model):
    """Clipboard copy/paste events"""
    __tablename__ = 'clipboard_events'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    content_type = Column(String(50))
    raw_content = Column(Text)
    source_app = Column(String(255))
    source_url = Column(String(500))
    processed_summary = Column(Text)
    tags = Column(String(1000))
    image_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    embedding = Column(JSON, nullable=True)
    event_metadata = Column(JSON, nullable=True)
    
    ocr_results = db.relationship('OCRResult', backref='clipboard_event', cascade='all, delete-orphan')


class ActivityEvent(db.Model):
    """Active window/application tracking"""
    __tablename__ = 'activity_events'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    window_title = Column(String(500))
    application = Column(String(255))
    url = Column(String(500))
    event_metadata = Column(String(2000))
    created_at = Column(DateTime, default=datetime.utcnow)


class CommandEvent(db.Model):
    """Shell command execution tracking"""
    __tablename__ = 'command_events'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    command = Column(Text)
    user_name = Column(String(100))
    working_directory = Column(String(500))
    exit_code = Column(Integer)
    event_metadata = Column(String(2000))
    created_at = Column(DateTime, default=datetime.utcnow)


class OCRResult(db.Model):
    """OCR processing results for clipboard images"""
    __tablename__ = 'ocr_results'
    
    id = Column(Integer, primary_key=True)
    clipboard_event_id = Column(Integer, ForeignKey('clipboard_events.id', ondelete='CASCADE'))
    extracted_text = Column(Text)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
