import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Database එක තියෙන තැන (URL එක) සඳහන් කිරීම.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/smart_pharmacy")

# 2. Connection Engine එක සෑදීම
engine = create_engine(DATABASE_URL)

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