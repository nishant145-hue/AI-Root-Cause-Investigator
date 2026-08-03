from typing import Optional

from sqlmodel import Session, func, or_, select

from app.models.investigation import Investigation, InvestigationStatus


class InvestigationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, investigation: Investigation) -> Investigation:
        self.session.add(investigation)
        self.session.commit()
        self.session.refresh(investigation)
        return investigation

    def get_by_id(self, investigation_id: int) -> Optional[Investigation]:
        statement = select(Investigation).where(
            Investigation.id == investigation_id
        )
        return self.session.exec(statement).first()

    from sqlmodel import or_, select

    def get_all(
    self,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    status: InvestigationStatus | None = None,
    ):

        statement = (
            select(Investigation)
            .where(Investigation.user_id == user_id)
    )

        if search:
            statement = statement.where(
                or_(
                    Investigation.title.ilike(f"%{search}%"),
                    Investigation.description.ilike(f"%{search}%"),
                )
            )

        if status:
            statement = statement.where(
                Investigation.status == status
            )

        statement = (
            statement
            .order_by(Investigation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def update(self, investigation: Investigation) -> Investigation:
        self.session.add(investigation)
        self.session.commit()
        self.session.refresh(investigation)
        return investigation

    def delete(self, investigation: Investigation) -> None:
        self.session.delete(investigation)
        self.session.commit()
        
    def get_by_title(
        self,
        title: str,
        user_id: int,
    ):
        statement = select(Investigation).where(
            Investigation.title == title,
            Investigation.user_id == user_id,
        )

        return self.session.exec(statement).first()
    
    def count(
    self,
    user_id: int,
    search: str | None = None,
    status: InvestigationStatus | None = None,
):

        statement = (
            select(func.count())
            .select_from(Investigation)
            .where(
                Investigation.user_id == user_id
            )
        )
        if status:
            statement = statement.where(
                Investigation.status == status
        )
        if search:
            statement = statement.where(
                or_(
                    Investigation.title.ilike(f"%{search}%"),
                    Investigation.description.ilike(f"%{search}%"),
                )
            )

        return self.session.exec(statement).one()