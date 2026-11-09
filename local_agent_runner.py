#!/usr/bin/env python3
"""
Local Agent Runner - Runs monitoring agents on this machine and saves to the Docker database

Usage:
    python local_agent_runner.py
"""

import os
import sys
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

try:
    import psycopg2
    from flask import Flask
    from extensions import db
    from agents.orchestrator import EventOrchestrator
    from models_extended import upgrade_schema
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Install dependencies with: pip install -r backend/requirements.txt")
    sys.exit(1)

DEFAULT_POSTGRES_URL = 'postgresql://postgres:postgres@localhost:5432/agentic_logger'


def create_db_app(postgres_url: str) -> Flask:
    """Create a minimal Flask app that owns the database connection"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = postgres_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        upgrade_schema()

    return app


def main():
    """Main entry point"""
    print("🎯 Local Agent Runner for Agentic Logger")
    print("=" * 50)

    postgres_url = os.getenv('POSTGRES_URL', DEFAULT_POSTGRES_URL)

    try:
        psycopg2.connect(postgres_url).close()
        print("✅ Database connection verified")
    except Exception as e:
        print(f"❌ Cannot connect to database: {e}")
        print("Make sure Docker containers are running:")
        print("   docker compose up -d postgres redis")
        sys.exit(1)

    orchestrator = EventOrchestrator(create_db_app(postgres_url), db)
    print(f"📋 Clipboard platform: {orchestrator.clipboard_watcher.platform}")
    orchestrator.start()

    print("\n🎯 Local agents are monitoring...")
    print("🌐 Frontend at http://localhost:3000 will show the data")
    print("\nPress Ctrl+C to stop")

    try:
        while orchestrator.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping agents...")
        orchestrator.stop()


if __name__ == '__main__':
    main()
