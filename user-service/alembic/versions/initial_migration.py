"""初始化用户表

Revision ID: 9b91adc19f8e
Revises: 
Create Date: 2023-04-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = '9b91adc19f8e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade():
    # 删除索引
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')

    # 删除表
    op.drop_table('users')