"""user_access_history_action

Revision ID: 3a553fb8b911
Revises: 138ca0a2b975
Create Date: 2023-01-27 16:03:25.497058

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3a553fb8b911"
down_revision = "138ca0a2b975"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user_access_history", sa.Column("action", sa.String(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user_access_history", "action")
    # ### end Alembic commands ###