"""
Order and Call data models.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel, Field

Base = declarative_base()


class OrderModel(Base):
    """SQLAlchemy model for orders."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_phone = Column(String, nullable=False)
    customer_name = Column(String)

    items = Column(JSON, default=list)
    total_amount = Column(Float, default=0.0)
    delivery_address = Column(String)
    special_instructions = Column(String)

    status = Column(String, default="confirmed")
    source = Column(String, default="voice")
    call_id = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime)
    delivered_at = Column(DateTime)

    business_id = Column(String, default="default")
    payment_status = Column(String, default="pending")
    whatsapp_message_sid = Column(String)
    whatsapp_sent_at = Column(DateTime)


class CallSessionModel(Base):
    """SQLAlchemy model for call sessions."""
    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String, unique=True, index=True)
    customer_phone = Column(String, nullable=False)
    customer_name = Column(String)

    duration_seconds = Column(Integer, default=0)
    transcript = Column(String)
    audio_url = Column(String)

    status = Column(String, default="initiated")
    error_message = Column(String)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    order = relationship("OrderModel", backref="calls")

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class OrderItem(BaseModel):
    name: str
    quantity: int = 1
    price: float = 0.0
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    customer_phone: str
    customer_name: Optional[str] = None
    items: List[Dict[str, Any]]
    total_amount: float
    delivery_address: Optional[str] = None
    special_instructions: Optional[str] = None
    status: str
    business_id: str
    whatsapp_sent: bool = False
    created_at: datetime
