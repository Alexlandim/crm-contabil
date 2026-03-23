from pydantic import BaseModel, Field
from datetime import date


class CustomerForm(BaseModel):
    kind: str = Field(default="lead")
    legal_name: str = Field(min_length=2, max_length=180)
    trade_name: str = ""
    document: str = ""
    email: str = ""
    phone: str = ""
    whatsapp: str = ""
    city: str = ""
    state: str = ""
    segment: str = ""
    contact_name: str = ""
    contact_role: str = ""
    lead_source: str = ""
    relationship_status: str = "ativo"
    notes: str = ""


class ProductForm(BaseModel):
    internal_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    category: str = ""
    commercial_description: str = ""
    technical_description: str = ""
    unit: str = "UN"
    base_price: float = 0
    estimated_cost: float = 0
    max_discount_percent: float = 0
    is_active: bool = True
    notes: str = ""


class OpportunityForm(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    customer_id: int
    stage_id: int
    owner_id: int
    estimated_value: float = 0
    close_probability: int = 10
    expected_close_date: date | None = None
    source: str = ""
    loss_reason: str = ""
    notes: str = ""
