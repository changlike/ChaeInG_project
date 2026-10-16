# Alembic 실행 환경 설정
# DB 접속 정보는 앱과 같은 설정(app.core.database의 engine)을 그대로 사용함
from alembic import context

from app.core.database import Base, engine

# 모델을 import해야 Base.metadata에 테이블 정보가 채워짐 (autogenerate 비교에 필요)
from app.models import user, profile, product, favorite  # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline():
    # DB에 연결하지 않고 SQL 문장만 출력하는 모드
    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
