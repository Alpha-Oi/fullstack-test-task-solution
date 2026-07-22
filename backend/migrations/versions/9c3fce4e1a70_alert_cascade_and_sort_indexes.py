"""add alert cascade and sort indexes

Revision ID: 9c3fce4e1a70
Revises: 0d6439d2e79f
"""

from collections.abc import Sequence

from alembic import op


revision: str = "9c3fce4e1a70"
down_revision: str | Sequence[str] | None = "0d6439d2e79f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("alerts_file_id_fkey", "alerts", type_="foreignkey")
    op.create_foreign_key(
        "alerts_file_id_fkey",
        "alerts",
        "files",
        ["file_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_files_created_at", "files", ["created_at"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_alerts_created_at", table_name="alerts")
    op.drop_index("ix_files_created_at", table_name="files")
    op.drop_constraint("alerts_file_id_fkey", "alerts", type_="foreignkey")
    op.create_foreign_key(
        "alerts_file_id_fkey",
        "alerts",
        "files",
        ["file_id"],
        ["id"],
    )
