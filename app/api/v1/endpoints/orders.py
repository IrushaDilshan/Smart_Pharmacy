from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import random

# Assuming you have a get_db dependency in your database module
from app.core.database import get_db

# Assuming your SQLAlchemy models are defined in app.models.models
# We'll import Medicine and Order. You might also have an OrderItem model
# depending on your exact database schema.
from app.models.models import Medicine, Order

router = APIRouter()

# --- Pydantic Schemas ---

class OrderItemCreate(BaseModel):
    medicine_id: int
    quantity: int

class OrderCreate(BaseModel):
    customer_id: int
    delivery_address: str
    items: List[OrderItemCreate]

class OrderStatusUpdate(BaseModel):
    status: str

class RiderAssign(BaseModel):
    rider_id: int

class DeliveryVerify(BaseModel):
    otp_code: str

# --- Endpoints ---

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    total_amount = 0.0
    
    # 1. Validate items and calculate total_amount
    for item in order_data.items:
        medicine = db.query(Medicine).filter(Medicine.id == item.medicine_id).first()
        
        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Medicine with ID {item.medicine_id} not found."
            )
            
        if medicine.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Not enough stock for medicine ID {item.medicine_id}. Available: {medicine.stock_quantity}"
            )
            
        total_amount += medicine.price * item.quantity

    # 2. Save the order
    new_order = Order(
        customer_id=order_data.customer_id,
        delivery_address=order_data.delivery_address,
        total_amount=total_amount,
        status="Pending"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    # 3. Deduct purchased quantity from stock_quantity
    # Note: Depending on your schema, you might also want to save each item into an OrderItem table here.
    for item in order_data.items:
        medicine = db.query(Medicine).filter(Medicine.id == item.medicine_id).first()
        medicine.stock_quantity -= item.quantity
        
        # Example of saving an order item if you have an OrderItem model:
        # order_item = OrderItem(order_id=new_order.id, medicine_id=item.medicine_id, quantity=item.quantity)
        # db.add(order_item)
        
    db.commit()
    
    return {
        "message": "Order created successfully",
        "order_id": new_order.id,
        "total_amount": total_amount,
        "status": new_order.status
    }

@router.get("/")
def get_orders(db: Session = Depends(get_db)):
    """Retrieve all orders from the database."""
    orders = db.query(Order).all()
    return orders

@router.patch("/{order_id}/status")
def update_order_status(order_id: int, status_update: OrderStatusUpdate, db: Session = Depends(get_db)):
    """Update the status of a specific order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Order not found."
        )
        
    order.status = status_update.status
    db.commit()
    db.refresh(order)
    
    return {
        "message": "Order status updated successfully", 
        "order_id": order.id, 
        "new_status": order.status
    }

@router.patch("/{order_id}/assign-rider")
def assign_rider(order_id: int, assignment: RiderAssign, db: Session = Depends(get_db)):
    """Assign a rider to an order and generate an OTP for delivery verification."""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Order not found."
        )
        
    order.rider_id = assignment.rider_id
    order.status = "Assigned"
    
    # Generate a random 4-digit numeric string for OTP
    order.otp_code = f"{random.randint(0, 9999):04d}"
    
    db.commit()
    db.refresh(order)
    
    return {
        "message": "Rider assigned successfully",
        "order_id": order.id,
        "rider_id": order.rider_id,
        "status": order.status,
        "otp_code": order.otp_code
    }

@router.post("/{order_id}/verify-delivery")
def verify_delivery(order_id: int, verification: DeliveryVerify, db: Session = Depends(get_db)):
    """Verify delivery using the OTP code."""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Order not found."
        )
        
    if order.status != "Assigned":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Order must be in 'Assigned' status to verify delivery."
        )
        
    if order.otp_code != verification.otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid OTP code."
        )
        
    order.status = "Delivered"
    
    db.commit()
    db.refresh(order)
    
    return {
        "message": "Delivery verified successfully",
        "order_id": order.id,
        "status": order.status
    }
