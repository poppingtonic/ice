"""add excerpt_hash column

Revision ID: 17de2671ac14
Revises: e458dd1343b4
Create Date: 2022-05-27 21:18:43.074645

"""
from typing import Optional

import sqlalchemy as sa
import sqlmodel

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "17de2671ac14"
down_revision: Optional[str] = "e458dd1343b4"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column(
        "completion",
        sa.Column(
            "excerpt_hash",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="default",
        ),
    )
    op.create_index(
        op.f("ix_completion_excerpt_hash"), "completion", ["excerpt_hash"], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    op.drop_index(op.f("ix_completion_excerpt_hash"), table_name="completion")
    op.drop_column("completion", "excerpt_hash")
    # ### end Alembic commands ###
