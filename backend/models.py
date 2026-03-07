"""
Event models and database schemas
"""
from app import db
from datetime import datetime

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    agent_id = db.Column(db.String(100))
    task_id = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    message = db.Column(db.Text)
    data = db.Column(db.JSON)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'agent_id': self.agent_id,
            'task_id': self.task_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'message': self.message,
            'data': self.data,
            'status': self.status
        }

class AgentSession(db.Model):
    __tablename__ = 'agent_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    event_count = db.Column(db.Integer, default=0)
    info = db.Column(db.JSON)
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'event_count': self.event_count
        }
