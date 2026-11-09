import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


@pytest.fixture(scope='session')
def app():
    from app import create_app
    return create_app('testing')


@pytest.fixture
def client(app):
    return app.test_client()
