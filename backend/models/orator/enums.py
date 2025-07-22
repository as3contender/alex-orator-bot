from enum import Enum


class Gender(str, Enum):
    """Пол пользователя"""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class WeekType(str, Enum):
    """Тип недели для регистрации"""

    CURRENT = "current"
    NEXT = "next"


class RegistrationStatus(str, Enum):
    """Статус регистрации на неделю"""

    ACTIVE = "active"
    CANCELLED = "cancelled"


class PairStatus(str, Enum):
    """Статус пары пользователей"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class FeedbackRating(int, Enum):
    """Рейтинг обратной связи"""

    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
