# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import sys

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")

if DATABASE_URL is None:
    print("❌ Error: POSTGRES_URL not set in .env")
    sys.exit(1)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create session and base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 🔧 This line creates all tables defined with `Base` (e.g., SevaEntry)
Base.metadata.create_all(bind=engine)

# Dependency to inject DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
