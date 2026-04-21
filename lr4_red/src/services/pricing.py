"""Паттерн Strategy для расчета стоимости брони."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal


class PricingStrategy(ABC):
    """Базовая стратегия расчета стоимости."""

    @abstractmethod
    def calculate(self, arena_price_per_hour: Decimal, start_time: datetime, end_time: datetime) -> Decimal:
        """Возвращает стоимость брони."""


class HourlyStrategy(PricingStrategy):
    """Почасовой тариф."""

    def calculate(self, arena_price_per_hour: Decimal, start_time: datetime, end_time: datetime) -> Decimal:
        if end_time <= start_time:
            raise ValueError("Время окончания должно быть больше времени начала.")
        hours = Decimal(str((end_time - start_time).total_seconds())) / Decimal("3600")
        return (hours * arena_price_per_hour).quantize(Decimal("0.01"))


class NightStrategy(PricingStrategy):
    """Фиксированная стоимость ночной сессии."""

    def __init__(self, fixed_price: Decimal = Decimal("1500.00")) -> None:
        self._fixed_price = fixed_price

    def calculate(self, arena_price_per_hour: Decimal, start_time: datetime, end_time: datetime) -> Decimal:
        if end_time <= start_time:
            raise ValueError("Время окончания должно быть больше времени начала.")
        return self._fixed_price.quantize(Decimal("0.01"))


class TournamentStrategy(PricingStrategy):
    """Бесплатная бронь для участников турнира."""

    def calculate(self, arena_price_per_hour: Decimal, start_time: datetime, end_time: datetime) -> Decimal:
        if end_time <= start_time:
            raise ValueError("Время окончания должно быть больше времени начала.")
        return Decimal("0.00")


class PricingContext:
    """Выбор активной стратегии расчета."""

    def get_strategy(self, start_time: datetime, end_time: datetime, is_tournament_participant: bool) -> PricingStrategy:
        """Возвращает стратегию расчета стоимости."""
        if is_tournament_participant:
            return TournamentStrategy()
        is_night = start_time.hour >= 22 or end_time.hour <= 8
        if is_night:
            return NightStrategy()
        return HourlyStrategy()
