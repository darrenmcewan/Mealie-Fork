import os
import pathlib

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from pydantic import BaseModel

from tests.utils.alembic_reader import ALEMBIC_MIGRATIONS, import_file


class AlembicMigration(BaseModel):
    path: pathlib.Path
    revision: str | None = None
    down_revision: str | None = None


def test_alembic_revisions_are_in_order() -> None:
    # read all files
    paths = sorted(ALEMBIC_MIGRATIONS.glob("*.py"))

    # convert to sorted list of AlembicMigration
    migrations: list[AlembicMigration] = []

    for path in paths:
        mod = import_file("alembic_version", path)

        revision = getattr(mod, "revision", None)
        down_revision = getattr(mod, "down_revision", None)

        migrations.append(
            AlembicMigration(
                path=path,
                revision=revision,
                down_revision=down_revision,
            )
        )

    # step through each migration and check
    #   - revision is in order
    #   - down_revision is in order
    #   - down_revision is the previous revision
    last = None
    for migration in migrations:
        if last is not None:
            assert last.revision == migration.down_revision, (
                f"{last.revision} != {migration.down_revision} for {migration.path}"
            )

        last = migration
        last = migration


@pytest.mark.parametrize(
    "database_url",
    [
        "sqlite://",
        *([os.environ["COOKING_MIGRATION_DATABASE_URL"]] if os.getenv("COOKING_MIGRATION_DATABASE_URL") else []),
    ],
)
def test_cooking_provenance_migration(database_url: str):
    engine = sa.create_engine(database_url)
    metadata = sa.MetaData()
    original = sa.Table(
        "recipe_timeline_events",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.String),
        sa.Column("timestamp", sa.DateTime),
        sa.Column("subject", sa.String),
    )
    migration = import_file(
        "cooking_provenance_migration",
        ALEMBIC_MIGRATIONS / "2026-10-05-19.00.00_a83f4c27d901_add_cooking_provenance.py",
    )
    try:
        with engine.begin() as connection:
            metadata.create_all(connection)
            connection.execute(original.insert().values(id=1, user_id="actor", subject="legacy subject"))
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
            migrated = sa.Table("recipe_timeline_events", sa.MetaData(), autoload_with=connection)
            assert migrated.c.cooking_source.nullable
            assert connection.execute(sa.select(migrated.c.subject, migrated.c.cooking_source)).one() == (
                "legacy subject",
                None,
            )
            assert "ix_timeline_actor_source_timestamp" in {
                index["name"] for index in sa.inspect(connection).get_indexes("recipe_timeline_events")
            }
            connection.execute(migrated.insert().values(id=2, subject="recorded subject", cooking_source="manual"))
            with Operations.context(MigrationContext.configure(connection)):
                migration.downgrade()
            restored = sa.Table("recipe_timeline_events", sa.MetaData(), autoload_with=connection)
            assert "cooking_source" not in restored.c
            assert connection.execute(sa.select(restored.c.subject).order_by(restored.c.id)).scalars().all() == [
                "legacy subject",
                "recorded subject",
            ]
    finally:
        metadata.drop_all(engine)
        engine.dispose()
