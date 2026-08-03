from sqlmodel import Session, func, select

from app.models.investigation_history import InvestigationHistory


class InvestigationHistoryRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        history: InvestigationHistory,
    ) -> InvestigationHistory:

        self.session.add(history)
        self.session.commit()
        self.session.refresh(history)

        return history

    def get_by_investigation(
        self,
        investigation_id: int,
    ) -> list[InvestigationHistory]:

        statement = (
            select(InvestigationHistory)
            .where(
                InvestigationHistory.investigation_id == investigation_id
            )
            .order_by(
                InvestigationHistory.created_at.asc()
            )
        )

        return list(self.session.exec(statement).all())

    def count(
        self,
        investigation_id: int,
    ) -> int:

        statement = (
            select(func.count())
            .select_from(InvestigationHistory)
            .where(
                InvestigationHistory.investigation_id == investigation_id
            )
        )

        return self.session.exec(statement).one()