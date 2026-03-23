from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import PricingSetting, PricingTaxRegime, PricingSegment


def get_pricing_snapshot(db: Session) -> dict:
    pricing_settings = db.execute(select(PricingSetting)).scalar_one_or_none()

    if not pricing_settings:
        return {
            "price_per_invoice": 0.0,
            "price_per_employee": 0.0,
            "tax_regimes": [],
            "segments": [],
        }

    tax_regimes = db.execute(
        select(PricingTaxRegime).order_by(PricingTaxRegime.name)
    ).scalars().all()

    segments = db.execute(
        select(PricingSegment).order_by(PricingSegment.name)
    ).scalars().all()

    return {
        "price_per_invoice": float(pricing_settings.price_per_invoice or 0),
        "price_per_employee": float(pricing_settings.price_per_employee or 0),
        "tax_regimes": tax_regimes,
        "segments": segments,
    }


def calculate_suggested_price(
    db: Session,
    tax_regime: str,
    business_segment: str,
    monthly_invoices_avg: int,
    employee_count: int,
) -> dict:
    pricing_settings = db.execute(select(PricingSetting)).scalar_one_or_none()

    price_per_invoice = float(pricing_settings.price_per_invoice or 0) if pricing_settings else 0.0
    price_per_employee = float(pricing_settings.price_per_employee or 0) if pricing_settings else 0.0

    tax_regime_row = db.execute(
        select(PricingTaxRegime).where(PricingTaxRegime.name == (tax_regime or ""))
    ).scalar_one_or_none()

    segment_row = db.execute(
        select(PricingSegment).where(PricingSegment.name == (business_segment or ""))
    ).scalar_one_or_none()

    regime_value = float(tax_regime_row.amount or 0) if tax_regime_row else 0.0
    segment_value = float(segment_row.amount or 0) if segment_row else 0.0
    invoices_value = max(monthly_invoices_avg or 0, 0) * price_per_invoice
    employees_value = max(employee_count or 0, 0) * price_per_employee

    suggested_price = regime_value + segment_value + invoices_value + employees_value

    return {
        "regime_value": regime_value,
        "segment_value": segment_value,
        "invoices_value": invoices_value,
        "employees_value": employees_value,
        "suggested_price": suggested_price,
        "price_per_invoice": price_per_invoice,
        "price_per_employee": price_per_employee,
    }