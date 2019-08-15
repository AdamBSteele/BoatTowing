"""Add stripe ID to customer model

Revision ID: 6ee5679a642d
Revises: a08b886822d7
Create Date: 2017-12-17 16:51:48.574629

"""

# revision identifiers, used by Alembic.
revision = '6ee5679a642d'
down_revision = 'a08b886822d7'


from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('terraintracker_user', sa.Column('stripe_customer_id', sa.String(length=32), nullable=True))


def downgrade():
    op.drop_column('terraintracker_user', 'stripe_customer_id')
