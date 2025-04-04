"""初始化通知服务表

Revision ID: 9b91adc45f2e
Revises: 
Create Date: 2023-04-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9b91adc45f2e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建通知类型枚举
    notification_type_enum = postgresql.ENUM(
        'follow', 'post_like', 'post_comment', 'comment_like', 'comment_reply', 'mention', 'system', 
        name='notificationtype'
    )
    notification_type_enum.create(op.get_bind())
    
    # 创建通知表
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('follow', 'post_like', 'post_comment', 'comment_like', 'comment_reply', 'mention', 'system', name='notificationtype'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('sender_id', sa.Integer(), nullable=True),
        sa.Column('sender_name', sa.String(), nullable=True),
        sa.Column('sender_avatar', sa.String(), nullable=True),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)


def downgrade():
    # 删除索引
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    
    # 删除表
    op.drop_table('notifications')
    
    # 删除枚举类型
    postgresql.ENUM(name='notificationtype').drop(op.get_bind())