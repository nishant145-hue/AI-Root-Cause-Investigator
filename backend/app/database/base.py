from sqlmodel import SQLModel

# Register all models here
from app.models.user import User


def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)