"""empty message

Revision ID: c8058ef5c526
Revises: 7b80dc943066
Create Date: 2018-05-13 18:40:37.878034

"""

# revision identifiers, used by Alembic.
revision = 'c8058ef5c526'
down_revision = '7b80dc943066'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('terraintracker_user', sa.Column('_phone_string', sa.String(length=20), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('terraintracker_user', '_phone_string')
    ### end Alembic commands ###