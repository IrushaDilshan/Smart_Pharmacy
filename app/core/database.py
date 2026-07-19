import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to SQLite for local development if DATABASE_URL is not provided (e.g. outside Docker)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_pharmacy.db")

# 2. Connection Engine එක සෑදීම
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# 3. Database එක සමඟ ගනුදෙනු කිරීමට සෙෂන් (Session) එකක් සෑදීම
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. අප සාදන සියලුම දත්ත වගු (Tables) උරුම කර ගන්නා මව් Base එක
Base = declarative_base()

# 5. API එකක් ක්‍රියාත්මක වන විට දත්ත සමුදායට සම්බන්ධ වී වැඩ ඉවර වූ පසු සම්බන්ධතාවය විසන්ධ කරන ශ්‍රිතය (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()