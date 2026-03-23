from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    CompanySetting,
    Customer,
    Opportunity,
    PipelineStage,
    PricingSegment,
    PricingSetting,
    PricingTaxRegime,
    Product,
    Role,
    User,
)
from app.security import hash_password


def seed_data(db: Session) -> None:
    settings = get_settings()

    if not db.execute(select(Role)).first():
        for name in ["admin", "gestor", "vendedor"]:
            db.add(Role(name=name))
        db.commit()

    roles = {role.name: role for role in db.execute(select(Role)).scalars().all()}

    if not db.execute(select(User)).first():
        admin_password = (settings.default_admin_password or "Admin@123").strip()[:72]

        db.add(
            User(
                full_name="Administrador",
                email=(settings.default_admin_email or "admin@crmpro.local").strip(),
                password_hash=hash_password(admin_password),
                role_id=roles["admin"].id,
            )
        )

        db.add(
            User(
                full_name="Gestor Comercial",
                email="gestor@crmpro.local",
                password_hash=hash_password("Gestor@123"),
                role_id=roles["gestor"].id,
            )
        )

        db.add(
            User(
                full_name="Vendedor 1",
                email="vendedor1@crmpro.local",
                password_hash=hash_password("Vendedor@123"),
                role_id=roles["vendedor"].id,
            )
        )

        db.add(
            User(
                full_name="Vendedor 2",
                email="vendedor2@crmpro.local",
                password_hash=hash_password("Vendedor@123"),
                role_id=roles["vendedor"].id,
            )
        )

        db.commit()

    if not db.execute(select(CompanySetting)).first():
        db.add(
            CompanySetting(
                company_name=settings.company_name,
                company_cnpj=settings.company_cnpj,
                company_email=settings.company_email,
                company_phone=settings.company_phone,
                company_site=settings.company_site,
                company_address=settings.company_address,
                proposal_footer="Validade conforme proposta. Sujeito a aprovação comercial.",
                default_validity_days=15,
                proposal_number_prefix="PROP",
            )
        )
        db.commit()

    if not db.execute(select(PricingSetting)).first():
        db.add(
            PricingSetting(
                price_per_invoice=4,
                price_per_employee=25,
            )
        )
        db.commit()

    if not db.execute(select(PricingTaxRegime)).first():
        for name, amount in [
            ("MEI", 150),
            ("Simples Nacional", 300),
            ("Lucro Presumido", 800),
            ("Lucro Real", 1500),
            ("Outros", 500),
        ]:
            db.add(PricingTaxRegime(name=name, amount=amount))
        db.commit()

    if not db.execute(select(PricingSegment)).first():
        for name, amount in [
            ("Serviços", 200),
            ("Comércio", 250),
            ("Industria", 400),
            ("Misto", 500),
            ("Outros", 300),
        ]:
            db.add(PricingSegment(name=name, amount=amount))
        db.commit()

    if not db.execute(select(PipelineStage)).first():
        stages = [
            ("Novo lead", 1, "secondary"),
            ("Contato inicial", 2, "info"),
            ("Qualificação", 3, "primary"),
            ("Reunião agendada", 4, "warning"),
            ("Proposta enviada", 5, "dark"),
            ("Negociação", 6, "success"),
            ("Fechado ganho", 7, "success"),
            ("Fechado perdido", 8, "danger"),
        ]

        for name, position, color in stages:
            db.add(
                PipelineStage(
                    name=name,
                    position=position,
                    color=color,
                )
            )
        db.commit()

    if not db.execute(select(Customer)).first():
        db.add(
            Customer(
                kind="lead",
                legal_name="Alpha Comércio Ltda",
                email="contato@alpha.com",
                city="São Paulo",
                state="SP",
                segment="Varejo",
                contact_name="Mariana",
                lead_source="Indicação",
            )
        )

        db.add(
            Customer(
                kind="cliente",
                legal_name="Beta Serviços S/A",
                email="financeiro@beta.com",
                city="Barueri",
                state="SP",
                segment="Serviços",
                contact_name="Carlos",
                lead_source="Site",
            )
        )
        db.commit()

    if not db.execute(select(Product)).first():
        db.add(
            Product(
                internal_code="SRV001",
                name="Assessoria Contábil",
                category="Serviço",
                commercial_description="Assessoria mensal",
                unit="MÊS",
                base_price=2500,
                estimated_cost=900,
                max_discount_percent=15,
            )
        )

        db.add(
            Product(
                internal_code="SRV002",
                name="BPO Financeiro",
                category="Serviço",
                commercial_description="Operação financeira",
                unit="MÊS",
                base_price=4200,
                estimated_cost=1500,
                max_discount_percent=10,
            )
        )
        db.commit()

    if not db.execute(select(Opportunity)).first():
        customer = db.execute(
            select(Customer).where(Customer.legal_name == "Alpha Comércio Ltda")
        ).scalar_one()

        stage = db.execute(
            select(PipelineStage).where(PipelineStage.name == "Qualificação")
        ).scalar_one()

        owner = db.execute(
            select(User).where(User.email == "vendedor1@crmpro.local")
        ).scalar_one()

        db.add(
            Opportunity(
                title="Proposta mensal Alpha",
                customer_id=customer.id,
                stage_id=stage.id,
                owner_id=owner.id,
                estimated_value=2500,
                close_probability=40,
                source="Indicação",
            )
        )
        db.commit()