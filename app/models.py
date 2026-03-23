from datetime import datetime, date

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Date,
    Boolean,
    ForeignKey,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)

    role = relationship("Role", back_populates="users")
    interactions = relationship("Interaction", back_populates="user")
    opportunities = relationship("Opportunity", back_populates="owner")
    proposals = relationship("Proposal", back_populates="owner")


class CompanySetting(Base, TimestampMixin):
    __tablename__ = "company_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    company_cnpj: Mapped[str] = mapped_column(String(20), default="")
    company_email: Mapped[str] = mapped_column(String(120), default="")
    company_phone: Mapped[str] = mapped_column(String(30), default="")
    company_site: Mapped[str] = mapped_column(String(150), default="")
    company_address: Mapped[str] = mapped_column(String(255), default="")
    proposal_footer: Mapped[str] = mapped_column(Text, default="Obrigado pela oportunidade.")
    default_validity_days: Mapped[int] = mapped_column(Integer, default=15)
    proposal_number_prefix: Mapped[str] = mapped_column(String(20), default="PROP")
    logo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)


class PricingSetting(Base, TimestampMixin):
    __tablename__ = "pricing_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    price_per_invoice: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    price_per_employee: Mapped[float] = mapped_column(Numeric(14, 2), default=0)


class PricingTaxRegime(Base, TimestampMixin):
    __tablename__ = "pricing_tax_regimes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)


class PricingSegment(Base, TimestampMixin):
    __tablename__ = "pricing_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), default="lead")
    legal_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    trade_name: Mapped[str] = mapped_column(String(180), default="")
    document: Mapped[str] = mapped_column(String(20), default="", index=True)
    email: Mapped[str] = mapped_column(String(150), default="")
    phone: Mapped[str] = mapped_column(String(30), default="")
    whatsapp: Mapped[str] = mapped_column(String(30), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    state: Mapped[str] = mapped_column(String(2), default="")
    segment: Mapped[str] = mapped_column(String(100), default="")
    contact_name: Mapped[str] = mapped_column(String(120), default="")
    contact_role: Mapped[str] = mapped_column(String(120), default="")
    lead_source: Mapped[str] = mapped_column(String(100), default="")
    relationship_status: Mapped[str] = mapped_column(String(50), default="ativo")
    notes: Mapped[str] = mapped_column(Text, default="")
    last_interaction_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    opportunities = relationship("Opportunity", back_populates="customer")
    proposals = relationship("Proposal", back_populates="customer")
    interactions = relationship("Interaction", back_populates="customer")


class PipelineStage(Base, TimestampMixin):
    __tablename__ = "pipeline_stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="secondary")

    opportunities = relationship("Opportunity", back_populates="stage")


class Opportunity(Base, TimestampMixin):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    stage_id: Mapped[int] = mapped_column(ForeignKey("pipeline_stages.id"), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    estimated_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    close_probability: Mapped[int] = mapped_column(Integer, default=10)
    expected_close_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="")
    loss_reason: Mapped[str] = mapped_column(String(255), default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    customer = relationship("Customer", back_populates="opportunities")
    stage = relationship("PipelineStage", back_populates="opportunities")
    owner = relationship("User", back_populates="opportunities")
    interactions = relationship("Interaction", back_populates="opportunity")


class Interaction(Base, TimestampMixin):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    next_step: Mapped[str] = mapped_column(String(255), default="")
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id"), nullable=True)

    user = relationship("User", back_populates="interactions")
    customer = relationship("Customer", back_populates="interactions")
    opportunity = relationship("Opportunity", back_populates="interactions")


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    internal_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="")
    commercial_description: Mapped[str] = mapped_column(Text, default="")
    technical_description: Mapped[str] = mapped_column(Text, default="")
    unit: Mapped[str] = mapped_column(String(20), default="UN")
    base_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    estimated_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    max_discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class Proposal(Base, TimestampMixin):
    __tablename__ = "proposals"
    __table_args__ = (UniqueConstraint("proposal_number", name="uq_proposal_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    issue_date: Mapped[date] = mapped_column(Date, default=date.today)
    validity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="rascunho")
    version: Mapped[int] = mapped_column(Integer, default=1)

    payment_terms: Mapped[str] = mapped_column(Text, default="")
    delivery_terms: Mapped[str] = mapped_column(Text, default="")
    scope_text: Mapped[str] = mapped_column(Text, default="")
    assumptions_text: Mapped[str] = mapped_column(Text, default="")
    exclusions_text: Mapped[str] = mapped_column(Text, default="")
    clauses_text: Mapped[str] = mapped_column(Text, default="")

    cnpj: Mapped[str] = mapped_column(String(20), default="")
    faturamento: Mapped[str] = mapped_column(String(100), default="")
    tax_regime: Mapped[str] = mapped_column(String(50), default="")
    business_segment: Mapped[str] = mapped_column(String(50), default="")
    employee_count: Mapped[int] = mapped_column(Integer, default=0)
    monthly_revenue_avg: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    monthly_invoices_avg: Mapped[int] = mapped_column(Integer, default=0)

    notes: Mapped[str] = mapped_column(Text, default="")
    global_discount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    subtotal_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)

    customer = relationship("Customer", back_populates="proposals")
    owner = relationship("User", back_populates="proposals")
    items = relationship("ProposalItem", back_populates="proposal", cascade="all, delete-orphan")
    document_base = relationship(
        "ProposalDocumentBase",
        back_populates="proposal",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ProposalItem(Base, TimestampMixin):
    __tablename__ = "proposal_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_id: Mapped[int] = mapped_column(ForeignKey("proposals.id"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 2), default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    line_total: Mapped[float] = mapped_column(Numeric(14, 2), default=0)

    proposal = relationship("Proposal", back_populates="items")


class ProposalBaseTemplate(Base, TimestampMixin):
    __tablename__ = "proposal_base_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)

    presentation: Mapped[str] = mapped_column(Text, default="")
    methodology: Mapped[str] = mapped_column(Text, default="")
    services_description: Mapped[str] = mapped_column(Text, default="")
    extra_services: Mapped[str] = mapped_column(Text, default="")
    closing: Mapped[str] = mapped_column(Text, default="")
    general_conditions: Mapped[str] = mapped_column(Text, default="")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProposalDocumentBase(Base, TimestampMixin):
    __tablename__ = "proposal_document_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_id: Mapped[int] = mapped_column(ForeignKey("proposals.id"), unique=True, nullable=False)

    template_name: Mapped[str] = mapped_column(String(150), default="Base padrão")
    presentation: Mapped[str] = mapped_column(Text, default="")
    methodology: Mapped[str] = mapped_column(Text, default="")
    services_description: Mapped[str] = mapped_column(Text, default="")
    extra_services: Mapped[str] = mapped_column(Text, default="")
    closing: Mapped[str] = mapped_column(Text, default="")
    general_conditions: Mapped[str] = mapped_column(Text, default="")

    proposal = relationship("Proposal", back_populates="document_base")


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_email: Mapped[str] = mapped_column(String(150), default="system")
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(50), default="")
    description: Mapped[str] = mapped_column(Text, default="")