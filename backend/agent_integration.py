"""
Integration module to wire agents and orchestrator into Flask app.

This module handles:
- Initializing the event orchestrator
- Starting background agents
- Managing agent lifecycle with Flask app
- Thread-safe event processing
"""

import threading
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class AgentIntegration:
    """Manages integration of agents with Flask app."""
    
    def __init__(self):
        self.orchestrator = None
        self.agent_thread = None
        self.running = False
        self.lock = threading.Lock()
    
    def _on_event(self, event_data):
        """Handle event from orchestrator."""
        logger.debug(f'Event processed: {event_data}')
    
    def init_app(self, app):
        """Initialize agents with Flask app context."""
        try:
            # Import orchestrator here to avoid circular imports
            try:
                from agents.orchestrator import EventOrchestrator
                from models_extended import db
            except ImportError:
                from .agents.orchestrator import EventOrchestrator
                from .models_extended import db
            
            with app.app_context():
                # Create orchestrator instance
                self.orchestrator = EventOrchestrator(
                    db_session=db.session,
                    on_event_callback=self._on_event
                )
                
                # Register cleanup on app shutdown
                def cleanup(exc=None):
                    self.stop_agents()
                
                app.teardown_appcontext(cleanup)
                
                logger.info('Agent integration initialized')
            
            return self
        except Exception as e:
            logger.error(f'Failed to initialize agent integration: {e}')
            # Don't raise - allow app to start without agents
            logger.warning('Continuing without agent integration')
            return self
    
    def start_agents(self):
        """Start background agent threads."""
        if self.running:
            logger.warning('Agents already running')
            return
        
        with self.lock:
            if self.running:
                return
            
            try:
                # Start orchestrator in background thread
                self.agent_thread = threading.Thread(
                    target=self._run_orchestrator,
                    daemon=True,
                    name='AgentOrchestrator'
                )
                self.agent_thread.start()
                self.running = True
                logger.info('Agent orchestrator started in background thread')
            except Exception as e:
                logger.error(f'Failed to start agents: {e}')
                self.running = False
    
    def stop_agents(self):
        """Stop background agent threads."""
        if not self.running:
            return
        
        with self.lock:
            if not self.running:
                return
            
            try:
                if self.orchestrator:
                    self.orchestrator.stop()
                self.running = False
                logger.info('Agent orchestrator stopped')
            except Exception as e:
                logger.error(f'Error stopping agents: {e}')
    
    def _run_orchestrator(self):
        """Run orchestrator in background."""
        try:
            if self.orchestrator:
                self.orchestrator.start()
        except Exception as e:
            logger.error(f'Orchestrator error: {e}')
            self.running = False
    
    def get_status(self) -> dict:
        """Get status of agents."""
        return {
            'running': self.running,
            'orchestrator': 'active' if self.orchestrator and self.running else 'inactive',
            'has_orchestrator': self.orchestrator is not None
        }


# Global instance
agent_integration = AgentIntegration()


def init_agent_integration(app):
    """Initialize agent integration with Flask app."""
    agent_integration.init_app(app)
    # Start agents if not in testing mode
    if not app.config.get('TESTING', False):
        agent_integration.start_agents()
    return agent_integration
