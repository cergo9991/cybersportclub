"""Сервис турниров и заявок по схеме D1-D5."""

from decimal import Decimal, ROUND_HALF_UP

from src.repositories.archive_event_repository import ArchiveEventRepository
from src.repositories.arena_repository import ArenaRepository
from src.repositories.game_category_repository import GameCategoryRepository
from src.repositories.team_repository import TeamRepository
from src.repositories.tournament_application_repository import TournamentApplicationRepository
from src.repositories.tournament_archive_repository import TournamentArchiveRepository
from src.repositories.tournament_hall_assignment_repository import TournamentHallAssignmentRepository
from src.repositories.tournament_repository import TournamentRepository
from src.repositories.user_repository import UserRepository
from src.schemas.archive_event import ArchiveEventRead
from src.schemas.game_category import GameCategoryRead
from src.schemas.team import TeamRead
from src.schemas.tournament import TournamentCloseResponse, TournamentCreate, TournamentRead
from src.schemas.tournament_application import TournamentApplicationRead
from src.schemas.tournament_archive import TournamentArchiveRead
from src.schemas.tournament_hall_assignment import TournamentHallAssignmentRead


class TournamentService:
    """Бизнес-логика процессов 2-5 для киберспортивного клуба."""

    def __init__(
        self,
        tournament_repository: TournamentRepository,
        tournament_application_repository: TournamentApplicationRepository | None = None,
        tournament_hall_assignment_repository: TournamentHallAssignmentRepository | None = None,
        game_category_repository: GameCategoryRepository | None = None,
        user_repository: UserRepository | None = None,
        arena_repository: ArenaRepository | None = None,
        archive_event_repository: ArchiveEventRepository | None = None,
        tournament_archive_repository: TournamentArchiveRepository | None = None,
        team_repository: TeamRepository | None = None,
    ) -> None:
        self._tournament_repository = tournament_repository
        self._tournament_application_repository = tournament_application_repository
        self._tournament_hall_assignment_repository = tournament_hall_assignment_repository
        self._game_category_repository = game_category_repository
        self._user_repository = user_repository
        self._arena_repository = arena_repository
        self._archive_event_repository = archive_event_repository
        self._tournament_archive_repository = tournament_archive_repository
        self._team_repository = team_repository

    async def create_tournament(self, payload: TournamentCreate, admin_user_id: int | None = None) -> TournamentRead:
        """Процесс 2: создание турниров."""
        start_date = payload.start_date
        if start_date is None and payload.start_datetime is not None:
            start_date = payload.start_datetime.date()
        if start_date is None:
            raise ValueError("Необходимо указать дату старта турнира.")

        tournament = await self._tournament_repository.create(
            name=payload.name,
            game_type=payload.game_type,
            category_name=payload.category_name,
            tournament_type=payload.tournament_type,
            entry_fee=payload.entry_fee,
            prize_pool=payload.prize_pool,
            start_date=start_date,
            start_datetime=payload.start_datetime,
        )
        if self._archive_event_repository is not None:
            start_text = payload.start_datetime.isoformat() if payload.start_datetime else str(start_date)
            await self._archive_event_repository.create(
                event_type="TOURNAMENT_CREATED",
                details=(
                    f"Турнир '{payload.name}' создан. "
                    f"Старт: {start_text}. Взнос: {payload.entry_fee}. Призовой фонд: {payload.prize_pool}."
                ),
                actor_user_id=admin_user_id,
                tournament_id=tournament.id,
            )
        return TournamentRead.model_validate(tournament)

    async def delete_tournament(self, tournament_id: int, admin_user_id: int | None = None) -> None:
        """Удаляет турнир вместе со связанными данными."""
        tournament = await self._tournament_repository.get_by_id(tournament_id)
        if tournament is None:
            raise LookupError("Турнир не найден.")

        deleted = await self._tournament_repository.delete_with_relations(tournament_id=tournament_id)
        if not deleted:
            raise LookupError("Турнир не найден.")

        if self._archive_event_repository is not None:
            await self._archive_event_repository.create(
                event_type="TOURNAMENT_DELETED",
                details=f"Турнир '{tournament.name}' удален администратором.",
                actor_user_id=admin_user_id,
                tournament_id=None,
            )

    async def close_tournament(
        self,
        tournament_id: int,
        winner_user_ids: list[int],
        result_text: str,
        admin_user_id: int,
    ) -> TournamentCloseResponse:
        """Закрывает турнир и распределяет победный фонд между победителями."""
        if self._tournament_application_repository is None or self._user_repository is None:
            raise RuntimeError("Сервис заявок/пользователей не настроен.")

        tournament = await self._tournament_repository.get_by_id(tournament_id)
        if tournament is None:
            raise LookupError("Турнир не найден.")
        if tournament.status == "closed":
            raise ValueError("Турнир уже закрыт.")

        applications = await self._tournament_application_repository.list_by_tournament(tournament_id)
        participants = [item for item in applications if item.status != "rejected"]
        participant_user_ids = {item.user_id for item in participants}
        participant_count = len(participant_user_ids)
        if participant_count == 0:
            raise ValueError("Нельзя закрыть турнир без зарегистрированных участников.")

        unique_winners: list[int] = []
        for winner_id in winner_user_ids:
            if winner_id not in unique_winners:
                unique_winners.append(winner_id)
        if not unique_winners:
            raise ValueError("Необходимо указать хотя бы одного победителя.")

        for winner_id in unique_winners:
            if winner_id not in participant_user_ids:
                raise ValueError(f"Игрок {winner_id} не зарегистрирован на турнир.")

        entry_total = Decimal(str(tournament.entry_fee or Decimal("0.00"))) * Decimal(participant_count)
        payout_total = (Decimal(str(tournament.prize_pool or Decimal("0.00"))) + entry_total).quantize(Decimal("0.01"))
        payout_per_winner = (payout_total / Decimal(len(unique_winners))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        winner_names: list[str] = []
        for winner_id in unique_winners:
            winner = await self._user_repository.get_by_id(winner_id)
            if winner is None:
                raise LookupError(f"Победитель {winner_id} не найден.")
            await self._user_repository.add_balance(user=winner, amount=payout_per_winner)
            winner_names.append(winner.username)

        await self._tournament_repository.close(tournament)

        if self._archive_event_repository is not None:
            await self._archive_event_repository.create(
                event_type="TOURNAMENT_CLOSED",
                details=(
                    f"Турнир '{tournament.name}' закрыт. Участников: {participant_count}. "
                    f"Победители: {', '.join(winner_names)}. Выплата каждому: {payout_per_winner}. "
                    f"Комментарий: {result_text}"
                ),
                actor_user_id=admin_user_id,
                tournament_id=tournament_id,
            )

        if self._tournament_archive_repository is not None:
            await self._tournament_archive_repository.upsert(
                tournament_id=tournament_id,
                result_summary=result_text,
                winner_name=", ".join(winner_names),
            )

        return TournamentCloseResponse(
            tournament_id=tournament_id,
            status="closed",
            participant_count=participant_count,
            winner_user_ids=unique_winners,
            payout_total=payout_total,
            payout_per_winner=payout_per_winner,
        )

    async def list_tournaments(self) -> list[TournamentRead]:
        """Возвращает список турниров."""
        tournaments = await self._tournament_repository.list_all()
        return [TournamentRead.model_validate(tournament) for tournament in tournaments]

    async def list_categories(self) -> list[GameCategoryRead]:
        """Возвращает категории дисциплин."""
        if self._game_category_repository is None:
            raise RuntimeError("Сервис категорий не настроен.")
        categories = await self._game_category_repository.list_all()
        return [GameCategoryRead.model_validate(category) for category in categories]

    async def list_teams(self) -> list[TeamRead]:
        """Возвращает список команд."""
        if self._team_repository is None:
            return []
        teams_with_counts = await self._team_repository.list_all()
        result: list[TeamRead] = []
        for team, member_count in teams_with_counts:
            team_read = TeamRead.model_validate(team)
            team_read.member_count = member_count
            result.append(team_read)
        return result

    async def assign_hall(self, tournament_id: int, arena_id: int, admin_user_id: int) -> TournamentHallAssignmentRead:
        """Процесс 3: распределение компьютерных залов."""
        if self._tournament_hall_assignment_repository is None or self._arena_repository is None:
            raise RuntimeError("Сервис распределения залов не настроен.")
        tournament = await self._tournament_repository.get_by_id(tournament_id)
        if tournament is None:
            raise LookupError("Турнир не найден.")
        arena = await self._arena_repository.get_by_id(arena_id)
        if arena is None:
            raise LookupError("Компьютерный зал не найден.")

        assignment = await self._tournament_hall_assignment_repository.upsert(
            tournament_id=tournament_id,
            arena_id=arena_id,
            admin_id=admin_user_id,
        )
        if self._archive_event_repository is not None:
            await self._archive_event_repository.create(
                event_type="HALL_ASSIGNED",
                details=f"Турниру '{tournament.name}' назначен зал #{arena.number} ({arena.hall_name}).",
                actor_user_id=admin_user_id,
                tournament_id=tournament_id,
            )
        return TournamentHallAssignmentRead.model_validate(assignment)

    async def list_hall_assignments(self) -> list[TournamentHallAssignmentRead]:
        """Возвращает все назначения залов по турнирам."""
        if self._tournament_hall_assignment_repository is None:
            raise RuntimeError("Сервис распределения залов не настроен.")
        assignments = await self._tournament_hall_assignment_repository.list_all()
        return [TournamentHallAssignmentRead.model_validate(item) for item in assignments]

    async def submit_application(
        self,
        user_id: int,
        tournament_id: int,
        team_name: str | None = None,
    ) -> TournamentApplicationRead:
        """Процесс 4: подача игроком заявки на участие."""
        if self._tournament_application_repository is None or self._user_repository is None:
            raise RuntimeError("Сервис заявок не настроен.")

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise LookupError("Игрок не найден.")
        tournament = await self._tournament_repository.get_by_id(tournament_id)
        if tournament is None:
            raise LookupError("Турнир не найден.")
        if tournament.status == "closed":
            raise ValueError("Турнир уже закрыт, регистрация невозможна.")

        existing = await self._tournament_application_repository.get_by_user_and_tournament(user_id, tournament_id)
        if existing is not None:
            raise ValueError("Заявка на этот турнир уже существует.")

        normalized_team_name = (team_name or "").strip()
        team_id: int | None = None
        if normalized_team_name and self._team_repository is not None:
            team = await self._team_repository.get_or_create(name=normalized_team_name, captain_id=user_id)
            await self._team_repository.ensure_member(team_id=team.id, user_id=user_id)
            team_id = team.id

        entry_fee = Decimal(str(tournament.entry_fee or Decimal("0.00"))).quantize(Decimal("0.01"))
        user_balance = Decimal(str(user.balance))
        if entry_fee > Decimal("0.00"):
            if user_balance < entry_fee:
                raise ValueError("Недостаточно средств для оплаты турнирного взноса.")
            await self._user_repository.subtract_balance(user=user, amount=entry_fee)

        application = await self._tournament_application_repository.create(
            user_id=user_id,
            tournament_id=tournament_id,
            team_id=team_id,
            entry_fee_charged=entry_fee,
        )
        if self._archive_event_repository is not None:
            team_part = f", команда '{normalized_team_name}'" if normalized_team_name else ""
            await self._archive_event_repository.create(
                event_type="APPLICATION_SUBMITTED",
                details=(
                    f"Игрок '{user.username}' подал заявку на турнир '{tournament.name}'"
                    f"{team_part}. Списан взнос: {entry_fee}."
                ),
                actor_user_id=user_id,
                tournament_id=tournament_id,
                application_id=application.id,
            )
        refreshed = await self._tournament_application_repository.get_by_id(application.id)
        if refreshed is None:
            raise LookupError("Заявка не найдена после создания.")
        return TournamentApplicationRead.model_validate(refreshed)

    async def review_application(
        self,
        application_id: int,
        admin_user_id: int,
        approve: bool,
        assigned_arena_id: int | None = None,
        admin_comment: str | None = None,
    ) -> TournamentApplicationRead:
        """Процесс 4: отслеживание и обработка заявок администратором."""
        if self._tournament_application_repository is None or self._user_repository is None:
            raise RuntimeError("Сервис заявок не настроен.")
        application = await self._tournament_application_repository.get_by_id(application_id)
        if application is None:
            raise LookupError("Заявка не найдена.")
        if application.status != "pending":
            raise ValueError("Заявка уже обработана.")

        if approve and assigned_arena_id is not None and self._arena_repository is not None:
            arena = await self._arena_repository.get_by_id(assigned_arena_id)
            if arena is None:
                raise LookupError("Компьютерный зал не найден.")

        reviewed = await self._tournament_application_repository.review(
            application=application,
            approved=approve,
            admin_id=admin_user_id,
            assigned_arena_id=assigned_arena_id if approve else None,
            admin_comment=admin_comment,
        )

        if not approve:
            charged = Decimal(str(reviewed.entry_fee_charged or Decimal("0.00"))).quantize(Decimal("0.01"))
            if charged > Decimal("0.00"):
                user = await self._user_repository.get_by_id(reviewed.user_id)
                if user is not None:
                    await self._user_repository.add_balance(user=user, amount=charged)

        if self._archive_event_repository is not None:
            status_text = "одобрена" if approve else "отклонена"
            await self._archive_event_repository.create(
                event_type="APPLICATION_REVIEWED",
                details=f"Заявка #{reviewed.id} ({reviewed.user_name}) {status_text}.",
                actor_user_id=admin_user_id,
                tournament_id=reviewed.tournament_id,
                application_id=reviewed.id,
            )
        refreshed = await self._tournament_application_repository.get_by_id(reviewed.id)
        if refreshed is None:
            raise LookupError("Заявка не найдена после обработки.")
        return TournamentApplicationRead.model_validate(refreshed)

    async def list_user_applications(self, user_id: int) -> list[TournamentApplicationRead]:
        """Возвращает заявки конкретного игрока."""
        if self._tournament_application_repository is None:
            raise RuntimeError("Сервис заявок не настроен.")
        items = await self._tournament_application_repository.list_by_user(user_id)
        return [TournamentApplicationRead.model_validate(item) for item in items]

    async def list_tournament_applications(self, tournament_id: int | None = None) -> list[TournamentApplicationRead]:
        """Возвращает заявки турнира или все pending-заявки."""
        if self._tournament_application_repository is None:
            raise RuntimeError("Сервис заявок не настроен.")
        if tournament_id is None:
            items = await self._tournament_application_repository.list_pending()
        else:
            items = await self._tournament_application_repository.list_by_tournament(tournament_id)
        return [TournamentApplicationRead.model_validate(item) for item in items]

    async def list_pending_applications(self) -> list[TournamentApplicationRead]:
        """Возвращает все ожидающие заявки."""
        return await self.list_tournament_applications(tournament_id=None)

    async def add_result_to_archive(
        self,
        tournament_id: int,
        result_text: str,
        admin_user_id: int,
        winner_team_id: int | None = None,
    ) -> ArchiveEventRead:
        """Процесс 5: ведение архива событий/результатов."""
        if self._archive_event_repository is None:
            raise RuntimeError("Сервис архива не настроен.")
        tournament = await self._tournament_repository.get_by_id(tournament_id)
        if tournament is None:
            raise LookupError("Турнир не найден.")

        winner_name: str | None = None
        if winner_team_id is not None and self._team_repository is not None:
            winner_team = await self._team_repository.get_by_id(winner_team_id)
            if winner_team is None:
                raise LookupError("Команда-победитель не найдена.")
            winner_name = winner_team.name

            prize_pool = Decimal(str(tournament.prize_pool or Decimal("0.00"))).quantize(Decimal("0.01"))
            if prize_pool > Decimal("0.00") and self._user_repository is not None:
                members = await self._team_repository.list_member_users(winner_team_id)
                if members:
                    reward = (prize_pool / Decimal(len(members))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    for member in members:
                        await self._user_repository.add_balance(user=member, amount=reward)
                    await self._archive_event_repository.create(
                        event_type="TEAM_REWARD_PAID",
                        details=(
                            f"Команда '{winner_name}' получила выплату {prize_pool}. "
                            f"Каждому участнику начислено {reward}."
                        ),
                        actor_user_id=admin_user_id,
                        tournament_id=tournament_id,
                    )

        winner_text = f" Победитель: {winner_name}." if winner_name else ""
        archive_item = await self._archive_event_repository.create(
            event_type="TOURNAMENT_RESULT",
            details=f"Турнир '{tournament.name}': {result_text}.{winner_text}".strip(),
            actor_user_id=admin_user_id,
            tournament_id=tournament_id,
        )
        if self._tournament_archive_repository is not None:
            await self._tournament_archive_repository.upsert(
                tournament_id=tournament_id,
                result_summary=result_text,
                winner_name=winner_name,
            )
        return ArchiveEventRead.model_validate(archive_item)

    async def edit_archive_event(
        self,
        event_id: int,
        event_type: str,
        details: str,
        admin_user_id: int,
    ) -> ArchiveEventRead:
        """Редактирует запись архива событий."""
        if self._archive_event_repository is None:
            raise RuntimeError("Сервис архива не настроен.")
        item = await self._archive_event_repository.get_by_id(event_id)
        if item is None:
            raise LookupError("Событие архива не найдено.")

        updated = await self._archive_event_repository.update(item=item, event_type=event_type, details=details)
        await self._archive_event_repository.create(
            event_type="ARCHIVE_EVENT_EDITED",
            details=f"Событие архива #{event_id} было отредактировано.",
            actor_user_id=admin_user_id,
            tournament_id=updated.tournament_id,
            application_id=updated.application_id,
        )
        return ArchiveEventRead.model_validate(updated)

    async def list_archive_events(self, limit: int = 50) -> list[ArchiveEventRead]:
        """Возвращает ленту архивных событий."""
        if self._archive_event_repository is None:
            raise RuntimeError("Сервис архива не настроен.")
        items = await self._archive_event_repository.list_recent(limit=limit)
        return [ArchiveEventRead.model_validate(item) for item in items]

    async def list_tournament_archive(self) -> list[TournamentArchiveRead]:
        """Возвращает архив турниров и результатов."""
        if self._tournament_archive_repository is None:
            raise RuntimeError("Сервис архива турниров не настроен.")
        items = await self._tournament_archive_repository.list_all()
        return [TournamentArchiveRead.model_validate(item) for item in items]

    async def register_user(self, user_id: int, tournament_id: int) -> TournamentApplicationRead:
        """Совместимость: старый метод регистрации -> теперь заявка."""
        return await self.submit_application(user_id=user_id, tournament_id=tournament_id)

    async def list_user_registrations(self, user_id: int) -> list[TournamentApplicationRead]:
        """Совместимость: старый метод получения регистраций -> заявки."""
        return await self.list_user_applications(user_id=user_id)
