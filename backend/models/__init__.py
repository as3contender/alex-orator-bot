# Models package

# Base models
from .base import BaseResponse, BaseEntity, PaginationParams, PaginatedResponse

# Auth models
from .auth import UserLogin, UserCreate, UserResponse, TokenResponse, User

# Orator bot models - import from new structure
from .orator import (
    # Base
    BaseEntity,
    BaseResponse,
    PaginationParams,
    PaginatedResponse,
    # Enums
    Gender,
    WeekType,
    RegistrationStatus,
    PairStatus,
    FeedbackRating,
    # Users
    User,
    UserResponse,
    TokenResponse,
    UserProfile,
    UserProfileUpdate,
    UserStats,
    # Weeks
    WeekRegistration,
    WeekRegistrationCreate,
    WeekRegistrationResponse,
    WeekInfo,
    # Topics
    TopicNode,
    UserTopic,
    UserTopicCreate,
    TopicTree,
    # Pairs
    UserPair,
    UserPairResponse,
    PairConfirmation,
    # Feedback
    SessionFeedback,
    SessionFeedbackCreate,
    SessionFeedbackResponse,
    # Content
    BotContent,
    BotContentCreate,
    BotContentUpdate,
    # Matching
    CandidateInfo,
    MatchRequest,
    MatchResponse,
)
