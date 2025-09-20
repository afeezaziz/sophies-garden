"""Garden logbook tables

Revision ID: 002_garden_logbook
Revises: 001
Create Date: 2025-09-20 04:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_garden_logbook'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'garden_plants',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('nickname', sa.String(length=100), nullable=True),
        sa.Column('plant_name', sa.String(length=100), nullable=False),
        sa.Column('scientific_name', sa.String(length=200), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('variety', sa.String(length=100), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('planting_date', sa.Date(), nullable=True),
        sa.Column('location', sa.String(length=120), nullable=True),
        sa.Column('image_url', sa.String(length=300), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='active', nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    op.create_table(
        'observations',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('plant_id', sa.Integer(), sa.ForeignKey('garden_plants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('height_cm', sa.Float(), nullable=True),
        sa.Column('leaves', sa.Integer(), nullable=True),
        sa.Column('flowers', sa.Integer(), nullable=True),
        sa.Column('fruits', sa.Integer(), nullable=True),
        sa.Column('pests', sa.String(length=200), nullable=True),
        sa.Column('diseases', sa.String(length=200), nullable=True),
        sa.Column('photo_url', sa.String(length=300), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    op.create_table(
        'care_events',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('plant_id', sa.Integer(), sa.ForeignKey('garden_plants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('amount', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    op.create_table(
        'harvests',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('plant_id', sa.Integer(), sa.ForeignKey('garden_plants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('quality', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('photo_url', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('harvests')
    op.drop_table('care_events')
    op.drop_table('observations')
    op.drop_table('garden_plants')
