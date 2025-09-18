"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-09-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create contact_messages table
    op.create_table(
        'contact_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default='0', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create plants table
    op.create_table(
        'plants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('scientific_name', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('image_url', sa.String(length=300), nullable=True),
        sa.Column('in_stock', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('plants')
    op.drop_table('contact_messages')