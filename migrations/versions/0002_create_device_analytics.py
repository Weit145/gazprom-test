"""create device analytics

Revision ID: 0002_create_device_analytics
Revises: 0001_create_users_devices
Create Date: 2026-05-15 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_create_device_analytics"
down_revision: Union[str, Sequence[str], None] = "0001_create_users_devices"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "device_analytics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("x_min", sa.Float(), nullable=False),
        sa.Column("x_max", sa.Float(), nullable=False),
        sa.Column("x_count", sa.Integer(), nullable=False),
        sa.Column("x_sum", sa.Float(), nullable=False),
        sa.Column("x_median", sa.Float(), nullable=False),
        sa.Column("y_min", sa.Float(), nullable=False),
        sa.Column("y_max", sa.Float(), nullable=False),
        sa.Column("y_count", sa.Integer(), nullable=False),
        sa.Column("y_sum", sa.Float(), nullable=False),
        sa.Column("y_median", sa.Float(), nullable=False),
        sa.Column("z_min", sa.Float(), nullable=False),
        sa.Column("z_max", sa.Float(), nullable=False),
        sa.Column("z_count", sa.Integer(), nullable=False),
        sa.Column("z_sum", sa.Float(), nullable=False),
        sa.Column("z_median", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["device.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id", name="unique_device_analytics_device_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("device_analytics")
