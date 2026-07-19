from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    stock_quantity = Column(Integer)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"))
    delivery_address = Column(String)
    total_amount = Column(Float)
    status = Column(String, default="Pending")
    rider_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    otp_code = Column(String, nullable=True)
