"""add document_id, question, recipe_slug, and mode columns

Revision ID: a87f533e2793
Revises: 17de2671ac14
Create Date: 2022-05-27 23:02:54.715015

"""
from typing import Optional

import sqlalchemy as sa
import sqlmodel

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a87f533e2793"
down_revision: Optional[str] = "17de2671ac14"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    op.add_column(
        "completion",
        sa.Column(
            "document_id",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="default",
        ),
    )
    op.add_column(
        "completion",
        sa.Column(
            "question",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="default",
        ),
    )
    op.add_column(
        "completion",
        sa.Column(
            "recipe_slug",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="default",
        ),
    )
    op.add_column(
        "completion",
        sa.Column(
            "mode",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="default",
        ),
    )
    op.create_index(
        op.f("ix_completion_document_id"), "completion", ["document_id"], unique=False
    )
    op.create_index(op.f("ix_completion_mode"), "completion", ["mode"], unique=False)
    op.create_index(
        op.f("ix_completion_recipe_slug"), "completion", ["recipe_slug"], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    op.drop_index(op.f("ix_completion_recipe_slug"), table_name="completion")
    op.drop_index(op.f("ix_completion_mode"), table_name="completion")
    op.drop_index(op.f("ix_completion_document_id"), table_name="completion")
    op.drop_column("completion", "mode")
    op.drop_column("completion", "recipe_slug")
    op.drop_column("completion", "question")
    op.drop_column("completion", "document_id")
    # ### end Alembic commands ###
