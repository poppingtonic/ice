"""Save Recipe slug in noderesult

Revision ID: 1121e7d93874
Revises: 6caacd5a1097
Create Date: 2022-06-14 16:01:33.633124

"""
from typing import Optional

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1121e7d93874"
down_revision: Optional[str] = "6caacd5a1097"
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "noderesult",
        sa.Column("recipe", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.execute("UPDATE noderesult SET recipe = ''")
    op.alter_column("noderesult", "recipe", nullable=False)
    op.create_index(
        op.f("ix_noderesult_recipe"), "noderesult", ["recipe"], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_noderesult_recipe"), table_name="noderesult")
    op.drop_column("noderesult", "recipe")
    # ### end Alembic commands ###
