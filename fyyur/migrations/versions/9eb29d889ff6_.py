"""empty message

Revision ID: 9eb29d889ff6
Revises: e8099e3a4360
Create Date: 2021-03-11 22:05:53.792405

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9eb29d889ff6'
down_revision = 'e8099e3a4360'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('shows', sa.Column('artist_id', sa.Integer(), nullable=False, server_default='1'))
    op.create_foreign_key(None, 'shows', 'artist', ['artist_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'shows', type_='foreignkey')
    op.drop_column('shows', 'artist_id')
    # ### end Alembic commands ###
