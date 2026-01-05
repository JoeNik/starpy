"""add wallet models

Revision ID: 002_wallet_models
Revises: 001_initial_tables
Create Date: 2025-01-15 13:07:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Numeric, Enum


# revision identifiers, used by Alembic.
revision = '002_wallet_models'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 savings_boxes 表
    op.create_table(
        'savings_boxes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('balance', Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_interest', Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('last_interest_date', sa.Date(), nullable=True),
        sa.Column('interest_rate', Numeric(precision=5, scale=4), nullable=False, server_default='0.0500'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('child_id')
    )
    op.create_index('idx_savings_child', 'savings_boxes', ['child_id'])
    
    # 创建 pocket_money 表
    op.create_table(
        'pocket_money',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('balance', Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('child_id')
    )
    op.create_index('idx_pocket_child', 'pocket_money', ['child_id'])
    
    # 创建 wallet_transactions 表
    op.create_table(
        'wallet_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('wallet_type', sa.String(20), nullable=False),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('amount', Numeric(precision=10, scale=2), nullable=False),
        sa.Column('balance_after', Numeric(precision=10, scale=2), nullable=False),
        sa.Column('remark', sa.String(500), nullable=True),
        sa.Column('interest_amount', Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE')
    )
    op.create_index('idx_child_created', 'wallet_transactions', ['child_id', 'created_at'])
    op.create_index('idx_child_wallet', 'wallet_transactions', ['child_id', 'wallet_type'])
    op.create_index('idx_transaction_type', 'wallet_transactions', ['transaction_type'])


def downgrade() -> None:
    op.drop_table('wallet_transactions')
    op.drop_table('pocket_money')
    op.drop_table('savings_boxes')