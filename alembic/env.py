from __future__ import with_statement
import os
from dotenv import load_dotenv
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Load environment variables from .env file
load_dotenv()

# Import database extensions
from extensions import db  # Ensure db is initialized in extensions.py

# Alembic Config object, provides access to .ini file values
config = context.config

# Interpret the config file for Python logging
if config.config_file_name:
    fileConfig(config.config_file_name)

# Set database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Set metadata for migrations
target_metadata = db.metadata

def run_migrations_online():
    """Run migrations in 'online' mode (when connected to the DB)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

def run_migrations_offline():
    """Run migrations in 'offline' mode (no active DB connection)."""
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

# Choose migration strategy based on the environment
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
