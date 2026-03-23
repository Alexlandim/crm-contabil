from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models import Proposal, ProposalItem, CompanySetting


def generate_proposal_number(db: Session) -> str:
    settings = db.execute(select(CompanySetting)).scalar_one()
    count = db.scalar(select(func.count(Proposal.id))) or 0
    return f"{settings.proposal_number_prefix}-{count + 1:05d}"


def recalculate_proposal(proposal: Proposal) -> None:
    subtotal = Decimal("0")

    for item in proposal.items:
        qty = Decimal(str(item.quantity or 0))
        unit_price = Decimal(str(item.unit_price or 0))
        discount_amount = Decimal(str(item.discount_amount or 0))

        line_total = (qty * unit_price) - discount_amount
        if line_total < 0:
            line_total = Decimal("0")

        item.line_total = float(line_total)
        subtotal += line_total

    proposal.subtotal_amount = float(subtotal)

    total = subtotal - Decimal(str(proposal.global_discount or 0))
    if total < 0:
        total = Decimal("0")

    proposal.total_amount = float(total)


def duplicate_proposal(db: Session, original: Proposal) -> Proposal:
    new_proposal = Proposal(
        proposal_number=generate_proposal_number(db),
        customer_id=original.customer_id,
        owner_id=original.owner_id,
        issue_date=original.issue_date,
        validity_date=original.validity_date,
        status="rascunho",
        version=1,
        cnpj=original.cnpj,
        faturamento=original.faturamento,
        tax_regime=original.tax_regime,
        business_segment=original.business_segment,
        employee_count=original.employee_count,
        monthly_revenue_avg=original.monthly_revenue_avg,
        monthly_invoices_avg=original.monthly_invoices_avg,
        notes=original.notes,
        global_discount=original.global_discount,
        payment_terms=original.payment_terms,
        delivery_terms=original.delivery_terms,
        scope_text=original.scope_text,
        assumptions_text=original.assumptions_text,
        exclusions_text=original.exclusions_text,
        clauses_text=original.clauses_text,
    )

    db.add(new_proposal)
    db.flush()

    for item in original.items:
        db.add(
            ProposalItem(
                proposal_id=new_proposal.id,
                product_id=item.product_id,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_amount=item.discount_amount,
                line_total=item.line_total,
            )
        )

    db.flush()
    db.refresh(new_proposal)
    recalculate_proposal(new_proposal)
    db.commit()
    db.refresh(new_proposal)

    return new_proposal