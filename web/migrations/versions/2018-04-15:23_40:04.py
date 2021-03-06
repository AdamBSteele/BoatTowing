"""empty message

Revision ID: af7ffeb8acff
Revises: 65edab12f83d
Create Date: 2018-04-15 23:40:04.140919

"""

# revision identifiers, used by Alembic.
revision = 'af7ffeb8acff'
down_revision = '65edab12f83d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tow_event', sa.Column('amount_paid', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tow_event', 'amount_paid')
    ### end Alembic commands ###
