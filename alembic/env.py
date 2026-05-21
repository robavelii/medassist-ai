import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from src.models.llm_cache_model import Base as BaseModel

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata for autogenerate support
target_metadata = BaseModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    db_url = os.getenv("DATABASE_URI")
    if db_url:
        if "postgresql+asyncpg://" in db_url:
            url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        elif "sqlite+aiosqlite://" in db_url:
            url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
        else:
            url = db_url

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
    configuration = config.get_section(config.config_ini_section, {})

    db_url = os.getenv("DATABASE_URI")
    if db_url:
        if "postgresql+asyncpg://" in db_url:
            configuration["sqlalchemy.url"] = db_url.replace(
                "postgresql+asyncpg://", "postgresql+psycopg2://"
            )
            configuration["sqlalchemy.drivername"] = "postgresql+psycopg2"
        elif "sqlite+aiosqlite://" in db_url:
            configuration["sqlalchemy.url"] = db_url.replace(
                "sqlite+aiosqlite://", "sqlite://"
            )
            configuration["sqlalchemy.drivername"] = "sqlite"
        else:
            configuration["sqlalchemy.url"] = db_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
