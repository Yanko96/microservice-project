"""初始化帖子服务表

Revision ID: 8b72e3a19f8e
Revises:
Create Date: 2023-04-04 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8b72e3a19f8e'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()

    # 创建枚举类型（使用 checkfirst=True 避免重复创建）
    media_enum = postgresql.ENUM('IMAGE', 'VIDEO', 'LINK', 'NONE', name='mediatype')
    visibility_enum = postgresql.ENUM('PUBLIC', 'FOLLOWERS', 'PRIVATE', name='visibility')
    reaction_enum = postgresql.ENUM('LIKE', 'LOVE', 'HAHA', 'WOW', 'SAD', 'ANGRY', name='reactiontype')

    media_enum.create(bind=bind, checkfirst=True)
    visibility_enum.create(bind=bind, checkfirst=True)
    reaction_enum.create(bind=bind, checkfirst=True)

    # 标签表
    op.create_table(
        'tags',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('post_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('name')
    )

    # 帖子表
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('media_type',
                  postgresql.ENUM('IMAGE', 'VIDEO', 'LINK', 'NONE', name='mediatype', create_type=False),
                  nullable=False,
                  server_default='NONE'),
        sa.Column('media_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('visibility',
                  postgresql.ENUM('PUBLIC', 'FOLLOWERS', 'PRIVATE', name='visibility', create_type=False),
                  nullable=False,
                  server_default='PUBLIC'),
        sa.Column('is_edited', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_pinned', sa.Boolean(), nullable=True, default=False),
        sa.Column('comment_count', sa.Integer(), nullable=True, default=0),
        sa.Column('like_count', sa.Integer(), nullable=True, default=0),
        sa.Column('share_count', sa.Integer(), nullable=True, default=0),
        sa.Column('view_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_posts_id'), 'posts', ['id'], unique=False)
    op.create_index(op.f('ix_posts_user_id'), 'posts', ['user_id'], unique=False)

    # 帖子-标签关联表
    op.create_table(
        'post_tag',
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('tag_name', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_name'], ['tags.name'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('post_id', 'tag_name')
    )

    # 评论表
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('like_count', sa.Integer(), nullable=True, default=0),
        sa.Column('reply_count', sa.Integer(), nullable=True, default=0),
        sa.Column('is_edited', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_id'), 'comments', ['id'], unique=False)
    op.create_index(op.f('ix_comments_post_id'), 'comments', ['post_id'], unique=False)
    op.create_index(op.f('ix_comments_user_id'), 'comments', ['user_id'], unique=False)
    op.create_index(op.f('ix_comments_parent_id'), 'comments', ['parent_id'], unique=False)

    # 反应表
    op.create_table(
        'reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type',
                  postgresql.ENUM('LIKE', 'LOVE', 'HAHA', 'WOW', 'SAD', 'ANGRY', name='reactiontype', create_type=False),
                  nullable=False,
                  server_default='LIKE'),
        sa.Column('post_id', sa.Integer(), nullable=True),
        sa.Column('comment_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'post_id', name='uix_user_post_reaction'),
        sa.UniqueConstraint('user_id', 'comment_id', name='uix_user_comment_reaction')
    )
    op.create_index(op.f('ix_reactions_id'), 'reactions', ['id'], unique=False)
    op.create_index(op.f('ix_reactions_user_id'), 'reactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_reactions_post_id'), 'reactions', ['post_id'], unique=False)
    op.create_index(op.f('ix_reactions_comment_id'), 'reactions', ['comment_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_reactions_comment_id'), table_name='reactions')
    op.drop_index(op.f('ix_reactions_post_id'), table_name='reactions')
    op.drop_index(op.f('ix_reactions_user_id'), table_name='reactions')
    op.drop_index(op.f('ix_reactions_id'), table_name='reactions')
    op.drop_table('reactions')

    op.drop_index(op.f('ix_comments_parent_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_user_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_post_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_id'), table_name='comments')
    op.drop_table('comments')

    op.drop_table('post_tag')

    op.drop_index(op.f('ix_posts_user_id'), table_name='posts')
    op.drop_index(op.f('ix_posts_id'), table_name='posts')
    op.drop_table('posts')

    op.drop_table('tags')

    bind = op.get_bind()
    postgresql.ENUM(name='reactiontype').drop(bind=bind, checkfirst=True)
    postgresql.ENUM(name='visibility').drop(bind=bind, checkfirst=True)
    postgresql.ENUM(name='mediatype').drop(bind=bind, checkfirst=True)
