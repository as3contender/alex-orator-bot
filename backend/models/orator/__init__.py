# Orator models package

# Base models
from .base import BaseEntity, BaseResponse, PaginationParams, PaginatedResponse

# Enums
from .enums import Gender, WeekType, RegistrationStatus, PairStatus, FeedbackRating

# User models
from .users import UserProfile, UserProfileUpdate, UserStats, User, UserResponse, TokenResponse

# Week registration models
from .weeks import (
    WeekRegistration, WeekRegistrationCreate, WeekRegistrationUpdate, WeekRegistrationResponse, WeekInfo
)

# Topic models
from .topics import TopicNode, UserTopic, UserTopicCreate, TopicTree

# Pair models
from .pairs import UserPair, UserPairResponse, PairConfirmation

# Feedback models
from .feedback import SessionFeedback, SessionFeedbackCreate, SessionFeedbackResponse

# Content models
from .content import BotContent, BotContentCreate, BotContentUpdate

# Matching models
from .matching import CandidateInfo, MatchRequest, MatchResponse

# Settings models
from .settings import OratorSettings, OratorSettingsUpdate, OratorSettingKeys
