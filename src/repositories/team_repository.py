"""Репозиторий команд."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import Team, TeamMember, User


class TeamRepository:
    """Доступ к данным команд и составов."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, captain_id: int) -> Team:
        """Создает команду."""
        team = Team(name=name, captain_id=captain_id)
        self._session.add(team)
        await self._session.flush()
        await self.ensure_member(team_id=team.id, user_id=captain_id)
        await self._session.commit()
        await self._session.refresh(team)
        return team

    async def get_by_id(self, team_id: int) -> Team | None:
        """Возвращает команду по id."""
        result = await self._session.execute(
            select(Team).options(selectinload(Team.members)).where(Team.id == team_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Team | None:
        """Возвращает команду по названию."""
        result = await self._session.execute(
            select(Team).options(selectinload(Team.members)).where(Team.name == name)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, name: str, captain_id: int) -> Team:
        """Возвращает существующую команду или создает новую."""
        existing = await self.get_by_name(name)
        if existing is not None:
            return existing
        return await self.create(name=name, captain_id=captain_id)

    async def ensure_member(self, team_id: int, user_id: int) -> TeamMember:
        """Гарантирует, что игрок состоит в команде."""
        result = await self._session.execute(
            select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if member is not None:
            return member
        member = TeamMember(team_id=team_id, user_id=user_id)
        self._session.add(member)
        await self._session.flush()
        return member

    async def list_member_users(self, team_id: int) -> list[User]:
        """Возвращает участников команды."""
        result = await self._session.execute(
            select(User)
            .join(TeamMember, TeamMember.user_id == User.id)
            .where(TeamMember.team_id == team_id)
            .order_by(User.username.asc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[tuple[Team, int]]:
        """Возвращает команды и количество участников."""
        result = await self._session.execute(
            select(Team, func.count(TeamMember.id))
            .outerjoin(TeamMember, TeamMember.team_id == Team.id)
            .group_by(Team.id)
            .order_by(Team.name.asc())
        )
        return [(team, int(member_count)) for team, member_count in result.all()]
