from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.db import Base, engine, SessionLocal
from app.seed import seed_data

from app.routers import (
    auth,
    dashboard,
    customers,
    products,
    opportunities,
    proposals,
    settings,
    users,
    pricing,
    proposal_base,
)

settings_obj = get_settings()

app = FastAPI(title=settings_obj.app_name)
app.state.settings = settings_obj
app.state.templates = Jinja2Templates(directory="app/templates")

Path(settings_obj.upload_dir).mkdir(parents=True, exist_ok=True)

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    seed_data(db)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings_obj.upload_dir), name="uploads")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(opportunities.router)
app.include_router(proposals.router)
app.include_router(settings.router)
app.include_router(users.router)
app.include_router(pricing.router)
app.include_router(proposal_base.router)