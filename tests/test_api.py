def test_health(client):
    assert client.get('/health').status_code == 200


def test_create_and_read_event(client):
    created = client.post('/api/events', json={'event_type': 'test', 'task_id': 'task-1', 'status': 'completed'})
    assert created.status_code == 201

    listed = client.get('/api/events?task_id=task-1').get_json()
    assert listed['total'] == 1
    assert listed['events'][0]['status'] == 'completed'


def test_agent_can_start_a_second_session(client):
    first = client.post('/api/sessions', json={'agent_id': 'agent-1'})
    client.put('/api/sessions/agent-1', json={'status': 'completed'})
    second = client.post('/api/sessions', json={'agent_id': 'agent-1'})

    assert first.status_code == second.status_code == 201
    assert second.get_json()['status'] == 'active'
    assert second.get_json()['ended_at'] is None


def test_unknown_exit_code_is_not_a_failure(app, client):
    from extensions import db
    from models_extended import CommandEvent

    with app.app_context():
        db.session.add(CommandEvent(command='echo hi'))
        db.session.commit()

    command = client.get('/api/commands').get_json()['data'][0]
    assert command['exit_code'] is None
    assert command['success'] is None


def test_clipboard_details_include_metadata(app, client):
    from extensions import db
    from models_extended import ClipboardEvent

    with app.app_context():
        event = ClipboardEvent(
            raw_content='hello',
            content_type='text',
            tags='a,b',
            event_metadata={'content': {'content_hash': 'abc'}},
        )
        db.session.add(event)
        db.session.commit()
        event_id = event.id

    details = client.get(f'/api/clipboard/{event_id}/details').get_json()
    assert details['content_analysis']['hash'] == 'abc'
    assert details['basic']['tags'] == ['a', 'b']
    assert details['full_metadata'] == {'content': {'content_hash': 'abc'}}


def test_cors_allows_only_the_dashboard(client):
    allowed = client.get('/health', headers={'Origin': 'http://localhost:3000'})
    blocked = client.get('/health', headers={'Origin': 'http://evil.test'})

    assert allowed.headers.get('Access-Control-Allow-Origin') == 'http://localhost:3000'
    assert 'Access-Control-Allow-Origin' not in blocked.headers
