# CRM Comercial Pro

Sistema comercial em Python com FastAPI, Jinja2 e SQLAlchemy.

## Funcionalidades

- autenticação com sessão
- dashboard comercial
- cadastro de clientes/leads
- cadastro de produtos/serviços
- oportunidades/pipeline
- propostas comerciais
- exportação em PDF e Word
- configurações da empresa
- auditoria básica

## Requisitos

- Python 3.11+
- VS Code

## Instalação

python -m venv .venv

### Windows
.venv\Scripts\activate

### Linux/Mac
source .venv/bin/activate

Instale as dependências:
pip install -r requirements.txt

Crie o arquivo `.env` com base no `.env.example`.

## Executando

python run.py

Acesse:
http://127.0.0.1:8000/login

## Credenciais padrão

Administrador:
- usuário: admin@crmpro.local
- senha: Admin@123

Gestor:
- usuário: gestor@crmpro.local
- senha: Gestor@123

Vendedor:
- usuário: vendedor1@crmpro.local
- senha: Vendedor@123

## Banco de dados

Por padrão usa SQLite:
DATABASE_URL=sqlite:///./crm_pro.db

Para PostgreSQL:
DATABASE_URL=postgresql+psycopg2://usuario:senha@localhost:5432/crm_pro

## Próximos passos recomendados

- adicionar Alembic para migrations
- CRUD completo de edição e exclusão
- anexos reais com upload
- RBAC granular por permissões
- API JSON complementar
- filtros avançados
- timeline de interações
- aceite interno da proposta
- assinatura eletrônica futura
- geração de proposta com template HTML + PDF avançado
