"""Add cooking provenance to recipe timeline events."""

import sqlalchemy as sa
from alembic import op

revision = "a83f4c27d901"
down_revision: str | None = "f6b2d1c8a903"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    with op.batch_alter_table("recipe_timeline_events") as batch_op:
        batch_op.add_column(sa.Column("cooking_source", sa.String(), nullable=True))
        batch_op.create_index("ix_timeline_actor_source_timestamp", ["user_id", "cooking_source", "timestamp"])


def downgrade():
    with op.batch_alter_table("recipe_timeline_events") as batch_op:
        batch_op.drop_index("ix_timeline_actor_source_timestamp")
        batch_op.drop_column("cooking_source")
