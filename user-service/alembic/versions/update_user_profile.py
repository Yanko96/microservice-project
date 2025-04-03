"""更新用户资料字段

Revision ID: 48a903c5e2f1
Revises: 9b91adc19f8e
Create Date: 2023-04-03 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '48a903c5e2f1'
down_revision = '9b91adc19f8e'
branch_labels = None
depends_on = None


def upgrade():
    # 创建性别枚举类型
    gender_enum = postgresql.ENUM('male', 'female', 'other', name='gender')
    gender_enum.create(op.get_bind())
    
    # 添加新的列
    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(), nullable=True))
    op.add_column('users', sa.Column('website', sa.String(), nullable=True))
    op.add_column('users', sa.Column('gender', sa.Enum('male', 'female', 'other', name='gender'), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('users', sa.Column('birth_date', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('github_id', sa.String(), nullable=True, unique=True))
    op.add_column('users', sa.Column('google_id', sa.String(), nullable=True, unique=True))
    op.add_column('users', sa.Column('is_private', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
    
    # 重命名 password 列为 hashed_password（如果尚未重命名）
    # op.alter_column('users', 'password', new_column_name='hashed_password')


def downgrade():
    # 删除列
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'is_private')
    op.drop_column('users', 'google_id')
    op.drop_column('users', 'github_id')
    op.drop_column('users', 'birth_date')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'gender')
    op.drop_column('users', 'website')
    op.drop_column('users', 'location')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'avatar_url')
    
    # 删除枚举类型
    postgresql.ENUM(name='gender').drop(op.get_bind())
    
    # 重命名 hashed_password 列为 password（如果我们在 upgrade 中重命名了）
    # op.alter_column('users', 'hashed_password', new_column_name='password')