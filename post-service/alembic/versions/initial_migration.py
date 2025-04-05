"""初始化帖子服务表

Revision ID: 8b72e3a19f8e
Revises: 
Create Date: 2023-04-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text, exc

# revision identifiers, used by Alembic.
revision = '8b72e3a19f8e'
down_revision = None
branch_labels = None
depends_on = None


def create_enum_if_not_exists(enum_name, enum_values):
    """
    创建枚举类型（如果不存在）

    参数:
        enum_name: 枚举类型名称
        enum_values: 枚举值列表
    """
    # 连接数据库
    conn = op.get_bind()
    
    # 检查枚举类型是否存在
    check_sql = text(f"SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = '{enum_name}')")
    exists = conn.execute(check_sql).scalar()
    
    if not exists:
        # 创建枚举类型
        values_str = ", ".join([f"'{v}'" for v in enum_values])
        create_sql = text(f"CREATE TYPE {enum_name} AS ENUM ({values_str})")
        conn.execute(create_sql)
        return True
    else:
        return False


def upgrade():
    """
    升级数据库架构
    """
    # 创建媒体类型枚举（如果不存在）
    try:
        media_values = ['image', 'video', 'link', 'none']
        if not create_enum_if_not_exists('mediatype', media_values):
            print("mediatype 枚举类型已存在，跳过创建")
    except exc.SQLAlchemyError as e:
        print(f"创建 mediatype 枚举类型时出错: {e}")
    
    # 创建可见性枚举（如果不存在）
    try:
        visibility_values = ['public', 'followers', 'private']
        if not create_enum_if_not_exists('visibility', visibility_values):
            print("visibility 枚举类型已存在，跳过创建")
    except exc.SQLAlchemyError as e:
        print(f"创建 visibility 枚举类型时出错: {e}")
    
    # 创建反应类型枚举（如果不存在）
    try:
        reaction_values = ['like', 'love', 'haha', 'wow', 'sad', 'angry']
        if not create_enum_if_not_exists('reactiontype', reaction_values):
            print("reactiontype 枚举类型已存在，跳过创建")
    except exc.SQLAlchemyError as e:
        print(f"创建 reactiontype 枚举类型时出错: {e}")
    
    # 创建标签表
    op.create_table(
        'tags',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('post_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('name')
    )
    
    # 创建帖子表
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('media_type', sa.Enum('image', 'video', 'link', 'none', name='mediatype'), nullable=False, server_default='none'),
        sa.Column('media_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('visibility', sa.Enum('public', 'followers', 'private', name='visibility'), nullable=False, server_default='public'),
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
    
    # 创建索引
    op.create_index(op.f('ix_posts_id'), 'posts', ['id'], unique=False)
    op.create_index(op.f('ix_posts_user_id'), 'posts', ['user_id'], unique=False)
    
    # 创建帖子-标签关联表
    op.create_table(
        'post_tag',
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('tag_name', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_name'], ['tags.name'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('post_id', 'tag_name')
    )
    
    # 创建评论表
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
    
    # 创建索引
    op.create_index(op.f('ix_comments_id'), 'comments', ['id'], unique=False)
    op.create_index(op.f('ix_comments_post_id'), 'comments', ['post_id'], unique=False)
    op.create_index(op.f('ix_comments_user_id'), 'comments', ['user_id'], unique=False)
    op.create_index(op.f('ix_comments_parent_id'), 'comments', ['parent_id'], unique=False)
    
    # 创建反应表
    op.create_table(
        'reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('like', 'love', 'haha', 'wow', 'sad', 'angry', name='reactiontype'), nullable=False, server_default='like'),
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
    
    # 创建索引
    op.create_index(op.f('ix_reactions_id'), 'reactions', ['id'], unique=False)
    op.create_index(op.f('ix_reactions_user_id'), 'reactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_reactions_post_id'), 'reactions', ['post_id'], unique=False)
    op.create_index(op.f('ix_reactions_comment_id'), 'reactions', ['comment_id'], unique=False)


def downgrade():
    """
    回滚数据库架构
    """
    # 删除表
    op.drop_table('reactions')
    op.drop_table('comments')
    op.drop_table('post_tag')
    op.drop_table('posts')
    op.drop_table('tags')
    
    # 删除枚举类型
    conn = op.get_bind()
    try:
        conn.execute(text("DROP TYPE IF EXISTS reactiontype"))
        conn.execute(text("DROP TYPE IF EXISTS visibility"))
        conn.execute(text("DROP TYPE IF EXISTS mediatype"))
    except exc.SQLAlchemyError as e:
        print(f"删除枚举类型时出错: {e}")