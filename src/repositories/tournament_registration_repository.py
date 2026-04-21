"""Репозиторий регистраций на турниры."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TournamentRegistration


class TournamentRegistrationRepository:
    """Доступ к данным регистраций на турниры."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: int, tournament_id: int) -> TournamentRegistration:
        """Создает регистрацию пользователя на турнир."""
        registration = TournamentRegistration(user_id=user_id, tournament_id=tournament_id)
        self._session.add(registration)
        await self._session.commit()
        await self._session.refresh(registration)
        return registration

    async def get_by_user_and_tournament(self, user_id: int, tournament_id: int) -> TournamentRegistration | None:
        """Ищет регистрацию пользователя на конкретный турнир."""
        result = await self._session.execute(
            select(TournamentRegistration).where(
                TournamentRegistration.user_id == user_id,
                TournamentRegistration.tournament_id == tournament_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[TournamentRegistration]:
        """Возвращает все регистрации пользователя."""
        result = await self._session.execute(
            select(TournamentRegistration)
            .where(TournamentRegistration.user_id == user_id)
            .order_by(TournamentRegistration.created_at.desc())
        )
        return list(result.scalars().all())

