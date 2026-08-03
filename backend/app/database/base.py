from sqlmodel import SQLModel

# Register all models here
from app.models.user import User
from app.models.investigation import Investigation
from app.models.investigation_history import InvestigationHistory


def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)