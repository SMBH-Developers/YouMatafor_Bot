"""init

Revision ID: adec750e35be
Revises: 320ce2a5a0c4
Create Date: 2024-03-25 08:32:42.739815

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adec750e35be'
down_revision = '320ce2a5a0c4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('sending_25_march', sa.TIMESTAMP(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'sending_25_march')
    # ### end Alembic commands ###