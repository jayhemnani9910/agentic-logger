"""
API Routes and Endpoints
"""
from flask import Blueprint, request, jsonify
from app import db, redis_client
from models import Event, AgentSession
from datetime import datetime, timedelta
import json
from sqlalchemy import text

api_bp = Blueprint('api', __name__)
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db.session.execute(text('SELECT 1'))
        redis_client.ping()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

# Event Endpoints
@api_bp.route('/events', methods=['POST'])
def create_event():
    """Create a new event"""
    try:
        data = request.get_json()
        
        event = Event(
            event_type=data.get('event_type'),
            agent_id=data.get('agent_id'),
            task_id=data.get('task_id'),
            message=data.get('message'),
            data=data.get('data'),
            status=data.get('status', 'pending')
        )
        
        db.session.add(event)
        db.session.commit()
        
        # Cache recent events
        cache_key = f"events:{data.get('agent_id')}"
        redis_client.lpush(cache_key, json.dumps(event.to_dict()))
        redis_client.expire(cache_key, 3600)
        
        return jsonify(event.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/events', methods=['GET'])
def list_events():
    """List events with filtering"""
    try:
        agent_id = request.args.get('agent_id')
        task_id = request.args.get('task_id')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = Event.query
        
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        if task_id:
            query = query.filter_by(task_id=task_id)
        
        total = query.count()
        events = query.order_by(Event.timestamp.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'total': total,
            'limit': limit,
            'offset': offset,
            'events': [e.to_dict() for e in events]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get event by ID"""
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        return jsonify(event.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Agent Session Endpoints
@api_bp.route('/sessions', methods=['POST'])
def create_session():
    """Create agent session"""
    try:
        data = request.get_json()
        
        session = AgentSession(
            agent_id=data.get('agent_id'),
            info=data.get('info')
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify(session.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/sessions/<agent_id>', methods=['GET'])
def get_session(agent_id):
    """Get agent session"""
    try:
        session = AgentSession.query.filter_by(agent_id=agent_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify(session.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/sessions/<agent_id>', methods=['PUT'])
def update_session(agent_id):
    """Update agent session"""
    try:
        data = request.get_json()
        session = AgentSession.query.filter_by(agent_id=agent_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if 'status' in data:
            session.status = data['status']
        if 'info' in data:
            session.info = data['info']
        
        if data.get('status') == 'completed':
            session.ended_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify(session.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Stats Endpoints
@api_bp.route('/stats/summary', methods=['GET'])
def get_stats():
    """Get statistics summary"""
    try:
        hours = request.args.get('hours', 24, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        total_events = Event.query.filter(Event.timestamp >= since).count()
        active_agents = AgentSession.query.filter_by(status='active').count()
        completed_tasks = Event.query.filter(
            Event.event_type == 'task_end',
            Event.status == 'completed',
            Event.timestamp >= since
        ).count()
        
        return jsonify({
            'total_events': total_events,
            'active_agents': active_agents,
            'completed_tasks': completed_tasks,
            'time_range_hours': hours
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Semantic Search Endpoints
@api_bp.route('/search/semantic', methods=['POST'])
def semantic_search():
    """Perform semantic search across clipboard events"""
    try:
        from agent_integration import agent_integration
        
        data = request.get_json()
        query = data.get('query')
        limit = data.get('limit', 20)
        
        if not query:
            return jsonify({'error': 'Query parameter required'}), 400
        
        # Use orchestrator's semantic search
        if hasattr(agent_integration, 'orchestrator') and agent_integration.orchestrator:
            results = agent_integration.orchestrator.semantic_search(query, limit)
            return jsonify({
                'query': query,
                'results': results,
                'count': len(results)
            }), 200
        else:
            return jsonify({'error': 'Orchestrator not initialized'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/search/keywords', methods=['POST'])
def keyword_search():
    """Perform keyword-based search"""
    try:
        from models_extended import ClipboardEvent
        
        data = request.get_json()
        keywords = data.get('keywords', [])
        limit = data.get('limit', 50)
        
        if not keywords:
            return jsonify({'error': 'Keywords parameter required'}), 400
        
        query_filter = None
        for keyword in keywords:
            if query_filter is None:
                query_filter = ClipboardEvent.raw_content.ilike(f'%{keyword}%')
            else:
                query_filter = query_filter | ClipboardEvent.raw_content.ilike(f'%{keyword}%')
        
        results = db.session.query(ClipboardEvent).filter(
            query_filter
        ).order_by(ClipboardEvent.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'keywords': keywords,
            'results': [{
                'id': r.id,
                'content': r.raw_content[:200],
                'app': r.source_app,
                'timestamp': r.timestamp.isoformat()
            } for r in results],
            'count': len(results)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500