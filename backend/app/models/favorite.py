# 컬럼 타입을 정의할 때 쓰는 도구들
from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# database.py에서 만들어둔 기본 틀(BASE)을 가져옴
from app.core.database import Base

# Product 모델을 직접 쓰진 않지만, relationship 연결을 위해 import해둠
from app.models.product import Product

# favorites 테이블을 파이썬 클래스로 표현한 것
class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 누가 찜했는지 (users 테이블의 id를 참조)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 어떤 제품을 찜했는지 (products 테이블의 id를 참조)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())

    # 찜한 제품의 상세 정보를 favorite.product로 바로 꺼내 쓸 수 있게 해주는 연결 통로
    product = relationship("Product")
