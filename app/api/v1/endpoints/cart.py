from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict

from app.core.database import get_db
from app.models.models import Medicine, Order

router = APIRouter()

# --- Schemas ---
class CartItemAdd(BaseModel):
    customer_id: int
    medicine_id: int
    quantity: int

class CheckoutRequest(BaseModel):
    delivery_address: str

# --- In-memory Cart ---
# Structure: { customer_id: [{"medicine_id": 1, "quantity": 2}, ...] }
class CartItem(BaseModel):
    medicine_id: int
    quantity: int

carts: Dict[int, List[CartItem]] = {}

# --- Endpoints ---

@router.post("/add", status_code=status.HTTP_200_OK)
def add_to_cart(item: CartItemAdd, db: Session = Depends(get_db)):
    """Add a medicine to the user's shopping cart."""
    medicine = db.query(Medicine).filter(Medicine.id == item.medicine_id).first()
    
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Medicine not found."
        )
        
    if medicine.stock_quantity < item.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Not enough stock. Available: {medicine.stock_quantity}"
        )
        
    # Initialize cart for customer if it doesn't exist
    if item.customer_id not in carts:
        carts[item.customer_id] = []
        
    # Check if medicine already exists in cart, then update quantity
    for cart_item in carts[item.customer_id]:
        if cart_item.medicine_id == item.medicine_id:
            # Validate total stock again just in case
            if medicine.stock_quantity < (cart_item.quantity + item.quantity):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Cannot add more of this item. Exceeds available stock."
                )
            cart_item.quantity += item.quantity
            return {"message": "Item quantity updated in cart.", "cart_item": cart_item}
            
    # Add new item
    new_cart_item = CartItem(medicine_id=item.medicine_id, quantity=item.quantity)
    carts[item.customer_id].append(new_cart_item)
    
    return {"message": "Item added to cart successfully.", "cart_item": new_cart_item}

@router.get("/{customer_id}", status_code=status.HTTP_200_OK)
def get_cart(customer_id: int, db: Session = Depends(get_db)):
    """Retrieve the user's cart and compute the total amount dynamically."""
    if customer_id not in carts or not carts[customer_id]:
        return {"customer_id": customer_id, "items": [], "total_amount": 0.0}
        
    cart_items = carts[customer_id]
    total_amount = 0.0
    detailed_items = []
    
    for cart_item in cart_items:
        medicine = db.query(Medicine).filter(Medicine.id == cart_item.medicine_id).first()
        if medicine:
            item_total = medicine.price * cart_item.quantity
            total_amount += item_total
            detailed_items.append({
                "medicine_id": medicine.id,
                "name": medicine.name,
                "price": medicine.price,
                "quantity": cart_item.quantity,
                "item_total": item_total
            })
            
    return {
        "customer_id": customer_id,
        "items": detailed_items,
        "total_amount": total_amount
    }

@router.post("/{customer_id}/checkout", status_code=status.HTTP_201_CREATED)
def checkout_cart(customer_id: int, checkout_req: CheckoutRequest, db: Session = Depends(get_db)):
    """Convert cart into an Order, deduct stock, and empty cart."""
    if customer_id not in carts or not carts[customer_id]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty."
        )
        
    cart_items = carts[customer_id]
    total_amount = 0.0
    
    # Pre-check stock for all items
    for cart_item in cart_items:
        medicine = db.query(Medicine).filter(Medicine.id == cart_item.medicine_id).first()
        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Medicine ID {cart_item.medicine_id} not found."
            )
        if medicine.stock_quantity < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Not enough stock for medicine '{medicine.name}'. Available: {medicine.stock_quantity}"
            )
        total_amount += medicine.price * cart_item.quantity
        
    # Create the order
    new_order = Order(
        customer_id=customer_id,
        delivery_address=checkout_req.delivery_address,
        total_amount=total_amount,
        status="Pending"
    )
    db.add(new_order)
    
    # Deduct stock
    for cart_item in cart_items:
        medicine = db.query(Medicine).filter(Medicine.id == cart_item.medicine_id).first()
        medicine.stock_quantity -= cart_item.quantity
        
    db.commit()
    db.refresh(new_order)
    
    # Empty the cart
    carts[customer_id] = []
    
    return {
        "message": "Checkout successful. Order created.",
        "order_id": new_order.id,
        "total_amount": new_order.total_amount,
        "status": new_order.status
    }
