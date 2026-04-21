"""ORM-модели предметной области киберспортивного клуба."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class User(Base):
    """Игрок системы."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")
    captained_teams: Mapped[list["Team"]] = relationship(back_populates="captain")


class Team(Base):
    """Команда игроков."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    captain_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    captain: Mapped[User] = relationship(back_populates="captained_teams")


class Arena(Base):
    """Игровое место/ПК."""

    __tablename__ = "arenas"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(unique=True, index=True)
    type: Mapped[str] = mapped_column(String(64))
    price_per_hour: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    bookings: Mapped[list["Booking"]] = relationship(back_populates="arena")


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
    start_date: Mapped[date] = mapped_column(Date)

    matches: Mapped[list["Match"]] = relationship(back_populates="tournament")


class Match(Base):
    """Матч турнира."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"), index=True)
    team1_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    team2_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    score: Mapped[str] = mapped_column(String(32))

    tournament: Mapped[Tournament] = relationship(back_populates="matches")

