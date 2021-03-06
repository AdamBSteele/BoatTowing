"""empty message

Revision ID: 9ecaa4d676bb
Revises: c8058ef5c526
Create Date: 2018-06-18 04:20:26.343667

"""

# revision identifiers, used by Alembic.
revision = '9ecaa4d676bb'
down_revision = 'c8058ef5c526'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('terraintracker_boat', sa.Column('length', sa.String(length=32), nullable=True))
    op.add_column('terraintracker_boat', sa.Column('make', sa.String(length=32), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('terraintracker_boat', 'make')
    op.drop_column('terraintracker_boat', 'length')
    ### end Alembic commands ###
