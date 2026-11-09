"""
Extended API routes for activity logging dashboard.

Provides REST endpoints for:
- Clipboard events
- Activity timeline
- Command history
- Semantic search
- System statistics
"""

from flask import request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import cast, func, desc
from sqlalchemy.dialects.postgresql import JSONB
import json

try:
    from models_extended import (
        ClipboardEvent, ActivityEvent, CommandEvent, OCRResult
    )
    from models import db
except ImportError:
    from .models_extended import (
        ClipboardEvent, ActivityEvent, CommandEvent, OCRResult
    )
    from .models import db


def _escape_like(s):
    """Escape LIKE wildcard characters in user input."""
    return s.replace('\\', '\\\\').replace('%', r'\%').replace('_', r'\_')


def _content_flag(name):
    """SQL expression for a boolean in event_metadata's content section."""
    flag = cast(ClipboardEvent.event_metadata, JSONB)['content'][name].as_boolean()
    return func.coalesce(flag, False)


def _parse_metadata(raw_metadata):
    """Parse event_metadata, handling both string and dict forms."""
    if not raw_metadata:
        return {}
    if isinstance(raw_metadata, dict):
        return raw_metadata
    try:
        return json.loads(raw_metadata)
    except (json.JSONDecodeError, TypeError):
        return {}


def _content_icon(content_analysis):
    """Determine content icon based on content analysis flags."""
    if content_analysis.get('is_url'):
        return '\U0001f517'
    if content_analysis.get('is_code'):
        return '\U0001f4bb'
    if content_analysis.get('is_json'):
        return '\U0001f4cb'
    return '\U0001f4dd'


def register_extended_routes(app):
    """Register all extended routes."""
    
    @app.route('/api/clipboard', methods=['GET'])
    def get_clipboard_events():
        """Get clipboard events with advanced filtering."""
        try:
            # Query parameters
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            content_type_filter = request.args.get('content_type', None)  # 'url', 'code', 'json', 'text'
            search_text = request.args.get('search', None)
            hours = request.args.get('hours', 24, type=int)
            min_size = request.args.get('min_size', None, type=int)
            max_size = request.args.get('max_size', None, type=int)
            app_filter = request.args.get('app', None)
            
            # Build query
            query = ClipboardEvent.query
            
            # Time filter
            since = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(ClipboardEvent.created_at >= since)
            
            # Search filter (exact content type)
            if search_text:
                escaped = _escape_like(search_text)
                query = query.filter(
                    (ClipboardEvent.raw_content.ilike(f'%{escaped}%')) |
                    (ClipboardEvent.processed_summary.ilike(f'%{escaped}%'))
                )

            # App filter
            if app_filter:
                query = query.filter(ClipboardEvent.source_app.ilike(f'%{_escape_like(app_filter)}%'))
            
            # Size filters (filter by raw_content length)
            if min_size is not None:
                query = query.filter(func.length(ClipboardEvent.raw_content) >= min_size)
            if max_size is not None:
                query = query.filter(func.length(ClipboardEvent.raw_content) <= max_size)
            
            # Metadata-based content type filter
            # This checks the event_metadata JSON for detected content types
            if content_type_filter:
                if content_type_filter in ('url', 'code', 'json'):
                    query = query.filter(_content_flag(f'is_{content_type_filter}'))
                elif content_type_filter == 'text':
                    # Text is default when none of the others match
                    query = query.filter(
                        ~_content_flag('is_url'),
                        ~_content_flag('is_code'),
                        ~_content_flag('is_json')
                    )
            
            # Get total count before pagination
            total = query.count()
            
            # Pagination and ordering
            events = query.order_by(desc(ClipboardEvent.created_at)).limit(limit).offset(offset).all()
            
            # Parse metadata for response
            data = []
            for e in events:
                metadata = _parse_metadata(e.event_metadata)
                content_analysis = metadata.get('content', {})
                system_state = metadata.get('system', {})

                data.append({
                    'id': e.id,
                    'timestamp': e.timestamp.isoformat() if e.timestamp else None,
                    'content_type': e.content_type,
                    'raw_content': e.raw_content[:200] if e.raw_content else None,
                    'source_app': e.source_app,
                    'source_url': e.source_url,
                    'summary': e.processed_summary,
                    'tags': e.tags.split(',') if e.tags else [],
                    'has_image': bool(e.image_path),
                    'ocr_count': len(e.ocr_results) if hasattr(e, 'ocr_results') else 0,
                    'created_at': e.created_at.isoformat() if e.created_at else None,
                    'event_metadata': {
                        'content_icon': _content_icon(content_analysis),
                        'content_length': content_analysis.get('content_length', 0),
                        'is_url': content_analysis.get('is_url', False),
                        'is_code': content_analysis.get('is_code', False),
                        'is_json': content_analysis.get('is_json', False),
                        'cpu_percent': system_state.get('cpu_percent'),
                        'memory_percent': system_state.get('memory_percent')
                    }
                })

            return jsonify({
                'success': True,
                'data': data,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total': total
                }
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    
    @app.route('/api/activity', methods=['GET'])
    def get_activity_timeline():
        """Get activity/window tracking events with filtering."""
        try:
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            app_filter = request.args.get('app', None)
            hours = request.args.get('hours', 24, type=int)
            search_text = request.args.get('search', None)
            
            query = ActivityEvent.query
            
            # Time filter
            since = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(ActivityEvent.created_at >= since)
            
            # Application filter
            if app_filter:
                query = query.filter(ActivityEvent.application.ilike(f'%{_escape_like(app_filter)}%'))

            # Search in window title and URL
            if search_text:
                escaped = _escape_like(search_text)
                query = query.filter(
                    (ActivityEvent.window_title.ilike(f'%{escaped}%')) |
                    (ActivityEvent.url.ilike(f'%{escaped}%'))
                )
            
            total = query.count()
            events = query.order_by(desc(ActivityEvent.created_at)).limit(limit).offset(offset).all()
            
            # Parse metadata for response
            data = []
            for e in events:
                metadata = _parse_metadata(e.event_metadata)
                system_state = metadata.get('system', {})
                system_info = metadata.get('system_info', {})

                data.append({
                    'id': e.id,
                    'timestamp': e.timestamp.isoformat() if e.timestamp else None,
                    'window_title': e.window_title,
                    'application': e.application,
                    'url': e.url,
                    'created_at': e.created_at.isoformat() if e.created_at else None,
                    'system_state': {
                        'cpu_percent': system_state.get('cpu_percent'),
                        'memory_percent': system_state.get('memory_percent')
                    },
                    'system_info': system_info,
                    'full_metadata': metadata
                })

            return jsonify({
                'success': True,
                'data': data,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total': total
                }
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    @app.route('/api/commands', methods=['GET'])
    def get_command_history():
        """Get shell command execution history with filtering."""
        try:
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            search_cmd = request.args.get('search', None)
            hours = request.args.get('hours', 24, type=int)
            exit_code = request.args.get('exit_code', None, type=int)
            
            query = CommandEvent.query
            
            # Time filter
            since = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(CommandEvent.created_at >= since)
            
            # Search filter
            if search_cmd:
                query = query.filter(CommandEvent.command.ilike(f'%{_escape_like(search_cmd)}%'))
            
            # Exit code filter
            if exit_code is not None:
                if exit_code == 0:
                    query = query.filter(CommandEvent.exit_code == 0)
                else:
                    query = query.filter(CommandEvent.exit_code != 0)
            
            total = query.count()
            events = query.order_by(desc(CommandEvent.created_at)).limit(limit).offset(offset).all()
            
            # Parse metadata for response
            data = []
            for e in events:
                metadata = _parse_metadata(e.event_metadata)
                system_state = metadata.get('system', {})
                system_info = metadata.get('system_info', {})

                data.append({
                    'id': e.id,
                    'timestamp': e.timestamp.isoformat() if e.timestamp else None,
                    'command': e.command,
                    'user': e.user_name,
                    'working_dir': e.working_directory,
                    'exit_code': e.exit_code,
                    'success': None if e.exit_code is None else e.exit_code == 0,
                    'created_at': e.created_at.isoformat() if e.created_at else None,
                    'system_state': {
                        'cpu_percent': system_state.get('cpu_percent'),
                        'memory_percent': system_state.get('memory_percent')
                    },
                    'system_info': system_info,
                    'full_metadata': metadata
                })
            
            return jsonify({
                'success': True,
                'data': data,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total': total
                }
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    
    @app.route('/api/search', methods=['POST'])
    def search_events():
        """Semantic search across all events."""
        try:
            data = request.get_json() or {}
            query_text = data.get('query', '')
            event_types = data.get('types', ['clipboard', 'activity', 'commands'])  # Which tables to search
            limit = data.get('limit', 50)
            hours = data.get('hours', 168)  # 1 week default
            
            if not query_text:
                return jsonify({'success': False, 'error': 'Query text required'}), 400
            
            results = []
            since = datetime.utcnow() - timedelta(hours=hours)
            
            escaped_query = _escape_like(query_text)

            # Search clipboard events
            if 'clipboard' in event_types:
                clipboard_results = ClipboardEvent.query.filter(
                    (ClipboardEvent.raw_content.ilike(f'%{escaped_query}%')) |
                    (ClipboardEvent.processed_summary.ilike(f'%{escaped_query}%')) |
                    (ClipboardEvent.tags.ilike(f'%{escaped_query}%')),
                    ClipboardEvent.created_at >= since
                ).limit(limit).all()
                
                for e in clipboard_results:
                    results.append({
                        'type': 'clipboard',
                        'id': e.id,
                        'timestamp': e.timestamp.isoformat() if e.timestamp else None,
                        'title': f"{e.content_type}: {e.source_app or 'Unknown'}",
                        'summary': e.processed_summary or e.raw_content[:100],
                        'tags': e.tags.split(',') if e.tags else [],
                        'relevance': 'high' if e.processed_summary and query_text.lower() in e.processed_summary.lower() else 'medium'
                    })
            
            # Search activity events
            if 'activity' in event_types:
                activity_results = ActivityEvent.query.filter(
                    (ActivityEvent.window_title.ilike(f'%{escaped_query}%')) |
                    (ActivityEvent.application.ilike(f'%{escaped_query}%')) |
                    (ActivityEvent.url.ilike(f'%{escaped_query}%')),
                    ActivityEvent.created_at >= since
                ).limit(limit).all()
                
                for e in activity_results:
                    results.append({
                        'type': 'activity',
                        'id': e.id,
                        'timestamp': e.timestamp.isoformat() if e.timestamp else None,
                        'title': e.application,
                        'summary': e.window_title,
                        'tags': [e.application],
                        'relevance': 'high'
                    })
            
            # Search command events
            if 'commands' in event_types:
                command_results = CommandEvent.query.filter(
                    CommandEvent.command.ilike(f'%{escaped_query}%'),
                    CommandEvent.created_at >= since
                ).limit(limit).all()
                
                for e in command_results:
                    results.append({
                        'type': 'command',
                        'id': e.id,
                        'timestamp': e.timestamp.isoformat() if e.timestamp else None,
                        'title': 'Shell Command',
                        'summary': e.command,
                        'tags': [f"exit:{e.exit_code}"] if e.exit_code is not None else [],
                        'relevance': 'high'
                    })
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return jsonify({
                'success': True,
                'query': query_text,
                'count': len(results),
                'data': results[:limit]
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    
    @app.route('/api/stats', methods=['GET'])
    def get_system_stats():
        """Get system statistics."""
        try:
            hours = request.args.get('hours', 24, type=int)
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Count events by type
            clipboard_count = ClipboardEvent.query.filter(
                ClipboardEvent.created_at >= since
            ).count()
            
            activity_count = ActivityEvent.query.filter(
                ActivityEvent.created_at >= since
            ).count()
            
            command_count = CommandEvent.query.filter(
                CommandEvent.created_at >= since
            ).count()
            
            ocr_count = OCRResult.query.filter(
                OCRResult.created_at >= since
            ).count()
            
            # Get top applications
            top_apps = db.session.query(
                ActivityEvent.application,
                func.count(ActivityEvent.id).label('count')
            ).filter(ActivityEvent.created_at >= since).group_by(
                ActivityEvent.application
            ).order_by(desc(func.count(ActivityEvent.id))).limit(10).all()
            
            # Get top clipboard sources
            top_sources = db.session.query(
                ClipboardEvent.source_app,
                func.count(ClipboardEvent.id).label('count')
            ).filter(ClipboardEvent.created_at >= since).group_by(
                ClipboardEvent.source_app
            ).order_by(desc(func.count(ClipboardEvent.id))).limit(10).all()
            
            return jsonify({
                'success': True,
                'period_hours': hours,
                'counts': {
                    'clipboard': clipboard_count,
                    'activity': activity_count,
                    'commands': command_count,
                    'ocr': ocr_count,
                    'total': clipboard_count + activity_count + command_count
                },
                'top_applications': [
                    {'app': app, 'count': count} for app, count in top_apps
                ] if top_apps else [],
                'top_clipboard_sources': [
                    {'app': app, 'count': count} for app, count in top_sources
                ] if top_sources else [],
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    
    @app.route('/api/clipboard/<int:event_id>/details', methods=['GET'])
    def get_clipboard_details(event_id):
        """Get full details of a clipboard event with all metadata parsed."""
        try:
            event = ClipboardEvent.query.get(event_id)
            if not event:
                return jsonify({'success': False, 'error': 'Event not found'}), 404
            
            # Parse metadata
            metadata = _parse_metadata(event.event_metadata)
            content_analysis = metadata.get('content', {})
            system_state = metadata.get('system', {})
            activity_context = metadata.get('activity', {})

            return jsonify({
                'success': True,
                'id': event.id,
                'timestamp': event.timestamp.isoformat() if event.timestamp else None,
                'created_at': event.created_at.isoformat() if event.created_at else None,
                'basic': {
                    'content_type': event.content_type,
                    'source_app': event.source_app,
                    'source_url': event.source_url,
                    'summary': event.processed_summary,
                    'tags': event.tags.split(',') if event.tags else [],
                    'has_image': bool(event.image_path),
                    'image_path': event.image_path
                },
                'raw_data': {
                    'content': event.raw_content,
                    'length': len(event.raw_content) if event.raw_content else 0
                },
                'content_analysis': {
                    'icon': _content_icon(content_analysis),
                    'length': content_analysis.get('content_length', 0),
                    'is_url': content_analysis.get('is_url', False),
                    'is_code': content_analysis.get('is_code', False),
                    'is_json': content_analysis.get('is_json', False),
                    'line_count': content_analysis.get('line_count', 0),
                    'word_count': content_analysis.get('word_count', 0),
                    'hash': content_analysis.get('content_hash', '')
                },
                'system_state': {
                    'cpu_percent': system_state.get('cpu_percent'),
                    'memory_percent': system_state.get('memory_percent'),
                    'disk_percent': system_state.get('disk_percent'),
                    'process_count': system_state.get('process_count')
                },
                'activity_context': {
                    'app': activity_context.get('app'),
                    'window': activity_context.get('window')
                },
                'system_info': metadata.get('system_info', {}),
                'ocr_count': len(event.ocr_results) if hasattr(event, 'ocr_results') else 0,
                'full_metadata': metadata
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    
    @app.route('/api/activity/<int:event_id>/details', methods=['GET'])
    def get_activity_details(event_id):
        """Get full details of an activity event with all metadata parsed."""
        try:
            event = ActivityEvent.query.get(event_id)
            if not event:
                return jsonify({'success': False, 'error': 'Event not found'}), 404
            
            metadata = _parse_metadata(event.event_metadata)
            system_state = metadata.get('system', {})
            system_info = metadata.get('system_info', {})

            return jsonify({
                'success': True,
                'id': event.id,
                'timestamp': event.timestamp.isoformat() if event.timestamp else None,
                'created_at': event.created_at.isoformat() if event.created_at else None,
                'basic': {
                    'window_title': event.window_title,
                    'application': event.application,
                    'url': event.url
                },
                'system_state': {
                    'cpu_percent': system_state.get('cpu_percent'),
                    'memory_percent': system_state.get('memory_percent'),
                    'disk_percent': system_state.get('disk_percent'),
                    'process_count': system_state.get('process_count')
                },
                'system_info': {
                    'os': system_info.get('os'),
                    'user': system_info.get('user'),
                    'machine': system_info.get('machine')
                },
                'full_metadata': metadata
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    
    @app.route('/api/commands/<int:event_id>/details', methods=['GET'])
    def get_command_details(event_id):
        """Get full details of a command event with all metadata parsed."""
        try:
            event = CommandEvent.query.get(event_id)
            if not event:
                return jsonify({'success': False, 'error': 'Event not found'}), 404
            
            metadata = _parse_metadata(event.event_metadata)
            system_state = metadata.get('system', {})
            system_info = metadata.get('system_info', {})
            success = None if event.exit_code is None else event.exit_code == 0
            status_icon = '❔' if success is None else '✅' if success else '❌'
            
            return jsonify({
                'success': True,
                'id': event.id,
                'timestamp': event.timestamp.isoformat() if event.timestamp else None,
                'created_at': event.created_at.isoformat() if event.created_at else None,
                'basic': {
                    'command': event.command,
                    'user': event.user_name,
                    'working_directory': event.working_directory,
                    'exit_code': event.exit_code,
                    'status': status_icon,
                    'success': success
                },
                'system_state': {
                    'cpu_percent': system_state.get('cpu_percent'),
                    'memory_percent': system_state.get('memory_percent'),
                    'disk_percent': system_state.get('disk_percent'),
                    'process_count': system_state.get('process_count')
                },
                'system_info': {
                    'os': system_info.get('os'),
                    'user': system_info.get('user'),
                    'machine': system_info.get('machine')
                },
                'duration': metadata.get('duration', None),
                'full_metadata': metadata
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    
    @app.route('/api/ocr/<int:clipboard_id>', methods=['GET'])
    def get_ocr_results(clipboard_id):
        """Get OCR results for a specific clipboard event."""
        try:
            results = OCRResult.query.filter(
                OCRResult.clipboard_event_id == clipboard_id
            ).all()
            
            return jsonify({
                'success': True,
                'clipboard_id': clipboard_id,
                'data': [{
                    'id': r.id,
                    'extracted_text': r.extracted_text,
                    'confidence': r.confidence,
                    'timestamp': r.timestamp.isoformat() if r.timestamp else None
                } for r in results]
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    
    @app.route('/api/health/extended', methods=['GET'])
    def extended_health_check():
        """Check health of extended features."""
        try:
            checks = {
                'clipboard_table': db.session.query(ClipboardEvent).first() is not None,
                'activity_table': db.session.query(ActivityEvent).first() is not None,
                'command_table': db.session.query(CommandEvent).first() is not None,
                'ocr_table': db.session.query(OCRResult).first() is not None,
            }
            
            return jsonify({
                'success': True,
                'status': 'healthy',
                'checks': checks,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        except Exception as e:
            return jsonify({
                'success': False,
                'status': 'unhealthy',
                'error': str(e)
            }), 500
