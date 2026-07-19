from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api.v1.endpoints import auth, medicines, orders, cart, ai

# Create database tables
Base.metadata.create_all(bind=engine)

# Core FastAPI Instance (MUST BE NAMED 'app')
app = FastAPI(title="Smart Pharmacy System")

# THIS MUST BE REGISTERED BEFORE ANY ROUTER
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(medicines.router, prefix="/api/v1/medicines", tags=["Medicines Management"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(cart.router, prefix="/api/v1/cart", tags=["Shopping Cart"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI Analytics"])

@app.get("/")
def home():
    return {
        "status": "success",
        "message": "Welcome to Smart Pharmacy API Engine."
    }
