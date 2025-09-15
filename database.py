from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

URL_DATABASE = 'postgresql://postgres:123456@localhost:5432/membership_db'

engine = create_engine(URL_DATABASE)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

try:
    with engine.connect() as conn:
        print("✅ 成功連接 PostgreSQL 資料庫")
except Exception as e:
        print("❌ 資料庫連線失敗：", e)

