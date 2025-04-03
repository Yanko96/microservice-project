from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250405_notification_enum'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()

    # 创建通知类型枚举（避免重复）
    notification_enum = postgresql.ENUM(
        'FOLLOW', 'POST_LIKE', 'POST_COMMENT', 'COMMENT_LIKE',
        'COMMENT_REPLY', 'MENTION', 'SYSTEM',
        name='notificationtype'
    )
    notification_enum.create(bind=bind, checkfirst=True)

    # 创建通知表
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', postgresql.ENUM(
            'FOLLOW', 'POST_LIKE', 'POST_COMMENT', 'COMMENT_LIKE',
            'COMMENT_REPLY', 'MENTION', 'SYSTEM',
            name='notificationtype', create_type=False
        ), nullable=False),
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
    )

    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])

def downgrade():
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
    bind = op.get_bind()
    postgresql.ENUM(name='notificationtype').drop(bind=bind, checkfirst=True)
