"""Create images table

Revision ID: 001
Revises: 
Create Date: 2025-09-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create images table
    op.create_table('images',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('original_path', sa.String(length=500), nullable=False),
        sa.Column('original_size', sa.Integer(), nullable=True),
        sa.Column('thumbnail_100_path', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_300_path', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_1200_path', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_images_id'), 'images', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_images_id'), table_name='images')
    op.drop_table('images')
