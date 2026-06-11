"""
Pydantic schemas for API validation and serialization
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator
from enum import Enum


# Enums
class UserRole(str, Enum):
    CHILD = "child"
    PARENT = "parent"
    ADMIN = "admin"


class LessonStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class GameType(str, Enum):
    MATCHING = "matching"
    MEMORY = "memory"
    SPELLING = "spelling"
    QUIZ = "quiz"
    SENTENCE_BUILDER = "sentence_builder"
    PICTURE_QUIZ = "picture_quiz"
    WORD_SEARCH = "word_search"


class AchievementCategory(str, Enum):
    LEARNING = "learning"
    STREAK = "streak"
    SOCIAL = "social"
    MASTERY = "mastery"


class TestType(str, Enum):
    PLACEMENT = "placement"
    LESSON = "lesson"
    FINAL = "final"


# Base schemas
class BaseResponse(BaseModel):
    """Base response schema"""
    class Config:
        from_attributes = True


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    language_preference: str = Field(default="ru", max_length=10)


class ChildCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    date_of_birth: Optional[date] = None
    parent_email: EmailStr  # Required for COPPA compliance
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_age(cls, v):
        if v:
            from datetime import date as date_type
            age = (date_type.today() - v).days // 365
            if age < 5 or age > 12:
                raise ValueError('Child must be between 5 and 12 years old')
        return v


class ParentCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    language_preference: str = Field(default="ru", max_length=10)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseResponse):
    id: uuid.UUID
    username: str
    email: Optional[str]
    role: UserRole
    avatar_url: Optional[str]
    date_of_birth: Optional[date]
    language_preference: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    role: str


# Category schemas
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    name_en: str = Field(..., max_length=100)
    description: Optional[str] = None
    icon_url: Optional[str] = None
    color: str = Field(default="#4CAF50", pattern="^#[0-9A-Fa-f]{6}$")


class CategoryCreate(CategoryBase):
    order_index: int = 0


class CategoryResponse(CategoryBase):
    id: uuid.UUID
    order_index: int
    is_active: bool


class CategoryWithLessons(CategoryResponse):
    lessons: List["LessonResponse"] = []


# Lesson schemas
class LessonBase(BaseModel):
    title: str = Field(..., max_length=200)
    title_en: str = Field(..., max_length=200)
    description: Optional[str] = None
    difficulty_level: int = Field(default=1, ge=1, le=5)
    estimated_minutes: int = Field(default=15, ge=5, le=60)
    xp_reward: int = Field(default=100, ge=0)


class LessonCreate(LessonBase):
    category_id: Optional[uuid.UUID] = None
    order_index: int = 0


class LessonResponse(LessonBase):
    id: uuid.UUID
    category_id: Optional[uuid.UUID]
    order_index: int
    is_active: bool
    created_at: datetime


class LessonWithVocabulary(LessonResponse):
    vocabulary_items: List["VocabularyItemResponse"] = []
    user_progress: Optional["UserProgressResponse"] = None


class LessonProgress(BaseModel):
    lesson_id: uuid.UUID
    status: LessonStatus
    score: int
    time_spent_seconds: int


# Vocabulary schemas
class VocabularyItemBase(BaseModel):
    word: str = Field(..., max_length=100)
    translation: str = Field(..., max_length=200)
    pronunciation: Optional[str] = None
    example_sentence: Optional[str] = None
    example_translation: Optional[str] = None
    difficulty_level: int = Field(default=1, ge=1, le=5)


class VocabularyItemCreate(VocabularyItemBase):
    lesson_id: Optional[uuid.UUID] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None


class VocabularyItemResponse(VocabularyItemBase):
    id: uuid.UUID
    lesson_id: Optional[uuid.UUID]
    image_url: Optional[str]
    audio_url: Optional[str]
    created_at: datetime


class VocabularyItemWithProgress(VocabularyItemResponse):
    progress: Optional["VocabularyProgressResponse"] = None


# Progress schemas
class UserProgressBase(BaseModel):
    status: LessonStatus = LessonStatus.NOT_STARTED
    score: int = Field(default=0, ge=0)
    time_spent_seconds: int = Field(default=0, ge=0)


class UserProgressResponse(UserProgressBase):
    id: uuid.UUID
    user_id: uuid.UUID
    lesson_id: uuid.UUID
    attempts: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    last_accessed: datetime


class VocabularyProgressResponse(BaseModel):
    id: uuid.UUID
    vocabulary_id: uuid.UUID
    mastery_level: int
    ease_factor: float
    interval_days: int
    repetitions: int
    next_review_date: date
    last_review_date: Optional[date]
    correct_count: int
    incorrect_count: int


class StartLessonRequest(BaseModel):
    lesson_id: uuid.UUID


class CompleteLessonRequest(BaseModel):
    lesson_id: uuid.UUID
    score: int = Field(..., ge=0, le=100)
    time_spent_seconds: int = Field(..., ge=0)
    vocabulary_results: List[Dict[str, Any]] = []


# Game schemas
class GameBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    game_type: GameType


class GameCreate(GameBase):
    difficulty_levels: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


class GameResponse(GameBase):
    id: uuid.UUID
    difficulty_levels: Optional[Dict[str, Any]]
    config: Optional[Dict[str, Any]]
    is_active: bool


class StartGameRequest(BaseModel):
    game_id: uuid.UUID
    lesson_id: Optional[uuid.UUID] = None
    difficulty_level: int = Field(default=1, ge=1, le=5)


class FinishGameRequest(BaseModel):
    session_id: uuid.UUID
    score: int
    correct_answers: int
    total_questions: int
    time_spent_seconds: int


class GameSessionResponse(BaseModel):
    id: uuid.UUID
    game_id: uuid.UUID
    lesson_id: Optional[uuid.UUID]
    score: int
    max_score: Optional[int]
    time_spent_seconds: Optional[int]
    correct_answers: int
    total_questions: int
    difficulty_level: int
    played_at: datetime


# Achievement schemas
class AchievementBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    category: AchievementCategory
    requirement_type: str
    requirement_value: int
    xp_bonus: int = 0


class AchievementCreate(AchievementBase):
    icon_url: Optional[str] = None


class AchievementResponse(AchievementBase):
    id: uuid.UUID
    icon_url: Optional[str]
    is_active: bool


class UserAchievementResponse(BaseModel):
    id: uuid.UUID
    achievement: AchievementResponse
    unlocked_at: datetime


# Streak and Daily Goal schemas
class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[date]


class DailyGoalResponse(BaseModel):
    id: uuid.UUID
    goal_date: date
    lessons_target: int
    lessons_completed: int
    words_target: int
    words_learned: int
    minutes_target: int
    minutes_spent: int
    xp_earned: int
    is_completed: bool


class DailyGoalProgress(BaseModel):
    lessons_progress: float
    words_progress: float
    minutes_progress: float
    is_completed: bool


# Test schemas
class TestBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    test_type: TestType
    difficulty_level: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    passing_score: int = Field(default=70, ge=0, le=100)


class QuestionOption(BaseModel):
    id: str
    text: str
    is_correct: bool = False


class Question(BaseModel):
    id: str
    type: str  # multiple_choice, fill_blank, matching, etc.
    question: str
    options: Optional[List[QuestionOption]] = None
    correct_answer: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    points: int = 1


class TestCreate(TestBase):
    questions: List[Question]


class TestResponse(TestBase):
    id: uuid.UUID
    is_active: bool


class TestWithQuestions(TestResponse):
    questions: List[Question]


class SubmitTestRequest(BaseModel):
    test_id: uuid.UUID
    answers: List[Dict[str, Any]]
    time_spent_seconds: int


class TestResultResponse(BaseModel):
    id: uuid.UUID
    test_id: uuid.UUID
    score: Optional[int]
    total_questions: Optional[int]
    correct_answers: Optional[int]
    time_spent_seconds: Optional[int]
    completed_at: datetime
    passed: bool


# Parent Dashboard schemas
class ChildProgressSummary(BaseModel):
    child_id: uuid.UUID
    username: str
    avatar_url: Optional[str]
    total_xp: int
    current_streak: int
    lessons_completed: int
    words_learned: int
    time_spent_minutes: int
    last_activity: Optional[datetime]
    achievements_count: int


class WeeklyReport(BaseModel):
    child_id: uuid.UUID
    week_start: date
    week_end: date
    lessons_completed: int
    words_learned: int
    time_spent_minutes: int
    average_score: float
    achievements_unlocked: List[AchievementResponse]
    daily_activity: List[Dict[str, Any]]


class ParentSettingsUpdate(BaseModel):
    daily_time_limit_minutes: Optional[int] = Field(None, ge=15, le=180)
    weekly_reports_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    content_restrictions: Optional[Dict[str, Any]] = None


class ParentSettingsResponse(BaseModel):
    daily_time_limit_minutes: int
    weekly_reports_enabled: bool
    email_notifications: bool
    push_notifications: bool
    content_restrictions: Optional[Dict[str, Any]]


# Spaced Repetition schemas
class ReviewItem(BaseModel):
    vocabulary_id: uuid.UUID
    word: str
    translation: str
    image_url: Optional[str]
    audio_url: Optional[str]
    mastery_level: int


class SubmitReviewRequest(BaseModel):
    vocabulary_id: uuid.UUID
    quality: int = Field(..., ge=0, le=5)  # 0-5 scale for SM-2 algorithm


class ReviewStats(BaseModel):
    total_due: int
    total_learned: int
    mastered: int
    learning: int
    new: int


# Dashboard schemas
class DashboardStats(BaseModel):
    total_xp: int
    level: int
    xp_to_next_level: int
    current_streak: int
    lessons_completed: int
    words_learned: int
    achievements_unlocked: int
    daily_goal_progress: DailyGoalProgress


class ActivityLogResponse(BaseModel):
    id: uuid.UUID
    activity_type: str
    activity_data: Optional[Dict[str, Any]]
    duration_seconds: Optional[int]
    created_at: datetime


# Reward schemas
class RewardResponse(BaseModel):
    id: uuid.UUID
    reward_type: str
    reward_data: Optional[Dict[str, Any]]
    earned_at: datetime


# Leaderboard schemas
class LeaderboardEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    username: str
    avatar_url: Optional[str]
    xp: int
    streak: int


class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    user_rank: Optional[int]
    timeframe: str  # daily, weekly, all-time


# Update forward references
CategoryWithLessons.model_rebuild()
LessonWithVocabulary.model_rebuild()
VocabularyItemWithProgress.model_rebuild()
