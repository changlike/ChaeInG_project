"""baseline: 기존 6개 테이블 (직접 SQL로 만들었던 스키마를 그대로 옮김)

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )
    op.create_table(
        "skin_profiles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("skin_type", sa.String(20), nullable=False),
        sa.Column("is_sensitive", sa.Boolean),
        sa.Column("concerns", sa.String(255)),
        sa.Column("preferred_ingredients", sa.String(255)),
        sa.Column("avoided_ingredients", sa.String(255)),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("brand", sa.String(100)),
        sa.Column("category", sa.String(50)),
        sa.Column("skin_type_target", sa.String(50)),
        sa.Column("source_url", sa.String(500)),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )
    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ingredient_name", sa.String(100), nullable=False),
        sa.Column("efficacy", sa.Text),
        sa.Column("caution", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )
    op.create_table(
        "product_ingredients",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id"), nullable=False),
        sa.Column("ingredient_id", sa.Integer, sa.ForeignKey("ingredients.id"), nullable=False),
    )
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )


def downgrade():
    for table in ["favorites", "product_ingredients", "ingredients", "products", "skin_profiles", "users"]:
        op.drop_table(table)
