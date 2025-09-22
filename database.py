from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://neondb_owner:npg_sC7UIqw4ehpz@ep-long-smoke-a1i6sv9g-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
)



engine = create_engine(URL_DATABASE)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

try:
    with engine.connect() as conn:
        print("✅ 成功連接 PostgreSQL 資料庫")
except Exception as e:
        print("❌ 資料庫連線失敗：", e)

