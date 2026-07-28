# 컬럼 타입을 정의할 때 쓰는 도구들
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func

# 두 테이블 사이의 관계를 파이썬 객체로 편하게 다루게 해주는 도구
from sqlalchemy.orm import relationship

# database.py에서 만들어둔 기본 틀(Base)을 가져옴
from app.core.database import Base

# products 테이블을 파이썬 클래스로 표현한 것
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=True)
    category = Column(String(50), nullable=True)
    skin_type_target = Column(String(50), nullable=True)
    source_url = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # relationship: 실제 DB 컬럼이 아니라, 파이썬에서 "이 제품에 연결된 성분들"을
    # product.ingredients로 편하게 꺼내 쓸 수 있게 해주는 가상의 연결 통로
    # secondary: 중간 연결 테이블(product_ingredients)을 거쳐서 연결됨을 알려줌
    ingredients = relationship(
        "Ingredient",
        secondary="product_ingredients",
        back_populates="products"
    )

# ingredients 테이블을 파이썬 클래스로 표현한 것
class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingredient_name = Column(String(100), nullable=False)
    efficacy = Column(Text, nullable=True)      # 효능 설명 (긴 글이라 text 타입)
    caution = Column(Text, nullable=True)       # 주의사항 설명
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 반대 방향 연결: ingredient.products로 "이 성분이 들어간 제품들"을 꺼낼 수 있음
    products = relationship(
        "Product",
        secondary="product_ingredients",
        back_populates="ingredients"
    )

# product_ingredients 테이블 (products와 ingredients를 이어주는 연결 다리 테이블)
class ProductIngredient(Base):
    __tablename__ = "product_ingredients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)

