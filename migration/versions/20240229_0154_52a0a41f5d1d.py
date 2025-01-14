"""comment

Revision ID: 52a0a41f5d1d
Revises: 659c94cbf842
Create Date: 2024-02-29 01:54:46.565240

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52a0a41f5d1d'
down_revision = '659c94cbf842'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('sending_29_feb', sa.TIMESTAMP(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'sending_29_feb')
    # ### end Alembic commands ###
