from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv(override=True)


from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv(override=True)


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "CRM Comercial Pro")
    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./crm_pro.db")
    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "crmpro_session")
    default_admin_email: str = (os.getenv("DEFAULT_ADMIN_EMAIL", "admin@crmpro.local") or "admin@crmpro.local").strip()
    default_admin_password: str = (os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123") or "Admin@123").strip()[:72]
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    company_name: str = os.getenv("COMPANY_NAME", "Empresa Exemplo Ltda")
    company_cnpj: str = os.getenv("COMPANY_CNPJ", "00.000.000/0001-00")
    company_email: str = os.getenv("COMPANY_EMAIL", "comercial@empresa.com")
    company_phone: str = os.getenv("COMPANY_PHONE", "(11) 99999-9999")
    company_site: str = os.getenv("COMPANY_SITE", "www.empresa.com")
    company_address: str = os.getenv("COMPANY_ADDRESS", "Rua Exemplo, 100 - São Paulo/SP")


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_settings() -> Settings:
    return Settings()
