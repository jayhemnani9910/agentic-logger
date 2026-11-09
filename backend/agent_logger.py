"""
Agent implementation for event logging
"""
import requests

REQUEST_TIMEOUT = 5

class AgentLogger:
    def __init__(self, api_url='http://localhost:8000/api', agent_id=None):
        self.api_url = api_url
        self.agent_id = agent_id or 'default_agent'
        self.session_id = None
        
    def start_session(self, info=None):
        """Start agent session"""
        try:
            resp = requests.post(
                f'{self.api_url}/sessions',
                json={
                    'agent_id': self.agent_id,
                    'info': info or {}
                },
                timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 201:
                self.session_id = resp.json()['id']
                return True
        except Exception as e:
            print(f'Error starting session: {e}')
        return False
    
    def log_event(self, event_type, message=None, data=None, status='pending', task_id=None):
        """Log event"""
        try:
            resp = requests.post(
                f'{self.api_url}/events',
                json={
                    'event_type': event_type,
                    'agent_id': self.agent_id,
                    'task_id': task_id,
                    'message': message,
                    'data': data or {},
                    'status': status
                },
                timeout=REQUEST_TIMEOUT
            )
            return resp.status_code == 201
        except Exception as e:
            print(f'Error logging event: {e}')
        return False
    
    def end_session(self):
        """End agent session"""
        try:
            resp = requests.put(
                f'{self.api_url}/sessions/{self.agent_id}',
                json={'status': 'completed'},
                timeout=REQUEST_TIMEOUT
            )
            return resp.status_code == 200
        except Exception as e:
            print(f'Error ending session: {e}')
        return False
    
    def log_task_start(self, task_id, data=None):
        """Log task start"""
        return self.log_event(
            'task_start',
            message=f'Task {task_id} started',
            data={'task_id': task_id, **(data or {})},
            task_id=task_id
        )
    
    def log_task_end(self, task_id, status='completed', data=None):
        """Log task end"""
        return self.log_event(
            'task_end',
            message=f'Task {task_id} {status}',
            data={'task_id': task_id, 'status': status, **(data or {})},
            status=status,
            task_id=task_id
        )
    
    def log_decision(self, decision_type, details=None):
        """Log decision"""
        return self.log_event(
            'decision',
            message=f'Decision: {decision_type}',
            data={'decision_type': decision_type, 'details': details}
        )
    
    def log_error(self, error_message, traceback=None):
        """Log error"""
        return self.log_event(
            'error',
            message=error_message,
            data={'traceback': traceback}
        )

if __name__ == '__main__':
    # Example usage
    logger = AgentLogger(agent_id='agent_001')
    logger.start_session({'version': '1.0'})
    logger.log_task_start('task_1')
    logger.log_event('info', 'Processing started')
    logger.log_task_end('task_1', 'completed')
    logger.end_session()
    print('Logging complete')
