from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.models.models import Medicine

router = APIRouter()

class MedicineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int

class MedicineResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int

    class Config:
        from_attributes = True

@router.get("", response_model=List[MedicineResponse])
@router.get("/", response_model=List[MedicineResponse], include_in_schema=False)
def get_medicines(db: Session = Depends(get_db)):
    medicines = db.query(Medicine).all()
    return medicines

@router.post("", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_medicine(medicine: MedicineCreate, db: Session = Depends(get_db)):
    new_medicine = Medicine(
        name=medicine.name,
        description=medicine.description,
        price=medicine.price,
        stock_quantity=medicine.stock_quantity
    )
    db.add(new_medicine)
    db.commit()
    db.refresh(new_medicine)
    return new_medicine

@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{medicine_id}/", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    db.delete(medicine)
    db.commit()
    return None

@router.put("/{medicine_id}/stock", response_model=MedicineResponse)
@router.put("/{medicine_id}/stock/", response_model=MedicineResponse, include_in_schema=False)
def update_stock(medicine_id: int, stock_quantity: int, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    medicine.stock_quantity = stock_quantity
    db.commit()
    db.refresh(medicine)
    return medicine

@router.put("/{medicine_id}", response_model=MedicineResponse)
@router.put("/{medicine_id}/", response_model=MedicineResponse, include_in_schema=False)
def update_medicine(medicine_id: int, medicine_update: MedicineCreate, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    medicine.name = medicine_update.name
    medicine.description = medicine_update.description
    medicine.price = medicine_update.price
    medicine.stock_quantity = medicine_update.stock_quantity
    
    db.commit()
    db.refresh(medicine)
    return medicine
