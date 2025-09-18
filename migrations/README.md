# Database Migrations

This project uses Alembic for database schema migrations.

## Usage

### Creating Migrations

```bash
# Create a new migration with a descriptive message
python migrate.py create "add_user_table"

# Or use the full command
python -m alembic -c migrations/alembic.ini revision --autogenerate -m "add_user_table"
```

### Running Migrations

```bash
# Run all pending migrations
python migrate.py

# Or use alembic directly
python -m alembic -c migrations/alembic.ini upgrade head

# Upgrade to a specific revision
python -m alembic -c migrations/alembic.ini upgrade 001

# Downgrade to a specific revision
python -m alembic -c migrations/alembic.ini downgrade base
```

### Migration Commands

```bash
# Show current revision
python -m alembic -c migrations/alembic.ini current

# Show migration history
python -m alembic -c migrations/alembic.ini history --verbose

# Check for new migrations
python -m alembic -c migrations/alembic.ini check
```

## Database Schema

The current schema includes:

- `contact_messages` - Stores contact form submissions
- `plants` - Stores plant inventory information

## Environment Variables

Set the `DATABASE_URL` environment variable for your PostgreSQL connection:

```
DATABASE_URL=postgresql://username:password@host:port/database_name
```

For production, use a secure connection string and consider using connection pooling.