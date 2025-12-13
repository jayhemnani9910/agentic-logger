"""
Enhanced API endpoints that return rich metadata

Add these routes to routes_extended.py or create new file
"""

def register_enhanced_routes(app):
    """Register enhanced routes with rich metadata"""
    
    @app.route('/api/clipboard/<int:event_id>/details')
    def get_clipboard_event_details(event_id):
        """Get full clipboard event details with metadata"""
        try:
            from models_extended import ClipboardEvent
            import json
            
            event = ClipboardEvent.query.get_or_404(event_id)
            metadata = {}
            try:
                metadata = json.loads(event.event_metadata or '{}')
            except:
                pass
            
            content_analysis = metadata.get('content', {})
            system_state = metadata.get('system', {})
            activity_context = metadata.get('activity', {})
            
            return jsonify({
                'success': True,
                'data': {
                    'id': event.id,
                    'timestamp': event.timestamp.isoformat(),
                    'created_at': event.created_at.isoformat(),
                    
                    # Content
                    'raw_content': event.raw_content,
                    'content_type': event.content_type,
                    
                    # AI Processing
                    'summary': event.processed_summary,
                    'tags': event.tags.split(',') if event.tags else [],
                    
                    # Source Context
                    'source': {
                        'app': event.source_app,
                        'url': event.source_url,
                    },
                    
                    # Content Analysis
                    'analysis': {
                        'content_length': content_analysis.get('content_length'),
                        'content_hash': content_analysis.get('content_hash'),
                        'is_url': content_analysis.get('is_url', False),
                        'is_code': content_analysis.get('is_code', False),
                        'is_json': content_analysis.get('is_json', False),
                        'line_count': content_analysis.get('line_count'),
                        'word_count': content_analysis.get('word_count'),
                        'has_code_patterns': content_analysis.get('has_code_patterns', False),
                    },
                    
                    # System State at capture time
                    'system_state': {
                        'cpu_percent': system_state.get('cpu_percent'),
                        'memory_percent': system_state.get('memory_percent'),
                        'disk_percent': system_state.get('disk_percent'),
                        'process_count': system_state.get('process_count'),
                    },
                    
                    # Activity Context
                    'activity': activity_context,
                    
                    # Image data if applicable
                    'image': {
                        'path': event.image_path,
                        'ocr_count': len(event.ocr_results) if hasattr(event, 'ocr_results') else 0,
                    } if event.content_type == 'image' else None,
                }
            })
        except Exception as e:
            return jsonify({'error': str(e), 'success': False}), 400
    
    @app.route('/api/clipboard/summary')
    def get_clipboard_summary():
        """Get summary of clipboard events with metadata"""
        try:
            from models_extended import ClipboardEvent
            from datetime import datetime, timedelta
            
            # Query parameters
            limit = request.args.get('limit', 20, type=int)
            hours = request.args.get('hours', 24, type=int)
            
            since = datetime.utcnow() - timedelta(hours=hours)
            events = ClipboardEvent.query.filter(
                ClipboardEvent.created_at >= since
            ).order_by(
                ClipboardEvent.created_at.desc()
            ).limit(limit).all()
            
            import json
            
            summary_data = []
            for event in events:
                metadata = {}
                try:
                    metadata = json.loads(event.event_metadata or '{}')
                except:
                    pass
                
                content_analysis = metadata.get('content', {})
                activity_context = metadata.get('activity', {})
                
                # Determine icon based on content type
                icon = '📝'  # default
                if content_analysis.get('is_url'):
                    icon = '🔗'
                elif content_analysis.get('is_code'):
                    icon = '💻'
                elif content_analysis.get('is_json'):
                    icon = '📋'
                elif event.content_type == 'image':
                    icon = '🖼️'
                
                summary_data.append({
                    'id': event.id,
                    'icon': icon,
                    'type': event.content_type,
                    'summary': event.processed_summary or event.raw_content[:100],
                    'tags': event.tags.split(',') if event.tags else [],
                    'source_app': event.source_app,
                    'source_window': activity_context.get('window'),
                    'timestamp': event.created_at.isoformat(),
                    'time_ago': self._time_ago(event.created_at),
                    'metadata': {
                        'length': content_analysis.get('content_length'),
                        'words': content_analysis.get('word_count'),
                        'lines': content_analysis.get('line_count'),
                    }
                })
            
            return jsonify({
                'success': True,
                'data': summary_data,
                'count': len(summary_data),
                'total': ClipboardEvent.query.filter(
                    ClipboardEvent.created_at >= since
                ).count(),
            })
        except Exception as e:
            return jsonify({'error': str(e), 'success': False}), 400
    
    @app.route('/api/activity/<int:event_id>/details')
    def get_activity_event_details(event_id):
        """Get full activity event details"""
        try:
            from models_extended import ActivityEvent
            import json
            
            event = ActivityEvent.query.get_or_404(event_id)
            metadata = {}
            try:
                metadata = json.loads(event.event_metadata or '{}')
            except:
                pass
            
            return jsonify({
                'success': True,
                'data': {
                    'id': event.id,
                    'timestamp': event.timestamp.isoformat(),
                    'window_title': event.window_title,
                    'application': event.application,
                    'url': event.url,
                    'system_info': metadata.get('system', {}),
                    'system_state': metadata.get('state', {}),
                }
            })
        except Exception as e:
            return jsonify({'error': str(e), 'success': False}), 400
    
    @app.route('/api/commands/<int:event_id>/details')
    def get_command_event_details(event_id):
        """Get full command event details"""
        try:
            from models_extended import CommandEvent
            import json
            
            event = CommandEvent.query.get_or_404(event_id)
            metadata = {}
            try:
                metadata = json.loads(event.event_metadata or '{}')
            except:
                pass
            
            return jsonify({
                'success': True,
                'data': {
                    'id': event.id,
                    'timestamp': event.timestamp.isoformat(),
                    'command': event.command,
                    'user': event.user_name,
                    'working_directory': event.working_directory,
                    'exit_code': event.exit_code,
                    'shell': metadata.get('shell'),
                    'duration': metadata.get('duration'),
                    'system_info': metadata.get('system', {}),
                    'system_state': metadata.get('state', {}),
                }
            })
        except Exception as e:
            return jsonify({'error': str(e), 'success': False}), 400

    @staticmethod
    def _time_ago(dt):
        """Convert datetime to 'X min ago' format"""
        from datetime import datetime
        now = datetime.utcnow()
        diff = now - dt
        
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"
