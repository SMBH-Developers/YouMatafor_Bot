"""10_march

Revision ID: 98c8d452dfaa
Revises: 52a0a41f5d1d
Create Date: 2024-03-11 03:04:06.348578

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98c8d452dfaa'
down_revision = '52a0a41f5d1d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('sending_10_march', sa.TIMESTAMP(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'sending_10_march')
    # ### end Alembic commands ###