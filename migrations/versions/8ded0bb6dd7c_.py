"""empty message

Revision ID: 8ded0bb6dd7c
Revises: 
Create Date: 2020-07-19 14:22:09.913067

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ded0bb6dd7c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_test_scores', sa.Column('test_day', sa.Date(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_test_scores', 'test_day')
    # ### end Alembic commands ###