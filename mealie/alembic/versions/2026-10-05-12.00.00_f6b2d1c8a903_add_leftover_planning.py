"""Add expected portions and linked leftover meal planning."""

import sqlalchemy as sa
from alembic import op

revision = "f6b2d1c8a903"
down_revision: str | None = "1d9a002d7234"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    with op.batch_alter_table("group_meal_plans", schema=None) as batch_op:
        batch_op.add_column(sa.Column("prepared_portions", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("eaten_portions", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("leftover_source_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("leftover_revision", sa.Integer(), server_default="0", nullable=False))
        batch_op.create_index("ix_group_meal_plans_leftover_source_id", ["leftover_source_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_mealplan_leftover_source", "group_meal_plans", ["leftover_source_id"], ["id"], ondelete="RESTRICT"
        )
        batch_op.create_check_constraint(
            "mealplan_portion_shape",
            "(leftover_source_id IS NULL AND prepared_portions IS NULL AND eaten_portions IS NULL) OR "
            "(leftover_source_id IS NULL AND prepared_portions IS NOT NULL AND eaten_portions IS NOT NULL "
            "AND prepared_portions > 0 AND eaten_portions >= 0 AND eaten_portions <= prepared_portions) OR "
            "(leftover_source_id IS NOT NULL AND prepared_portions IS NULL "
            "AND eaten_portions IS NOT NULL AND eaten_portions > 0)",
        )
        batch_op.create_check_constraint("mealplan_leftover_revision", "leftover_revision >= 0")


def downgrade():
    with op.batch_alter_table("group_meal_plans", schema=None) as batch_op:
        batch_op.drop_constraint("mealplan_leftover_revision", type_="check")
        batch_op.drop_constraint("mealplan_portion_shape", type_="check")
        batch_op.drop_constraint("fk_mealplan_leftover_source", type_="foreignkey")
        batch_op.drop_index("ix_group_meal_plans_leftover_source_id")
        batch_op.drop_column("leftover_revision")
        batch_op.drop_column("leftover_source_id")
        batch_op.drop_column("eaten_portions")
        batch_op.drop_column("prepared_portions")