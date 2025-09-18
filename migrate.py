#!/usr/bin/env python3
"""
Database migration script for deployment
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

def run_migrations():
    """Run Alembic migrations"""
    try:
        # Run migrations
        result = subprocess.run([
            sys.executable, '-m', 'alembic',
            '-c', 'migrations/alembic.ini',
            'upgrade', 'head'
        ], capture_output=True, text=True, env=os.environ)

        if result.returncode == 0:
            print("✅ Database migrations completed successfully")
            print(result.stdout)
        else:
            print("❌ Migration failed")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

    return True

def create_migration(message="auto"):
    """Create a new migration"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'alembic',
            '-c', 'migrations/alembic.ini',
            'revision', '--autogenerate', '-m', message
        ], capture_output=True, text=True, env=os.environ)

        if result.returncode == 0:
            print("✅ Migration created successfully")
            print(result.stdout)
        else:
            print("❌ Migration creation failed")
            print(result.stderr)

    except Exception as e:
        print(f"❌ Error creating migration: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'create':
        message = sys.argv[2] if len(sys.argv) > 2 else 'auto'
        create_migration(message)
    else:
        run_migrations()