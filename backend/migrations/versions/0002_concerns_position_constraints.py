"""제품 주력 고민/검수 여부, 성분 순번, UNIQUE 제약 추가

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    # products: 주력 고민 태그 + 검수 여부 + 제품 식별용 URL 유일 제약
    op.add_column("products", sa.Column("main_concerns", sa.String(255), nullable=True))
    op.add_column(
        "products",
        sa.Column("is_concerns_verified", sa.Boolean, nullable=False, server_default="0"),
    )
    op.create_unique_constraint("uq_products_source_url", "products", ["source_url"])

    # ingredients: 성분명 유일
    op.create_unique_constraint("uq_ingredients_name", "ingredients", ["ingredient_name"])

    # product_ingredients: 성분표 순번 + 같은 제품-성분 중복 금지
    op.add_column("product_ingredients", sa.Column("position", sa.Integer, nullable=True))
    op.add_column("product_ingredients", sa.Column("amount_note", sa.String(50), nullable=True))
    op.create_unique_constraint(
        "uq_product_ingredient", "product_ingredients", ["product_id", "ingredient_id"]
    )

    # favorites / skin_profiles: DB 차원의 중복 방지
    op.create_unique_constraint("uq_favorite_user_product", "favorites", ["user_id", "product_id"])
    op.create_unique_constraint("uq_skin_profiles_user", "skin_profiles", ["user_id"])


def downgrade():
    # MySQL은 외래키가 쓰는 인덱스를 지울 수 없어서, 일반 인덱스를 먼저 만들고 UNIQUE를 지움
    op.create_index("ix_skin_profiles_user_id", "skin_profiles", ["user_id"])
    op.drop_constraint("uq_skin_profiles_user", "skin_profiles", type_="unique")

    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    op.drop_constraint("uq_favorite_user_product", "favorites", type_="unique")

    op.create_index("ix_product_ingredients_product_id", "product_ingredients", ["product_id"])
    op.drop_constraint("uq_product_ingredient", "product_ingredients", type_="unique")
    op.drop_column("product_ingredients", "amount_note")
    op.drop_column("product_ingredients", "position")

    op.drop_constraint("uq_ingredients_name", "ingredients", type_="unique")

    op.drop_constraint("uq_products_source_url", "products", type_="unique")
    op.drop_column("products", "is_concerns_verified")
    op.drop_column("products", "main_concerns")
