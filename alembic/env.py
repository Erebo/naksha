from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Append application path
sys.path.insert(0, os.path.abspath("."))

from naksha.core.config import get_settings
from naksha.database.connection import Base
from naksha.database.models import (
    CanonicalParcelModel,
    SurveyHistoryModel,
    AgencyRecordModel,
    AuditLedgerModel,
)

settings = get_settings()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_target_url() -> str:
    """Determine database URL based on runtime context (-x db=test or default settings)."""
    # 1. If explicit config option was set programmatically (e.g. by test runner)
    explicit_url = config.get_main_option("sqlalchemy.url")
    if explicit_url:
        return explicit_url

    # 2. If -x db=test is passed
    x_args = context.get_x_argument(as_dictionary=True)
    if x_args.get("db") == "test":
        url = settings.test_database_url or os.environ.get("NAKSHA_TEST_DATABASE_URL")
        if not url:
            raise ValueError(
                "Test database URL not configured. Set NAKSHA_TEST_DATABASE_URL or configure test_database_url in settings."
            )
        return url

    # 3. Default target is settings.database_url (or DATABASE_URL env var)
    return os.environ.get("DATABASE_URL") or settings.database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_target_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    target_url = get_target_url()
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = target_url

    connect_args = {}
    if target_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
