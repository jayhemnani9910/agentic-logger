#!/usr/bin/env python3
"""
Test script to verify metadata saving works
"""

import os
import sys
import json
import psycopg2
from datetime import datetime

# Connect to database
conn = psycopg2.connect(
    "postgresql://postgres:postgres@localhost:5432/agentic_logger"
)
cursor = conn.cursor()

# Test query
cursor.execute("""
    SELECT id, raw_content, event_metadata, source_app, created_at 
    FROM clipboard_events 
    ORDER BY created_at DESC 
    LIMIT 3
""")

rows = cursor.fetchall()

print("📊 Recent Clipboard Entries:")
for row in rows:
    print(f"ID: {row[0]}")
    print(f"App: {row[3]}")
    print(f"Content: {row[1][:100]}...")
    print(f"Metadata: {row[2]}")
    print(f"Created: {row[4]}")
    print("-" * 50)

conn.close()