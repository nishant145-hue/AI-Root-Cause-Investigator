from sqlmodel import Session, select

from app.models.user import User


class UserRepository:

    @staticmethod
    def get_by_email(session: Session, email: str):
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()

    @staticmethod
    def get_by_username(session: Session, username: str):
        statement = select(User).where(User.username == username)
        return session.exec(statement).first()

    @staticmethod
    def create(session: Session, user: User):
        session.add(user)
        session.commit()
        session.refresh(user)
        return user