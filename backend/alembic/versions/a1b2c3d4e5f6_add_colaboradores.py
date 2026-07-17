"""add colaboradores table

Revision ID: a1b2c3d4e5f6
Revises: 51d1cd45edb1
Create Date: 2026-07-17 02:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'dfd34eaf14d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'colaboradores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('matricula', sa.String(length=50), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('funcao', sa.String(length=150), nullable=True),
        sa.Column('obra_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ATIVO'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['obra_id'], ['obras.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_colaboradores_id', 'colaboradores', ['id'], unique=False)
    op.create_index('ix_colaboradores_matricula', 'colaboradores', ['matricula'], unique=True)
    op.create_index('ix_colaboradores_nome', 'colaboradores', ['nome'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_colaboradores_nome', table_name='colaboradores')
    op.drop_index('ix_colaboradores_matricula', table_name='colaboradores')
    op.drop_index('ix_colaboradores_id', table_name='colaboradores')
    op.drop_table('colaboradores')
