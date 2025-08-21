import random
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from uuid import UUID
from loguru import logger

from models.orator import CandidateInfo, Gender
from services.orator_database import OratorDatabaseService


class MatchingService:
    def __init__(self, orator_db: OratorDatabaseService):
        self.orator_db = orator_db

    async def find_candidates(
        self, user_id: UUID, week_start: date, limit: int = None, max_pairs_per_user: int = None
    ) -> List[CandidateInfo]:
        """Найти кандидатов для подбора пары"""
        try:
            # Получаем настройки, если не переданы
            if limit is None:
                limit = await self.orator_db.get_setting_int("max_candidates_per_request", 3)
            if max_pairs_per_user is None:
                max_pairs_per_user = await self.orator_db.get_setting_int("max_pairs_per_user", 3)

            # Получаем информацию о пользователе
            user_info = await self._get_user_info(user_id, week_start)
            if not user_info:
                return []

            # Получаем всех активных пользователей на эту неделю
            all_candidates = await self._get_active_candidates(
                week_start, exclude_user_id=user_id, max_pairs_per_user=max_pairs_per_user
            )

            if not all_candidates:
                logger.info(f"No candidates found for user {user_id} on week {week_start}")
                return []

            logger.info(f"Found {len(all_candidates)} initial candidates for user {user_id}")

            # Рассчитываем score для каждого кандидата
            scored_candidates = []
            for candidate in all_candidates:
                score = await self._calculate_match_score(user_info, candidate)
                candidate_info = CandidateInfo(
                    user_id=str(candidate["user_id"]),
                    name=candidate["name"],
                    gender=candidate.get("gender"),
                    total_sessions=candidate["total_sessions"],
                    preferred_time_msk=candidate["preferred_time_msk"],
                    selected_topics=candidate["topics"],
                    match_score=score,
                )
                scored_candidates.append(candidate_info)

            # Сортируем по score и возвращаем топ кандидатов
            scored_candidates.sort(key=lambda x: x.match_score, reverse=True)

            # Добавляем элемент случайности для топ кандидатов
            top_candidates = scored_candidates[: min(limit * 2, len(scored_candidates))]
            selected_candidates = self._add_randomness(top_candidates, limit)

            logger.info(f"Found {len(selected_candidates)} candidates for user {user_id}")
            return selected_candidates

        except Exception as e:
            logger.error(f"Error finding candidates for user {user_id}: {e}")
            return []

    async def _get_user_info(self, user_id: UUID, week_start: date) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе для матчинга"""
        try:
            # Получаем профиль пользователя
            profile = await self.orator_db.get_user_profile(user_id)
            if not profile:
                return None

            # Получаем регистрацию на неделю
            registration = await self.orator_db.get_user_week_registration(user_id, week_start)
            if not registration:
                return None

            # Получаем выбранные темы
            topics = await self.orator_db.get_user_topics(registration["id"])

            return {
                "user_id": user_id,
                "name": f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
                "gender": profile.get("gender"),
                "total_sessions": profile.get("total_sessions", 0),
                "preferred_time_msk": registration["preferred_time_msk"],
                "topics": topics,
                "registration_id": registration["id"],
            }

        except Exception as e:
            logger.error(f"Error getting user info for {user_id}: {e}")
            return None

    async def _get_active_candidates(
        self, week_start: date, exclude_user_id: UUID, max_pairs_per_user: int = 3
    ) -> List[Dict[str, Any]]:
        """Получить всех активных кандидатов на неделю"""
        try:
            async with self.orator_db.pool.acquire() as conn:
                # Получаем пользователей с активными регистрациями, исключая тех, у кого уже max_pairs_per_user+ пар
                # И исключая тех, с кем уже есть пара в статусе pending или confirmed
                rows = await conn.fetch(
                    """
                    SELECT 
                        u.id as user_id,
                        u.first_name, u.last_name, u.gender,
                        u.total_sessions,
                        wr.preferred_time_msk,
                        wr.id as registration_id
                    FROM users u
                    JOIN week_registrations wr ON u.id = wr.user_id
                    WHERE wr.week_start_date = $1 
                    AND wr.status = 'active'
                    AND u.id != $2
                    AND u.is_active = TRUE
                    AND (
                        SELECT COUNT(*)
                        FROM user_pairs up2
                        JOIN week_registrations wr2 ON up2.week_registration_id = wr2.id
                        WHERE (up2.user1_id = u.id OR up2.user2_id = u.id)
                        AND wr2.week_start_date = $1
                        AND up2.status IN ('pending', 'confirmed')
                    ) < $3
                    AND NOT EXISTS (
                        SELECT 1
                        FROM user_pairs up3
                        JOIN week_registrations wr3 ON up3.week_registration_id = wr3.id
                        WHERE wr3.week_start_date = $1
                        AND up3.status IN ('pending', 'confirmed')
                        AND (
                            (up3.user1_id = $2 AND up3.user2_id = u.id)
                            OR (up3.user1_id = u.id AND up3.user2_id = $2)
                        )
                    )
                    """,
                    week_start,
                    exclude_user_id,
                    max_pairs_per_user,
                )

                candidates = []
                for row in rows:
                    # Получаем темы для каждого кандидата
                    topics = await self.orator_db.get_user_topics(row["registration_id"])

                    candidate = {
                        "user_id": row["user_id"],
                        "name": f"{row['first_name'] or ''} {row['last_name'] or ''}".strip(),
                        "gender": row["gender"],
                        "total_sessions": row["total_sessions"],
                        "preferred_time_msk": row["preferred_time_msk"],
                        "topics": topics,
                        "registration_id": row["registration_id"],
                    }
                    candidates.append(candidate)

                return candidates

        except Exception as e:
            logger.error(f"Error getting active candidates: {e}")
            return []

    async def _calculate_match_score(self, user_info: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        """Рассчитать score совместимости между пользователями"""
        score = 0.0

        # 1. Временное совпадение (вес: 0.4)
        time_score = self._calculate_time_compatibility(
            user_info["preferred_time_msk"], candidate["preferred_time_msk"]
        )
        score += time_score * 0.4

        # 2. Совпадение тем (вес: 0.3)
        topic_score = self._calculate_topic_overlap(user_info["topics"], candidate["topics"])
        score += topic_score * 0.3

        # 3. Совместимость по опыту (вес: 0.2)
        experience_score = self._calculate_experience_compatibility(
            user_info["total_sessions"], candidate["total_sessions"]
        )
        score += experience_score * 0.2

        # 4. Дополнительные факторы (вес: 0.1)
        bonus_score = self._calculate_bonus_factors(user_info, candidate)
        score += bonus_score * 0.1

        return min(score, 1.0)  # Ограничиваем максимальным значением 1.0

    def _calculate_time_compatibility(self, time1: str, time2: str) -> float:
        """Рассчитать совместимость по времени"""
        try:
            # Парсим время в минуты от начала дня
            def time_to_minutes(time_str: str) -> int:
                hours, minutes = map(int, time_str.split(":"))
                return hours * 60 + minutes

            minutes1 = time_to_minutes(time1)
            minutes2 = time_to_minutes(time2)

            # Разница во времени в минутах
            time_diff = abs(minutes1 - minutes2)

            # Если разница меньше 30 минут - отличная совместимость
            if time_diff <= 30:
                return 1.0
            # Если разница меньше 2 часов - хорошая совместимость
            elif time_diff <= 120:
                return 0.7
            # Если разница меньше 4 часов - средняя совместимость
            elif time_diff <= 240:
                return 0.4
            # Большая разница - низкая совместимость
            else:
                return 0.1

        except Exception as e:
            logger.error(f"Error calculating time compatibility: {e}")
            return 0.5  # Нейтральный score при ошибке

    def _calculate_topic_overlap(self, topics1: List[str], topics2: List[str]) -> float:
        """Рассчитать совпадение тем с учетом иерархии"""
        if not topics1 or not topics2:
            return 0.0

        # Находим точное пересечение тем
        common_topics = set(topics1) & set(topics2)

        # Находим совпадения по родительским группам
        parent_matches = self._find_parent_topic_matches(topics1, topics2)

        # Рассчитываем общий score
        exact_match_score = (
            len(common_topics) / max(len(topics1), len(topics2)) if max(len(topics1), len(topics2)) > 0 else 0.0
        )

        # Улучшенный расчет score по родительским группам
        # Учитываем не только количество совпадений, но и их качество
        parent_match_score = 0.0
        if parent_matches > 0:
            # Нормализуем по количеству уникальных групп
            unique_groups1 = len(set(self._extract_parent_group(t) for t in topics1 if self._extract_parent_group(t)))
            unique_groups2 = len(set(self._extract_parent_group(t) for t in topics2 if self._extract_parent_group(t)))
            max_unique_groups = max(unique_groups1, unique_groups2)

            if max_unique_groups > 0:
                parent_match_score = parent_matches / max_unique_groups

        # Взвешенная сумма: точные совпадения важнее родительских
        total_score = (exact_match_score * 0.7) + (parent_match_score * 0.3)

        # Бонус за точное совпадение всех тем
        if len(common_topics) == len(topics1) == len(topics2):
            total_score += 0.2

        # Бонус за совпадение по родительским группам (если нет точных совпадений)
        elif len(common_topics) == 0 and parent_matches > 0:
            total_score += 0.1

        return min(total_score, 1.0)

    def _find_parent_topic_matches(self, topics1: List[str], topics2: List[str]) -> int:
        """Найти количество совпадений по родительским группам тем"""
        if not topics1 or not topics2:
            return 0

        # Извлекаем родительские группы из тем
        parent_groups1 = set()
        parent_groups2 = set()

        for topic in topics1:
            parent = self._extract_parent_group(topic)
            if parent:
                parent_groups1.add(parent)

        for topic in topics2:
            parent = self._extract_parent_group(topic)
            if parent:
                parent_groups2.add(parent)

        # Находим пересечение родительских групп
        common_parents = parent_groups1 & parent_groups2

        return len(common_parents)

    def _extract_parent_group(self, topic_path: str) -> Optional[str]:
        """Извлечь родительскую группу из пути темы"""
        if not topic_path:
            return None

        # Разбиваем путь по разделителям
        parts = topic_path.split(" - ")

        # Возвращаем первую часть как родительскую группу
        if len(parts) >= 1:
            return parts[0].strip()

        return None

    def _calculate_experience_compatibility(self, sessions1: int, sessions2: int) -> float:
        """Рассчитать совместимость по опыту"""
        # Разница в количестве сессий
        experience_diff = abs(sessions1 - sessions2)

        # Если разница небольшая - хорошая совместимость
        if experience_diff <= 2:
            return 1.0
        elif experience_diff <= 5:
            return 0.8
        elif experience_diff <= 10:
            return 0.6
        else:
            return 0.3

    def _calculate_bonus_factors(self, user_info: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        """Рассчитать дополнительные факторы совместимости"""
        bonus = 0.0

        # Бонус за разный пол (если указан)
        if user_info.get("gender") and candidate.get("gender") and user_info["gender"] != candidate["gender"]:
            bonus += 0.1

        # Бонус за активность (больше сессий = больше опыта)
        if candidate["total_sessions"] > 5:
            bonus += 0.05

        # Бонус за разнообразие тем
        if len(candidate["topics"]) > 1:
            bonus += 0.05

        return min(bonus, 0.2)  # Ограничиваем бонус

    def _add_randomness(self, candidates: List[CandidateInfo], limit: int) -> List[CandidateInfo]:
        """Добавить элемент случайности в выбор кандидатов"""
        if len(candidates) <= limit:
            return candidates

        # Берем топ кандидатов, но добавляем случайность
        top_candidates = candidates[: limit * 2]

        # Сортируем по score, но с небольшим элементом случайности
        def random_score(candidate: CandidateInfo) -> float:
            # Добавляем случайность ±10% к score
            random_factor = random.uniform(0.9, 1.1)
            return candidate.match_score * random_factor

        # Сортируем с учетом случайности
        randomized_candidates = sorted(top_candidates, key=random_score, reverse=True)

        return randomized_candidates[:limit]

    async def get_candidate_stats(self, week_start: date) -> Dict[str, Any]:
        """Получить статистику по кандидатам на неделю"""
        try:
            async with self.orator_db.pool.acquire() as conn:
                # Общее количество активных регистраций
                total_registrations = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM week_registrations
                    WHERE week_start_date = $1 AND status = 'active'
                    """,
                    week_start,
                )

                # Количество созданных пар
                total_pairs = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM user_pairs up
                    JOIN week_registrations wr ON up.week_registration_id = wr.id
                    WHERE wr.week_start_date = $1
                    """,
                    week_start,
                )

                # Количество подтвержденных пар
                confirmed_pairs = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM user_pairs up
                    JOIN week_registrations wr ON up.week_registration_id = wr.id
                    WHERE wr.week_start_date = $1 AND up.status = 'confirmed'
                    """,
                    week_start,
                )

                return {
                    "total_registrations": total_registrations,
                    "total_pairs": total_pairs,
                    "confirmed_pairs": confirmed_pairs,
                    "confirmation_rate": (confirmed_pairs / total_pairs * 100) if total_pairs > 0 else 0,
                }

        except Exception as e:
            logger.error(f"Error getting candidate stats: {e}")
            return {"total_registrations": 0, "total_pairs": 0, "confirmed_pairs": 0, "confirmation_rate": 0}

    async def check_existing_pairs(self, user_id: UUID, week_start: date) -> List[Dict[str, Any]]:
        """Проверить существующие пары пользователя на неделю"""
        try:
            async with self.orator_db.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT 
                        up.id as pair_id,
                        up.status,
                        up.created_at,
                        CASE 
                            WHEN up.user1_id = $1 THEN up.user2_id
                            ELSE up.user1_id
                        END as partner_id,
                        u.first_name || ' ' || COALESCE(u.last_name, '') as partner_name
                    FROM user_pairs up
                    JOIN week_registrations wr ON up.week_registration_id = wr.id
                    JOIN users u ON (
                        CASE 
                            WHEN up.user1_id = $1 THEN up.user2_id
                            ELSE up.user1_id
                        END = u.id
                    )
                    WHERE wr.week_start_date = $2
                    AND (up.user1_id = $1 OR up.user2_id = $1)
                    AND up.status IN ('pending', 'confirmed')
                    ORDER BY up.created_at DESC
                    """,
                    user_id,
                    week_start,
                )

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error checking existing pairs for user {user_id}: {e}")
            return []


# Создаем экземпляр сервиса
from .orator_database import orator_db

matching_service = MatchingService(orator_db)
