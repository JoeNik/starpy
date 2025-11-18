"""初始数据库表结构

Revision ID: 001
Revises: 
Create Date: 2025-01-15 03:30:00.000000

创建4个核心表:
1. children - 小朋友表
2. rewards - 奖品表
3. reward_children - 奖品-小朋友关联表
4. star_records - 星星记录表
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库: 创建所有表"""
    
    # 1. 创建children表
    op.create_table(
        'children',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('birthday', sa.Date(), nullable=False),
        sa.Column('gender', sa.String(length=10), nullable=False),
        sa.Column('avatar', sa.String(length=255), nullable=True),
        sa.Column('star_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_children_name', 'children', ['name'])

    # 2. 创建rewards表
    op.create_table(
        'rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('image', sa.String(length=255), nullable=True),
        sa.Column('star_cost', sa.Integer(), nullable=False),
        sa.Column('is_redeemed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('redeemed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rewards_is_redeemed', 'rewards', ['is_redeemed'])

    # 3. 创建reward_children关联表
    op.create_table(
        'reward_children',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reward_id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('deduction_amount', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reward_id'], ['rewards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reward_id', 'child_id', name='unique_reward_child')
    )
    op.create_index('ix_reward_children_reward_id', 'reward_children', ['reward_id'])
    op.create_index('ix_reward_children_child_id', 'reward_children', ['child_id'])

    # 4. 创建star_records表
    op.create_table(
        'star_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('reward_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['child_id'], ['children.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reward_id'], ['rewards.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    # 复合索引: 按child_id+created_at查询最近记录
    op.create_index('ix_star_records_child_created', 'star_records', ['child_id', 'created_at'])
    # 索引: 按child_id+type统计不同类型操作
    op.create_index('ix_star_records_child_type', 'star_records', ['child_id', 'type'])
    # 索引: 按reward_id查询关联的兑换记录
    op.create_index('ix_star_records_reward', 'star_records', ['reward_id'])


def downgrade() -> None:
    """降级数据库: 删除所有表"""
    
    # 按依赖关系逆序删除表
    op.drop_index('ix_star_records_reward', table_name='star_records')
    op.drop_index('ix_star_records_child_type', table_name='star_records')
    op.drop_index('ix_star_records_child_created', table_name='star_records')
    op.drop_table('star_records')
    
    op.drop_index('ix_reward_children_child_id', table_name='reward_children')
    op.drop_index('ix_reward_children_reward_id', table_name='reward_children')
    op.drop_table('reward_children')
    
    op.drop_index('ix_rewards_is_redeemed', table_name='rewards')
    op.drop_table('rewards')
    
    op.drop_index('ix_children_name', table_name='children')
    op.drop_table('children')