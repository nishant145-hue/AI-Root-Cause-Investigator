from sqlmodel import Session, select

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:

    @staticmethod
    def create(
        session: Session,
        refresh_token: RefreshToken,
    ):
        session.add(refresh_token)
        session.commit()
        session.refresh(refresh_token)
        return refresh_token

    @staticmethod
    def get_by_hash(
        session: Session,
        token_hash: str,
    ):
        statement = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )

        return session.exec(statement).first()

    @staticmethod
    def revoke(
        session: Session,
        refresh_token: RefreshToken,
    ):
        refresh_token.revoked = True

        session.add(refresh_token)
        session.commit()
        session.refresh(refresh_token)

        return refresh_token