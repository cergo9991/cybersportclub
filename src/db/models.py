"""ORM-модели предметной области киберспортивного клуба."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class User(Base):
    """Игрок/пользователь системы."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("5000.00"))

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")
    captained_teams: Mapped[list["Team"]] = relationship(back_populates="captain")
    team_memberships: Mapped[list["TeamMember"]] = relationship(back_populates="user")
    tournament_registrations: Mapped[list["TournamentRegistration"]] = relationship(back_populates="user")
    tournament_applications: Mapped[list["TournamentApplication"]] = relationship(
        foreign_keys="TournamentApplication.user_id",
        back_populates="user",
    )
    processed_applications: Mapped[list["TournamentApplication"]] = relationship(
        foreign_keys="TournamentApplication.processed_by_admin_id",
        back_populates="processed_by_admin",
    )
    hall_assignments: Mapped[list["TournamentHallAssignment"]] = relationship(back_populates="assigned_by_admin")
    archive_events: Mapped[list["ArchiveEvent"]] = relationship(back_populates="actor_user")


class GameCategory(Base):
    """Категория киберспортивных дисциплин."""

    __tablename__ = "game_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tournaments: Mapped[list["Tournament"]] = relationship(back_populates="category")


class Team(Base):
    """Команда игроков."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    captain_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    captain: Mapped[User] = relationship(back_populates="captained_teams")
    members: Mapped[list["TeamMember"]] = relationship(back_populates="team")
    tournament_applications: Mapped[list["TournamentApplication"]] = relationship(back_populates="team")


class TeamMember(Base):
    """Связь игрока с командой."""

    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_member"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    team: Mapped[Team] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="team_memberships")


class Arena(Base):
    """Игровое место/ПК."""

    __tablename__ = "arenas"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(unique=True, index=True)
    type: Mapped[str] = mapped_column(String(64))
    hall_name: Mapped[str] = mapped_column(String(128), default="General Hall")
    price_per_hour: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    bookings: Mapped[list["Booking"]] = relationship(back_populates="arena")
    tournament_assignments: Mapped[list["TournamentHallAssignment"]] = relationship(back_populates="arena")
    application_assignments: Mapped[list["TournamentApplication"]] = relationship(back_populates="assigned_arena")


class Booking(Base):
    """Бронь игрового места."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    arena_id: Mapped[int] = mapped_column(ForeignKey("arenas.id"), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_paid: Mapped[bool] = mapped_column(default=False)

    user: Mapped[User] = relationship(back_populates="bookings")
    arena: Mapped[Arena] = relationship(back_populates="bookings")


class Tournament(Base):
    """Турнир по киберспортивной дисциплине."""

    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    game_type: Mapped[str] = mapped_column(String(64))
    category_id: Mapped[int] = mapped_column(ForeignKey("game_categories.id"), index=True)
    tournament_type: Mapped[str] = mapped_column(String(16), default="amateur")
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    entry_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    prize_pool: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    start_date: Mapped[date] = mapped_column(Date)
    start_datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    category: Mapped[GameCategory] = relationship(back_populates="tournaments")
    matches: Mapped[list["Match"]] = relationship(back_populates="tournament")
    registrations: Mapped[list["TournamentRegistration"]] = relationship(back_populates="tournament")
    applications: Mapped[list["TournamentApplication"]] = relationship(back_populates="tournament")
    hall_assignment: Mapped["TournamentHallAssignment | None"] = relationship(back_populates="tournament")
    archive_events: Mapped[list["ArchiveEvent"]] = relationship(back_populates="tournament")
    archive_results: Mapped[list["TournamentArchive"]] = relationship(back_populates="tournament")

    @property
    def category_name(self) -> str:
        """Возвращает название категории игры."""
        return self.category.name if self.category is not None else ""

    @property
    def has_prize(self) -> bool:
        """Признак наличия призового фонда."""
        return Decimal(str(self.prize_pool)) > Decimal("0.00")

    @property
    def is_closed(self) -> bool:
        """Признак закрытого турнира."""
        return self.status == "closed"


class Match(Base):
    """Матч турнира."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"), index=True)
    team1_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    team2_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    score: Mapped[str] = mapped_column(String(32))

    tournament: Mapped[Tournament] = relationship(back_populates="matches")


class TournamentRegistration(Base):
    """Регистрация пользователя на турнир (legacy)."""

    __tablename__ = "tournament_registrations"
    __table_args__ = (UniqueConstraint("user_id", "tournament_id", name="uq_tournament_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    user: Mapped[User] = relationship(back_populates="tournament_registrations")
    tournament: Mapped[Tournament] = relationship(back_populates="registrations")


class TournamentApplication(Base):
    """D4: заявка игрока на участие в турнире."""

    __tablename__ = "tournament_applications"
    __table_args__ = (UniqueConstraint("user_id", "tournament_id", name="uq_application_user_tournament"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    assigned_arena_id: Mapped[int | None] = mapped_column(ForeignKey("arenas.id"), nullable=True)
    processed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    admin_comment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entry_fee_charged: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(foreign_keys=[user_id], back_populates="tournament_applications")
    tournament: Mapped[Tournament] = relationship(back_populates="applications")
    team: Mapped[Team | None] = relationship(back_populates="tournament_applications")
    assigned_arena: Mapped[Arena | None] = relationship(back_populates="application_assignments")
    processed_by_admin: Mapped[User | None] = relationship(
        foreign_keys=[processed_by_admin_id],
        back_populates="processed_applications",
    )
    archive_events: Mapped[list["ArchiveEvent"]] = relationship(back_populates="application")

    @property
    def user_name(self) -> str:
        """Имя пользователя заявки."""
        return self.user.username if self.user is not None else ""

    @property
    def team_name(self) -> str | None:
        """Название команды заявки."""
        return self.team.name if self.team is not None else None


class TournamentHallAssignment(Base):
    """D3: распределение компьютерных залов по турнирам."""

    __tablename__ = "tournament_hall_assignments"
    __table_args__ = (UniqueConstraint("tournament_id", name="uq_tournament_single_hall"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"), index=True)
    arena_id: Mapped[int] = mapped_column(ForeignKey("arenas.id"), index=True)
    assigned_by_admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    tournament: Mapped[Tournament] = relationship(back_populates="hall_assignment")
    arena: Mapped[Arena] = relationship(back_populates="tournament_assignments")
    assigned_by_admin: Mapped[User] = relationship(back_populates="hall_assignments")


class ArchiveEvent(Base):
    """D5: архив событий и результатов."""

    __tablename__ = "archive_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    details: Mapped[str] = mapped_column(String(500))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    tournament_id: Mapped[int | None] = mapped_column(ForeignKey("tournaments.id"), nullable=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("tournament_applications.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)

    actor_user: Mapped[User | None] = relationship(back_populates="archive_events")
    tournament: Mapped[Tournament | None] = relationship(back_populates="archive_events")
    application: Mapped[TournamentApplication | None] = relationship(back_populates="archive_events")


class TournamentArchive(Base):
    """Архив турниров и их результатов."""

    __tablename__ = "tournament_archives"
    __table_args__ = (UniqueConstraint("tournament_id", name="uq_tournament_archive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"), index=True)
    result_summary: Mapped[str] = mapped_column(String(500))
    winner_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    archived_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)

    tournament: Mapped[Tournament] = relationship(back_populates="archive_results")
